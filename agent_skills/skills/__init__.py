#!/usr/bin/env python3
"""
Agent Skills Manager

Discovers and manages MCP-based agent skills from .agents/skills/ directory.

Usage:
    from agent_skills import SkillManager
    manager = SkillManager()
    manager.load_all_skills()
    result = manager.call_tool('linkedin-watcher', 'get_status', {})
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError
import subprocess
import threading
import time
import atexit

logger = logging.getLogger('AgentSkills')

class SkillManager:
    """Manages discovery and execution of agent skills"""

    def __init__(self, skills_dir: str = 'agent_skills/skills'):
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, 'Skill'] = {}
        self.running_servers: Dict[str, subprocess.Popen] = {}
        self._mcp_connections: Dict[str, 'MCPConnection'] = {}

    def discover_skills(self) -> List[str]:
        """Discover all skills in the skills directory"""
        self.skills = {}

        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return []

        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir() and not skill_path.name.startswith('.'):
                skill = Skill(skill_path)
                if skill.is_valid():
                    self.skills[skill.name] = skill
                    logger.info(f"Discovered skill: {skill.name}")

        return list(self.skills.keys())

    def get_skill(self, name: str) -> Optional['Skill']:
        """Get a skill by name"""
        return self.skills.get(name)

    def list_skills(self) -> List[Dict]:
        """List all available skills with their metadata"""
        return [
            {
                'name': skill.name,
                'description': skill.description,
                'tools': skill.tools,
                'path': str(skill.path)
            }
            for skill in self.skills.values()
        ]

    def start_skill_server(self, skill_name: str, port: int = None, vault_path: str = None) -> bool:
        """Start a skill's MCP server"""
        skill = self.skills.get(skill_name)
        if not skill:
            logger.error(f"Skill not found: {skill_name}")
            return False

        if skill_name in self.running_servers:
            logger.warning(f"Skill {skill_name} server already running")
            return True

        # Find start script
        start_script = skill.path / 'scripts' / 'start-server.sh'
        if not start_script.exists():
            logger.error(f"No start script for skill: {skill_name}")
            return False

        # Determine port
        if port is None:
            port = skill.default_port or 50051 + len(self.running_servers)

        # Determine vault path - by default use skills_dir.parent (vault root)
        # The skills_dir is typically agent_skills/skills, so parent is agent_skills, need vault
        # The actual vault root is the parent of agent_skills directory
        if vault_path is None:
            # skills_dir should be set to 'agent_skills/skills' by default
            # vault is two levels up from skills_dir (because skills_dir = vault/agent_skills/skills?)
            # Actually: skills_dir passed to SkillManager is 'agent_skills/skills'
            # So self.skills_dir.parent = agent_skills
            # Vault should be parent of that = current directory by default
            vault_path = str(self.skills_dir.parent.parent)

        try:
            import subprocess
            # Start script with: PORT VAULT_PATH
            # The start-server.sh handles its own cwd (cd to vault_path)
            proc = subprocess.Popen(
                [str(start_script), str(port), str(vault_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait a moment for startup
            time.sleep(2)

            if proc.poll() is not None:
                # Process exited
                _, stderr = proc.communicate()
                logger.error(f"Failed to start {skill_name}: {stderr}")
                return False

            self.running_servers[skill_name] = proc
            logger.info(f"Started {skill_name} on port {port}")
            return True

        except Exception as e:
            logger.error(f"Error starting {skill_name}: {e}")
            return False

    def stop_skill_server(self, skill_name: str):
        """Stop a skill's MCP server"""
        proc = self.running_servers.get(skill_name)
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            del self.running_servers[skill_name]
            logger.info(f"Stopped {skill_name} server")

    def call_tool(self, skill_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """Call a tool on a skill's MCP server"""
        # Ensure server is running
        if skill_name not in self._mcp_connections:
            skill = self.skills.get(skill_name)
            if not skill:
                raise ValueError(f"Skill not found: {skill_name}")

            port = skill.default_port
            if port is None:
                raise ValueError(f"Skill {skill_name} has no default port configured")

            self._mcp_connections[skill_name] = MCPConnection(
                f'http://localhost:{port}/mcp'
            )

        conn = self._mcp_connections[skill_name]
        return conn.call_tool(tool_name, arguments)

    def shutdown(self):
        """Shutdown all running servers and connections"""
        for skill_name in list(self.running_servers.keys()):
            self.stop_skill_server(skill_name)

        for conn in self._mcp_connections.values():
            conn.close()
        self._mcp_connections.clear()


class Skill:
    """Represents a single agent skill"""

    def __init__(self, path: Path):
        self.path = path.resolve()
        self.name = path.name
        self._description = None
        self._tools = None
        self._default_port = None
        self._load_metadata()

    def _load_metadata(self):
        """Load skill metadata from SKILL.md and config"""
        skill_md = self.path / 'SKILL.md'
        if skill_md.exists():
            content = skill_md.read_text()
            # Extract first section after yaml frontmatter if present
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    # Parse YAML frontmatter
                    try:
                        import yaml
                        metadata = yaml.safe_load(parts[1])
                        self._description = metadata.get('description', '')
                    except ImportError:
                        # Fallback: extract manually
                        for line in parts[1].split('\n'):
                            if line.startswith('description:'):
                                self._description = line.split(':', 1)[1].strip().strip('|')
                                break
                # Get rest as content
                content = parts[2] if len(parts) > 2 else ''
            else:
                content = content

            # Take first paragraph as description if not in frontmatter
            if not self._description:
                lines = content.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('#'):
                        self._description = line.strip()
                        break

        # Load default port from main script
        main_script = self.path / 'scripts' / 'start-server.sh'
        if main_script.exists():
            # Read to find default port
            content = main_script.read_text()
            if 'PORT=${1:-' in content:
                try:
                    port_str = content.split('PORT=${1:-')[1].split('}')[0]
                    self._default_port = int(port_str)
                except:
                    pass

    @property
    def description(self) -> str:
        return self._description or f"Skill: {self.name}"

    @property
    def tools(self) -> List[Dict]:
        if self._tools is not None:
            return self._tools

        # Try to get tools from running server or references
        tools_ref = self.path / 'references' / 'tools.json'
        if tools_ref.exists():
            try:
                self._tools = json.loads(tools_ref.read_text())
                return self._tools
            except:
                pass

        # Fallback: return placeholder
        self._tools = [{'name': 'check_for_updates', 'description': 'Check for updates'}]
        return self._tools

    @property
    def default_port(self) -> Optional[int]:
        return self._default_port

    def is_valid(self) -> bool:
        """Check if this is a valid skill"""
        required_files = ['SKILL.md', 'scripts']
        for f in required_files:
            if not (self.path / f).exists():
                return False
        return True


class MCPConnection:
    """HTTP connection to an MCP server"""

    def __init__(self, url: str):
        self.url = url.rstrip('/')
        if not self.url.endswith('/mcp'):
            self.url += '/mcp'
        self._session_id = None
        self._initialized = False

    def _ensure_initialized(self):
        """Initialize the MCP session"""
        if self._initialized:
            return

        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'agent-skills', 'version': '1.0.0'}
            }
        }

        response = self._request(payload)
        self._session_id = response.get('headers', {}).get('Mcp-Session-Id')
        self._initialized = True

        # Send initialized notification
        self._request({
            'jsonrpc': '2.0',
            'method': 'notifications/initialized'
        }, expect_response=False)

    def _request(self, payload: dict, expect_response: bool = True) -> dict:
        """Send request to MCP server"""
        import urllib.request

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream'
        }
        if self._session_id:
            headers['Mcp-Session-Id'] = self._session_id

        req = Request(
            self.url,
            data=json.dumps(payload).encode(),
            headers=headers,
            method='POST'
        )

        try:
            with urlopen(req, timeout=30) as resp:
                body = resp.read().decode()
                if expect_response:
                    return json.loads(body)
                return {}
        except Exception as e:
            logger.error(f"MCP request failed: {e}")
            raise

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict:
        """Call a tool on the MCP server"""
        self._ensure_initialized()

        payload = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/call',
            'params': {
                'name': name,
                'arguments': arguments
            }
        }

        response = self._request(payload)
        return response.get('result', {})

    def list_tools(self) -> List[Dict]:
        """List available tools"""
        self._ensure_initialized()

        payload = {
            'jsonrpc': '2.0',
            'id': 3,
            'method': 'tools/list',
            'params': {}
        }

        response = self._request(payload)
        return response.get('result', {}).get('tools', [])

    def close(self):
        """Close the connection"""
        self._initialized = False
        self._session_id = None


