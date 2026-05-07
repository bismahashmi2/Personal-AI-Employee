import time
import logging
import os
import sys
from pathlib import Path
from base_watcher import BaseWatcher
import random
from datetime import datetime, timedelta
import json
import requests

class LinkedInWatcher(BaseWatcher):
    def __init__(self, vault_path: str, access_token: str = None):
        super().__init__(vault_path, check_interval=300)  # Check every 5 minutes
        self.access_token = access_token or self._load_token()
        self.refresh_token = None
        self.last_checked = time.time()
        self.person_urn = None
        self.organization_urn = None
        self._config_path = Path(vault_path) / 'linkedin_config.json'
        self._rate_limit_reset = 0
        self._rate_limit_remaining = 100
        self._load_config()

        # Demo topics for fallback mode
        self.mock_topics = [
            {'id': '1', 'title': 'AI Automation Trends for 2025', 'score': 0.95, 'category': 'Technology'},
            {'id': '2', 'title': 'Small Business Digital Transformation', 'score': 0.87, 'category': 'Business'},
            {'id': '3', 'title': 'Remote Work Best Practices', 'score': 0.82, 'category': 'Workplace'},
            {'id': '4', 'title': 'Personal AI Assistants Revolution', 'score': 0.91, 'category': 'AI'},
            {'id': '5', 'title': 'SMB Marketing Strategies That Work', 'score': 0.89, 'category': 'Marketing'},
        ]

        # API configuration
        # LinkedIn no longer requires explicit API version headers for most endpoints
        # Using the standard Restli protocol version
        self.restli_version = '2.0.0'

        # Log configuration status
        self._log_status()

    @staticmethod
    def _is_retryable_error(exception):
        """Determine if an exception should trigger a retry"""
        if isinstance(exception, requests.exceptions.RequestException):
            if hasattr(exception, 'response') and exception.response is not None:
                status = exception.response.status_code
                # Retry on rate limits (429) and server errors (5xx)
                return status == 429 or status >= 500
        return False

    def _check_rate_limit(self):
        """Check if we need to wait due to rate limiting"""
        now = time.time()
        if now < self._rate_limit_reset:
            wait_time = self._rate_limit_reset - now
            self.logger.warning(f"Rate limit active, waiting {wait_time:.1f}s")
            time.sleep(wait_time)

    def _make_api_request(self, method, url, **kwargs):
        """
        Make an API request with retry logic and rate limiting.

        Args:
            method: HTTP method (get, post, etc.)
            url: API endpoint URL
            **kwargs: Additional arguments for requests (headers, json, params, etc.)

        Returns:
            Response object or None if all retries failed
        """
        self._check_rate_limit()

        # Set default headers if not provided
        headers = kwargs.get('headers', {}).copy()
        # LinkedIn v2 API only requires X-Restli-Protocol-Version header
        # No LinkedIn-Version header needed for v2 endpoints
        if 'X-Restli-Protocol-Version' not in headers:
            headers['X-Restli-Protocol-Version'] = '2.0.0'
        kwargs['headers'] = headers
        kwargs['timeout'] = kwargs.get('timeout', 30)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.request(method, url, **kwargs)
                self._update_rate_limit(response)

                if response.status_code in (200, 201):
                    return response
                elif response.status_code == 429:
                    # Rate limited - extract retry after if available
                    self.logger.warning(f"Rate limited (429): {response.text}")
                    if 'Retry-After' in response.headers:
                        wait_time = int(response.headers['Retry-After'])
                        self.logger.info(f"Waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                    else:
                        # Exponential backoff
                        time.sleep(min(2 ** attempt * 5, 60))
                    continue
                elif response.status_code >= 500:
                    # Server error - retry
                    self.logger.warning(f"Server error {response.status_code}, retry {attempt + 1}/{max_retries}")
                    time.sleep(min(2 ** attempt * 2, 30))
                    continue
                elif response.status_code == 401:
                    # Unauthorized - token may be expired
                    self._handle_auth_error()
                    return None
                else:
                    # Other client error - don't retry
                    self.logger.error(f"API request failed: {response.status_code} - {response.text}")
                    return None

            except requests.exceptions.RequestException as e:
                if hasattr(e, 'response') and e.response is not None:
                    status = e.response.status_code
                    if status >= 500 or status == 429:
                        if attempt < max_retries - 1:
                            time.sleep(min(2 ** attempt * 2, 30))
                            continue
                self.logger.error(f"Request exception: {e}")
                return None

        self.logger.error(f"Max retries exceeded for {method} {url}")
        return None

    def _update_rate_limit(self, response):
        """Update rate limit info from response headers"""
        if 'X-RestLi-Request-Version' in response.headers:
            # LinkedIn uses various rate limit headers
            remaining = response.headers.get('X-RestLi-Request-Version')
        # Check for rate limit headers (LinkedIn may use different headers)
        if 'X-RateLimit-Remaining' in response.headers:
            self._rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
        if 'X-RateLimit-Reset' in response.headers:
            self._rate_limit_reset = float(response.headers['X-RateLimit-Reset'])
        elif 'Retry-After' in response.headers:
            self._rate_limit_reset = time.time() + int(response.headers['Retry-After'])

    def _load_config(self):
        """Load watcher configuration"""
        if self._config_path.exists():
            try:
                config = json.loads(self._config_path.read_text())
                self.organization_urn = config.get('organization_urn')
                self.person_urn = config.get('person_urn')  # Load cached person_urn
                self.logger.info(f"Config loaded: organization_urn={self.organization_urn}, person_urn={self.person_urn}")
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")

    def _log_status(self):
        """Log the current configuration status"""
        if self.access_token:
            if self.organization_urn:
                self.logger.info(f"✅ LinkedIn watcher ready - monitoring org: {self.organization_urn} + personal profile: {self.person_urn}")
            elif self.person_urn:
                self.logger.info(f"✅ LinkedIn watcher ready - monitoring personal profile: {self.person_urn}")
            else:
                self.logger.info("✅ LinkedIn watcher ready - token found, will discover profile on first run")
        else:
            self.logger.info("⚠️ LinkedIn watcher in demo mode - no access token found")

    def _load_token(self):
        """Load access token from linkedin_token.json"""
        token_path = Path('linkedin_token.json')
        if token_path.exists():
            try:
                token_data = json.loads(token_path.read_text())
                # Check if token is expired (LinkedIn tokens are long-lived but check anyway)
                expires_at_str = token_data.get('expires_at')
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    if expires_at > datetime.now():
                        self.access_token = token_data['access_token']
                        self.refresh_token = token_data.get('refresh_token')
                        self.logger.info("Loaded valid LinkedIn access token")
                        return token_data['access_token']
                    else:
                        self.logger.warning("LinkedIn token expired. Attempting to refresh...")
                        if self._refresh_access_token():
                            return self.access_token
                        else:
                            self.logger.warning("Token refresh failed. Please run linkedin_oauth_setup.py to refresh.")
                else:
                    # No expiry info, assume token is valid
                    self.access_token = token_data['access_token']
                    self.refresh_token = token_data.get('refresh_token')
                    return token_data['access_token']
            except Exception as e:
                self.logger.error(f"Error loading token: {e}")
        return None

    def _refresh_access_token(self) -> bool:
        """Refresh the access token using refresh_token"""
        if not self.refresh_token:
            self.logger.error("No refresh_token available")
            return False

        try:
            token_path = Path('linkedin_token.json')
            token_data = json.loads(token_path.read_text())

            # LinkedIn OAuth 2.0 token refresh endpoint
            response = requests.post(
                'https://www.linkedin.com/oauth/v2/accessToken',
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': self.refresh_token,
                    'client_id': token_data.get('client_id'),
                    'client_secret': token_data.get('client_secret'),
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )

            if response.status_code == 200:
                new_token_data = response.json()
                # Update token with new values
                new_access_token = new_token_data['access_token']
                expires_in = new_token_data.get('expires_in', 5184000)  # Default 60 days

                # Create updated token file
                token_data['access_token'] = new_access_token
                token_data['expires_at'] = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
                if 'refresh_token' in new_token_data:
                    token_data['refresh_token'] = new_token_data['refresh_token']

                token_path.write_text(json.dumps(token_data, indent=2))
                self.access_token = new_access_token
                self.logger.info("Successfully refreshed LinkedIn access token")
                return True
            else:
                self.logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"Error refreshing token: {e}")
            return False

    def _handle_auth_error(self):
        """Handle authentication errors - invalidate token and prompt for re-auth"""
        self.logger.warning("Authentication failed. Invalidating token.")
        self.access_token = None
        token_path = Path('linkedin_token.json')
        if token_path.exists():
            try:
                os.remove(token_path)
                self.logger.info("Removed expired token file. Run linkedin_oauth_setup.py to re-authenticate.")
            except Exception as e:
                self.logger.error(f"Error removing token file: {e}")

    def check_for_updates(self) -> list:
        """Check for LinkedIn trending topics from company page."""
        try:
            if self.access_token:
                # REAL API: Fetch posts from organization page
                return self._fetch_organization_topics()
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

    def _fetch_organization_topics(self) -> list:
        """Fetch and analyze posts. Uses personal feed if organization_urn is not set."""
        topics = []

        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0',
            }

            # Step 1: Get person URN - use cached from config first, only fetch if needed
            if not self.person_urn:
                # Try loading from config file (may have been set manually)
                if not self.person_urn:
                    self.person_urn = self._get_person_urn(headers)
                if not self.person_urn:
                    self.logger.error("Could not get person URN. Add it manually to linkedin_config.json")
                    return []

            # Step 2: Determine mode - organization or personal
            if self.organization_urn:
                self.logger.info(f"Mode: Organization monitoring ({self.organization_urn})")
                posts = self._fetch_organization_posts(headers)
            else:
                self.logger.info("Mode: Personal profile monitoring (no organization configured)")
                posts = self._fetch_personal_posts(headers)

            if not posts:
                self.logger.info("No posts found")
                return []

            # Step 3: Analyze posts to extract topics/insights
            topics = self._analyze_posts_for_topics(posts)
            self.logger.info(f"Analyzed {len(posts)} posts, found {len(topics)} topic opportunities")

        except Exception as e:
            self.logger.error(f'Error fetching topics: {e}')
            return []

        return topics

    def _get_person_urn(self, headers: dict) -> str:
        """Get the authenticated person's URN using OpenID Connect."""
        # If we already have a person_urn in config, use it
        if self.person_urn:
            return self.person_urn

        # Try to get person URN from OpenID userinfo endpoint
        # This works with openid scope and returns the 'sub' field
        try:
            response = self._make_api_request(
                'get',
                'https://api.linkedin.com/v2/userinfo',
                headers=headers
            )
            if response:
                data = response.json()
                user_id = data.get('sub')
                if user_id:
                    # Use person URN format with OpenID sub
                    person_urn = f"urn:li:person:{user_id}"
                    self.logger.info(f"Got person URN from OpenID: {person_urn}")
                    self.person_urn = person_urn
                    self._save_config()  # Persist for future use
                    return person_urn
                else:
                    self.logger.error("OpenID userinfo response missing 'sub' field")
        except Exception as e:
            self.logger.error(f"Error getting person URN from OpenID: {e}")

        # Final fallback: prompt user to manually set person_urn
        self.logger.error(
            "Cannot get person URN from API. "
            "Please manually add your URN to linkedin_config.json as 'person_urn' "
            "(format: urn:li:person:YOUR_ID from OpenID 'sub' field). "
        )
        return None

    def _find_organization_urn(self, headers: dict) -> str:
        """Find the organization URN for pages the user administers."""
        try:
            response = self._make_api_request(
                'get',
                'https://api.linkedin.com/rest/organizationAcls',
                headers=headers,
                params={
                    'q': 'roleAssignee',
                    'assignee': self.person_urn,
                    'state': 'APPROVED',
                    'role': 'ADMINISTRATOR',
                }
            )
            if response:
                data = response.json()
                elements = data.get('elements', [])
                if elements:
                    # Get first administered organization
                    org_urn = elements[0].get('organization')
                    org_name = elements[0].get('organizationName', 'Unknown')
                    self.logger.info(f"Found administered organization: {org_name} ({org_urn})")
                    return org_urn
                else:
                    self.logger.warning("No administered organizations found. You must be an admin of a LinkedIn Company Page.")
            return None
        except Exception as e:
            self.logger.error(f"Error finding organization: {e}")
        return None

    def _fetch_personal_posts(self, headers: dict, count: int = 50) -> list:
        """Fetch recent posts from the authenticated user's feed (personal profile)."""
        try:
            # Option 1: Use the shares endpoint for the person's own posts
            response = self._make_api_request(
                'get',
                'https://api.linkedin.com/rest/shares',
                headers=headers,
                params={
                    'q': 'members',
                    'members': f'List({self.person_urn})',
                    'count': count,
                    'sortBy': 'LAST_MODIFIED',
                }
            )
            if response:
                data = response.json()
                posts = data.get('elements', [])
                self.logger.info(f"Fetched {len(posts)} posts from personal profile")
                return posts
            return []
        except Exception as e:
            self.logger.error(f"Error fetching personal posts: {e}")
        return []

    def _fetch_organization_posts(self, headers: dict, count: int = 50) -> list:
        """Fetch recent posts from the organization page."""
        try:
            response = self._make_api_request(
                'get',
                'https://api.linkedin.com/rest/posts',
                headers=headers,
                params={
                    'q': 'authors',
                    'authors': f'List({self.organization_urn})',
                    'count': count,
                    'sortBy': 'LAST_MODIFIED',
                }
            )
            if response:
                data = response.json()
                posts = data.get('elements', [])
                self.logger.info(f"Fetched {len(posts)} posts from organization page")
                return posts
            return []
        except Exception as e:
            self.logger.error(f"Error fetching posts: {e}")
        return []

    def _analyze_posts_for_topics(self, posts: list) -> list:
        """Analyze posts (organization or personal) to extract trending topics and insights."""
        topics = []
        seen_titles = set()

        for post in posts:
            try:
                # Extract post content (handle both personal shares and organization posts)
                post_id = post.get('id', '').split(':')[-1]
                content = ''

                # Organization posts use specificContent
                if 'specificContent' in post:
                    share_content = post.get('specificContent', {}).get('com.linkedin.ugc.ShareContent', {})
                    if 'shareCommentary' in share_content:
                        content = share_content['shareCommentary'].get('text', '')

                # Personal shares may have 'text' directly or 'shareCommentary'
                elif 'text' in post:
                    content = post.get('text', '')
                elif 'shareCommentary' in post:
                    content = post.get('shareCommentary', {}).get('text', '')

                # Fallback: check various paths
                if not content:
                    # Try to extract from any nested text fields
                    def find_text(obj):
                        if isinstance(obj, str):
                            return obj
                        if isinstance(obj, dict):
                            for key in ['text', 'value', 'commentary']:
                                if key in obj:
                                    result = find_text(obj[key])
                                    if result:
                                        return result
                            for val in obj.values():
                                result = find_text(val)
                                if result:
                                    return result
                        return None
                    content = find_text(post) or ''

                # Get engagement metrics
                social_metrics = post.get('socialMetadata', {})
                reactions = social_metrics.get('numReactions', 0)
                comments = social_metrics.get('numComments', 0)
                shares = social_metrics.get('numShares', 0)
                total_engagement = reactions + comments + (shares * 2)  # Weight shares higher

                # Get creation date
                created_at = post.get('createdAt', {}).get('start', 0) / 1000  # Convert from ms
                created_date = datetime.fromtimestamp(created_at) if created_at else datetime.now()

                # Extract keywords/topics from content
                extracted_topics = self._extract_keywords(content)

                for keyword, category in extracted_topics:
                    if keyword in seen_titles:
                        continue
                    seen_titles.add(keyword)

                    # Score based on engagement and recency
                    recency_days = (datetime.now() - created_date).days
                    recency_score = max(0, 1 - (recency_days / 30))  # Decay over 30 days
                    engagement_score = min(1, total_engagement / 100)  # Cap at 100

                    score = (engagement_score * 0.6) + (recency_score * 0.4)

                    if score > 0.3:  # Only include relevant topics
                        topics.append({
                            'id': f"org_{post_id[:8]}_{len(topics)}",
                            'title': keyword,
                            'score': round(score, 2),
                            'category': category,
                            'engagement': {
                                'reactions': reactions,
                                'comments': comments,
                                'shares': shares,
                                'total': total_engagement,
                            },
                            'post_id': post_id,
                            'created_date': created_date.strftime('%Y-%m-%d'),
                        })

            except Exception as e:
                self.logger.warning(f"Error analyzing post: {e}")
                continue

        # Sort by score descending
        topics.sort(key=lambda x: x['score'], reverse=True)
        return topics[:10]  # Return top 10 topics

    def _extract_keywords(self, content: str) -> list:
        """Extract meaningful keywords from post content."""
        if not content:
            return []

        import re
        from collections import Counter

        # Remove URLs, mentions, hashtags from word extraction
        content = re.sub(r'https?://\S+', '', content)
        content = re.sub(r'@\S+', '', content)

        # Extract hashtags as topics (high relevance)
        hashtags = re.findall(r'#(\w+)', content)
        keywords = []

        for tag in hashtags:
            if len(tag) > 2 and tag.lower() not in ['ai', 'business', 'automation']:
                keywords.append((tag.title(), 'hashtag'))

        # Extract capitalized phrases (likely topics)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        for phrase in capitalized:
            if len(phrase.split()) <= 3 and len(phrase) > 5:
                keywords.append((phrase, 'capitalized'))

        # If no hashtags/capitalized, use common keywords
        if len(keywords) < 3:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
            stop_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'your', 'have', 'more', 'about'}
            words = [w for w in words if w not in stop_words]
            counter = Counter(words)
            for word, _ in counter.most_common(3):
                keywords.append((word.title(), 'keyword'))

        return keywords

    def _save_config(self):
        """Save configuration to file."""
        config = {
            'organization_urn': self.organization_urn,
            'person_urn': self.person_urn,
            'mode': 'organization' if self.organization_urn else 'personal',
            'updated_at': datetime.now().isoformat()
        }
        try:
            self._config_path.write_text(json.dumps(config, indent=2))
            self.logger.debug(f"Config saved to {self._config_path}")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def setup_organization(self, organization_urn: str = None) -> str:
        """
        Manual setup: configure the organization URN.
        Returns the person URN needed to discover organization.

        Call this if automatic discovery fails.
        """
        if not self.person_urn:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            self.person_urn = self._get_person_urn(headers)

        if not organization_urn:
            self.logger.info("To find your organization URN:")
            self.logger.info("1. Go to your LinkedIn Company Page")
            self.logger.info("2. URL format: linkedin.com/company/{company-name}")
            self.logger.info("3. Organization URN format: urn:li:organization:{company-id}")
            self.logger.info("   (company-id is numeric, find via LinkedIn API or page source)")
            return self.person_urn

        self.organization_urn = organization_urn
        self._save_config()
        return self.person_urn

    def post_to_linkedin(self, content: str, image_path: str = None, as_organization: bool = False) -> bool:
        """
        Post content to LinkedIn as the authenticated user or organization.

        Args:
            content: The post text (max 3000 chars)
            image_path: Optional path to an image file to upload
            as_organization: If True and organization_urn is set, post as the organization

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

            # Get person URN if needed
            if not self.person_urn:
                self.person_urn = self._get_person_urn(headers)
                if not self.person_urn:
                    return False

            # Determine author
            author = self.organization_urn if (as_organization and self.organization_urn) else self.person_urn
            if not author:
                self.logger.error("No author URN available")
                return False

            # Upload image if provided
            asset = None
            if image_path:
                asset = self._upload_image(image_path, headers, author)
                if not asset:
                    self.logger.warning("Failed to upload image, posting without it")

            # Create post
            post_data = {
                'author': author,
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
                    'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC' if not as_organization else 'CONNECTIONS'
                }
            }

            if asset:
                post_data['specificContent']['com.linkedin.ugc.ShareContent']['media'] = [{
                    'status': 'READY',
                    'media': asset,
                    'title': {'text': 'Image'}
                }]
                post_data['specificContent']['com.linkedin.ugc.ShareContent']['shareMediaCategory'] = 'IMAGE'

            response = self._make_api_request(
                'post',
                'https://api.linkedin.com/v2/ugcPosts',
                headers=headers,
                json=post_data
            )

            if response:
                post_urn = response.headers.get('X-RestLi-Id') or response.json().get('id', 'unknown')
                self.logger.info(f"Successfully posted to LinkedIn: {content[:50]}... (URN: {post_urn})")
                return True
            return False

        except Exception as e:
            self.logger.error(f' LinkedIn post error: {e}')
            return False

    def _upload_image(self, image_path: str, headers: dict, owner_urn: str) -> dict:
        """Upload an image to LinkedIn and return the asset URN."""
        try:
            image_file = Path(image_path)
            if not image_file.exists():
                self.logger.error(f"Image not found: {image_path}")
                return None

            # Step 1: Register upload
            register_response = self._make_api_request(
                'post',
                'https://api.linkedin.com/rest/assets?action=registerUpload',
                headers=headers,
                json={
                    "registerUploadRequest": {
                        "owner": owner_urn,
                        "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                        "serviceRelationships": [
                            {
                                "relationshipType": "OWNER",
                                "identifier": "urn:li:userGeneratedContent"
                            }
                        ]
                    }
                }
            )
            if not register_response:
                return None

            upload_info = register_response.json()['value']
            upload_url = upload_info['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset = upload_info['asset']

            # Step 2: Upload the image bytes (this is a direct PUT to pre-signed URL, no auth needed)
            with open(image_file, 'rb') as f:
                image_data = f.read()

            upload_response = requests.put(
                upload_url,
                headers={'Content-Type': 'application/octet-stream'},
                data=image_data,
                timeout=60  # Image uploads can take longer
            )

            if upload_response.status_code not in (200, 201):
                self.logger.error(f"Failed to upload image data: {upload_response.status_code}")
                return None

            self.logger.info(f"Image uploaded successfully, asset: {asset}")
            return {'asset': asset}

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Image upload network error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Image upload error: {e}")
            return None

    def create_action_file(self, topic) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"LINKEDIN_{topic['id']}_{timestamp}.md"
        filepath = self.needs_action / filename
        has_token = self.access_token is not None
        org_configured = self.organization_urn is not None
        is_personal_mode = self.person_urn and not org_configured

        engagement = topic.get('engagement', {})
        engagement_text = f"""
