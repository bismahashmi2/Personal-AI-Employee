from base_watcher import BaseWatcher
import time
import logging
from pathlib import Path
from datetime import datetime
import re

class WhatsAppWatcher(BaseWatcher):
    def __init__(self, vault_path: str, check_interval: int = 60):
        super().__init__(vault_path, check_interval)
        self.session_file = Path.home() / ".whatsapp_session.json"
        self.processed_ids = set()
        self.keywords = ['urgent', 'invoice', 'payment', 'help', 'emergency', 'important']

    def check_for_updates(self) -> list:
        """Check WhatsApp Web for new messages containing keywords"""
        try:
            # Check if we have a saved session
            if not self.session_file.exists():
                self.logger.info("No WhatsApp session found, need to login first")
                return []

            # Navigate to WhatsApp Web
            self.browser_navigate(url="https://web.whatsapp.com")

            # Wait for page to load
            self.browser_wait_for(time=10)

            # Get chat list
            chats = self._get_chat_list()
            new_messages = []

            for chat in chats:
                chat_name = chat.get('name', '')
                last_message = chat.get('last_message', '')
                message_id = chat.get('message_id', '')

                # Check if message contains keywords and hasn't been processed
                if any(keyword.lower() in last_message.lower() for keyword in self.keywords):
                    if message_id not in self.processed_ids:
                        new_messages.append({
                            'chat_name': chat_name,
                            'message': last_message,
                            'message_id': message_id,
                            'timestamp': datetime.now().isoformat()
                        })

            return new_messages

        except Exception as e:
            self.logger.error(f"Error checking WhatsApp: {e}")
            return []

    def create_action_file(self, item) -> Path:
        """Create markdown file for new message"""
        content = f"""---
type: whatsapp
from: {item['chat_name']}
message: {item['message']}
received: {item['timestamp']}
priority: high
status: pending
---

## WhatsApp Message

**From:** {item['chat_name']}

**Message:** {item['message']}

## Suggested Actions
- [ ] Reply to {item['chat_name']}
- [ ] Check if urgent payment/invoice is needed
- [ ] Provide help if requested
- [ ] Forward to relevant team member if needed
- [ ] Mark as completed after handling
"""

        # Create filename with timestamp and message ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"WHATSAPP_{timestamp}_{item['message_id']}.md"
        filepath = self.needs_action / filename
        filepath.write_text(content)

        self.processed_ids.add(item['message_id'])
        return filepath

    def _get_chat_list(self):
        """Extract chat list from WhatsApp Web"""
        try:
            # Get the DOM structure
            snapshot = self.browser_snapshot()

            # Extract chat information using JavaScript
            script = """
            async (page) => {
                const chats = [];

                // Find chat elements
                const chatElements = await page.$$('[role="grid"] [role="gridcell"]');

                for (const element of chatElements) {
                    // Get chat name
                    const nameElement = await element.$('[title]');
                    const name = nameElement ? await nameElement.getAttribute('title') : 'Unknown';

                    // Get last message
                    const messageElement = await element.$('div.copyable-text');
                    let message = '';
                    if (messageElement) {
                        const messageText = await messageElement.textContent();
                        if (messageText) {
                            // Extract actual message content
                            message = messageText.trim();
                        }
                    }

                    // Get message ID for tracking
                    const messageId = await messageElement.getAttribute('data-id') || Date.now().toString();

                    chats.push({
                        name: name,
                        last_message: message,
                        message_id: messageId
                    });
                }

                return chats;
            }
            """

            result = self.browser_run_code(code=script)
            return result.get('chats', [])

        except Exception as e:
            self.logger.error(f"Error getting chat list: {e}")
            return []

    def run(self):
        """Main run loop with login handling"""
        self.logger.info(f'Starting WhatsAppWatcher')

        while True:
            try:
                # Check if we need to login
                if not self.session_file.exists():
                    self._perform_login()

                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)

            except Exception as e:
                self.logger.error(f'Error: {e}')
                # If login session expired, clear it
                if 'login' in str(e).lower() or 'session' in str(e).lower():
                    self.logger.info("Login session may have expired, clearing")
                    if self.session_file.exists():
                        self.session_file.unlink()

            time.sleep(self.check_interval)

    def _perform_login(self):
        """Handle WhatsApp Web login flow"""
        try:
            self.logger.info("Navigating to WhatsApp Web for login")
            self.browser_navigate(url="https://web.whatsapp.com")

            # Wait for QR code to appear
            self.browser_wait_for(time=15)

            # Take screenshot for user to scan QR code
            self.browser_take_screenshot(filename="whatsapp_qr_code.png")
            self.logger.info("QR code captured. Please scan with your phone to login to WhatsApp Web.")

            # Wait for login to complete
            self.browser_wait_for(time=30)

            # Save session
            self._save_session()

        except Exception as e:
            self.logger.error(f"Login error: {e}")

    def _save_session(self):
        """Save session data for future use"""
        try:
            # This would typically save cookies or session data
            # For now, we'll just create a marker file
            self.session_file.touch()
            self.logger.info("WhatsApp session saved")
        except Exception as e:
            self.logger.error(f"Error saving session: {e}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python whatsapp_watcher.py <vault_path>")
        sys.exit(1)

    vault_path = sys.argv[1]
    watcher = WhatsAppWatcher(vault_path, check_interval=120)
    watcher.run()