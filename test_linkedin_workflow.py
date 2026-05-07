#!/usr/bin/env python3
"""
Test LinkedIn Auto-Posting Workflow
Tests the complete Silver Tier LinkedIn auto-posting implementation.
"""

import time
import json
from pathlib import Path
from datetime import datetime

def test_workflow():
    """Test the complete LinkedIn auto-posting workflow"""

    print("=" * 70)
    print("🧪 Testing LinkedIn Auto-Posting Workflow")
    print("=" * 70)
    print()

    vault_path = Path('.')

    # Check required directories
    print("1️⃣ Checking directory structure...")
    required_dirs = ['Needs_Action', 'Plans', 'Pending_Approval', 'Approved', 'Done']
    for dir_name in required_dirs:
        dir_path = vault_path / dir_name
        if dir_path.exists():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ❌ {dir_name}/ - MISSING")
            dir_path.mkdir(exist_ok=True)
            print(f"   ✅ Created {dir_name}/")
    print()

    # Check LinkedIn token
    print("2️⃣ Checking LinkedIn authentication...")
    token_path = vault_path / 'linkedin_token.json'
    if token_path.exists():
        try:
            token_data = json.loads(token_path.read_text())
            expires_at = token_data.get('expires_at', 'Unknown')
            print(f"   ✅ Token found")
            print(f"   📅 Expires: {expires_at}")
        except Exception as e:
            print(f"   ⚠️ Token file exists but couldn't parse: {e}")
    else:
        print(f"   ❌ linkedin_token.json not found")
        print(f"   Run: python linkedin_oauth_setup.py")
    print()

    # Check workflow components
    print("3️⃣ Checking workflow components...")
    components = [
        'linkedin_watcher.py',
        'linkedin_workflow_coordinator.py',
        'linkedin_post_executor.py',
        'linkedin_auto_posting.py'
    ]
    for component in components:
        if (vault_path / component).exists():
            print(f"   ✅ {component}")
        else:
            print(f"   ❌ {component} - MISSING")
    print()

    # Create a test action file
    print("4️⃣ Creating test action file...")
    test_file = vault_path / 'Needs_Action' / 'LINKEDIN_test_123.md'

    test_content = f"""---
type: linkedin_opportunity
opportunity: AI Automation Testing
trend_score: 0.95
category: Technology
detected: {datetime.now().isoformat()}
status: pending
---

# LinkedIn Test Opportunity

## 🔍 Topic Detected
**AI Automation Testing**

This is a test topic for the LinkedIn auto-posting workflow.

## 📊 Performance Metrics
- **Reactions:** 50
- **Comments:** 10
- **Shares:** 5
- **Total Engagement:** 65

## 🎯 Business Opportunity
This topic is gaining traction. Consider creating content on this theme.

## 💡 Recommended Actions
- [ ] Research this topic for deeper insights
- [ ] Create follow-up content expanding on this theme
- [ ] Craft a LinkedIn post with your business perspective

## 📝 Post Template
Testing the LinkedIn auto-posting workflow! 🚀

This is a test post to verify the complete Silver Tier implementation. The workflow includes:
✅ Automatic topic detection
✅ Claude reasoning loop
✅ Human-in-the-loop approval
✅ Automatic posting to LinkedIn

#AI #Automation #Testing #SilverTier

## 🚀 Auto-Publish Options
- [x] LinkedIn API token configured
- [ ] Organization not configured (using personal profile posting)

## 📋 Notes
- This is a test post for workflow verification
- High engagement = your connections care about this
- Add your unique business perspective
"""

    test_file.write_text(test_content)
    print(f"   ✅ Created: {test_file.name}")
    print()

    # Create a test plan (simulating Claude's output)
    print("5️⃣ Creating test plan (simulating Claude output)...")
    plan_file = vault_path / 'Plans' / 'PLAN_LINKEDIN_test_123.md'

    plan_content = f"""---
type: linkedin_plan
opportunity: AI Automation Testing
trend_score: 0.95
created: {datetime.now().isoformat()}
status: ready_for_approval
---

# LinkedIn Post Plan

## 🎯 Objective
Create a LinkedIn post about AI Automation Testing to engage our audience.

## 📝 Post Content

Testing the LinkedIn auto-posting workflow! 🚀

This is a test post to verify the complete Silver Tier implementation. The workflow includes:

✅ Automatic topic detection from LinkedIn trends
✅ Claude reasoning loop for content generation
✅ Human-in-the-loop approval for safety
✅ Automatic posting to LinkedIn via OAuth 2.0

This demonstrates a complete autonomous workflow while maintaining human oversight for quality control.

#AI #Automation #Testing #SilverTier #ClaudeCode

## ✅ Ready for Approval

This plan is complete and ready for human approval.

## 📊 Expected Engagement
Based on similar posts, we expect:
- 30-50 reactions
- 5-10 comments
- 2-5 shares

## 🎯 Call to Action
Engage with comments asking about their automation experiences.
"""

    plan_file.write_text(plan_content)
    print(f"   ✅ Created: {plan_file.name}")
    print()

    # Instructions for next steps
    print("=" * 70)
    print("✅ Test Setup Complete!")
    print("=" * 70)
    print()
    print("📋 Next Steps:")
    print()
    print("1️⃣ Run the workflow coordinator to process the plan:")
    print("   python linkedin_workflow_coordinator.py --vault . --once")
    print()
    print("2️⃣ Check Pending_Approval/ for the approval request:")
    print("   ls -la Pending_Approval/")
    print()
    print("3️⃣ Review and approve the post:")
    print("   # Review the file in Pending_Approval/")
    print("   # Then move it to Approved/:")
    print("   mv Pending_Approval/SOCIAL_POST_*.md Approved/")
    print()
    print("4️⃣ Run the post executor to publish:")
    print("   python linkedin_post_executor.py --vault . --once")
    print()
    print("5️⃣ Check your LinkedIn profile to see the post!")
    print()
    print("=" * 70)
    print("🚀 Or run the complete workflow:")
    print("   python linkedin_auto_posting.py --vault . --mode full")
    print("=" * 70)
    print()

    return True


if __name__ == '__main__':
    try:
        success = test_workflow()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        exit(1)
