#!/bin/bash
# Stop LinkedIn Watcher MCP server
# Usage: ./stop-server.sh [port]

PORT=${1:-50056}
PID_FILE="/tmp/linkedin-watcher-${PORT}.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping LinkedIn watcher (PID: $PID)..."
        kill "$PID"
        sleep 1

        # Force kill if still running
        if kill -0 "$PID" 2>/dev/null; then
            echo "Force killing..."
            kill -9 "$PID"
        fi

        rm -f "$PID_FILE"
        echo "Stopped."
    else
        echo "Process $PID not running, cleaning up PID file"
        rm -f "$PID_FILE"
    fi
else
    # Try to find by port
    PID=$(lsof -ti :$PORT 2>/dev/null)
    if [ -n "$PID" ]; then
        echo "Stopping LinkedIn watcher on port $PORT (PID: $PID)..."
        kill "$PID" 2>/dev/null
        sleep 1
        echo "Stopped."
    else
        echo "No LinkedIn watcher found running on port $PORT"
    fi
fi
