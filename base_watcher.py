import time
import logging
import json
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class BaseWatcher(ABC):
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        self.running = False
        self._server = None
        self._server_thread = None

    @abstractmethod
    def check_for_updates(self) -> list:
        """Return list of new items to process"""
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create .md file in Needs_Action folder"""
        pass

    def run(self):
        """Run watcher in foreground (blocking)"""
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.running = True
        while self.running:
            try:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
            except Exception as e:
                self.logger.error(f'Error: {e}')
            time.sleep(self.check_interval)

    def stop(self):
        """Stop the watcher"""
        self.running = False
        self.logger.info(f'Stopped {self.__class__.__name__}')

    def run_mcp_server(self, host: str = 'localhost', port: int = 50051):
        """
        Run the watcher as an MCP server with HTTP transport.

        This allows other agents to call tools on this watcher.
        """
        self.logger.info(f'Starting {self.__class__.__name__} MCP server on {host}:{port}')

        # Create MCP request handler with access to this watcher instance
        watcher_instance = self

        class MCPRequestHandler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'

            def do_POST(self):
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)

                try:
                    request = json.loads(body)
                    method = request.get('method', '')
                    params = request.get('params', {})
                    request_id = request.get('id')

                    # Handle MCP methods
                    result = self.handle_mcp_request(method, params, watcher_instance)

                    response = {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'result': result
                    }
                except json.JSONDecodeError as e:
                    response = {
                        'jsonrpc': '2.0',
                        'id': None,
                        'error': {
                            'code': -32700,
                            'message': f'Parse error: {str(e)}'
                        }
                    }
                except Exception as e:
                    response = {
                        'jsonrpc': '2.0',
                        'id': request.get('id') if 'request' in locals() else None,
                        'error': {
                            'code': -32603,
                            'message': f'Internal error: {str(e)}'
                        }
                    }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Mcp-Session-Id', 'session-' + str(int(time.time())))
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

            def handle_mcp_request(self, method: str, params: dict, watcher) -> dict:
                """Handle MCP protocol methods"""
                if method == 'initialize':
                    return {
                        'protocolVersion': '2024-11-05',
                        'capabilities': {
                            'tools': {'listChanged': False},
                            'resources': {'subscribe': False, 'listChanged': False},
                            'prompts': {'listChanged': False}
                        },
                        'serverInfo': {
                            'name': watcher.__class__.__name__,
                            'version': '1.0.0'
                        }
                    }
                elif method == 'tools/list':
                    return {'tools': watcher._get_mcp_tools()}
                elif method == 'tools/call':
                    tool_name = params.get('name')
                    arguments = params.get('arguments', {})
                    return watcher._handle_tool_call(tool_name, arguments)
                elif method == 'resources/list':
                    return {'resources': []}
                elif method == 'prompts/list':
                    return {'prompts': []}
                else:
                    raise Exception(f'Unknown method: {method}')

            def log_message(self, format, *args):
                # Suppress HTTP logs
                pass

        self._server = HTTPServer((host, port), MCPRequestHandler)
        self._server_thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._server_thread.start()
        self.logger.info(f'MCP server started on {host}:{port}')

        try:
            self._server_thread.join()
        except KeyboardInterrupt:
            self.logger.info('MCP server shutting down...')
            self._server.shutdown()

    def _get_mcp_tools(self) -> List[Dict]:
        """Return list of MCP tools exposed by this watcher"""
        return [
            {
                'name': 'get_status',
                'description': 'Get current status and configuration of the watcher',
                'inputSchema': {
                    'type': 'object',
                    'properties': {},
                }
            },
            {
                'name': 'check_for_updates',
                'description': 'Manually trigger a check for new items',
                'inputSchema': {
                    'type': 'object',
                    'properties': {},
                }
            },
            {
                'name': 'stop',
                'description': 'Stop the watcher',
                'inputSchema': {
                    'type': 'object',
                    'properties': {},
                }
            }
        ]

    def _handle_tool_call(self, tool_name: str, arguments: dict) -> dict:
        """Handle a tool call and return result"""
        if tool_name == 'get_status':
            return {
                'watcher': self.__class__.__name__,
                'vault_path': str(self.vault_path),
                'check_interval': self.check_interval,
                'running': self.running
            }
        elif tool_name == 'check_for_updates':
            items = self.check_for_updates()
            created = []
            for item in items:
                path = self.create_action_file(item)
                created.append(str(path))
            return {
                'items_found': len(items),
                'action_files': created
            }
        elif tool_name == 'stop':
            self.stop()
            return {'stopped': True}
        else:
            raise Exception(f'Unknown tool: {tool_name}')
