#!/usr/bin/env python3
"""
Run: python -m .agents.skills [arguments]

This is an entry point for the agent-skills module.
"""

from . import get_manager

if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python -m .agents.skills [list|start|stop|call] [args...]")
        print("\nCommands:")
        print("  list                          - List all discovered skills")
        print("  start <skill> [port]          - Start a skill MCP server")
        print("  stop <skill>                  - Stop a skill MCP server")
        print("  call <skill> <tool> <args>    - Call a tool (args as JSON)")
        sys.exit(1)

    manager = get_manager()
    command = sys.argv[1]

    if command == 'list':
        skills = manager.list_skills()
        print(json.dumps(skills, indent=2))

    elif command == 'start':
        if len(sys.argv) < 3:
            print("Usage: start <skill> [port]")
            sys.exit(1)
        skill = sys.argv[2]
        port = int(sys.argv[3]) if len(sys.argv) > 3 else None
        if manager.start_skill_server(skill, port):
            print(f"Started {skill}")
        else:
            print(f"Failed to start {skill}")
            sys.exit(1)

    elif command == 'stop':
        if len(sys.argv) < 3:
            print("Usage: stop <skill>")
            sys.exit(1)
        manager.stop_skill_server(sys.argv[2])
        print(f"Stopped {sys.argv[2]}")

    elif command == 'call':
        if len(sys.argv) < 5:
            print("Usage: call <skill> <tool> <json_args>")
            sys.exit(1)
        skill, tool, args_json = sys.argv[2], sys.argv[3], sys.argv[4]
        try:
            result = manager.call_tool(skill, tool, json.loads(args_json))
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
