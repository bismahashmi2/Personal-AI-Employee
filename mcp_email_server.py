import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import logging
import time

class EmailMCPServer:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger('EmailMCPServer')

    def _load_config(self, config_path: str):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Expand environment variables in config values
            for key, value in config.items():
                if isinstance(value, str):
                    # Replace ${VAR} with environment variable
                    if value.startswith('${') and value.endswith('}'):
                        var_name = value[2:-1]
                        config[key] = os.getenv(var_name, value)
                    # Also handle $VAR format
                    elif value.startswith('$'):
                        var_name = value[1:]
                        config[key] = os.getenv(var_name, value)

            return config
        except Exception as e:
            self.logger.error(f'Failed to load config: {e}')
            return {}

    def send_email(self, to: str, subject: str, body: str, from_email: str = None) -> dict:
        """Send an email through MCP interface"""
        if not from_email:
            from_email = self.config.get('default_from', 'noreply@business.com')

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to
            msg['Subject'] = subject

            # Add body
            msg.attach(MIMEText(body, 'plain'))

            # Connect to SMTP server
            server = smtplib.SMTP(self.config['smtp_host'], self.config['smtp_port'])
            if self.config.get('smtp_use_tls', True):
                server.starttls()
            if self.config.get('smtp_auth', False):
                server.login(self.config['smtp_user'], self.config['smtp_password'])

            # Send email
            server.send_message(msg)
            server.quit()

            self.logger.info(f'Email sent to {to}')
            return {'status': 'success', 'message': 'Email sent successfully'}

        except Exception as e:
            self.logger.error(f'Failed to send email: {e}')
            return {'status': 'error', 'message': str(e)}

    def draft_email(self, to: str, subject: str, body: str, from_email: str = None) -> dict:
        """Create a draft email (for approval workflow)"""
        draft_path = Path(f'drafts/{to}_{subject.replace(" ", "_")}.md')

        content = f"""---
type: email_draft
to: {to}
subject: {subject}
from: {from_email or 'noreply@business.com'}
created: {time.strftime('%Y-%m-%d %H:%M:%S')}
status: pending_approval
---

## Email Draft

{body}

## Approval Required
Move this file to /Approved to send.
"""

        draft_path.write_text(content)
        self.logger.info(f'Email draft created for {to}')
        return {'status': 'success', 'message': 'Email draft created', 'path': str(draft_path)}

    def list_drafts(self) -> list:
        """List all pending email drafts"""
        drafts_dir = Path('drafts')
        if not drafts_dir.exists():
            return []

        drafts = []
        for draft_file in drafts_dir.glob('*.md'):
            content = draft_file.read_text()
            # Parse basic info from content
            drafts.append({
                'file': str(draft_file),
                'subject': draft_file.stem,
                'status': 'pending'
            })

        return drafts