- **Reactions:** {engagement.get('reactions', 0)}
- **Comments:** {engagement.get('comments', 0)}
- **Shares:** {engagement.get('shares', 0)}
- **Total Engagement:** {engagement.get('total', 0)}""" if engagement else ""

        post_text = f"Exploring {topic['title']} today. This resonated with my audience ({engagement.get('total', 0)} engagements). What are your thoughts? #Business #Growth"

        if org_configured:
            header = "# LinkedIn Company Page Insight"
            source_text = "your organization page"
            post_as_note = "Post as organization (requires admin rights)"
            note_text = "- This topic came from YOUR organization page analytics"
        else:
            header = "# LinkedIn Personal Feed Insight"
            source_text = "your personal feed"
            post_as_note = "Post to personal profile (w_member_social scope)"
            note_text = "- This topic came from YOUR LinkedIn feed\n- Consider how this relates to your expertise and business"

        content = f"""---
type: linkedin_opportunity
opportunity: {topic['title']}
trend_score: {topic['score']}
category: {topic.get('category', 'Unknown')}
detected: {datetime.now().isoformat()}
person_urn: {self.person_urn or 'Not configured'}
organization_urn: {self.organization_urn or 'Not configured'}
post_id: {topic.get('post_id', 'N/A')}
created_date: {topic.get('created_date', 'Unknown')}
status: pending
---

