import schedule
import time
import logging
from datetime import datetime
from pathlib import Path
import subprocess

class Scheduler:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logger = logging.getLogger('Scheduler')
        self.setup_schedule()

    def setup_schedule(self):
        """Set up scheduled tasks"""
        # Daily briefing at 8 AM
        schedule.every().day.at("08:00").do(self.daily_briefing)

        # Process needs_action every 15 minutes
        schedule.every(15).minutes.do(self.process_needs_action)

        # Weekly audit every Sunday at 9 PM
        schedule.every().sunday.at("21:00").do(self.weekly_audit)

    def process_needs_action(self):
        """Process needs_action folder"""
        self.logger.info("Processing needs_action folder...")

        # Run the reasoning loop
        reasoning_loop = ClaudeReasoningLoop(str(self.vault_path))
        plans_created = reasoning_loop.process_needs_action()

        self.logger.info(f"Created {len(plans_created)} plans")

    def daily_briefing(self):
        """Generate daily briefing"""
        self.logger.info("Generating daily briefing...")

        # Create dashboard update
        dashboard = self.vault_path / 'Dashboard.md'
        if dashboard.exists():
            content = dashboard.read_text()
            # Add today's date and summary
            new_content = f"""# Daily Briefing - {datetime.now().strftime('%Y-%m-%d')}

{content}

## Today's Summary
- Tasks processed: TBD
- Messages handled: TBD
- Business opportunities: TBD

## Priority Actions
- Review new plans in /Plans folder
- Check pending approvals in /Pending_Approval
- Update any urgent items
"""
            dashboard.write_text(new_content)

    def weekly_audit(self):
        """Generate weekly audit"""
        self.logger.info("Generating weekly audit...")

        # Create audit report
        audit_path = self.vault_path / f'Audits/weekly_{datetime.now().strftime("%Y_%m_%d")}.md'
        audit_path.parent.mkdir(exist_ok=True)

        content = f"""# Weekly Business Audit

## Period: Last 7 days

## Key Metrics
- Tasks completed: TBD
- Messages processed: TBD
- Business opportunities: TBD

## Financial Summary
- Revenue generated: TBD
- Expenses incurred: TBD
- Profit: TBD

## Issues Identified
- TBD

## Recommendations
- TBD

## Next Steps
- Review all pending items
- Plan for upcoming week
- Update business strategies as needed
"""

        audit_path.write_text(content)

    def run(self):
        """Run the scheduler"""
        self.logger.info("Scheduler started")

        while True:
            schedule.run_pending()
            time.sleep(60)  # Wait one minute

# Example usage:
# scheduler = Scheduler('/path/to/vault')
# scheduler.run()