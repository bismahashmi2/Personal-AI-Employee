import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

VAULT_PATH = Path(".")
INBOX_PATH = VAULT_PATH / "Inbox"
NEEDS_ACTION_PATH = VAULT_PATH / "Needs_Action"

class InboxHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            task_name = file_path.stem

            new_task = NEEDS_ACTION_PATH / f"{task_name}.md"
            new_task.write_text(f"# Task: {task_name}\n\nStatus: Needs Action\n")

            print(f"Created task file: {new_task}")

if __name__ == "__main__":
    event_handler = InboxHandler()
    observer = Observer()
    observer.schedule(event_handler, str(INBOX_PATH), recursive=False)
    observer.start()

    print("Watcher is running... Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()