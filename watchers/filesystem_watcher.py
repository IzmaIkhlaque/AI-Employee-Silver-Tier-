#!/usr/bin/env python3
"""
FileSystem Watcher - Bronze Tier
Monitors a drop folder and creates action files in /Needs_Action.
"""

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from queue import Queue
from threading import Thread

# Allow running from any directory (fixes ModuleNotFoundError for base_watcher)
sys.path.insert(0, str(Path(__file__).parent))

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from base_watcher import BaseWatcher


class FileDropHandler(FileSystemEventHandler):
    """Handle file system events for dropped files."""

    def __init__(self, queue: Queue):
        self.queue = queue

    def on_created(self, event: FileCreatedEvent):
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Ignore hidden files (starting with . or ~)
        if file_path.name.startswith('.') or file_path.name.startswith('~'):
            return

        self.queue.put(file_path)


class FileSystemWatcher(BaseWatcher):
    """Watch a directory for new files and create action items."""

    def __init__(
        self,
        watch_path: str | None = None,
        vault_path: str | None = None,
        dry_run: bool = False,
    ):
        super().__init__(dry_run=dry_run)

        # Set up paths
        self.watch_path = Path(watch_path or os.path.expanduser("~/AI_Drop"))
        self.vault_path = Path(vault_path or Path(__file__).parent.parent)
        self.needs_action_path = self.vault_path / "Needs_Action"

        # Create directories if they don't exist
        self.watch_path.mkdir(parents=True, exist_ok=True)
        self.needs_action_path.mkdir(parents=True, exist_ok=True)

        # Queue for file events
        self.file_queue: Queue[Path] = Queue()

        # Set up watchdog observer
        self.event_handler = FileDropHandler(self.file_queue)
        self.observer = Observer()

    def check_for_updates(self) -> list:
        """Check queue for new files."""
        items = []
        while not self.file_queue.empty():
            items.append(self.file_queue.get())
        return items

    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type from extension."""
        ext = file_path.suffix.lower()
        type_map = {
            '.pdf': 'PDF Document',
            '.doc': 'Word Document',
            '.docx': 'Word Document',
            '.xls': 'Excel Spreadsheet',
            '.xlsx': 'Excel Spreadsheet',
            '.txt': 'Text File',
            '.md': 'Markdown File',
            '.jpg': 'Image',
            '.jpeg': 'Image',
            '.png': 'Image',
            '.gif': 'Image',
            '.eml': 'Email',
            '.msg': 'Email',
            '.csv': 'CSV Data',
            '.json': 'JSON Data',
            '.zip': 'Archive',
        }
        return type_map.get(ext, 'Unknown File')

    def _get_suggested_actions(self, file_type: str) -> list[str]:
        """Get suggested actions based on file type."""
        actions = {
            'PDF Document': [
                'Review document contents',
                'Extract key information',
                'File appropriately',
            ],
            'Word Document': [
                'Review document contents',
                'Check for required actions',
                'File appropriately',
            ],
            'Excel Spreadsheet': [
                'Review data',
                'Check for calculations needed',
                'File appropriately',
            ],
            'Email': [
                'Read email contents',
                'Determine if response needed',
                'Extract action items',
            ],
            'Image': [
                'Review image',
                'Determine context',
                'File appropriately',
            ],
            'CSV Data': [
                'Review data structure',
                'Analyze contents',
                'Process as needed',
            ],
        }
        return actions.get(file_type, [
            'Review file contents',
            'Determine required action',
            'Process accordingly',
        ])

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable form."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def create_action_file(self, item: Path) -> Path:
        """Create an action file in /Needs_Action for a dropped file."""
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        readable_time = now.strftime("%Y-%m-%d %H:%M:%S")

        # Get file info
        try:
            file_size = item.stat().st_size
        except OSError:
            file_size = 0

        file_type = self._get_file_type(item)
        suggested_actions = self._get_suggested_actions(file_type)

        # Create action file name
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in item.stem)
        action_filename = f"FILE_{safe_name}_{timestamp}.md"
        action_path = self.needs_action_path / action_filename

        # Build content
        content = f"""---
type: file_drop
original_name: {item.name}
original_path: {item}
size: {file_size}
detected: {readable_time}
status: pending
---

# New File: {item.name}

## File Information

- **Name:** {item.name}
- **Type:** {file_type}
- **Size:** {self._format_size(file_size)}
- **Detected:** {readable_time}
- **Location:** {item}

## Suggested Actions

"""
        for action in suggested_actions:
            content += f"- [ ] {action}\n"

        content += """
## Notes

_Add any notes about this file here._
"""

        if self.dry_run:
            print(f"[DRY RUN] Would create: {action_path}")
            print(f"[DRY RUN] Content preview:")
            print("-" * 40)
            print(content[:500])
            print("-" * 40)
        else:
            action_path.write_text(content, encoding="utf-8")
            print(f"[FileSystemWatcher] Created: {action_path.name}")

        return action_path

    def run(self):
        """Start watching for file drops."""
        print(f"[FileSystemWatcher] Watching: {self.watch_path}")
        print(f"[FileSystemWatcher] Actions go to: {self.needs_action_path}")
        if self.dry_run:
            print("[FileSystemWatcher] DRY RUN MODE - No files will be created")
        print("[FileSystemWatcher] Press Ctrl+C to stop\n")

        self.observer.schedule(self.event_handler, str(self.watch_path), recursive=False)
        self.observer.start()
        self.running = True

        try:
            while self.running:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[FileSystemWatcher] Stopping...")
        finally:
            self.observer.stop()
            self.observer.join()
            print("[FileSystemWatcher] Stopped.")

    def stop(self):
        """Stop the watcher."""
        self.running = False
        self.observer.stop()


def main():
    parser = argparse.ArgumentParser(
        description="Watch a folder for new files and create action items."
    )
    parser.add_argument(
        "--watch-path",
        type=str,
        default=None,
        help="Directory to watch (default: ~/AI_Drop)",
    )
    parser.add_argument(
        "--vault-path",
        type=str,
        default=None,
        help="Path to the vault (default: parent of this script)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without creating files",
    )

    args = parser.parse_args()

    watcher = FileSystemWatcher(
        watch_path=args.watch_path,
        vault_path=args.vault_path,
        dry_run=args.dry_run,
    )
    watcher.run()


if __name__ == "__main__":
    main()
