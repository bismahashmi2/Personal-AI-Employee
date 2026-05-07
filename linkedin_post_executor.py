#!/usr/bin/env python3
"""
LinkedIn Post Executor
Monitors Approved/ folder for LinkedIn post approvals and executes them automatically.
Part of the Silver Tier automatic LinkedIn posting workflow.
"""

import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class LinkedInPostExecutor(FileSystemEventHandler):
    """
    Monitors Approved/ folder and automatically posts approved LinkedIn content.

    Workflow:
    1. Watches Approved/ folder for new files
    2. Parses approval files for LinkedIn post details
    3. Executes the post using LinkedInWatcher
    4. Moves completed files to Done/
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.logger = logging.getLogger('LinkedInPostExecutor')

        # Create directories if they don't exist
        self.approved.mkdir(exist_ok=True)
        self.done.mkdir(exist_ok=True)

        # Initialize LinkedIn watcher
        self.linkedin_watcher = None
        self._init_linkedin()

    def _init_linkedin(self):
        """Initialize LinkedIn watcher for posting"""
        try:
            from linkedin_watcher import LinkedInWatcher
            self.linkedin_watcher = LinkedInWatcher(str(self.vault_path))
            if self.linkedin_watcher.access_token:
                self.logger.info("✅ LinkedIn watcher initialized - ready to post")
            else:
                self.logger.warning("⚠️ LinkedIn watcher in demo mode - posting disabled")
        except Exception as e:
            self.logger.error(f"❌ Error initializing LinkedIn watcher: {e}")

    def on_created(self, event):
        """Handle new files in Approved/ folder"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process markdown files
        if file_path.suffix != '.md':
            return

        # Only process LinkedIn-related approvals
        if 'LINKEDIN' not in file_path.name.upper() and 'SOCIAL_POST' not in file_path.name.upper():
            return

        self.logger.info(f"📥 New approval detected: {file_path.name}")

        # Small delay to ensure file is fully written
        time.sleep(0.5)

        # Process the approval
        self.process_approval(file_path)

    def process_approval(self, approval_file: Path) -> bool:
        """Process an approved LinkedIn post"""
        try:
            self.logger.info(f"🔍 Processing approval: {approval_file.name}")

            # Parse the approval file
            action = self._parse_approval_file(approval_file)

            if not action:
                self.logger.error(f"❌ Could not parse approval file: {approval_file.name}")
                return False

            # Check if it's a LinkedIn post
            action_type = action.get('type', '')
            if action_type not in ['social_post', 'linkedin_post']:
                self.logger.info(f"⏭️ Skipping non-LinkedIn action: {action_type}")
                return False

            # Execute the post
            success = self._execute_linkedin_post(action)

            if success:
                # Move to Done/
                done_path = self.done / approval_file.name
                approval_file.rename(done_path)
                self.logger.info(f"✅ Post executed and moved to Done: {done_path.name}")
                return True
            else:
                self.logger.error(f"❌ Failed to execute post: {approval_file.name}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error processing approval {approval_file.name}: {e}")
            return False

    def _parse_approval_file(self, approval_file: Path) -> Optional[Dict[str, Any]]:
        """Parse approval file to extract action details"""
        try:
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

            # Parse JSON details block
            if '## Details' in content:
                details_section = content.split('## Details')[1].strip()
                try:
                    # Try to parse as JSON
                    action['details'] = json.loads(details_section)
                except json.JSONDecodeError:
                    # Fallback: extract key-value pairs
                    action['details'] = {}
                    for line in details_section.split('\n'):
                        if line.strip() and ':' in line and not line.strip().startswith('#'):
                            k, v = line.split(':', 1)
                            action['details'][k.strip()] = v.strip()

            return action if action else None

        except Exception as e:
            self.logger.error(f"Error parsing approval file: {e}")
            return None

    def _execute_linkedin_post(self, action: Dict[str, Any]) -> bool:
        """Execute the approved LinkedIn post"""
        if not self.linkedin_watcher:
            self.logger.error("LinkedIn watcher not available")
            return False

        if not self.linkedin_watcher.access_token:
            self.logger.error("LinkedIn access token not available")
            return False

        details = action.get('details', {})

        # Extract post details
        content = details.get('content', '')
        topic = details.get('topic', '')
        image_path = details.get('image_path')
        as_organization = details.get('as_organization', False)

        # Use content if provided, otherwise generate from topic
        if not content and topic:
            content = f"Exploring {topic} today. This resonated with our audience. What are your thoughts? #Business #Growth"
        elif not content:
            self.logger.error("No content or topic provided for LinkedIn post")
            return False

        self.logger.info(f"📤 Posting to LinkedIn: {content[:50]}...")

        try:
            success = self.linkedin_watcher.post_to_linkedin(
                content=content,
                image_path=image_path,
                as_organization=as_organization
            )

            if success:
                self.logger.info("✅ LinkedIn post published successfully!")
            else:
                self.logger.error("❌ LinkedIn post failed")

            return success

        except Exception as e:
            self.logger.error(f"❌ Error executing LinkedIn post: {e}")
            return False

    def process_existing_approvals(self):
        """Process any existing approval files in the Approved/ folder"""
        self.logger.info("🔍 Checking for existing approvals...")

        processed = 0
        for approval_file in self.approved.glob('*.md'):
            if 'LINKEDIN' in approval_file.name.upper() or 'SOCIAL_POST' in approval_file.name.upper():
                if self.process_approval(approval_file):
                    processed += 1

        if processed > 0:
            self.logger.info(f"✅ Processed {processed} existing approval(s)")
        else:
            self.logger.info("No existing LinkedIn approvals found")

    def run(self):
        """Start monitoring the Approved/ folder"""
        self.logger.info("=" * 60)
        self.logger.info("LinkedIn Post Executor Starting")
        self.logger.info("=" * 60)
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Monitoring: {self.approved}")
        self.logger.info(f"Completed: {self.done}")

        # Process any existing approvals first
        self.process_existing_approvals()

        # Set up file system observer
        observer = Observer()
        observer.schedule(self, str(self.approved), recursive=False)
        observer.start()

        self.logger.info("✅ Monitoring started - waiting for approvals...")
        self.logger.info("Press Ctrl+C to stop")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Stopping...")
            observer.stop()

        observer.join()
        self.logger.info("LinkedIn Post Executor stopped")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="LinkedIn Post Executor")
    parser.add_argument('--vault', default='.', help='Path to vault directory')
    parser.add_argument('--once', action='store_true', help='Process existing approvals and exit')

    args = parser.parse_args()

    executor = LinkedInPostExecutor(args.vault)

    if args.once:
        # Process existing approvals and exit
        executor.process_existing_approvals()
    else:
        # Run continuously
        executor.run()


if __name__ == '__main__':
    main()
