# LinkedIn Watcher - Tool Reference

This document describes the MCP tools exposed by the LinkedIn Watcher server.

## Connection

The LinkedIn watcher MCP server uses streamable HTTP transport:

```
http://localhost:50056/mcp
```

## Tools

### `check_for_updates`

Manually trigger a LinkedIn check for trending topics.

**Parameters:** None

**Returns:** JSON array of topic objects:
```json
[
  {
    "id": "string",
    "title": "string",
    "score": 0.95,
    "category": "Technology",
    "engagement": {
      "reactions": 100,
      "comments": 50,
      "shares": 25,
      "total": 175
    },
    "post_id": "string",
    "created_date": "2025-01-15"
  }
]
```

### `get_status`

Get the current configuration and status of the watcher.

**Parameters:** None

**Returns:**
```json
{
  "access_token": "configured" | "demo_mode",
  "person_urn": "urn:li:person:xxx" | null,
  "organization_urn": "urn:li:organization:xxx" | null,
  "config_path": "/path/to/linkedin_config.json",
  "token_path": "/path/to/linkedin_token.json",
  "check_interval": 300,
  "rate_limit_remaining": 95,
  "last_check": "2025-01-15T10:30:00"
}
```

### `refresh_token`

Manually refresh the OAuth access token using the stored refresh token.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "expires_at": "2025-03-16T10:30:00",
  "message": "Token refreshed successfully"
}
```

### `setup_organization`

Run interactive organization setup to discover or configure the organization URN.

**Parameters:** None

**Returns:**
```json
{
  "person_urn": "urn:li:person:xxx",
  "organization_urn": "urn:li:organization:xxx" | null,
  "message": "Setup complete"
}
```

### `post_to_linkedin`

Post content to LinkedIn (used by approval workflow).

**Parameters:**
```json
{
  "content": "string (required, max 3000 chars)",
  "image_path": "/path/to/image.jpg" | null,
  "as_organization": false | true
}
```

**Returns:**
```json
{
  "success": true,
  "post_urn": "urn:li:share:xxx",
  "message": "Posted successfully"
}
```

## Events

The watcher runs continuously and emits events to the vault's file system:

1. **Topics Detected**: Creates files in `Needs_Action/LINKEDIN_*.md`
2. **Posts Published**: Logged when content is auto-published from `Approved/`

## Error Handling

- **429 Rate Limited**: Automatic exponential backoff (5s, 10s, 20s max)
- **401 Unauthorized**: Token invalidated, manual re-auth required
- **5xx Server Errors**: Automatic retry (up to 3 attempts)
- **Network Errors**: Logged, next scheduled check will retry

## Integration with Approval Workflow

When a LinkedIn topic file is moved to `Approved/`, the approval workflow:
1. Parses the file for post content and organization flag
2. Calls `post_to_linkedin()` with the content
3. Logs success/failure
4. Moves file to `Done/`

## Demo Mode

If no access token is found, the watcher runs in demo mode:
- Returns random mock topics with 10% probability per check
- Useful for testing the workflow without API access
- No real posts are created

## Monitoring

Check the log output for status:
- Startup: Configuration summary
- Each check: Number of topics found
- Errors: With stack traces for debugging
