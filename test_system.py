#!/usr/bin/env python3
"""
Quick test script for the AI Employee system
Tests all major components
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_decision_engine():
    """Test Gold Tier Decision Engine"""
    print("\n=== Testing Decision Engine (Gold Tier) ===")
    from decision_engine import DecisionEngine, DecisionRequest, DecisionContext, DecisionContextType, DecisionPriority

    engine = DecisionEngine()

    # Test business decision
    request = DecisionRequest(
        user_id="test_user",
        request_id="test_001",
        problem_statement="Should we approve the budget increase?",
        context_type=DecisionContextType.BUSINESS,
        urgency=DecisionPriority.MEDIUM,
        required_confidence=0.6
    )

    context = DecisionContext(
        user_id="test_user",
        context_type=DecisionContextType.BUSINESS,
        business_rules={"budget_available": True},
        user_preferences={"preferred_actions": ["approve"]}
    )

    result = asyncio.run(engine.make_decision(request, context))

    print(f"Selected: {result.selected_option.description if result.selected_option else 'None'}")
    print(f"Confidence: {result.confidence_score:.2f}")
    print(f"Reasoning steps: {len(result.reasoning_chain)}")
    print("✓ Decision Engine works!")
    return True

def test_silver_components():
    """Test Silver Tier components"""
    print("\n=== Testing Silver Tier Components ===")
    vault_path = Path(__file__).parent

    # Test Claude Reasoning Loop
    print("Testing Claude Reasoning Loop...")
    from claude_reasoning_loop import ClaudeReasoningLoop
    reasoning = ClaudeReasoningLoop(str(vault_path))
    print("✓ Reasoning Loop initialized")

    # Test Approval Workflow
    print("Testing Approval Workflow...")
    from approval_workflow import ApprovalWorkflow
    approval = ApprovalWorkflow(str(vault_path))
    approval_file = approval.create_approval_request('email_send', {
        'to': 'test@example.com',
        'subject': 'Test',
        'body': 'Test email'
    })
    print(f"✓ Created approval: {approval_file.name}")

    # Test Scheduler
    print("Testing Scheduler...")
    from scheduler import Scheduler
    scheduler = Scheduler(str(vault_path))
    print("✓ Scheduler initialized with daily briefing and weekly audit")

    return True

def test_orchestrator():
    """Test Orchestrator"""
    print("\n=== Testing Orchestrator ===")
    from orchestrator import Orchestrator

    orchestrator = Orchestrator()
    orchestrator.register_watcher("test_service", "localhost", 50051, priority=1)
    print(f"Registered watcher: test_service")
    print(f"Total watchers: {len(orchestrator.watchers)}")
    print("✓ Orchestrator works!")
    return True

def test_mcp_server():
    """Test MCP Email Server"""
    print("\n=== Testing MCP Email Server ===")
    from mcp_email_server import EmailMCPServer
    import tempfile
    import json

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_use_tls": True,
            "smtp_auth": True,
            "smtp_user": "test@gmail.com",
            "smtp_password": "test_pass"
        }
        json.dump(config, f)
        config_path = f.name

    try:
        server = EmailMCPServer(config_path)
        print("✓ MCP Email Server initialized (dry-run mode)")
        return True
    finally:
        Path(config_path).unlink(missing_ok=True)

def main():
    print("=" * 50)
    print("AI Employee System Test")
    print("=" * 50)

    tests = [
        ("Decision Engine (Gold)", test_decision_engine),
        ("Silver Components", test_silver_components),
        ("Orchestrator", test_orchestrator),
        ("MCP Email Server", test_mcp_server),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {name} failed: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Results: {passed}/{len(tests)} passed")
    print("=" * 50)

    if failed == 0:
        print("\n🎉 All systems operational!")
        print("\nNext steps:")
        print("1. Set up your vault structure with real folders")
        print("2. Configure credentials in .env file")
        print("3. Run silver_tier_main.py to start the full system")
        print("4. Check Dashboard.md for real-time updates")
    else:
        print(f"\n⚠️  {failed} test(s) failed - check errors above")

    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
