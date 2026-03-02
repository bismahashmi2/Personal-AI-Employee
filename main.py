import os
import time

VAULT_PATH = "/mnt/d/Code/hackathon0/AI_Employee_Vault"

INBOX = os.path.join(VAULT_PATH, "Inbox")
NEEDS_ACTION = os.path.join(VAULT_PATH, "Needs_Action")
DONE = os.path.join(VAULT_PATH, "Done")
LOGS = os.path.join(VAULT_PATH, "Logs")


def log(message):
    with open(os.path.join(LOGS, "watcher.log"), "a") as f:
        f.write(message + "\n")
    print(message)


def process_file(filename):
    if not filename.endswith(".txt"):
        return

    input_path = os.path.join(INBOX, filename)
    output_filename = filename.replace(".txt", ".md")
    output_path = os.path.join(NEEDS_ACTION, output_filename)

    with open(input_path, "r") as f:
        content = f.read()

    md_content = f"# Task: {filename}\n\n{content}"

    with open(output_path, "w") as f:
        f.write(md_content)

    # Move original file to Done
    os.rename(input_path, os.path.join(DONE, filename))

    log(f"Processed and moved to Done: {filename}")


def watch():
    log("Watcher started...")

    while True:
        files = os.listdir(INBOX)
        for file in files:
            process_file(file)
        time.sleep(5)


if __name__ == "__main__":
    watch()