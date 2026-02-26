#!/usr/bin/env python3
"""
LinkedIn Poster - Playwright Automation

Posts approved content to LinkedIn using browser automation.
Only posts content that has been moved to /Approved folder.

Usage:
    python scripts/linkedin_poster.py --post-file Approved/APPROVAL_social_post_linkedin_*.md
    python scripts/linkedin_poster.py --login-only  # Just save session
    python scripts/linkedin_poster.py --dry-run --post-file ...  # Test without posting
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("ERROR: Playwright not installed. Run: uv add playwright && playwright install chromium")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv()

# Paths
VAULT_PATH = Path(__file__).parent.parent
SESSION_PATH = VAULT_PATH / "config" / "linkedin_session.json"
LOGS_PATH = VAULT_PATH / "memory" / "linkedin_logs.json"


def log_action(action: str, details: dict) -> None:
    """Log LinkedIn actions to memory/linkedin_logs.json"""
    LOGS_PATH.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        **details,
    }

    logs = []
    if LOGS_PATH.exists():
        try:
            with open(LOGS_PATH, "r") as f:
                logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            logs = []

    logs.append(log_entry)
    logs = logs[-500:]  # Keep last 500 entries

    with open(LOGS_PATH, "w") as f:
        json.dump(logs, f, indent=2)

    print(f"[LinkedIn] {action}: {details.get('status', 'OK')}")


def extract_post_content(file_path: Path) -> tuple[str, dict]:
    """Extract post content from approval file."""
    content = file_path.read_text(encoding="utf-8")

    # Extract frontmatter
    frontmatter = {}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()
            content = parts[2]

    # Find the post content between ## Preview and the next ---
    preview_match = re.search(r"## Preview\s*\n(.*?)(?=\n---|\n## )", content, re.DOTALL)

    if preview_match:
        post_content = preview_match.group(1).strip()
    else:
        # Fallback: Look for content after "# LinkedIn Post Draft"
        draft_match = re.search(r"# LinkedIn Post Draft\s*\n(.*?)(?=\n---|\n## Approval)", content, re.DOTALL)
        if draft_match:
            post_content = draft_match.group(1).strip()
        else:
            # Last fallback: use everything after frontmatter
            post_content = content.strip()

    return post_content, frontmatter


def save_session(context) -> None:
    """Save browser session for reuse."""
    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    storage = context.storage_state()
    with open(SESSION_PATH, "w") as f:
        json.dump(storage, f)
    print(f"[LinkedIn] Session saved to {SESSION_PATH}")


def load_session(context) -> bool:
    """Load saved browser session if available."""
    if SESSION_PATH.exists():
        try:
            return str(SESSION_PATH)
        except Exception as e:
            print(f"[LinkedIn] Could not load session: {e}")
    return None


def login_to_linkedin(page, save_after: bool = True) -> bool:
    """
    Navigate to LinkedIn and wait for manual login.
    Returns True if login successful.
    """
    print("\n" + "=" * 50)
    print("LinkedIn Login Required")
    print("=" * 50)

    page.goto("https://www.linkedin.com/login")

    print("\nPlease log in to LinkedIn in the browser window.")
    print("The script will continue automatically once logged in.")
    print("\nWaiting for login...")

    try:
        # Wait for feed page or profile element that indicates logged in
        page.wait_for_selector(
            "div.feed-identity-module, div.global-nav__me, button[aria-label*='Start a post']",
            timeout=300000  # 5 minute timeout for manual login
        )
        print("\n✅ Login successful!")
        return True
    except PlaywrightTimeout:
        print("\n❌ Login timeout. Please try again.")
        return False


def post_to_linkedin(page, content: str, dry_run: bool = False) -> dict:
    """
    Post content to LinkedIn.
    Returns dict with status and details.
    """
    result = {
        "success": False,
        "message": "",
        "timestamp": datetime.now().isoformat(),
    }

    if dry_run:
        print("\n[DRY RUN] Would post the following content:")
        print("-" * 40)
        print(content[:500] + "..." if len(content) > 500 else content)
        print("-" * 40)
        result["success"] = True
        result["message"] = "Dry run - no actual post made"
        return result

    try:
        # Navigate to LinkedIn feed
        page.goto("https://www.linkedin.com/feed/")
        time.sleep(2)

        # Click "Start a post" button
        start_post_btn = page.locator("button:has-text('Start a post'), button[aria-label*='Start a post']")
        if start_post_btn.count() == 0:
            # Alternative: click the text input area
            start_post_btn = page.locator(".share-box-feed-entry__trigger")

        start_post_btn.first.click()
        time.sleep(1)

        # Wait for post modal
        page.wait_for_selector(".share-creation-state__text-editor, .ql-editor", timeout=10000)

        # Find the text editor and type content
        editor = page.locator(".ql-editor, div[role='textbox'][contenteditable='true']").first
        editor.click()

        # Type the content (use fill for speed, or type for more natural behavior)
        editor.fill(content)
        time.sleep(1)

        # Click Post button
        post_btn = page.locator("button:has-text('Post'), button.share-actions__primary-action")
        post_btn.first.click()

        # Wait for post to complete
        time.sleep(3)

        # Verify post was made (check for success indicators)
        result["success"] = True
        result["message"] = "Post published successfully"

        print("\n✅ Post published successfully!")

    except PlaywrightTimeout as e:
        result["message"] = f"Timeout error: {str(e)}"
        print(f"\n❌ Posting failed: {result['message']}")

    except Exception as e:
        result["message"] = f"Error: {str(e)}"
        print(f"\n❌ Posting failed: {result['message']}")

    return result


def update_approval_file(file_path: Path, result: dict) -> None:
    """Add execution log to the approval file."""
    content = file_path.read_text(encoding="utf-8")

    status = "✅ Successfully posted" if result["success"] else f"❌ Failed: {result['message']}"

    log_section = f"""

