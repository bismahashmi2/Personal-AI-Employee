import time
import logging
from pathlib import Path
from base_watcher import BaseWatcher
import random
from datetime import datetime
import json
import requests

class LinkedInWatcher(BaseWatcher):
    def __init__(self, vault_path: str, access_token: str = None):
        super().__init__(vault_path, check_interval=300)  # Check every 5 minutes
        self.access_token = access_token or self._load_token()
        self.last_checked = time.time()
        self.mock_topics = [
            {'id': '1', 'title': 'AI Automation Trends for 2025', 'score': 0.95, 'category': 'Technology'},
            {'id': '2', 'title': 'Small Business Digital Transformation', 'score': 0.87, 'category': 'Business'},
            {'id': '3', 'title': 'Remote Work Best Practices', 'score': 0.82, 'category': 'Workplace'},
            {'id': '4', 'title': 'Personal AI Assistants Revolution', 'score': 0.91, 'category': 'AI'},
            {'id': '5', 'title': 'SMB Marketing Strategies That Work', 'score': 0.89, 'category': 'Marketing'},
        ]

    def _load_token(self):
        """Load access token from token.json"""
        token_path = Path('token.json')
        if token_path.exists():
            try:
                token_data = json.loads(token_path.read_text())
                # Check if token is expired (LinkedIn tokens are long-lived but check anyway)
                expires_at = datetime.fromisoformat(token_data.get('expires_at', ''))
                if expires_at > datetime.now():
                    return token_data['access_token']
                else:
                    self.logger.warning("LinkedIn token expired. Please run linkedin_oauth_setup.py to refresh.")
            except Exception as e:
                self.logger.error(f"Error loading token: {e}")
        return None

    def check_for_updates(self) -> list:
        """Check for LinkedIn trending topics."""
        try:
            if self.access_token:
                # REAL API: Fetch trending topics from LinkedIn
                return self._fetch_linkedin_topics()
            else:
                # DEMO MODE: Return random trending topics for demonstration
                self.logger.debug("No LinkedIn access token - running in demo mode")
                time.sleep(1)  # Simulate API latency

                # Return 1-2 random topics occasionally (10% chance per check)
                if random.random() < 0.1:
                    num_topics = random.randint(1, 2)
                    selected = random.sample(self.mock_topics, num_topics)
                    self.logger.info(f"Found {len(selected)} LinkedIn opportunities (demo)")
                    return selected

                return []

        except Exception as e:
            self.logger.error(f'LinkedIn watcher error: {e}')
            return []

    def _fetch_linkedin_topics(self) -> list:
        """Fetch real trending topics from LinkedIn API."""
        # Note: LinkedIn doesn't have a public trending topics endpoint
        # This is a placeholder - you would need to implement actual API calls
        # based on your use case (e.g., company page updates, feed trends)

        self.logger.warning("LinkedIn API integration not fully implemented")
        self.logger.info("Using demo topics instead. To implement, modify _fetch_linkedin_topics()")

        # For now, return empty (no demo topics when real token exists)
        return []

    def post_to_linkedin(self, content: str, image_path: str = None) -> bool:
        """
        Post content to LinkedIn as the authenticated user.

        Args:
            content: The post text (max 3000 chars)
            image_path: Optional path to an image file to upload

        Returns:
            True if post was created successfully
        """
        if not self.access_token:
            self.logger.error("No LinkedIn access token. Run linkedin_oauth_setup.py first.")
            return False

        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0',
            }

            # Upload image if provided
            asset = None
            if image_path:
                asset = self._upload_image(image_path, headers)
                if not asset:
                    self.logger.warning("Failed to upload image, posting without it")

            # Create post
            post_data = {
                'author': 'urn:li:person:{AUTHOR_URN}',  # Get this from your profile API
                'lifecycleState': 'PUBLISHED',
                'specificContent': {
                    'com.linkedin.ugc.ShareContent': {
                        'shareCommentary': {
                            'text': content[:3000]  # Truncate to limit
                        },
                        'shareMediaCategory': 'NONE' if not asset else 'IMAGE',
                    }
                },
                'visibility': {
                    'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
                }
            }

            if asset:
                post_data['specificContent']['com.linkedin.ugc.ShareContent']['media'] = [{
                    'status': 'READY',
                    'media': asset,
                    'title': {'text': 'Image'}
                }]
                post_data['specificContent']['com.linkedin.ugc.ShareContent']['shareMediaCategory'] = 'IMAGE'

            response = requests.post(
                'https://api.linkedin.com/rest/ugcPosts',
                headers=headers,
                json=post_data
            )

            if response.status_code in (200, 201):
                self.logger.info(f"Successfully posted to LinkedIn: {content[:50]}...")
                return True
            else:
                self.logger.error(f"LinkedIn post failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            self.logger.error(f' LinkedIn post error: {e}')
            return False

    def _upload_image(self, image_path: str, headers: dict) -> dict:
        """Upload an image to LinkedIn and return the asset URN."""
        try:
            image_file = Path(image_path)
            if not image_file.exists():
                self.logger.error(f"Image not found: {image_path}")
                return None

            # First, register upload
            register_data = {
                "initializeUploadRequest": {
                    "owner": "urn:li:person:{AUTHOR_URN}",
                }
            }

            # You need to get the person URN first via profile API
            # This is simplified - implement proper URN retrieval
            return None  # Placeholder

        except Exception as e:
            self.logger.error(f"Image upload error: {e}")
            return None

    def create_action_file(self, topic) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"LINKEDIN_{topic['id']}_{timestamp}.md"
        filepath = self.needs_action / filename
        has_token = self.access_token is not None

        post_text = f"Exploring {topic['title']} today. This is a hot topic in {topic['category']} with a relevance score of {topic['score']:.2f}. What are your thoughts? #AI #Business #Automation"

        content = f"""---
type: linkedin_opportunity
opportunity: {topic['title']}
trend_score: {topic['score']}
category: {topic['category']}
detected: {datetime.now().isoformat()}
status: pending
---

# LinkedIn Business Opportunity

## Trending Topic
**{topic['title']}**

## Metrics
- **Relevance Score:** {topic['score']}
- **Category:** {topic['category']}
- **Detected:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Analysis
This trending topic presents a business development opportunity. Creating content around this could generate leads and increase brand visibility.

## Recommended Actions
- [ ] Research the topic in depth
- [ ] Craft LinkedIn post with business insights
- [ ] Include relevant hashtags (#AI, #Business, #Automation)
- [ ] Tag relevant industry influencers
- [ ] Add call-to-action for services
- [ ] Schedule for optimal engagement time
- [ ] Monitor comments and engage

## Auto-Post Ready
{f'- [x] LinkedIn API configured (token.json exists)' if has_token else '- [ ] Run linkedin_oauth_setup.py to enable auto-posting'}

## Post Template
{post_text}

## Notes
- To auto-post: approve the action and the system will publish to LinkedIn
- You can also copy this template and customize before posting
"""

        filepath.write_text(content)
        self.logger.info(f"Created LinkedIn opportunity file: {filepath}")
        return filepath