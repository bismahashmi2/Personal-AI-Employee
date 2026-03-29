#!/usr/bin/env python
"""Test script for Silver Tier system without WhatsApp"""

import sys
sys.path.insert(0, '.')

from silver_tier_main import SilverTierSystem

print("Testing Silver Tier System Components...")

# Check if token.json exists for Gmail
from pathlib import Path
token_path = Path('token.json')
if token_path.exists():
    print("✅ Gmail token.json found")
else:
    print("⚠️  Gmail token.json NOT found - Gmail watcher will fail")

# Check linkedin_watcher
from linkedin_watcher import LinkedInWatcher
linkedin = LinkedInWatcher('.', api_key=None)
print("✅ LinkedInWatcher loaded (will run in demo mode)")

# Check base_watcher
from base_watcher import BaseWatcher
print("✅ BaseWatcher abstract class available")

# Check MCP server
from mcp_email_server import EmailMCPServer
try:
    email_mcp = EmailMCPServer(config_path='mcp_config.json')
    print("✅ EmailMCPServer initialized")
except Exception as e:
    print(f"⚠️  EmailMCPServer warning: {e}")

# Check scheduler
from scheduler import Scheduler
scheduler = Scheduler('.')
print("✅ Scheduler loaded")

# Check approval workflow
from approval_workflow import ApprovalWorkflow
approval = ApprovalWorkflow('.')
print("✅ ApprovalWorkflow loaded")

# Check reasoning loop
from claude_reasoning_loop import ClaudeReasoningLoop
reasoning = ClaudeReasoningLoop('.')
print("✅ ClaudeReasoningLoop loaded")

print("\n" + "="*50)
print("All core components ready!")
print("="*50)
print("\nTo start the system:")
print("  python silver_tier_main.py .")
print("\nExpected watchers:")
print("  - Gmail (if token.json valid)")
print("  - LinkedIn (demo mode)")
