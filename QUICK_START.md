# Quick Start Guide - LinkedIn OAuth Setup

## Current Status: 5/6 Checks Passed ✅

You're **almost ready** for the hackathon! Only LinkedIn OAuth token is missing.

## What You Need to Do (15 minutes)

### Option 1: Automated Setup (Recommended)

Run the automated setup script:

```bash
cd /mnt/d/Code/hackathon0/AI_Employee_Vault
./setup_linkedin_ngrok.sh
```

This script will:
1. Ask for your ngrok authtoken (get it from https://dashboard.ngrok.com/get-started/your-authtoken)
2. Start ngrok tunnel automatically
3. Show you the ngrok URL to add to LinkedIn Developer Portal
4. Update the OAuth script with the correct URL
5. Run the OAuth flow
6. Test the connection

### Option 2: Manual Setup

If the script doesn't work, follow these steps:

#### Step 1: Get ngrok authtoken
```bash
# Go to: https://dashboard.ngrok.com/get-started/your-authtoken
# Copy your token and run:
./ngrok authtoken YOUR_TOKEN_HERE
```

#### Step 2: Start ngrok (keep this terminal open)
```bash
./ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

#### Step 3: Update LinkedIn Developer Portal
1. Go to: https://www.linkedin.com/developers/apps
2. Select your app (Client ID: `777hia0543ib7x`)
3. Auth tab → Redirect URLs
4. Add: `https://YOUR_NGROK_URL/callback`
5. Click Update

#### Step 4: Update OAuth script
Edit `linkedin_oauth_setup.py` line 15:
```python
REDIRECT_URI = 'https://YOUR_NGROK_URL/callback'
```

#### Step 5: Run OAuth
```bash
python3 linkedin_oauth_setup.py
```

Authorize in the browser when it opens.

#### Step 6: Verify
```bash
cat linkedin_token.json
python3 linkedin_watcher.py --once
```

## After OAuth Setup

### Test LinkedIn Posting
```bash
python3 -c "
from linkedin_watcher import LinkedInWatcher
watcher = LinkedInWatcher('.')
result = watcher.post_to_linkedin('Testing my AI Employee! 🤖 #AI #Automation')
print('✅ Post successful!' if result else '❌ Post failed')
"
```

### Start Your AI Employee
```bash
python3 silver_tier_main.py .
```

This will:
- Monitor Gmail for important emails
- Monitor LinkedIn for trending topics
- Create action files in `Needs_Action/`
- Wait for your approval in `Pending_Approval/`
- Execute approved actions

### Check Status Anytime
```bash
python3 check_hackathon_readiness.py
```

## Troubleshooting

### "This site can't be reached" after LinkedIn authorization
- ngrok stopped running
- Solution: Restart ngrok and try again

### "bummer, something went wrong" on LinkedIn
- Redirect URL mismatch
- Solution: Make sure LinkedIn Developer Portal URL exactly matches the URL in `linkedin_oauth_setup.py`

### ngrok URL changes every time
- Free ngrok accounts get random URLs
- Solution: Keep the same ngrok session running, or update LinkedIn redirect URL each time

### LinkedIn auto-starts when opening laptop
```bash
# Stop running processes
pkill -f "python.*orchestrator"
pkill -f "python.*silver_tier"

# Check Windows Task Scheduler (from Windows, not WSL)
# Win + R → taskschd.msc → Look for AI Employee tasks → Disable
```

## Your Configuration

- **Client ID:** `777hia0543ib7x`
- **Client Secret:** Configured ✅
- **Person URN:** `urn:li:person:1273293335` ✅
- **Scopes:** `w_member_social` (post to personal profile)
- **Organization:** Not configured (will post to your personal profile)

## Silver Tier Hackathon Requirements

- ✅ Obsidian vault with folder structure
- ✅ Two or more Watcher scripts (Gmail + LinkedIn)
- ⏳ Automatically Post on LinkedIn (needs OAuth token)
- ✅ Claude reasoning loop with Plan.md files
- ✅ Human-in-the-loop approval workflow
- ✅ Basic scheduling capability

**You're 95% ready!** Just complete the OAuth setup and you're good to go.

## Next Steps After OAuth

1. **Create test content:** Let the system detect a LinkedIn opportunity
2. **Review in Needs_Action/:** Check the generated action files
3. **Approve posting:** Move files to `Approved/` folder
4. **Watch it work:** System will post to LinkedIn automatically
5. **Document your work:** Take screenshots for hackathon submission

## Resources

- **Full Setup Guide:** `NGROK_LINKEDIN_SETUP.md`
- **Hackathon Document:** `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`
- **LinkedIn Setup Guide:** `LINKEDIN_SETUP_GUIDE.md`

## Support

If you get stuck:
1. Check `ngrok.log` for ngrok errors
2. Check terminal output for Python errors
3. Run `python3 check_hackathon_readiness.py` to diagnose
4. Review the troubleshooting section above

Good luck with your hackathon! 🚀
