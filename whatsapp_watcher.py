from base_watcher import BaseWatcher
import time
import logging
from pathlib import Path
from datetime import datetime
import re
from playwright.sync_api import sync_playwright

class WhatsAppWatcher(BaseWatcher):
    def __init__(self, vault_path: str, check_interval: int = 30, session_path: str = None):
        super().__init__(vault_path, check_interval)
        self.session_path = Path(session_path) if session_path else Path(vault_path) / 'whatsapp_session'
        self.session_path.mkdir(exist_ok=True)
        self.processed_ids = set()
        self.keywords = ['urgent', 'asap', 'invoice', 'payment', 'help', 'pricing', 'quote']
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def check_for_updates(self) -> list:
        """Check WhatsApp Web for new messages containing keywords"""
        try:
            # Initialize browser if needed
            if not self.page:
                self._init_browser()

            # Navigate to WhatsApp Web
            self.page.goto("https://web.whatsapp.com", timeout=30000)

            # Wait for the chat list to load (wait for main panel)
            try:
                self.page.wait_for_selector('[data-testid="chat-list"]', timeout=30000)
            except:
                self.logger.warning("Chat list not found, might need to scan QR code")
                return []

            # Give page a moment to stabilize
            time.sleep(2)

            # Get chat list with unread messages
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
                        self.logger.info(f"Found keyword message from {chat_name}: {last_message[:50]}...")

            return new_messages

        except Exception as e:
            self.logger.error(f"Error checking WhatsApp: {e}")
            self._cleanup()
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
            chats = []

            # Get all chat panels (unread and recent)
            chat_panels = self.page.query_selector_all('[data-testid="chat-list"] [role="row"]')

            for panel in chat_panels[:20]:  # Limit to first 20 for performance
                try:
                    # Get chat name/title
                    title_elem = panel.query_selector('[title]')
                    name = title_elem.get_attribute('title') if title_elem else 'Unknown'

                    # Get message preview
                    msg_elem = panel.query_selector('.copyable-text, [data-pre-plain-text]')
                    message = msg_elem.inner_text().strip() if msg_elem else ''

                    # Generate a simple message ID
                    message_id = f"{name}_{int(time.time())}"

                    if name and message:
                        chats.append({
                            'name': name,
                            'last_message': message,
                            'message_id': message_id
                        })
                except:
                    continue

            self.logger.info(f"Found {len(chats)} chats")
            return chats

        except Exception as e:
            self.logger.error(f"Error getting chat list: {e}")
            return []

    def _init_browser(self):
        """Initialize Playwright browser with persistent context"""
        try:
            self.playwright = sync_playwright().start()
            # Use persistent context to maintain WhatsApp session
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),
                headless=False,  # Set to True for headless
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            self.logger.info("Browser initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            raise

    def _cleanup(self):
        """Clean up browser resources"""
        try:
            if self.context:
                self.context.close()
            if self.playwright:
                self.playwright.stop()
            self.page = None
            self.context = None
            self.playwright = None
        except:
            pass

    def run(self):
        """Main run loop with error recovery"""
        self.logger.info(f'Starting WhatsAppWatcher')

        while True:
            try:
                if not self.page:
                    self._init_browser()

                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)

            except Exception as e:
                self.logger.error(f'Error: {e}')
                self._cleanup()

            time.sleep(self.check_interval)

    def _perform_login(self):
        """Handle WhatsApp Web login flow - DEPRECATED, use browser init"""
        self.logger.info("WhatsApp login handled via persistent browser context")
        self.logger.info("If WhatsApp requires authentication, please run with headless=False")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WhatsApp Watcher - MCP Service")
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=50053, help='Port to bind to')
    parser.add_argument('--vault', default='.', help='Path to vault directory')
    parser.add_argument('--session', default=None, help='Path to WhatsApp session directory')
    parser.add_argument('--interval', type=int, default=120, help='Check interval in seconds')

    args = parser.parse_args()

    vault_path = args.vault
    session_path = args.session

    watcher = WhatsAppWatcher(vault_path, check_interval=args.interval, session_path=session_path)
    print(f"WhatsApp Watcher MCP Service starting on {args.host}:{args.port}")
    print(f"Vault: {vault_path}")
    watcher.run_mcp_server(host=args.host, port=args.port)