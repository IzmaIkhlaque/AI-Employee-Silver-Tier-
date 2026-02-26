#!/usr/bin/env python3
"""
AI Employee Orchestrator (Silver Tier)

A simple orchestrator that monitors vault folders and coordinates actions.
Polls /Needs_Action and /Approved folders every 30 seconds.

Usage:
    python orchestrator.py
    python orchestrator.py --dry-run
    python orchestrator.py --vault-path /custom/path
    python orchestrator.py --interval 60
"""

import argparse
import json
import logging
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configuration
DEFAULT_INTERVAL = 30  # seconds
STATE_FILE = "memory/orchestrator_state.json"
LOG_FILE = "orchestrator.log"


def setup_logging(vault_path: Path) -> logging.Logger:
    """Set up logging to both file and console."""
    logger = logging.getLogger("orchestrator")
    logger.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler(vault_path / LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "[%(asctime)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class OrchestratorState:
    """Manages persistent state across restarts."""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self._load()

    def _load(self) -> dict:
        """Load state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "processed_needs_action": [],
            "processed_approved": [],
            "last_run": None,
            "stats": {
                "needs_action_processed": 0,
                "approved_executed": 0,
                "errors": 0,
            }
        }

    def save(self) -> None:
        """Save state to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state["last_run"] = datetime.now().isoformat()
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def is_processed(self, folder: str, filename: str) -> bool:
        """Check if a file has been processed."""
        key = f"processed_{folder}"
        return filename in self.state.get(key, [])

    def mark_processed(self, folder: str, filename: str) -> None:
        """Mark a file as processed."""
        key = f"processed_{folder}"
        if key not in self.state:
            self.state[key] = []
        if filename not in self.state[key]:
            self.state[key].append(filename)
        # Keep only last 500 entries
        self.state[key] = self.state[key][-500:]

    def increment_stat(self, stat: str) -> None:
        """Increment a statistic counter."""
        if stat in self.state["stats"]:
            self.state["stats"][stat] += 1


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content."""
    frontmatter = {}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()
    return frontmatter


def call_claude(
    vault_path: Path,
    prompt: str,
    logger: logging.Logger,
    dry_run: bool = False
) -> tuple[bool, str]:
    """
    Call Claude Code with a prompt.

    Returns (success, output) tuple.
    """
    if dry_run:
        logger.info(f"[DRY RUN] Would call Claude with prompt:\n{prompt[:200]}...")
        return True, "Dry run - no action taken"

    try:
        result = subprocess.run(
            ["claude", "--print"],
            input=prompt,
            capture_output=True,
            text=True,
            cwd=str(vault_path),
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            return True, result.stdout
        else:
            logger.error(f"Claude returned error: {result.stderr}")
            return False, result.stderr

    except subprocess.TimeoutExpired:
        logger.error("Claude timed out after 5 minutes")
        return False, "Timeout"

    except FileNotFoundError:
        logger.error("Claude Code not found. Is it installed and in PATH?")
        return False, "Claude not found"

    except Exception as e:
        logger.error(f"Error calling Claude: {e}")
        return False, str(e)


def process_needs_action(
    file_path: Path,
    vault_path: Path,
    logger: logging.Logger,
    dry_run: bool = False
) -> bool:
    """Process a file from /Needs_Action."""
    logger.info(f"Processing: {file_path.name}")

    prompt = f"""
Process the file at Needs_Action/{file_path.name}

1. Read the file content
2. Use the file-processing skill to:
   - Classify priority using Company_Handbook.md keywords
   - Create a summary
   - Determine if any follow-up actions are needed
3. If multi-step task, use task-planner skill to create a plan in /Plans
4. Move processed file to /Done with DONE_ prefix
5. Update Dashboard.md with the action

Be concise. Report what was done.
"""

    success, output = call_claude(vault_path, prompt, logger, dry_run)

    if success:
        logger.info(f"Processed: {file_path.name}")
    else:
        logger.error(f"Failed to process: {file_path.name}")

    return success


def execute_approved_action(
    file_path: Path,
    vault_path: Path,
    logger: logging.Logger,
    dry_run: bool = False
) -> bool:
    """Execute an approved action from /Approved."""
    logger.info(f"Executing approved action: {file_path.name}")

    # Read the file to understand what action to take
    try:
        content = file_path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
    except Exception as e:
        logger.error(f"Could not read {file_path.name}: {e}")
        return False

    action_type = frontmatter.get("action", "unknown")
    target = frontmatter.get("target", "unknown")

    logger.info(f"Action type: {action_type}, Target: {target}")

    # Build prompt based on action type
    if action_type == "email_send":
        prompt = f"""
An email send action has been approved.

1. Read the approved file at Approved/{file_path.name}
2. Use the email-actions skill to send the email
3. Extract recipient, subject, and body from the approval file
4. Send the email using the email MCP server
5. Log the result in the approval file
6. Move to /Done with DONE_ prefix
7. Update Dashboard.md

Report the result.
"""
    elif action_type == "social_post":
        platform = frontmatter.get("platform", "linkedin")
        prompt = f"""
A social media post has been approved for {platform}.

1. Read the approved file at Approved/{file_path.name}
2. Extract the post content from the ## Preview section
3. For LinkedIn: Run the poster script or use MCP
4. Log the result in the approval file
5. Move to /Done with DONE_ prefix
6. Update Dashboard.md

Report the result.
"""
    elif action_type == "file_delete":
        prompt = f"""
A file deletion has been approved.

1. Read the approved file at Approved/{file_path.name}
2. Identify the file(s) to delete from the target field
3. Perform the deletion carefully
4. Log what was deleted
5. Move approval file to /Done with DONE_ prefix
6. Update Dashboard.md

Report the result.
"""
    else:
        prompt = f"""
An action has been approved.

1. Read the approved file at Approved/{file_path.name}
2. Understand what action was approved based on frontmatter:
   - Action: {action_type}
   - Target: {target}
3. Execute the action appropriately
4. Log the result
5. Move to /Done with DONE_ prefix
6. Update Dashboard.md

Report the result.
"""

    success, output = call_claude(vault_path, prompt, logger, dry_run)

    if success:
        logger.info(f"Executed: {file_path.name} ({action_type})")
    else:
        logger.error(f"Failed to execute: {file_path.name}")

    return success


def scan_folder(folder: Path) -> list[Path]:
    """Get all .md files in a folder (excluding hidden files)."""
    if not folder.exists():
        return []
    return [
        f for f in folder.glob("*.md")
        if not f.name.startswith(".")
    ]


def run_orchestrator(
    vault_path: Path,
    interval: int,
    dry_run: bool,
    logger: logging.Logger
) -> None:
    """Main orchestrator loop."""

    state_file = vault_path / STATE_FILE
    state = OrchestratorState(state_file)

    needs_action_path = vault_path / "Needs_Action"
    approved_path = vault_path / "Approved"

    logger.info("=" * 50)
    logger.info("AI Employee Orchestrator (Silver Tier)")
    logger.info("=" * 50)
    logger.info(f"Vault path: {vault_path}")
    logger.info(f"Check interval: {interval}s")
    logger.info(f"Dry run: {dry_run}")
    logger.info(f"State file: {state_file}")
    logger.info("=" * 50)
    logger.info("Starting monitoring loop... (Ctrl+C to stop)")
    logger.info("")

    try:
        while True:
            # Check /Needs_Action
            needs_action_files = scan_folder(needs_action_path)
            for file_path in needs_action_files:
                if not state.is_processed("needs_action", file_path.name):
                    logger.info(f"New item in Needs_Action: {file_path.name}")

                    success = process_needs_action(
                        file_path, vault_path, logger, dry_run
                    )

                    if success or dry_run:
                        state.mark_processed("needs_action", file_path.name)
                        state.increment_stat("needs_action_processed")
                    else:
                        state.increment_stat("errors")

                    state.save()

            # Check /Approved
            approved_files = scan_folder(approved_path)
            for file_path in approved_files:
                if not state.is_processed("approved", file_path.name):
                    logger.info(f"New approved action: {file_path.name}")

                    success = execute_approved_action(
                        file_path, vault_path, logger, dry_run
                    )

                    if success or dry_run:
                        state.mark_processed("approved", file_path.name)
                        state.increment_stat("approved_executed")
                    else:
                        state.increment_stat("errors")

                    state.save()

            # Sleep until next check
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("")
        logger.info("Shutting down orchestrator...")
        state.save()
        logger.info(f"Stats: {json.dumps(state.state['stats'])}")
        logger.info("Goodbye!")


def main():
    parser = argparse.ArgumentParser(
        description="AI Employee Orchestrator (Silver Tier)"
    )
    parser.add_argument(
        "--vault-path",
        type=Path,
        default=Path(__file__).parent,
        help="Path to the vault directory",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        help=f"Check interval in seconds (default: {DEFAULT_INTERVAL})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without executing",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (no loop)",
    )

    args = parser.parse_args()
    vault_path = args.vault_path.resolve()

    # Validate vault path
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    # Ensure required folders exist
    for folder in ["Needs_Action", "Approved", "Done", "memory"]:
        (vault_path / folder).mkdir(exist_ok=True)

    # Set up logging
    logger = setup_logging(vault_path)

    if args.once:
        # Single run mode
        logger.info("Running single check...")

        state_file = vault_path / STATE_FILE
        state = OrchestratorState(state_file)

        needs_action_path = vault_path / "Needs_Action"
        approved_path = vault_path / "Approved"

        # Process Needs_Action
        for file_path in scan_folder(needs_action_path):
            if not state.is_processed("needs_action", file_path.name):
                process_needs_action(file_path, vault_path, logger, args.dry_run)
                state.mark_processed("needs_action", file_path.name)

        # Process Approved
        for file_path in scan_folder(approved_path):
            if not state.is_processed("approved", file_path.name):
                execute_approved_action(file_path, vault_path, logger, args.dry_run)
                state.mark_processed("approved", file_path.name)

        state.save()
        logger.info("Single run complete.")
    else:
        # Continuous monitoring mode
        run_orchestrator(vault_path, args.interval, args.dry_run, logger)


if __name__ == "__main__":
    main()
