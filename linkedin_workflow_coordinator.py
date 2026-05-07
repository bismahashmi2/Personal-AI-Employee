#!/usr/bin/env python3
"""
LinkedIn Workflow Coordinator
Coordinates the full LinkedIn auto-posting workflow for Silver Tier.

Workflow:
1. LinkedIn Watcher detects trending topics → creates files in Needs_Action/
2. Claude reasoning loop reads files → generates post content → creates Plans/
3. System moves to Pending_Approval/ (Human-in-the-Loop)
4. Human approves → moves to Approved/
5. LinkedIn Post Executor automatically posts
6. Moves to Done/
"""

import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class LinkedInWorkflowCoordinator:
    """
    Coordinates the LinkedIn auto-posting workflow.
    Bridges the gap between Claude reasoning and automatic posting.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.plans = self.vault_path / 'Plans'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.logger = logging.getLogger('LinkedInWorkflowCoordinator')

        # Create directories
        for directory in [self.needs_action, self.plans, self.pending_approval,
                         self.approved, self.done]:
            directory.mkdir(exist_ok=True)

        # Track processed files
        self.processed_files = set()

    def monitor_plans(self):
        """
        Monitor Plans/ folder for LinkedIn plans ready for approval.
        Moves them to Pending_Approval/ automatically.
        """
        self.logger.info("🔍 Checking Plans/ for LinkedIn posts ready for approval...")

        for plan_file in self.plans.glob('PLAN_LINKEDIN_*.md'):
            if plan_file.name in self.processed_files:
                continue

            try:
                content = plan_file.read_text()

                # Check if plan is complete and ready for approval
                if self._is_plan_ready_for_approval(content):
                    self.logger.info(f"📋 Plan ready for approval: {plan_file.name}")

                    # Extract post content from plan
                    post_details = self._extract_post_from_plan(content)

                    if post_details:
                        # Create approval request
                        approval_file = self._create_approval_request(post_details, plan_file.name)
                        self.logger.info(f"✅ Created approval request: {approval_file.name}")

                        # Move plan to Done (it's been processed)
                        done_plan = self.done / plan_file.name
                        plan_file.rename(done_plan)
                        self.logger.info(f"📁 Moved plan to Done: {done_plan.name}")

                        self.processed_files.add(plan_file.name)

            except Exception as e:
                self.logger.error(f"❌ Error processing plan {plan_file.name}: {e}")

    def _is_plan_ready_for_approval(self, content: str) -> bool:
        """Check if a plan is ready for approval"""
        # Look for indicators that the plan is complete
        indicators = [
            'ready for approval',
            'ready to post',
            'post content:',
            'draft post:',
            'linkedin post:',
            '## Post Content',
            '## Draft Post'
        ]

        content_lower = content.lower()
        return any(indicator in content_lower for indicator in indicators)

    def _extract_post_from_plan(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract post details from a plan file"""
        try:
            post_details = {
                'platform': 'linkedin',
                'content': '',
                'topic': '',
                'as_organization': False
            }

            # Extract frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    for line in frontmatter.strip().split('\n'):
                        if ': ' in line:
                            key, value = line.split(': ', 1)
                            key = key.strip()
                            value = value.strip()
                            if key == 'opportunity':
                                post_details['topic'] = value
                            elif key == 'organization_urn':
                                post_details['as_organization'] = bool(value and value != 'Not configured')

            # Extract post content
            # Look for sections like "## Post Content", "## Draft Post", etc.
            content_markers = [
                '## Post Content',
                '## 📝 Post Content',
                '## Draft Post',
                '## LinkedIn Post',
                '## Proposed Post',
                '## Post Template',
                '## 📝 Post Template'
            ]

            for marker in content_markers:
                if marker in content:
                    # Extract content after the marker
                    after_marker = content.split(marker, 1)[1]
                    # Get content until next ## heading or end
                    if '\n##' in after_marker:
                        post_content = after_marker.split('\n##', 1)[0].strip()
                    else:
                        post_content = after_marker.strip()

                    # Clean up the content
                    post_content = post_content.strip('`').strip()

                    if post_content and len(post_content) > 20:
                        post_details['content'] = post_content
                        break

            # If no explicit content found, try to extract from template section
            if not post_details['content'] and '## 📝 Post Template' in content:
                template_section = content.split('## 📝 Post Template', 1)[1]
                if '\n##' in template_section:
                    template_content = template_section.split('\n##', 1)[0].strip()
                else:
                    template_content = template_section.strip()

                if template_content and len(template_content) > 20:
                    post_details['content'] = template_content

            # Validate we have content
            if not post_details['content']:
                self.logger.warning("No post content found in plan")
                return None

            return post_details

        except Exception as e:
            self.logger.error(f"Error extracting post from plan: {e}")
            return None

    def _create_approval_request(self, post_details: Dict[str, Any], plan_name: str) -> Path:
        """Create an approval request file"""
        timestamp = int(time.time())
        filename = f'SOCIAL_POST_{timestamp}.md'
        filepath = self.pending_approval / filename

        content = f"""---
type: approval_request
action: social_post
created: {datetime.now().isoformat()}
expires: {datetime.fromtimestamp(timestamp + 86400).isoformat()}
status: pending
source_plan: {plan_name}
---

# LinkedIn Post Approval Request

## 📝 Post Content

{post_details['content']}

## 📊 Post Details

- **Platform:** LinkedIn
- **Topic:** {post_details.get('topic', 'Business content')}
- **Post as Organization:** {post_details.get('as_organization', False)}
- **Character Count:** {len(post_details['content'])}

## ✅ To Approve

Move this file to `/Approved` folder to publish this post to LinkedIn.

## ❌ To Reject

Move this file to `/Rejected` folder to cancel this post.

## ⏰ Approval Deadline

This approval request expires in 24 hours: {datetime.fromtimestamp(timestamp + 86400).strftime('%Y-%m-%d %H:%M:%S')}

## Details

{json.dumps(post_details, indent=2)}
"""

        filepath.write_text(content)
        self.logger.info(f"📄 Created approval request: {filepath}")
        return filepath

    def run_once(self):
        """Run one cycle of the workflow"""
        self.logger.info("=" * 60)
        self.logger.info("LinkedIn Workflow Coordinator - Single Run")
        self.logger.info("=" * 60)

        # Monitor plans and create approval requests
        self.monitor_plans()

        self.logger.info("✅ Workflow cycle complete")

    def run(self, interval: int = 60):
        """Run continuously, checking for new plans"""
        self.logger.info("=" * 60)
        self.logger.info("LinkedIn Workflow Coordinator Starting")
        self.logger.info("=" * 60)
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Check interval: {interval} seconds")
        self.logger.info("Press Ctrl+C to stop")

        try:
            while True:
                self.monitor_plans()
                time.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info("Stopping...")

        self.logger.info("LinkedIn Workflow Coordinator stopped")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="LinkedIn Workflow Coordinator")
    parser.add_argument('--vault', default='.', help='Path to vault directory')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    parser.add_argument('--once', action='store_true', help='Run once and exit')

    args = parser.parse_args()

    coordinator = LinkedInWorkflowCoordinator(args.vault)

    if args.once:
        coordinator.run_once()
    else:
        coordinator.run(args.interval)


if __name__ == '__main__':
    main()