# Global manager instance
_manager: Optional[SkillManager] = None

def get_manager() -> SkillManager:
    """Get or create the global skill manager"""
    global _manager
    if _manager is None:
        _manager = SkillManager()
        _manager.discover_skills()
        atexit.register(_manager.shutdown)
    return _manager


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Agent Skills Manager')
    parser.add_argument('--skills-dir', default='agent_skills/skills', help='Skills directory')
    parser.add_argument('--start', help='Start a skill server')
    parser.add_argument('--stop', help='Stop a skill server')
    parser.add_argument('--list', action='store_true', help='List available skills')
    parser.add_argument('--call', nargs=3, metavar=('SKILL', 'TOOL', 'ARGS_JSON'),
                       help='Call a tool: skill_name tool_name \'{"arg": "value"}\'')

    args = parser.parse_args()

    manager = SkillManager(args.skills_dir)
    manager.discover_skills()

    if args.list:
        print("Available Skills:")
        for skill in manager.list_skills():
            print(f"\n  {skill['name']}")
            print(f"    {skill['description']}")
            print(f"    Tools: {', '.join(t['name'] for t in skill['tools'])}")

    elif args.start:
        if manager.start_skill_server(args.start):
            print(f"Started {args.start}")
        else:
            print(f"Failed to start {args.start}")
            exit(1)

    elif args.stop:
        manager.stop_skill_server(args.stop)
        print(f"Stopped {args.stop}")

    elif args.call:
        skill_name, tool_name, args_json = args.call
        try:
            arguments = json.loads(args_json)
            result = manager.call_tool(skill_name, tool_name, arguments)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}")
            exit(1)
