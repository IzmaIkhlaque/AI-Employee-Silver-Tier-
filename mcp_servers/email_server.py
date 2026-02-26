#!/usr/bin/env python3
"""
Email MCP Server for AI Employee

A FastMCP server that provides email capabilities:
- send_email: Send emails via Gmail SMTP
- draft_email: Save email drafts locally
- search_emails: Search Gmail via API

Requires:
- SMTP credentials in .env file
- Gmail API credentials for search functionality
"""

import base64
import json
import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("email-mcp")

# Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# Paths
VAULT_PATH = Path(__file__).parent.parent
DRAFTS_PATH = VAULT_PATH / "Drafts"
LOGS_PATH = VAULT_PATH / "memory" / "email_logs.json"

# Ensure directories exist
DRAFTS_PATH.mkdir(parents=True, exist_ok=True)
LOGS_PATH.parent.mkdir(parents=True, exist_ok=True)


def log_action(action: str, details: dict) -> None:
    """Log email actions to memory/email_logs.json"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        **details,
    }

    # Load existing logs
    logs = []
    if LOGS_PATH.exists():
        try:
            with open(LOGS_PATH, "r") as f:
                logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            logs = []

    # Append new entry
    logs.append(log_entry)

    # Keep last 1000 entries
    logs = logs[-1000:]

    # Save
    with open(LOGS_PATH, "w") as f:
        json.dump(logs, f, indent=2)

    print(f"[EmailMCP] {action}: {details.get('to', details.get('subject', 'N/A'))}")


def validate_smtp_config() -> tuple[bool, str]:
    """Validate SMTP configuration is present."""
    if not SMTP_USER:
        return False, "SMTP_USER not configured in .env"
    if not SMTP_PASSWORD:
        return False, "SMTP_PASSWORD not configured in .env"
    return True, "OK"


@mcp.tool()
def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    html: bool = False,
) -> str:
    """
    Send an email via Gmail SMTP.

    IMPORTANT: Only use this after verifying approval exists in /Approved folder.

    Args:
        to: Recipient email address(es), comma-separated for multiple
        subject: Email subject line
        body: Email body content
        cc: CC recipients (optional), comma-separated
        bcc: BCC recipients (optional), comma-separated
        html: If True, body is treated as HTML content

    Returns:
        Success message with timestamp, or error message
    """
    # Validate config
    valid, msg = validate_smtp_config()
    if not valid:
        log_action("send_failed", {"error": msg, "to": to, "subject": subject})
        return f"ERROR: {msg}"

    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["From"] = SMTP_USER
        message["To"] = to
        message["Subject"] = subject

        if cc:
            message["Cc"] = cc
        if bcc:
            message["Bcc"] = bcc

        # Attach body
        content_type = "html" if html else "plain"
        message.attach(MIMEText(body, content_type))

        # Build recipient list
        recipients = [addr.strip() for addr in to.split(",")]
        if cc:
            recipients.extend([addr.strip() for addr in cc.split(",")])
        if bcc:
            recipients.extend([addr.strip() for addr in bcc.split(",")])

        # Send email
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, recipients, message.as_string())

        # Log success
        log_action(
            "send_success",
            {
                "to": to,
                "subject": subject,
                "cc": cc,
                "bcc": bcc,
            },
        )

        timestamp = datetime.now().isoformat()
        return f"SUCCESS: Email sent to {to} at {timestamp}"

    except smtplib.SMTPAuthenticationError:
        error = "SMTP authentication failed. Check SMTP_USER and SMTP_PASSWORD in .env"
        log_action("send_failed", {"error": error, "to": to, "subject": subject})
        return f"ERROR: {error}"

    except smtplib.SMTPException as e:
        error = f"SMTP error: {str(e)}"
        log_action("send_failed", {"error": error, "to": to, "subject": subject})
        return f"ERROR: {error}"

    except Exception as e:
        error = f"Unexpected error: {str(e)}"
        log_action("send_failed", {"error": error, "to": to, "subject": subject})
        return f"ERROR: {error}"


@mcp.tool()
def draft_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """
    Save an email draft without sending.

    Use this to prepare emails for review before sending.
    Drafts are saved to the /Drafts folder.

    Args:
        to: Intended recipient(s)
        subject: Email subject line
        body: Email body content
        cc: CC recipients (optional)
        notes: Internal notes about this draft (optional)

    Returns:
        Path to the saved draft file
    """
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")

    # Sanitize subject for filename
    safe_subject = "".join(c if c.isalnum() or c in " -_" else "" for c in subject)
    safe_subject = safe_subject.replace(" ", "_")[:30].strip("_").lower()

    filename = f"DRAFT_email_{safe_subject}_{timestamp_str}.md"
    filepath = DRAFTS_PATH / filename

    content = f"""---
