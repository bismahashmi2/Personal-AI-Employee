#!/bin/bash
# Start LinkedIn Watcher MCP server
# Usage: ./start-server.sh [port] [vault_path]

PORT=${1:-50056}
VAULT_PATH=${2:-.}
PID_FILE="/tmp/linkedin-watcher-${PORT}.pid"

# Check if already running
if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "LinkedIn watcher already running on port $PORT (PID: $(cat $PID_FILE))"
    exit 0
fi

# Validate vault path
if [ ! -d "$VAULT_PATH" ]; then
    echo "Error: Vault path does not exist: $VAULT_PATH"
    exit 1
fi

# Check for token
if [ ! -f "$VAULT_PATH/linkedin_token.json" ]; then
    echo "Warning: No linkedin_token.json found in vault."
    echo "         Run: python linkedin_oauth_setup.py"
    echo "         The watcher will run in demo mode."
fi

# Start server
cd "$VAULT_PATH"
python linkedin_watcher.py --host localhost --port "$PORT" --vault "$VAULT_PATH" &
echo $! > "$PID_FILE"

sleep 2

if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "LinkedIn watcher MCP server started on port $PORT (PID: $(cat $PID_FILE))"
    echo "Vault: $VAULT_PATH"
    echo "Check Needs_Action/ for detected opportunities."
else
    echo "Failed to start LinkedIn watcher"
    rm -f "$PID_FILE"
    exit 1
fi
