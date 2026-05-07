import os
import time
import logging
from pathlib import Path
from gmail_watcher import GmailWatcher
from linkedin_watcher import LinkedInWatcher
from mcp_email_server import EmailMCPServer
from claude_reasoning_loop import ClaudeReasoningLoop
from scheduler import Scheduler
from approval_workflow import ApprovalWorkflow

class SilverTierSystem:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logger = logging.getLogger('SilverTierSystem')
        self._setup_logging()
        self._setup_components()

    def _setup_logging(self):
        """Set up logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_components(self):
        """Set up all Silver Tier components"""
        self.logger.info("Setting up Silver Tier components...")

        # Watchers
        # Gmail Watcher - uses token.json for OAuth2 credentials
        credentials_path = os.getenv('GMAIL_TOKEN_PATH', str(self.vault_path / 'token.json'))
        try:
            self.gmail_watcher = GmailWatcher(str(self.vault_path), credentials_path)
            self.gmail_enabled = True
        except Exception as e:
            self.logger.warning(f"Gmail watcher could not be initialized: {e}")
            self.gmail_enabled = False

        # LinkedIn Watcher - uses OAuth token if available, otherwise demo mode
        linkedin_token = self._load_linkedin_token()
        self.linkedin_watcher = LinkedInWatcher(str(self.vault_path), access_token=linkedin_token)

        # MCP Server
        self.email_mcp = EmailMCPServer(config_path=str(self.vault_path / 'mcp_config.json'))

        # Reasoning Loop
        self.reasoning_loop = ClaudeReasoningLoop(str(self.vault_path))

        # Scheduler
        self.scheduler = Scheduler(str(self.vault_path))

        # Approval Workflow
        self.approval_workflow = ApprovalWorkflow(str(self.vault_path))

        self.logger.info("Silver Tier components setup complete")

    def _load_linkedin_token(self):
        """Load LinkedIn OAuth access token from linkedin_token.json"""
        import json
        from datetime import datetime
        token_path = self.vault_path / 'linkedin_token.json'
        if token_path.exists():
            try:
                token_data = json.loads(token_path.read_text())
                expires_at = datetime.fromisoformat(token_data.get('expires_at', ''))
                if expires_at > datetime.now():
                    return token_data['access_token']
                else:
                    self.logger.warning("LinkedIn token expired. Run linkedin_oauth_setup.py to refresh.")
            except Exception as e:
                self.logger.error(f"Error loading LinkedIn token: {e}")
        return None

    def start_watchers(self):
        """Start all watcher scripts"""
        self.logger.info("Starting watchers...")

        import threading

        # Start Gmail watcher if enabled
        if hasattr(self, 'gmail_enabled') and self.gmail_enabled:
            gmail_thread = threading.Thread(target=self.gmail_watcher.run, daemon=True)
            gmail_thread.start()
            self.logger.info("Gmail watcher started")

        # Start LinkedIn watcher in background
        linkedin_thread = threading.Thread(target=self.linkedin_watcher.run, daemon=True)
        linkedin_thread.start()
        self.logger.info("LinkedIn watcher started")

        self.logger.info("Watchers started (WhatsApp disabled for privacy/demo)")

    def start_scheduler(self):
        """Start the scheduler"""
        self.logger.info("Starting scheduler...")
        self.scheduler.run()

    def process_approvals(self):
        """Process any approved actions"""
        self.logger.info("Processing approvals...")
        executed = self.approval_workflow.check_approvals()
        self.logger.info(f"Executed {len(executed)} approved actions")

    def run(self):
        """Main run loop for Silver Tier system"""
        self.logger.info("Starting Silver Tier system...")

        # Start watchers
        self.start_watchers()

        # Start scheduler (this runs indefinitely)
        try:
            self.start_scheduler()
        except KeyboardInterrupt:
            self.logger.info("Silver Tier system stopped")

if __name__ == "__main__":
    import sys
    vault_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    system = SilverTierSystem(vault_path)
    system.run()