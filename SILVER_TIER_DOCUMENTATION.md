# Silver Tier Documentation

## Overview
Silver Tier represents a functional AI assistant that can autonomously monitor communications, generate business content, and execute actions with human approval.

## Architecture

### Core Components

#### 1. Watcher Scripts
- **WhatsApp Watcher**: Monitors WhatsApp Web for urgent messages using Playwright
- **LinkedIn Watcher**: Monitors LinkedIn for trending business topics
- **File System Watcher**: Monitors local directories for dropped files

#### 2. Reasoning Engine
- **Claude Reasoning Loop**: Processes Needs_Action folder and creates Plan.md files
- **Context Management**: Uses Company_Handbook.md for response guidelines

#### 3. MCP Servers
- **Email MCP Server**: Handles email sending and drafting
- **Future MCP Servers**: Extendable for other services

#### 4. Approval Workflow
- **Human-in-the-Loop System**: File-based approval for sensitive actions
- **Security Rules**: Approval thresholds based on action type and amount

#### 5. Scheduler
- **Automated Processing**: Regular processing of needs_action folder
- **Time-Based Triggers**: Daily briefings, weekly audits, etc.

## Setup Instructions

### Prerequisites
- Python 3.8+
- Playwright (`pip install playwright`)
- Google Chrome (for WhatsApp Web automation)
- SMTP access for email functionality

### Installation

1. **Install Dependencies**
```bash
pip install playwright requests schedule
playwright install
```

2. **Set Up Environment**
```bash
# Create vault structure
mkdir -p vault/{Needs_Action,Plans,Done,Pending_Approval,Approved,Rejected,Audits}

# Create session directories
mkdir -p vault/whatsapp_session
```

3. **Configure MCP Server**
Create `vault/mcp_config.json`:
```json
{
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_use_tls": true,
  "smtp_auth": true,
  "smtp_user": "your-email@gmail.com",
  "smtp_password": "your-app-password"
}
```

### Configuration

#### Environment Variables
```bash
# LinkedIn API (for business topic monitoring)
export LINKEDIN_API_KEY="your_linkedin_api_key"

# Email Configuration
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
```

## Usage

### Starting the System
```bash
# Start the Silver Tier system
python silver_tier_main.py --vault /path/to/vault
```

### Manual Processing
```python
from silver_tier_main import SilverTierSystem

# Initialize system
silver_system = SilverTierSystem('/path/to/vault')

# Process needs_action folder
silver_system.reasoning_loop.process_needs_action()

# Check for approved actions
silver_system.approval_workflow.check_approvals()
```

## File Structure

```
vault/
├── Needs_Action/           # Incoming triggers (emails, messages, files)
├── Plans/                 # Generated plans for processing
├── Done/                  # Completed items
├── Pending_Approval/      # Actions waiting for human approval
├── Approved/              # Approved actions ready for execution
├── Rejected/              # Rejected actions
├── Audits/                # Generated audit reports
├── Company_Handbook.md    # Response guidelines and rules
├── Dashboard.md           # Real-time status dashboard
└── drafts/               # Email draft storage
```

## Security Features

### Approval Thresholds
- **Email Sending**: Requires approval for new recipients or bulk sends
- **Payments**: Requires approval for amounts > $50 or new payees
- **Social Media**: Requires approval for replies, DMs, and new content types
- **Data Sharing**: Always requires approval for sensitive information

### Audit Trail
- All actions logged with timestamps and context
- Immutable audit logs for compliance
- Searchable audit database

## Troubleshooting

### Common Issues

#### WhatsApp Watcher Not Working
1. Ensure Chrome is installed
2. Check Playwright browser installation: `playwright install`
3. Verify WhatsApp Web session directory exists
4. Check network connectivity to web.whatsapp.com

#### Email MCP Server Connection Issues
1. Verify SMTP credentials in config
2. Check SMTP server accessibility
3. Ensure proper authentication setup
4. Verify TLS/SSL settings

#### Watcher Scripts Not Triggering
1. Check log files for errors
2. Verify vault structure exists
3. Check file permissions
4. Verify Python process is running

### Log Files
- System logs: `logging.INFO` level by default
- Error logs: Check for exceptions in terminal output
- Audit logs: Stored in `/Audits` directory

## Performance Considerations

### Resource Usage
- **Memory**: ~100MB for main system
- **CPU**: Minimal during idle periods
- **Network**: Periodic API calls (every 15-30 minutes)

### Scalability
- System supports multiple watcher instances
- MCP servers can be extended for new services
- Modular architecture allows easy additions

## Next Steps

### From Silver to Gold Tier
1. Add Odoo accounting integration
2. Implement multiple specialized MCP servers
3. Add comprehensive error recovery
4. Implement weekly business audits
5. Add Ralph Wiggum autonomous loop

### Enhancement Ideas
1. Voice message processing
2. Multi-language support
3. Advanced analytics and reporting
4. Mobile app integration
5. Real-time collaboration features

## Support

### Documentation
- All components are documented in source code
- Usage examples provided in main files
- Test suite demonstrates functionality

### Community
- Open source contributions welcome
- Bug reports and feature requests accepted
- Documentation improvements encouraged