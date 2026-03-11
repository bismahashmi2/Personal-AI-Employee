from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import shutil
import time


class DropFolderHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'

    def on_created(self, event):
        if event.is_directory:
            return

        source = Path(str(event.src_path))

        # Copy file to Needs_Action
        dest = self.needs_action / f'FILE_{source.name}'
        shutil.copy2(source, dest)

        # Create metadata markdown file
        self.create_metadata(source, dest)

        # Move original to Done
        source.rename(self.done / source.name)

    def create_metadata(self, source: Path, dest: Path):
        meta_path = dest.with_suffix('.md')

        meta_path.write_text(f'''---
type: file_drop
original_name: {source.name}
size: {source.stat().st_size}
status: pending
---

New file dropped for processing.
''')


if __name__ == "__main__":
    vault_path = "/mnt/d/AI_Employee_Vault"
    drop_folder = Path(vault_path) / "Inbox"

    event_handler = DropFolderHandler(vault_path)
    observer = Observer()
    observer.schedule(event_handler, str(drop_folder), recursive=False)
    observer.start()

    print("Filesystem watcher started...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()