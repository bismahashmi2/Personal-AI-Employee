#!/usr/bin/env python3
"""
Test script for LinkedIn posting functionality.
Run this after getting "Share on LinkedIn" product approval.
"""

import logging
from linkedin_watcher import LinkedInWatcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("=" * 60)
    print("LinkedIn Integration Test")
    print("=" * 60)

    # Initialize watcher
    print("\n1. Initializing LinkedIn watcher...")
    watcher = LinkedInWatcher('.')

    if not watcher.access_token:
        print("❌ No access token found!")
        print("   Run: python3 linkedin_oauth_setup.py")
        return False

    print(f"✅ Token loaded (expires: {watcher.access_token[:20]}...)")
    print(f"✅ Member URN: {watcher.person_urn}")

    # Test posting
    print("\n2. Testing LinkedIn post...")
    test_message = """🚀 AI Employee Vault is now live!

Excited to share that our AI-powered business automation system is successfully integrated with LinkedIn.

Key features:
✅ Automated email monitoring and responses
✅ LinkedIn opportunity tracking
✅ Smart task prioritization
✅ Multi-channel communication management

#AI #Automation #BusinessTools #Productivity"""

    result = watcher.post_to_linkedin(test_message)

    if result:
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Post created on LinkedIn!")
        print("=" * 60)
        print("\nCheck your LinkedIn profile to see the post:")
        print("https://www.linkedin.com/in/me/")
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ FAILED to post to LinkedIn")
        print("=" * 60)
        print("\nPossible reasons:")
        print("1. LinkedIn app doesn't have 'Share on LinkedIn' product access")
        print("2. Token needs to be refreshed after product approval")
        print("3. API endpoint or format issue")
        print("\nNext steps:")
        print("- Check LinkedIn Developer Portal for product approval status")
        print("- Re-run OAuth setup after approval: python3 linkedin_oauth_setup.py")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
