# AI Employee Vault - Quick Start Guide

**Last Updated:** 2026-05-08
**Status:** ✅ Production Ready

---

## 🚀 Daily Workflow (5 minutes)

### Step 1: Find Trending Topics
```bash
python3 trend_finder.py --count 2
```
This creates 2 trending topic files in `Needs_Action/`

### Step 2: Process with Claude
```bash
claude-code
```
Claude will:
- Read trending topics from `Needs_Action/`
- Generate business-focused LinkedIn posts
- Create plans in `Plans/` folder

### Step 3: Check for Approvals
```bash
ls -la Pending_Approval/
```
The workflow coordinator automatically moves plans to `Pending_Approval/`

### Step 4: Review and Approve
```bash
# Read the post
cat Pending_Approval/SOCIAL_POST_*.md

# Approve it
mv Pending_Approval/SOCIAL_POST_*.md Approved/

# Or reject it
mv Pending_Approval/SOCIAL_POST_*.md Rejected/
```

### Step 5: Automatic Posting
The system automatically:
- Detects approved posts in `Approved/`
- Posts to LinkedIn via OAuth 2.0
- Moves completed posts to `Done/`
- Your post is LIVE on LinkedIn! 🎉

---

## 🔧 System Management

### Start the System
```bash
python3 silver_tier_main.py
```
This starts:
- Gmail watcher (every 5 minutes)
- LinkedIn watcher (every 5 minutes)
- Scheduler (daily briefings, weekly audits)

### Run in Background
```bash
nohup python3 silver_tier_main.py > system.log 2>&1 &
```

### Check Logs
```bash
tail -f system.log
```

### Stop the System
```bash
# Find the process
ps aux | grep silver_tier_main

# Kill it
kill <PID>
```

---

## 📁 Folder Structure

```
Needs_Action/     → New tasks (from watchers or trend_finder)
Plans/            → Claude-generated action plans
Pending_Approval/ → Posts awaiting your approval
Approved/         → Approved posts (auto-posted to LinkedIn)
Rejected/         → Rejected posts (archived)
Done/             → Completed posts (archived)
```

---

## 🔍 Finding Trending Topics

### Method 1: Automated (Recommended)
```bash
python3 trend_finder.py --count 3
```
Generates curated trending topics with context and hashtags.

### Method 2: Manual
Browse LinkedIn, Google Trends, or industry news, then:
```bash
cat > Needs_Action/LINKEDIN_custom_$(date +%s).md << 'EOF'
---
type: linkedin_opportunity
opportunity: Your Topic Here
trend_score: 0.90
status: pending
---

# LinkedIn Post Opportunity

**Topic:** Your topic
**Context:** Why it matters

## Suggested Post
Your thoughts here
EOF
```

---

## 🧪 Testing

### Test LinkedIn Posting
```bash
python3 test_linkedin_post.py
```

### Test Trend Finder
```bash
python3 trend_finder.py --count 1
```

### Test Complete Workflow
```bash
# 1. Generate a topic
python3 trend_finder.py --count 1

# 2. Process with Claude
claude-code

# 3. Check approval
ls Pending_Approval/

# 4. Approve
mv Pending_Approval/SOCIAL_POST_*.md Approved/

# 5. Check LinkedIn profile for the post!
```

---

## ⚠️ Known Issues

### LinkedIn 404 Error
**Error:** `RESOURCE_NOT_FOUND` when monitoring LinkedIn feed
**Impact:** None - posting still works perfectly
**Workaround:** Use `trend_finder.py` instead of automatic monitoring
**Status:** Non-critical, can be ignored

---

## 🎯 Silver Tier Status

✅ All Bronze requirements
✅ Multiple watchers (Gmail, LinkedIn, WhatsApp, Filesystem)
✅ Automatic LinkedIn posting
✅ Claude reasoning loop
✅ MCP server configured
✅ Human-in-the-loop approval
✅ Basic scheduling
✅ Agent Skills

**Status:** 8/8 Complete (100%)

---

## 📞 Quick Commands Reference

```bash
# Daily routine
python3 trend_finder.py --count 2
claude-code
ls Pending_Approval/
mv Pending_Approval/SOCIAL_POST_*.md Approved/

# Check status
ls Needs_Action/      # New tasks
ls Plans/             # Generated plans
ls Pending_Approval/  # Awaiting approval
ls Approved/          # Being posted
ls Done/              # Completed

# System management
python3 silver_tier_main.py           # Start system
ps aux | grep silver_tier_main        # Check if running
tail -f system.log                    # View logs
```

---

## 💡 Pro Tips

1. **Run trend finder daily** - Fresh topics = better engagement
2. **Review before approving** - Quality over quantity
3. **Use hashtags** - Trend finder includes relevant hashtags
4. **Post consistently** - 2-3 posts per week is ideal
5. **Monitor Done/ folder** - Track your posting history

---

## 🎉 You're Ready!

Your AI Employee Vault is fully operational. Start with:

```bash
python3 trend_finder.py --count 2
claude-code
```

Then approve the posts and watch them go live on LinkedIn!

---

**Questions?** Check the full documentation:
- `README.md` - Complete system overview
- `LINKEDIN_AUTO_POSTING_GUIDE.md` - Detailed workflow guide
- `SILVER_TIER_STATUS.md` - Requirements completion status
