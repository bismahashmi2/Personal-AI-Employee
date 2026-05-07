# Agent Skills System

A plugin-based architecture for extending your AI Employee with MCP (Model Context Protocol) capabilities.

## Overview

The Agent Skills system provides:

- **Modular Skills**: Each skill is a self-contained capability
- **MCP Protocol**: Skills run as standalone servers accessible via HTTP
- **Automatic Discovery**: Skills discovered from `.agents/skills/` directory
- **Lifecycle Management**: Start/stop/restart skills with health monitoring
- **Orchestrator Integration**: All skills managed by central orchestrator

## Available Skills

### 1. LinkedIn Watcher (`linkedin-watcher`)

Monitors your LinkedIn company page for trending topics and engagement insights.

**Tools:**
- `get_status` - Get status and configuration
- `refresh_token` - Refresh OAuth access token
- `setup_organization` - Discover and configure organization URN
- `test_connection` - Test LinkedIn API connectivity
- `check_for_updates` - Manually trigger topic discovery

**Port:** 50056

**Setup:**
```bash
# OAuth authentication
python linkedin_oauth_setup.py

# Interactive organization setup
python linkedin_watcher.py --setup

# Start the server
./.agents/skills/linkedin-watcher/scripts/start-server.sh

# Verify it's working
python .agents/skills/linkedin-watcher/scripts/verify.py
```

### 2. Browsing with Playwright (`browsing-with-playwright`)

Browser automation for web interactions, form submissions, and data extraction.

**Tools:**
- `browser_navigate`, `browser_click`, `browser_type`
- `browser_snapshot`, `browser_take_screenshot`
- `browser_evaluate`, `browser_run_code`
- And more...

**Port:** 8808

**Setup:**
```bash
./.agents/skills/browsing-with-playwright/scripts/start-server.sh
```

## Starting Skills

### Manual Start

Each skill has a `start-server.sh` script:

```bash
# LinkedIn watcher
.agents/skills/linkedin-watcher/scripts/start-server.sh [port]

# Playwright browser
.agents/skills/browsing-with-playwright/scripts/start-server.sh [port]
```

### Via Orchestrator

The orchestrator reads `mcp.json` and starts all configured services:

```bash
python orchestrator.py
```

### Via Python API

```python
from .agents.skills import get_manager

manager = get_manager()
manager.discover_skills()
manager.start_skill_server('linkedin-watcher', 50056)
```

## Creating a New Skill

1. **Create skill directory:**
   ```bash
   mkdir -p .agents/skills/my-skill/{scripts,references}
   ```

2. **Add SKILL.md** with YAML frontmatter:
   ```markdown
   ---
   name: my-skill
   description: What this skill does
   ---
   # Documentation
   ...
   ```

3. **Implement MCP server** in `scripts/server.py` or use an existing MCP implementation.

4. **Add start/stop scripts:**
   - `scripts/start-server.sh` - Start the MCP server
   - `scripts/stop-server.sh` - Stop the server
   - `scripts/verify.py` - Health check

5. **Add tool documentation** to `references/README.md`

6. **Add to mcp.json:**
   ```json
   "my-skill": {
     "command": "python",
     "args": ["my-skill.py", "--host", "localhost", "--port", "50057"],
     "env": {}
   }
   ```

## MCP Protocol

Skills expose tools via the Model Context Protocol (JSON-RPC 2.0 over HTTP):

### Initialize

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": { ... }
}
```

### List Tools

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

### Call Tool

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": { "param": "value" }
  }
}
```

## Python Base Classes

All watchers extend `BaseWatcher`:

```python
from base_watcher import BaseWatcher

class MyWatcher(BaseWatcher):
    def __init__(self, vault_path):
        super().__init__(vault_path, check_interval=60)

    def check_for_updates(self) -> list:
        """Check for new items, return list"""
        return [...]
```

For MCP server capabilities, override:

```python
    def _get_mcp_tools(self) -> list:
        """Add custom tools beyond get_status, check_for_updates, stop"""
        return [
            {
                'name': 'my_custom_tool',
                'description': 'Does something useful',
                'inputSchema': { ... }
            }
        ]

    def _handle_tool_call(self, tool_name: str, arguments: dict) -> dict:
        """Handle custom tool calls"""
        if tool_name == 'my_custom_tool':
            # Do work
            return {'result': 'success'}
        return super()._handle_tool_call(tool_name, arguments)
```

## Command Line Usage

```bash
# List all skills
python -m .agents.skills --list

# Start a skill server
python -m .agents.skills --start linkedin-watcher

# Call a tool
python -m .agents.skills --call linkedin-watcher get_status '{}'
```

## Skill Structure

```
.agents/skills/
├── my-skill/
│   ├── SKILL.md           # Description, usage, setup
│   ├── scripts/
│   │   ├── start-server.sh   # Start the service
│   │   ├── stop-server.sh    # Stop the service
│   │   ├── verify.py         # Health check script
│   │   ├── server.py         # MCP server implementation
│   │   └── client.py         # Example client usage
│   └── references/
│       └── README.md       # Tool reference documentation
└── __init__.py            # Skill manager
└── __main__.py            # CLI interface
```

## Health Checks

Skills should implement `verify.py` that returns 0 on success:

```python
import json, urllib.request

url = 'http://localhost:PORT/mcp'
req = urllib.request.Request(url, data=json.dumps({
    'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {}
}).encode(), headers={'Content-Type': 'application/json'})

with urllib.request.urlopen(req, timeout=5) as resp:
    response = json.loads(resp.read())
    if 'error' in response:
        exit(1)
print("OK")
exit(0)
```

## Troubleshooting

### "Port already in use"
```bash
# Find and kill process
lsof -ti :50056 | xargs kill
# Or use stop-server.sh
.agents/skills/linkedin-watcher/scripts/stop-server.sh 50056
```

### "Connection refused"
- Verify the skill is running: `ps aux | grep -i skill-name`
- Check port matches in mcp.json and skill config
- Look at skill logs for startup errors

### "Unknown tool"
- Check available tools: `python -m .agents.skills --call skill-name tools/list '{}'`
- Verify tool name matches exactly
- Ensure skill server is running