{header}

## 🔍 Topic Detected
**{topic['title']}**

This content appeared on {source_text}. High engagement topics indicate what resonates with your audience.

## 📊 Performance Metrics{engagement_text}

## 🎯 Business Opportunity
This topic is gaining traction on LinkedIn. Consider:
- ✅ Creating NEW content on this topic
- ✅ Repurposing this successful angle for your own perspective
- ✅ Adding your unique business lens to the conversation

## 💡 Recommended Actions
- [ ] Research this topic for deeper insights
- [ ] Create follow-up content expanding on this theme
- [ ] Craft a LinkedIn post with your business perspective
- [ ] Include relevant hashtags from the original post
- [ ] Add a call-to-action for your services
- [ ] Monitor comments for additional ideas

## 📝 Post Template
{post_text}

## 🚀 Auto-Publish Options
{f'- [x] LinkedIn API token configured' if has_token else '- [ ] Run: `python linkedin_oauth_setup.py` to enable posting'}
{f'- [x] Organization page set: {self.organization_urn}' if org_configured else '- [ ] Organization not configured (using personal profile posting)'}

## 📋 Notes
{note_text}
- High engagement = your connections care about this
- Replicate success with similar content themes
- Add your unique business perspective
"""

        filepath.write_text(content)
        self.logger.info(f"Created LinkedIn opportunity file: {filepath}")
        return filepath

    def _handle_tool_call(self, tool_name: str, arguments: dict) -> dict:
        """Handle a tool call and return result"""
        # Handle base tools that we want to override first
        if tool_name == 'get_status':
            token_path = Path('linkedin_token.json')
            config_path = self._config_path
            return {
                'watcher': 'LinkedInWatcher',
                'vault_path': str(self.vault_path),
                'check_interval': self.check_interval,
                'running': self.running,
                'access_token': 'configured' if self.access_token else 'demo_mode',
                'person_urn': self.person_urn,
                'organization_urn': self.organization_urn,
                'config_path': str(config_path),
                'config_exists': config_path.exists(),
                'token_path': str(token_path),
                'token_exists': token_path.exists(),
                'rate_limit_remaining': self._rate_limit_remaining,
                'last_check': datetime.fromtimestamp(self.last_checked).isoformat() if self.last_checked else None
            }
        elif tool_name == 'stop':
            self.stop()
            return {'stopped': True}
        elif tool_name == 'check_for_updates':
            items = self.check_for_updates()
            created = []
            for item in items:
                path = self.create_action_file(item)
                created.append(str(path))
            return {
                'items_found': len(items),
                'action_files': created
            }

        # Handle LinkedIn-specific tools
        if tool_name == 'refresh_token':
            if self._refresh_access_token():
                return {
                    'success': True,
                    'expires_at': (datetime.now() + timedelta(seconds=5184000)).isoformat(),
                    'message': 'Token refreshed successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Token refresh failed. Run linkedin_oauth_setup.py to re-authenticate.'
                }
        elif tool_name == 'setup_organization':
            # Run setup and return results
            result = {'person_urn': None, 'organization_urn': None, 'message': ''}

            if not self.access_token:
                result['message'] = 'No access token. Run linkedin_oauth_setup.py first.'
                return result

            # Get person URN if not cached
            if not self.person_urn:
                headers = {'Authorization': f'Bearer {self.access_token}'}
                self.person_urn = self._get_person_urn(headers)

            if not self.person_urn:
                result['message'] = 'Could not authenticate with LinkedIn API'
                return result

            result['person_urn'] = self.person_urn

            # Try to discover organizations
            headers = {'Authorization': f'Bearer {self.access_token}'}
            discovered_org = self._find_organization_urn(headers)

            if discovered_org:
                self.organization_urn = discovered_org
                self._save_config()
                result['organization_urn'] = discovered_org
                result['message'] = f'Organization auto-discovered and configured: {discovered_org}'
            else:
                result['message'] = 'No administered organizations found. Set organization_urn manually in linkedin_config.json'

            return result
        elif tool_name == 'test_connection':
            headers = {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}
            result = {
                'mode': 'demo' if not self.access_token else 'live',
                'person_urn': None,
                'organization_urn': None,
                'organization_count': 0
            }

            if self.access_token:
                # Test person URN fetch
                person_urn = self._get_person_urn(headers)
                result['person_urn'] = person_urn

                if person_urn:
                    # Test organization discovery
                    org_urn = self._find_organization_urn(headers)
                    result['organization_urn'] = org_urn
                    result['organization_count'] = 1 if org_urn else 0

            return result
        else:
            raise Exception(f'Unknown tool: {tool_name}')

    def _get_mcp_tools(self) -> list:
        """Return list of MCP tools exposed by this watcher"""
        # Include base class tools (get_status, check_for_updates, stop) plus LinkedIn-specific ones
        base_tools = super()._get_mcp_tools()
        linkedin_tools = [
            {
                'name': 'refresh_token',
                'description': 'Manually refresh the OAuth access token',
                'inputSchema': {
                    'type': 'object',
                    'properties': {},
                }
            },
            {
                'name': 'setup_organization',
                'description': 'Run interactive setup to discover or configure the organization URN',
                'inputSchema': {
                    'type': 'object',
                    'properties': {},
                }
            },
            {
                'name': 'test_connection',
                'description': 'Test LinkedIn API connection and return results',
                'inputSchema': {
                    'type': 'object',
                    'properties': {},
                }
            }
        ]
        return base_tools + linkedin_tools


def setup_organization_watcher(vault_path: str, organization_urn: str = None):
    """
    Helper function to configure the LinkedIn organization watcher.
    Run this to discover your organization URN and save configuration.

    Usage:
        python -c "from linkedin_watcher import setup_organization_watcher; setup_organization_watcher('.')"

    Or add to silver_tier_main.py for interactive setup.
    """
    import sys
    from pathlib import Path

    vault = Path(vault_path)
    token_path = vault / 'linkedin_token.json'

    if not token_path.exists():
        print("❌ No linkedin_token.json found!")
        print("   Run: python linkedin_oauth_setup.py first")
        return

    # Load token and create watcher
    token_data = json.loads(token_path.read_text())
    access_token = token_data['access_token']

    watcher = LinkedInWatcher(vault_path, access_token)

    # Test token and get person URN
    print("\n" + "="*60)
    print("🔧 LinkedIn Organization Setup")
    print("="*60)

    print("\n1. Testing access token...")
    if not watcher.person_urn:
        headers = {'Authorization': f'Bearer {access_token}'}
        watcher.person_urn = watcher._get_person_urn(headers)

    if not watcher.person_urn:
        print("❌ Could not authenticate with LinkedIn API")
        print("   Check your token and try re-authenticating")
        return

    print(f"   ✅ Authenticated as: {watcher.person_urn}")

    # Check if organization already configured
    if watcher.organization_urn:
        print(f"   ℹ️ Organization already configured: {watcher.organization_urn}")
        response = input("\n   Reconfigure? (y/N): ").strip().lower()
        if response != 'y':
            print("   Setup complete!")
            return

    # Try to discover organizations
    print("\n2. Looking for administered organizations...")
    headers = {'Authorization': f'Bearer {access_token}'}

    if not organization_urn:
        discovered_org = watcher._find_organization_urn(headers)

    if organization_urn:
        # Manual URN provided
        watcher.organization_urn = organization_urn
        watcher._save_config()
        print(f"   ✅ Organization configured: {organization_urn}")
    elif discovered_org:
        response = input(f"\n3. Found: {discovered_org}\n   Use this? (Y/n): ").strip().lower()
        if response != 'n':
            watcher.organization_urn = discovered_org
            watcher._save_config()
            print(f"   ✅ Organization configured: {discovered_org}")
        else:
            print("\n   Please enter your organization URN manually.")
            print("   Format: urn:li:organization:{company-id}")
            manual_urn = input("   > ").strip()
            if manual_urn.startswith('urn:li:organization:'):
                watcher.organization_urn = manual_urn
                watcher._save_config()
                print(f"   ✅ Organization configured: {manual_urn}")
            else:
                print("   Invalid format. Configuration not saved.")
                return
    else:
        print("\n   ⚠️ No administered organizations found!")
        print("\n   To monitor your company page, ensure:")
        print("   1. You have a LinkedIn Company Page")
        print("   2. Your user account is an ADMIN of that page")
        print("   3. Your app has r_organization_social scope (requires Marketing Developer access)")

        print("\n   Manual configuration:")
        print("   a) Find your company ID:")
        print("      - Go to your company page")
        print("      - URL: linkedin.com/company/{company-name}")
        print("      - Company ID is numeric - find via Page Source or LinkedIn API explorer")
        print("\n   b) Create linkedin_config.json manually:")

        manual_config = {
            "organization_urn": "urn:li:organization:YOUR_COMPANY_ID"
        }
        print(f"      {json.dumps(manual_config, indent=2)}")

        return

    print("\n" + "="*60)
    print("✅ Setup complete!")
    print("="*60)
    print(f"\nYour watcher is configured to monitor:")
    print(f"  Person: {watcher.person_urn}")
    print(f"  Organization: {watcher.organization_urn}")
    print("\nRun the watcher:")
    print("  python silver_tier_main.py --vault .")
    print("\nIt will create action files in Needs_Action/ when:")
    print("  - New posts are published on your company page")
    print("  - Existing posts gain high engagement")
    print("\nCheck Needs_Action/ for content opportunities!")


if __name__ == '__main__':
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="LinkedIn Watcher - MCP Service")
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=50056, help='Port to bind to')
    parser.add_argument('--vault', default='.', help='Path to vault directory')
    parser.add_argument('--setup', action='store_true', help='Run interactive organization setup')
    parser.add_argument('--once', action='store_true', help='Run one check and exit (for testing)')

    args = parser.parse_args()

    if args.setup:
        # Run interactive setup
        setup_organization_watcher(args.vault)
        sys.exit(0)

    # Initialize watcher
    vault_path = Path(args.vault).resolve()

    # Load token if available
    token_path = vault_path / 'linkedin_token.json'
    access_token = None
    if token_path.exists():
        try:
            token_data = json.loads(token_path.read_text())
            access_token = token_data['access_token']
        except Exception as e:
            print(f"Warning: Could not load token: {e}")

    watcher = LinkedInWatcher(str(vault_path), access_token)

    if args.once:
        # Single check mode for testing
        print("Running single check...")
        topics = watcher.check_for_updates()
        print(f"Found {len(topics)} topics")
        for topic in topics:
            print(f"  - {topic['title']} (score: {topic['score']})")
            action_file = watcher.create_action_file(topic)
            print(f"    Created: {action_file}")
        sys.exit(0)

    # Run as MCP service with continuous monitoring
    print(f"LinkedIn Watcher MCP Service starting on {args.host}:{args.port}")
    print(f"Vault: {vault_path}")
    watcher.run_mcp_server(host=args.host, port=args.port)