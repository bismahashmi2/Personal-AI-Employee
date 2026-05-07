
# Personal AI Employee - Silver Tier

An autonomous AI employee system built with Claude Code that monitors communications, processes tasks with human-in-the-loop approval, and manages business operations 24/7.

**🎯 Current Status: ✅ 100% COMPLETE - Production Ready**

**Last Updated:** 2026-05-07
**LinkedIn Integration:** ✅ Fully Operational
**Last Test:** 2026-05-07 14:26 UTC - SUCCESS

## Tier Declaration

**Silver Tier** - ✅ COMPLETE

All 8 Silver Tier requirements successfully implemented and tested:
- ✅ All Bronze requirements
- ✅ Multiple watchers (Gmail, LinkedIn, WhatsApp, Filesystem)
- ✅ Automatic LinkedIn posting (OAuth 2.0 authenticated)
- ✅ Claude reasoning loop with Plan.md files
- ✅ MCP server configured
- ✅ Human-in-the-loop approval workflow
- ✅ Basic scheduling system
- ✅ AI functionality as Agent Skills

## Features

- **Multi-Channel Monitoring**: Gmail, LinkedIn, and filesystem watchers
- **Claude-Powered Reasoning**: Automatic plan generation from incoming tasks
- **Human-in-the-Loop**: Secure approval workflow for sensitive actions
- **LinkedIn Auto-Posting**: Automatically post business content to LinkedIn
- **Scheduled Automation**: Daily briefings, weekly audits, continuous processing
- **MCP Integration**: Email sending via Model Context Protocol
- **Analytics Dashboard**: Real-time KPIs and system health monitoring
- **Audit Logging**: Comprehensive security and compliance tracking

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Watchers  │────▶│   Claude    │────▶│  Approval   │
│  (Gmail,    │     │  Reasoning  │     │  Workflow   │
│  LinkedIn)  │     │   Loop      │     │   (HITL)    │
└─────────────┘     └─────────────┘     └─────────────┘
                                                        │
┌─────────────┐     ┌─────────────┘                   ▼
│   MCP       │     │                          ┌─────────────┐
│  Servers    │◀────┘                          │    Vault    │
│ (Email, etc)│                                │ (Obsidian)  │
└─────────────┘                                └─────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Claude Code with API access
- LinkedIn Developer Account (OAuth already configured)
- Gmail API credentials

### Installation

```bash
# Clone or navigate to the project
cd /mnt/d/Code/hackathon0/AI_Employee_Vault

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### Configuration

1. Create `.env` file with your credentials:
```bash
ANTHROPIC_API_KEY=your_key_here
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
```

2. LinkedIn OAuth is already configured and working
   - Token valid until: 2026-07-03
   - Person URN: `urn:li:person:0Z5qF8BbEK`
   - Last tested: 2026-05-07 ✅

### Running the System

```bash
# Start the AI Employee
python3 silver_tier_main.py

# Test LinkedIn posting anytime
python3 test_linkedin_post.py
```

### Workflow Directories

The system monitors these folders:
- `Needs_Action/` - New tasks from watchers
- `Plans/` - Claude-generated action plans
- `Pending_Approval/` - Items awaiting human approval
- `Approved/` - Approved actions ready for execution
- `Done/` - Completed tasks

## 📚 Documentation

### Current Documentation
- **SILVER_TIER_STATUS.md** - Silver Tier requirements completion report
- **LINKEDIN_SUCCESS.md** - LinkedIn OAuth 2.0 integration guide
- **PROJECT_STRUCTURE.md** - Clean project organization
- **COMPLETION_SUMMARY.md** - Comprehensive project summary
- **README.md** - This file

### Testing
- **test_linkedin_post.py** - Test LinkedIn posting functionality

### Key Features Verified
- ✅ LinkedIn OAuth 2.0 authentication working
- ✅ Automatic posting to LinkedIn tested
- ✅ Multi-channel monitoring (Gmail, LinkedIn, WhatsApp)
- ✅ Claude AI reasoning and planning
- ✅ Human approval workflow implemented
- ✅ Task scheduling ready

## Prerequisites

- Python 3.12+
- Claude Code with API access
- LinkedIn Developer Account (OAuth configured)
- Gmail API credentials
- ngrok account (for OAuth token refresh only)

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

## Configuration

1. Create `.env` file (copy from `.env.example` and fill in):
```bash
ANTHROPIC_API_KEY=your_key_here
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
```

2. Ensure vault folders exist:
```bash
mkdir -p {Needs_Action,Plans,Done,Pending_Approval,Approved,Rejected,Audits,Logs}
```

### LinkedIn OAuth (Already Configured ✅)

LinkedIn integration is fully operational:
- **Status:** Working
- **Token expires:** 2026-07-03
- **Person URN:** `urn:li:person:0Z5qF8BbEK`
- **Last tested:** 2026-05-07 14:26 UTC

To refresh token when expired:
```bash
# Terminal 1: Start ngrok tunnel
./ngrok http 8000