## Execution Log

- **Posted at:** {result['timestamp']}
- **Status:** {status}
- **Message:** {result['message']}
"""

    # Append log before the last section or at the end
    if "## Approval Instructions" in content:
        content = content.replace("## Approval Instructions", log_section + "\n## Approval Instructions")
    else:
        content += log_section

    file_path.write_text(content, encoding="utf-8")


def move_to_done(file_path: Path) -> Path:
    """Move completed file to Done folder."""
    done_folder = VAULT_PATH / "Done"
    done_folder.mkdir(exist_ok=True)

    # Generate new filename
    new_name = f"DONE_{file_path.name}"
    done_path = done_folder / new_name

    file_path.rename(done_path)
    print(f"[LinkedIn] Moved to: {done_path}")

    return done_path


def main():
    parser = argparse.ArgumentParser(
        description="Post approved content to LinkedIn"
    )
    parser.add_argument(
        "--post-file",
        type=Path,
        help="Path to approval file to post",
    )
    parser.add_argument(
        "--login-only",
        action="store_true",
        help="Just login and save session",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be posted without posting",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (no visible browser)",
    )

    args = parser.parse_args()

    if not args.login_only and not args.post_file:
        parser.error("Either --post-file or --login-only is required")

    if args.post_file and not args.post_file.exists():
        print(f"ERROR: File not found: {args.post_file}")
        sys.exit(1)

    # Check that file is in Approved folder (safety check)
    if args.post_file and "Approved" not in str(args.post_file):
        print("ERROR: Can only post files from the /Approved folder!")
        print("Move the file to /Approved first to confirm you want to post it.")
        sys.exit(1)

    print("=" * 50)
    print("LinkedIn Poster")
    print("=" * 50)

    with sync_playwright() as p:
        # Check for saved session
        session_file = load_session(None)

        # Launch browser
        browser = p.chromium.launch(
            headless=args.headless,
            slow_mo=100,  # Slow down for stability
        )

        # Create context with session if available
        if session_file:
            print(f"[LinkedIn] Loading saved session...")
            context = browser.new_context(storage_state=session_file)
        else:
            context = browser.new_context()

        page = context.new_page()

        # Check if logged in
        page.goto("https://www.linkedin.com/feed/")
        time.sleep(2)

        # Check for login page redirect
        if "login" in page.url or "checkpoint" in page.url:
            if not login_to_linkedin(page):
                browser.close()
                sys.exit(1)
            save_session(context)
        else:
            print("[LinkedIn] Already logged in")

        if args.login_only:
            save_session(context)
            print("\nSession saved. You can now run the poster without logging in again.")
            browser.close()
            return

        # Extract and post content
        post_content, metadata = extract_post_content(args.post_file)

        print(f"\n[LinkedIn] Posting content from: {args.post_file.name}")
        print(f"[LinkedIn] Character count: {len(post_content)}")

        result = post_to_linkedin(page, post_content, dry_run=args.dry_run)

        # Log the action
        log_action(
            "post_attempt",
            {
                "file": str(args.post_file.name),
                "success": result["success"],
                "dry_run": args.dry_run,
                "character_count": len(post_content),
            }
        )

        if not args.dry_run:
            # Update the approval file with result
            update_approval_file(args.post_file, result)

            if result["success"]:
                # Move to Done folder
                move_to_done(args.post_file)

        # Save session for next time
        save_session(context)

        browser.close()

    print("\nDone!")


if __name__ == "__main__":
    main()
