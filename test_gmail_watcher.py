#!/usr/bin/env python
"""Quick test of Gmail watcher"""

import sys
sys.path.insert(0, '.')
from gmail_watcher import GmailWatcher
from pathlib import Path

vault_path = '.'
credentials_path = 'token.json'

print(f"Initializing GmailWatcher...")
print(f"Vault path: {vault_path}")
print(f"Credentials: {credentials_path}")

try:
    watcher = GmailWatcher(vault_path, credentials_path)
    print("✅ GmailWatcher initialized successfully!")

    print("\nChecking for unread important emails...")
    messages = watcher.check_for_updates()

    print(f"\nFound {len(messages)} new message(s)")

    if messages:
        print("\nProcessing messages:")
        for msg in messages:
            filepath = watcher.create_action_file(msg)
            print(f"  Created: {filepath}")
    else:
        print("\nNo new important unread emails found.")
        print("\nTips:")
        print("  - Mark your sister's email as 'Important' in Gmail (click the marker icon)")
        print("  - Keep the email as 'unread' (don't open it)")
        print("  - The watcher checks every 2 minutes")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
