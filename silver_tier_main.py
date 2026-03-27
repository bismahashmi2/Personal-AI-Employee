import os
import time
import logging
from pathlib import Path
from whatsapp_watcher import WhatsAppWatcher
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
        self.whatsapp_watcher = WhatsAppWatcher(str(self.vault_path),
                                               session_path=str(self.vault_path / 'whatsapp_session'))
        self.linkedin_watcher = LinkedInWatcher(str(self.vault_path),
                                               api_key=os.getenv('LINKEDIN_API_KEY', 'demo_key'))

        # MCP Server
        self.email_mcp = EmailMCPServer(config_path=str(self.vault_path / 'mcp_config.json'))

        # Reasoning Loop
        self.reasoning_loop = ClaudeReasoningLoop(str(self.vault_path))

        # Scheduler
        self.scheduler = Scheduler(str(self.vault_path))

        # Approval Workflow
        self.approval_workflow = ApprovalWorkflow(str(self.vault_path))

        self.logger.info("Silver Tier components setup complete")

    def start_watchers(self):
        """Start all watcher scripts"""
        self.logger.info("Starting watchers...")

        # Start WhatsApp watcher in background
        import threading
        whatsapp_thread = threading.Thread(target=self.whatsapp_watcher.run, daemon=True)
        whatsapp_thread.start()

        # Start LinkedIn watcher in background
        linkedin_thread = threading.Thread(target=self.linkedin_watcher.run, daemon=True)
        linkedin_thread.start()

        self.logger.info("Watchers started")

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