# LinkedIn Watcher Skill

Monitor your LinkedIn company page for trending topics and engagement insights.

## What This Skill Does

This skill runs the LinkedIn watcher as an MCP server that:
- Polls your LinkedIn company page every 5 minutes (configurable)
- Analyzes post performance to identify trending topics
- Creates action files in your vault when opportunities are detected
- Can auto-post approved content back to LinkedIn

## Setup

### Prerequisites

1. **LinkedIn App Setup**
   - Create a LinkedIn Developer app at https://www.linkedin.com/developers/
   - Add these OAuth 2.0 scopes:
     - `w_member_social` - Post as member
     - `r_liteprofile` - Read basic profile
     - `r_organization_social` - Read organization posts (requires Marketing Developer Platform approval)
     - `rw_organization_admin` - Write to organization page (requires Marketing Developer Platform approval)
   - Set redirect URI: `http://localhost:8000/callback`
   - Copy Client ID and Client Secret

2. **Environment Configuration**
   ```bash
   export LINKEDIN_CLIENT_ID="your-client-id"
   export LINKEDIN_CLIENT_SECRET="your-client-secret"
   ```

### Installation

```bash
# Run the OAuth setup to get your access token
python linkedin_oauth_setup.py

# Configure the organization to monitor
python linkedin_watcher.py --setup

# Or use the helper function
python -c "from linkedin_watcher import setup_organization_watcher; setup_organization_watcher('.')"
```

## Usage

### Start the MCP Server

```bash
# Start as background service
./scripts/start-server.sh 50056

# Or run directly
python linkedin_watcher.py --host localhost --port 50056 --vault /path/to/vault
```

### Check Your Vault

The watcher creates markdown files in `Needs_Action/` when it finds opportunities:
- Topics with high engagement from your page
- Trending content patterns
- Suggested post templates

Move files to `Approved/` to auto-publish to LinkedIn.

### Available Tools

When running as an MCP server, the following tools are available:

| Tool | Description |
|------|-------------|
| `check_for_updates` | Manually trigger a LinkedIn check (returns list of topics) |
| `get_status` | Get watcher configuration and token status |
| `refresh_token` | Manually refresh the OAuth access token |
| `setup_organization` | Configure which organization to monitor (interactive) |
| `post_to_linkedin` | Post content to LinkedIn (requires approval) |

## How It Works

1. **Authentication**: Uses OAuth 2.0 with a long-lived (60-day) access token
2. **Topic Discovery**: Fetches posts from your organization page
3. **Scoring Algorithm**:
   - Engagement (reactions + comments + shares×2): 60% weight
   - Recency (30-day decay): 40% weight
4. **Threshold**: Only topics with score > 0.3 are reported
5. **Approval Workflow**: Generated content must be approved before posting

## Configuration Files

- `linkedin_token.json` - OAuth access token (auto-generated)
- `linkedin_config.json` - Organization URN and person URN (auto-saved)

## Troubleshooting

### "No administered organizations found"
- Ensure your LinkedIn user is an ADMIN of the company page
- Your app needs `r_organization_social` and `rw_organization_admin` scopes
- These scopes require Marketing Developer Platform application approval

### "Token expired"
- Run `python linkedin_oauth_setup.py` to re-authenticate
- Or use the refresh flow: `python -c "from linkedin_watcher import LinkedInWatcher; w=LinkedInWatcher('.'); w._refresh_access_token()"`

### Rate Limiting
- Standard LinkedIn apps: ~100 calls/day
- The watcher implements exponential backoff on 429 errors
- Consider increasing check_interval if hitting limits

## Stopping the Server

```bash
# If using start-server.sh
./scripts/stop-server.sh 50056

# Or find and kill the process
pkill -f "linkedin_watcher.py.*50056"
```

## Advanced Configuration

Edit `linkedin_watcher.py` to customize:
- `check_interval` (default: 300 seconds / 5 minutes)
- `api_version` (default: 202305)
- Engagement scoring weights
- Thresholds
