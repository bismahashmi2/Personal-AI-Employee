import os
import time
import json
from pathlib import Path
from typing import Dict, Any, List
import logging

class ApprovalWorkflow:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.done = self.vault_path / 'Done'
        self.logger = logging.getLogger('ApprovalWorkflow')

        # Create directories if they don't exist
        self.pending_approval.mkdir(exist_ok=True)
        self.approved.mkdir(exist_ok=True)
        self.rejected.mkdir(exist_ok=True)
        self.done.mkdir(exist_ok=True)

        # Initialize LinkedIn watcher for posting
        self.linkedin_watcher = None
        self._init_linkedin()

    def _init_linkedin(self):
        """Initialize LinkedIn watcher for posting capabilities"""
        try:
            from linkedin_watcher import LinkedInWatcher
            self.linkedin_watcher = LinkedInWatcher(str(self.vault_path))
            if self.linkedin_watcher.access_token:
                self.logger.info("LinkedIn watcher initialized for posting")
            else:
                self.logger.warning("LinkedIn watcher in demo mode - posting disabled")
        except ImportError as e:
            self.logger.error(f"Could not import LinkedInWatcher: {e}")
        except Exception as e:
            self.logger.error(f"Error initializing LinkedIn watcher: {e}")

    def create_approval_request(self, action_type: str, details: Dict[str, Any]) -> Path:
        """Create an approval request file"""
        timestamp = int(time.time())
        filename = f'{action_type.upper()}_{timestamp}.md'
        filepath = self.pending_approval / filename

        content = self._generate_approval_content(action_type, details, timestamp)
        filepath.write_text(content)
        return filepath

    def _generate_approval_content(self, action_type: str, details: Dict[str, Any], timestamp: int) -> str:
        """Generate approval request content"""
        action_description = self._get_action_description(action_type, details)
        approval_deadline = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp + 86400))  # 24 hours from now

        return f"""---
type: approval_request
action: {action_type}
created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}
expires: {approval_deadline}
status: pending
---

# Approval Request

## Action Details

{action_description}

## Action Type
{action_type.replace('_', ' ').title()}

## Created
{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}

## Approval Deadline
{approval_deadline}

## To Approve
Move this file to /Approved folder.

## To Reject
Move this file to /Rejected folder.

## Details

{json.dumps(details, indent=2)}
"""

    def _get_action_description(self, action_type: str, details: Dict[str, Any]) -> str:
        """Get human-readable description of the action"""
        descriptions = {
            'email_send': f"Send email to {details.get('to', 'unknown recipient')}",
            'payment': f"Make payment of ${details.get('amount', 0)} to {details.get('recipient', 'unknown payee')}",
            'social_post': f"Post to {details.get('platform', 'unknown platform')} about {details.get('topic', 'unknown topic')}",
            'data_share': f"Share data with {details.get('recipient', 'unknown party')}"
        }
        return descriptions.get(action_type, f"Perform {action_type} action")

    def check_approvals(self) -> List[Path]:
        """Check for approved actions and execute them"""
        executed = []

        for approval_file in self.approved.glob('*.md'):
            try:
                action = self._parse_approval_file(approval_file)
                if action:
                    success = self._execute_action(action)
                    if success:
                        executed.append(approval_file)
                        approval_file.rename(self.done / approval_file.name)
            except Exception as e:
                print(f"Error processing approval {approval_file}: {e}")

        return executed

    def _parse_approval_file(self, approval_file: Path) -> Dict[str, Any]:
        """Parse approval file to extract action details"""
        content = approval_file.read_text()
        action = {}

        # Parse frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                for line in frontmatter.strip().split('\n'):
                    if ': ' in line:
                        key, value = line.split(': ', 1)
                        key = key.strip()
                        if key == 'action':
                            action['type'] = value.strip()
                        elif key == 'created':
                            action['created'] = value.strip()

        # Parse JSON details block at the end
        if '## Details' in content:
            details_section = content.split('## Details')[1].strip()
            try:
                action['details'] = json.loads(details_section)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract key-value pairs
                action['details'] = {}
                for line in details_section.split('\n'):
                    if line.strip() and ':' in line:
                        k, v = line.split(':', 1)
                        action['details'][k.strip()] = v.strip()

        return action

    def _execute_action(self, action: Dict[str, Any]) -> bool:
        """Execute the approved action"""
        action_type = action['type']
        details = action['details']

        if action_type == 'email_send':
            return self._execute_email_send(details)
        elif action_type == 'payment':
            return self._execute_payment(details)
        elif action_type == 'social_post':
            return self._execute_social_post(details)
        else:
            print(f"Unknown action type: {action_type}")
            return False

    def _execute_email_send(self, details: Dict[str, Any]) -> bool:
        """Execute approved email send"""
        # This would call the MCP email server
        print(f"Executing email send to {details['to']}")
        # email_server.send_email(details['to'], details['subject'], details['body'])
        return True

    def _execute_payment(self, details: Dict[str, Any]) -> bool:
        """Execute approved payment"""
        print(f"Executing payment of ${details['amount']} to {details['recipient']}")
        # payment_processor.make_payment(details)
        return True

    def _execute_social_post(self, details: Dict[str, Any]) -> bool:
        """Execute approved social post"""
        platform = details.get('platform', '').lower()

        if platform != 'linkedin':
            self.logger.error(f"Unsupported platform: {platform}. Only 'linkedin' is supported.")
            return False

        if not self.linkedin_watcher:
            self.logger.error("LinkedIn watcher not available")
            return False

        # Extract post details
        content = details.get('content', '')
        topic = details.get('topic', '')
        image_path = details.get('image_path')
        as_organization = details.get('as_organization', False)

        # Use content if provided, otherwise fall back to topic
        if not content and topic:
            content = f"Exploring {topic} today. This resonated with our audience. What are your thoughts? #Business #Growth"
        elif not content:
            self.logger.error("No content or topic provided for social post")
            return False

        self.logger.info(f"Posting to LinkedIn: {content[:50]}... (as_organization={as_organization})")

        try:
            success = self.linkedin_watcher.post_to_linkedin(
                content=content,
                image_path=image_path,
                as_organization=as_organization
            )
            if success:
                self.logger.info("LinkedIn post executed successfully")
            else:
                self.logger.error("LinkedIn post failed")
            return success
        except Exception as e:
            self.logger.error(f"Error executing LinkedIn post: {e}")
            return False

# Example usage:
# approval_workflow = ApprovalWorkflow('/path/to/vault')
# approval_file = approval_workflow.create_approval_request('email_send', {
#     'to': 'client@example.com',
#     'subject': 'Invoice #123',
#     'body': 'Please find attached your invoice...'
# })
# print(f'Created approval request: {approval_file}')