# Terminal 2: Run OAuth setup
python3 linkedin_oauth_setup.py
```

## Running the System

```bash
# Start the Silver Tier system
python3 silver_tier_main.py

# Test LinkedIn posting
python3 test_linkedin_post.py
```

This starts:
- Gmail watcher (monitors emails)
- LinkedIn watcher (monitors and posts every 5 minutes)
- WhatsApp watcher (monitors every 30 seconds)
- Scheduler (processes tasks every 15 min, daily briefing at 8 AM, weekly audit Sundays 9 PM)

## Project Structure

```
AI_Employee_Vault/
├── silver_tier_main.py          # Main orchestrator
├── claude_reasoning_loop.py     # Claude API integration
├── whatsapp_watcher.py          # WhatsApp Web monitoring
├── linkedin_watcher.py          # LinkedIn monitoring & posting ✅
├── gmail_watcher.py             # Gmail monitoring
├── scheduler.py                 # Time-based automation
├── approval_workflow.py         # Human-in-the-loop
├── orchestrator.py              # Service coordination
├── base_watcher.py              # Base watcher class
├── linkedin_oauth_setup.py      # OAuth token refresh
├── test_linkedin_post.py        # LinkedIn testing
├── requirements.txt             # Python dependencies
├── mcp.json                     # MCP server configuration
├── linkedin_config.json         # LinkedIn configuration
├── linkedin_token.json          # OAuth access token
├── Dashboard.md                 # Live dashboard (auto-updated)
├── Company_Handbook.md          # Business rules
├── Business_Goals.md            # Objectives and metrics
├── Needs_Action/                # Incoming triggers
├── Plans/                       # Generated plans
├── Done/                        # Completed items
├── Pending_Approval/            # Awaiting approval
├── Approved/                    # Approved actions
├── Rejected/                    # Rejected actions
├── Audits/                      # Generated reports
└── agent_skills/                # AI agent skills
```

## Workflow Example

1. **Trigger:** Email arrives in Gmail with action required
2. **File Created:** `Needs_Action/EMAIL_[id].md`
3. **Claude Processing:** Creates `Plans/PLAN_EMAIL_[id].md` with action steps
4. **Approval Required:** Sensitive actions create `Pending_Approval/` file
5. **Human Approval:** Move file to `Approved/` folder
6. **Execution:** System executes approved actions
7. **Completion:** Files moved to `Done/`, Dashboard updated

## Security Features

- **No Auto-Execute:** Sensitive actions require manual approval
- **Audit Trail:** All actions logged with timestamps
- **Sandboxed:** Dry-run mode available for testing
- **Rate Limiting:** Configurable action limits
- **Secret Management:** Credentials via environment variables only
- **OAuth 2.0:** Secure LinkedIn authentication

## Testing

```bash
# Test LinkedIn posting
python3 test_linkedin_post.py

# Test specific watchers
python3 gmail_watcher.py
python3 linkedin_watcher.py
```

## Technology Stack

- **Language:** Python 3.12+
- **AI Engine:** Claude Code (Anthropic API)
- **UI/Dashboard:** Obsidian Markdown
- **Browser Automation:** Playwright
- **Communication:** SMTP, WhatsApp Web, LinkedIn API v2
- **Authentication:** OAuth 2.0 (LinkedIn)
- **Architecture:** File-based messaging, MCP servers

## LinkedIn Integration Details

- **API Version:** v2 (stable)
- **Authentication:** OAuth 2.0 with OpenID Connect
- **Scopes:** openid, profile, w_member_social
- **Rate Limits:** 150 posts/day per member
- **Token Validity:** 60 days (expires 2026-07-03)
- **Person URN:** urn:li:person:0Z5qF8BbEK
- **Status:** ✅ Fully operational

## Support & Resources

- **LinkedIn Developer Portal:** https://www.linkedin.com/developers/apps/
- **LinkedIn API Docs:** https://learn.microsoft.com/en-us/linkedin/
- **Project Documentation:** See `COMPLETION_SUMMARY.md` for full details

---

**Status:** ✅ Production Ready | **Silver Tier:** Complete | **Last Updated:** 2026-05-07