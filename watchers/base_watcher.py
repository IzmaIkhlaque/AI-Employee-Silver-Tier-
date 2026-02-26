from abc import ABC, abstractmethod
from pathlib import Path
import time


class BaseWatcher(ABC):
    """Abstract base class for all watchers."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.running = False

    @abstractmethod
    def check_for_updates(self) -> list:
        """Check for new items to process.

        Returns:
            list: Items that need action files created.
        """
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create an action file in /Needs_Action for the given item.

        Args:
            item: The item to create an action file for.

        Returns:
            Path: Path to the created action file.
        """
        pass

    def run(self):
        """Main loop - continuously check for updates."""
        self.running = True
        print(f"[{self.__class__.__name__}] Starting watcher...")

        while self.running:
            try:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
                time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n[{self.__class__.__name__}] Stopping watcher...")
                self.running = False
                break
            except Exception as e:
                print(f"[{self.__class__.__name__}] Error: {e}")
                time.sleep(5)

    def stop(self):
        """Stop the watcher."""
        self.running = False
