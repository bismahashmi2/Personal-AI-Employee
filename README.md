
# Personal AI Employee - Silver Tier

An autonomous AI employee system built with Claude Code that monitors communications, processes tasks with human-in-the-loop approval, and manages business operations 24/7.

**🎯 Current Status: 95% Ready - LinkedIn OAuth Setup Required**

## Tier Declaration

**Silver Tier** - Functional Assistant with autonomous monitoring, Claude reasoning, MCP integration, and approval workflows.

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

## 🚀 Quick Start (15 Minutes)

### Step 1: Check System Status

```bash
cd /mnt/d/Code/hackathon0/AI_Employee_Vault
python3 check_hackathon_readiness.py
```

### Step 2: Complete LinkedIn OAuth Setup

**This is the ONLY missing piece!**

```bash
./setup_linkedin_ngrok.sh
```

This automated script will:
1. Ask for your ngrok authtoken (get from https://dashboard.ngrok.com)
2. Start ngrok tunnel
3. Guide you through LinkedIn Developer Portal setup
4. Complete OAuth flow
5. Test the connection

**Time required:** 10-15 minutes

### Step 3: Test LinkedIn Posting

```bash
python3 -c "from linkedin_watcher import LinkedInWatcher; w=LinkedInWatcher('.'); print('✅ Success!' if w.post_to_linkedin('Testing my AI Employee! 🤖 #AI #Automation') else '❌ Failed')"
```

### Step 4: Start Your AI Employee

```bash
python3 silver_tier_main.py .
```

## 📚 Documentation

- **SETUP_SUMMARY.md** - Complete overview and troubleshooting
- **QUICK_START.md** - Quick reference guide
- **NGROK_LINKEDIN_SETUP.md** - Detailed LinkedIn OAuth instructions
- **Personal AI Employee Hackathon 0...md** - Full hackathon requirements

## Prerequisites

- Python 3.12+
- Claude Code with API access
- LinkedIn Developer Account (for OAuth)
- Gmail API credentials
- ngrok account (free tier works)

  # Install dependencies
  pip install -r requirements.txt
  playwright install chromium

  Configuration

  1. Create .env file (copy from .env.example and fill in):
  ANTHROPIC_API_KEY=your_key_here
  SMTP_HOST=smtp.gmail.com
  SMTP_USER=your-email@gmail.com
  SMTP_PASSWORD=your-app-password

  ### LinkedIn OAuth (Optional - for LinkedIn posting)

  First, get LinkedIn API credentials:

  1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
  2. Create an app or select your existing app
  3. In **Settings** tab, note your **Client ID** and **Client Secret**
  4. In **Auth** tab, add redirect URL: `http://localhost:8000/callback`
  5. Request access to **"Share on LinkedIn"** product
  6. Once approved, add these to `.env`:

  ```
  LINKEDIN_CLIENT_ID=your_client_id
  LINKEDIN_CLIENT_SECRET=your_client_secret
  ```

  7. Run the OAuth setup:

  ```bash
  python linkedin_oauth_setup.py
  ```

  This will:
  - Open your browser for LinkedIn authorization
  - Start a local server on port 8000 to receive the callback
  - Save the access token to `linkedin_token.json`

  2. Ensure vault folders exist:
  mkdir -p {Needs_Action,Plans,Done,Pending_Approval,Approved,Rejected,Audits,Logs}

  Running the System

  # Test all components
  python test_system.py

  # Start the Silver Tier system
  python silver_tier_main.py .

  This starts:
  - WhatsApp watcher (monitors every 30 seconds)
  - LinkedIn watcher (monitors every 5 minutes)
  - Scheduler (processes tasks every 15 min, daily briefing at 8 AM, weekly audit Sundays 9 PM)

  Project Structure

  AI_Employee_Vault/
  ├── silver_tier_main.py      # Main orchestrator
  ├── claude_reasoning_loop.py # Claude API integration
  ├── whatsapp_watcher.py      # WhatsApp Web monitoring
  ├── linkedin_watcher.py      # LinkedIn trends monitoring
  ├── gmail_watcher.py         # Gmail monitoring
  ├── mcp_email_server.py      # Email MCP server
  ├── scheduler.py             # Time-based automation
  ├── approval_workflow.py     # Human-in-the-loop
  ├── analytics.py             # KPI tracking
  ├── orchestrator.py          # Service coordination
  ├── audit.py                 # Security logging
  ├── integration_framework.py # Extensible integrations
  ├── base_watcher.py          # Base watcher class
  ├── requirements.txt         # Python dependencies
  ├── Dashboard.md             # Live dashboard (auto-updated)
  ├── Company_Handbook.md      # Business rules
  ├── Business_Goals.md        # Objectives and metrics
  ├── Needs_Action/            # Incoming triggers
  ├── Plans/                   # Generated plans
  ├── Done/                    # Completed items
  ├── Pending_Approval/        # Awaiting approval
  ├── Approved/                # Approved actions
  ├── Rejected/                # Rejected actions
  └── Audits/                  # Generated reports

  Workflow Example

  1. Trigger: WhatsApp message with keyword detected
  2. File Created: Needs_Action/WHATSAPP_20260107_103000.md
  3. Claude Processing: Creates Plans/PLAN_WHATSAPP_...md with action steps
  4. Approval Required: Sensitive actions create Pending_Approval/ file
  5. Human Approval: Move file to Approved/ folder
  6. MCP Execution: Email MCP sends response
  7. Completion: Files moved to Done/, Dashboard updated

  Security Features

  - No Auto-Execute: Sensitive actions require manual approval
  - Audit Trail: All actions logged with timestamps
  - Sandboxed: Dry-run mode available for testing
  - Rate Limiting: Configurable action limits
  - Secret Management: Credentials via environment variables only

  Testing

  # Run full test suite
  python test_system.py

  # Test specific components
  python decision_engine.py --test
  python analytics.py --test

  Technology Stack

  - Language: Python 3.12+
  - AI Engine: Claude Code (Anthropic API)
  - UI/Dashboard: Obsidian Markdown
  - Browser Automation: Playwright
  - Communication: SMTP, WhatsApp Web, LinkedIn API
  - Architecture: File-based messaging, MCP servers