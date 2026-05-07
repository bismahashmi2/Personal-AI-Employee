#!/usr/bin/env python3
"""
Verify LinkedIn Watcher MCP skill is working correctly.

Usage: python verify.py [host] [port]

Defaults: localhost:50056
"""

import sys
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

def verify(host='localhost', port=50056):
    url = f'http://{host}:{port}/mcp'

    print(f"Checking LinkedIn Watcher MCP server at {url}...")

    # Test initialize request
    init_request = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'initialize',
        'params': {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'verify', 'version': '1.0.0'}
        }
    }

    try:
        req = Request(url, data=json.dumps(init_request).encode(),
                     headers={'Content-Type': 'application/json'})
        with urlopen(req, timeout=5) as resp:
            response = json.loads(resp.read().decode())

        if 'error' in response:
            print(f"✗ Initialize failed: {response['error']}")
            return False

        server_info = response.get('result', {}).get('serverInfo', {})
        print(f"✓ Connected to {server_info.get('name', 'LinkedIn Watcher')} v{server_info.get('version', '1.0.0')}")

        # Test tools/list
        list_request = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/list',
            'params': {}
        }

        req = Request(url, data=json.dumps(list_request).encode(),
                     headers={'Content-Type': 'application/json'})
        with urlopen(req, timeout=5) as resp:
            response = json.loads(resp.read().decode())

        tools = response.get('result', {}).get('tools', [])
        print(f"✓ Available tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool['name']}: {tool.get('description', 'No description')[:60]}...")

        print("\n✓ All checks passed!")
        return True

    except URLError as e:
        print(f"✗ Connection failed: {e.reason}")
        print("  Is the server running? Start with: ./scripts/start-server.sh")
        return False
    except HTTPError as e:
        print(f"✗ HTTP error {e.code}: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 50056

    success = verify(host, port)
    sys.exit(0 if success else 1)