type: email_draft
to: {to}
subject: {subject}
cc: {cc or ""}
created: {timestamp.isoformat()}
status: draft
---

# Email Draft: {subject}

## Recipients

- **To:** {to}
- **CC:** {cc or "None"}

## Subject

{subject}

## Body

{body}

## Notes

{notes or "_No notes_"}

---

## Actions

- [ ] Review content
- [ ] Request approval (move to /Pending_Approval)
- [ ] Send after approval
"""

    filepath.write_text(content, encoding="utf-8")

    log_action(
        "draft_saved",
        {
            "to": to,
            "subject": subject,
            "file": str(filepath.name),
        },
    )

    return f"SUCCESS: Draft saved to {filepath}"


@mcp.tool()
def search_emails(
    query: str,
    max_results: int = 10,
) -> str:
    """
    Search Gmail for emails matching a query.

    Uses Gmail API (requires OAuth credentials in config/).

    Args:
        query: Gmail search query (e.g., "from:john@example.com", "subject:invoice")
        max_results: Maximum number of results to return (default: 10)

    Returns:
        JSON string with matching email summaries
    """
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        token_path = VAULT_PATH / "config" / "token.json"
        credentials_path = VAULT_PATH / "config" / "credentials.json"

        if not token_path.exists():
            log_action("search_failed", {"error": "No token.json - run OAuth flow first"})
            return "ERROR: Gmail not authenticated. Run the gmail_watcher.py first to complete OAuth."

        creds = Credentials.from_authorized_user_file(str(token_path))

        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_path, "w") as f:
                    f.write(creds.to_json())
            else:
                return "ERROR: Gmail token expired. Re-run OAuth flow."

        service = build("gmail", "v1", credentials=creds)

        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )

        messages = results.get("messages", [])

        if not messages:
            log_action("search_complete", {"query": query, "count": 0})
            return json.dumps({"query": query, "count": 0, "messages": []})

        email_summaries = []
        for msg_ref in messages:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_ref["id"], format="metadata")
                .execute()
            )

            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}

            email_summaries.append(
                {
                    "id": msg["id"],
                    "from": headers.get("from", "Unknown"),
                    "subject": headers.get("subject", "No Subject"),
                    "date": headers.get("date", ""),
                    "snippet": msg.get("snippet", "")[:200],
                }
            )

        log_action("search_complete", {"query": query, "count": len(email_summaries)})

        return json.dumps(
            {
                "query": query,
                "count": len(email_summaries),
                "messages": email_summaries,
            },
            indent=2,
        )

    except ImportError:
        return "ERROR: Google API libraries not installed. Run: uv add google-api-python-client google-auth-oauthlib"

    except Exception as e:
        log_action("search_failed", {"query": query, "error": str(e)})
        return f"ERROR: Search failed - {str(e)}"


@mcp.tool()
def get_email_logs(limit: int = 20) -> str:
    """
    Get recent email action logs.

    Args:
        limit: Number of recent logs to return (default: 20)

    Returns:
        JSON string with recent log entries
    """
    if not LOGS_PATH.exists():
        return json.dumps({"logs": [], "count": 0})

    try:
        with open(LOGS_PATH, "r") as f:
            logs = json.load(f)

        recent = logs[-limit:]
        recent.reverse()  # Most recent first

        return json.dumps({"logs": recent, "count": len(recent)}, indent=2)

    except Exception as e:
        return f"ERROR: Could not read logs - {str(e)}"


@mcp.tool()
def check_smtp_status() -> str:
    """
    Check if SMTP is configured and can connect.

    Returns:
        Status message indicating SMTP health
    """
    valid, msg = validate_smtp_config()
    if not valid:
        return f"NOT CONFIGURED: {msg}"

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            # Don't actually login, just check connection
            return f"OK: SMTP connection to {SMTP_HOST}:{SMTP_PORT} successful. User: {SMTP_USER}"

    except Exception as e:
        return f"ERROR: Cannot connect to SMTP - {str(e)}"


if __name__ == "__main__":
    print("=" * 50)
    print("Email MCP Server for AI Employee")
    print("=" * 50)
    print(f"SMTP Host: {SMTP_HOST}")
    print(f"SMTP Port: {SMTP_PORT}")
    print(f"SMTP User: {SMTP_USER or 'NOT SET'}")
    print(f"Vault Path: {VAULT_PATH}")
    print("=" * 50)

    # Run the server
    mcp.run()
