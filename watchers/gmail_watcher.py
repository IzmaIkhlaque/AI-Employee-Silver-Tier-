"""Gmail Watcher - Monitors Gmail for unread important emails."""

import argparse
import base64
import json
import re
import time
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from base_watcher import BaseWatcher

# Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Priority classification keywords
PRIORITY_KEYWORDS = {
    "critical": ["urgent", "emergency", "asap", "immediately"],
    "high": ["important", "deadline", "payment", "invoice"],
    "medium": ["question", "update", "follow-up", "meeting"],
}

# Priority emoji mapping
PRIORITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}


class GmailWatcher(BaseWatcher):
    """Watches Gmail for unread important emails and creates action files."""

    def __init__(
        self,
        vault_path: Path,
        credentials_path: Path,
        dry_run: bool = False,
        check_interval: int = 120,
    ):
        super().__init__(dry_run=dry_run)
        self.vault_path = Path(vault_path)
        self.credentials_path = Path(credentials_path)
        self.check_interval = check_interval
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.memory_path = self.vault_path / "memory"
        self.processed_ids_file = self.memory_path / "gmail_processed_ids.json"
        self.token_path = self.vault_path / "config" / "token.json"

        # Ensure directories exist
        self.needs_action_path.mkdir(parents=True, exist_ok=True)
        self.memory_path.mkdir(parents=True, exist_ok=True)

        # Load processed IDs
        self.processed_ids = self._load_processed_ids()

        # Initialize Gmail service
        self.service = None

    def _load_processed_ids(self) -> set:
        """Load previously processed email IDs from disk."""
        if self.processed_ids_file.exists():
            try:
                with open(self.processed_ids_file, "r") as f:
                    data = json.load(f)
                    return set(data.get("processed_ids", []))
            except (json.JSONDecodeError, IOError) as e:
                print(f"[GmailWatcher] Warning: Could not load processed IDs: {e}")
        return set()

    def _save_processed_ids(self):
        """Save processed email IDs to disk."""
        try:
            with open(self.processed_ids_file, "w") as f:
                json.dump(
                    {
                        "processed_ids": list(self.processed_ids),
                        "last_updated": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )
        except IOError as e:
            print(f"[GmailWatcher] Warning: Could not save processed IDs: {e}")

    def _authenticate(self) -> Credentials:
        """Authenticate with Gmail API using OAuth 2.0."""
        creds = None

        # Check for existing token
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
            except Exception as e:
                print(f"[GmailWatcher] Could not load token: {e}")

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("[GmailWatcher] Refreshing expired token...")
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"[GmailWatcher] Token refresh failed: {e}")
                    creds = None

            if not creds:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}\n"
                        "Run /gmail-setup skill for setup instructions."
                    )

                print("[GmailWatcher] Starting OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for future runs
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
            print(f"[GmailWatcher] Token saved to {self.token_path}")

        return creds

    def _init_service(self):
        """Initialize the Gmail API service."""
        if self.service is None:
            creds = self._authenticate()
            self.service = build("gmail", "v1", credentials=creds)
            print("[GmailWatcher] Gmail API service initialized")

    def _classify_priority(self, subject: str, body: str) -> str:
        """Classify email priority based on keywords."""
        text = f"{subject} {body}".lower()

        for priority, keywords in PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return priority

        return "low"

    def _parse_email(self, message: dict) -> dict:
        """Parse Gmail message into structured data."""
        headers = message.get("payload", {}).get("headers", [])
        header_dict = {h["name"].lower(): h["value"] for h in headers}

        # Extract sender
        sender = header_dict.get("from", "Unknown")

        # Extract subject
        subject = header_dict.get("subject", "No Subject")

        # Extract date
        date_str = header_dict.get("date", "")

        # Extract body/snippet
        body = message.get("snippet", "")

        # Try to get full body text
        payload = message.get("payload", {})
        parts = payload.get("parts", [])

        if parts:
            for part in parts:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        try:
                            body = base64.urlsafe_b64decode(data).decode("utf-8")
                        except Exception:
                            pass
                        break
        elif payload.get("body", {}).get("data"):
            try:
                body = base64.urlsafe_b64decode(
                    payload["body"]["data"]
                ).decode("utf-8")
            except Exception:
                pass

        # Truncate long bodies
        if len(body) > 3000:
            body = body[:3000] + "\n\n... [truncated]"

        # Clean up body text
        body = body.strip()

        return {
            "id": message["id"],
            "sender": sender,
            "subject": subject,
            "date": date_str,
            "body": body,
        }

    def check_for_updates(self) -> list:
        """Check Gmail for unread important emails."""
        self._init_service()

        try:
            # Query for unread important emails
            results = self.service.users().messages().list(
                userId="me",
                q="is:unread is:important",
                maxResults=20,
            ).execute()

            messages = results.get("messages", [])

            if not messages:
                return []

            new_emails = []

            for msg_ref in messages:
                msg_id = msg_ref["id"]

                # Skip already processed
                if msg_id in self.processed_ids:
                    continue

                # Fetch full message
                message = self.service.users().messages().get(
                    userId="me",
                    id=msg_id,
                    format="full",
                ).execute()

                email_data = self._parse_email(message)
                email_data["priority"] = self._classify_priority(
                    email_data["subject"],
                    email_data["body"],
                )

                new_emails.append(email_data)
                print(
                    f"[GmailWatcher] New email: {email_data['subject'][:50]}... "
                    f"({PRIORITY_EMOJI[email_data['priority']]} {email_data['priority']})"
                )

            return new_emails

        except Exception as e:
            print(f"[GmailWatcher] Error checking emails: {e}")
            return []

    def create_action_file(self, item: dict) -> Path:
        """Create an action file in /Needs_Action for the email."""
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")

        # Sanitize subject for filename
        safe_subject = re.sub(r"[^\w\s-]", "", item["subject"])
        safe_subject = re.sub(r"\s+", "_", safe_subject)[:30].strip("_").lower()

        filename = f"EMAIL_{safe_subject}_{timestamp}.md"
        filepath = self.needs_action_path / filename

        priority_emoji = PRIORITY_EMOJI.get(item["priority"], "🟢")

        content = f"""---
type: email
id: {item['id']}
from: {item['sender']}
subject: {item['subject']}
date: {item['date']}
received: {now.isoformat()}
priority: {priority_emoji} {item['priority']}
status: pending
---

# Email: {item['subject']}

## From

{item['sender']}

## Content

{item['body']}

## Suggested Actions

- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
"""

        if self.dry_run:
            print(f"[GmailWatcher] DRY RUN - Would create: {filepath}")
            print(f"  Subject: {item['subject']}")
            print(f"  From: {item['sender']}")
            print(f"  Priority: {priority_emoji} {item['priority']}")
        else:
            filepath.write_text(content, encoding="utf-8")
            print(f"[GmailWatcher] Created: {filepath.name}")

        # Mark as processed
        self.processed_ids.add(item["id"])
        self._save_processed_ids()

        return filepath

    def run(self):
        """Main loop with custom check interval."""
        self.running = True
        print(f"[GmailWatcher] Starting watcher...")
        print(f"[GmailWatcher] Check interval: {self.check_interval}s")
        print(f"[GmailWatcher] Vault path: {self.vault_path}")
        print(f"[GmailWatcher] Dry run: {self.dry_run}")
        print(f"[GmailWatcher] Previously processed: {len(self.processed_ids)} emails")

        while self.running:
            try:
                print(f"\n[GmailWatcher] Checking for new emails... ({datetime.now().strftime('%H:%M:%S')})")
                items = self.check_for_updates()

                if items:
                    print(f"[GmailWatcher] Found {len(items)} new email(s)")
                    for item in items:
                        self.create_action_file(item)
                else:
                    print("[GmailWatcher] No new emails")

                # Wait for next check
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                print(f"\n[GmailWatcher] Stopping watcher...")
                self.running = False
                break
            except Exception as e:
                print(f"[GmailWatcher] Error: {e}")
                time.sleep(30)  # Wait before retry on error


def main():
    parser = argparse.ArgumentParser(
        description="Gmail Watcher - Monitor Gmail for unread important emails"
    )
    parser.add_argument(
        "--vault-path",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Path to the vault directory (default: parent of watchers/)",
    )
    parser.add_argument(
        "--credentials",
        type=Path,
        default=None,
        help="Path to credentials.json (default: config/credentials.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without creating files",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=120,
        help="Check interval in seconds (default: 120)",
    )

    args = parser.parse_args()

    # Resolve paths
    vault_path = args.vault_path.resolve()
    credentials_path = args.credentials or (vault_path / "config" / "credentials.json")

    print("=" * 50)
    print("Gmail Watcher for AI Employee")
    print("=" * 50)

    watcher = GmailWatcher(
        vault_path=vault_path,
        credentials_path=credentials_path,
        dry_run=args.dry_run,
        check_interval=args.interval,
    )

    watcher.run()


if __name__ == "__main__":
    main()
