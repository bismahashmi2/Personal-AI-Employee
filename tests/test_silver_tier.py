import unittest
import time
import os
from pathlib import Path
from whatsapp_watcher import WhatsAppWatcher
from linkedin_watcher import LinkedInWatcher
from claude_reasoning_loop import ClaudeReasoningLoop
from approval_workflow import ApprovalWorkflow

class TestSilverTier(unittest.TestCase):
    def setUp(self):
        self.test_vault = Path('/tmp/silver_tier_test')
        self.test_vault.mkdir(exist_ok=True)

        # Create test directories
        (self.test_vault / 'Needs_Action').mkdir(exist_ok=True)
        (self.test_vault / 'Plans').mkdir(exist_ok=True)
        (self.test_vault / 'Done').mkdir(exist_ok=True)
        (self.test_vault / 'Pending_Approval').mkdir(exist_ok=True)
        (self.test_vault / 'Approved').mkdir(exist_ok=True)
        (self.test_vault / 'Rejected').mkdir(exist_ok=True)

    def test_whatsapp_watcher_implementation(self):
        """Test WhatsApp watcher class structure"""
        watcher = WhatsAppWatcher(str(self.test_vault), session_path='/tmp/test_session')
        self.assertEqual(watcher.check_interval, 30)
        self.assertEqual(watcher.keywords, ['urgent', 'asap', 'invoice', 'payment', 'help', 'pricing', 'quote'])

    def test_linkedin_watcher_implementation(self):
        """Test LinkedIn watcher class structure"""
        watcher = LinkedInWatcher(str(self.test_vault), api_key='test_key')
        self.assertEqual(watcher.check_interval, 300)  # 5 minutes

    def test_reasoning_loop_creation(self):
        """Test Claude reasoning loop initialization"""
        reasoning_loop = ClaudeReasoningLoop(str(self.test_vault))
        self.assertEqual(reasoning_loop.needs_action, self.test_vault / 'Needs_Action')
        self.assertEqual(reasoning_loop.plans, self.test_vault / 'Plans')

    def test_approval_workflow_creation(self):
        """Test approval workflow initialization"""
        approval_workflow = ApprovalWorkflow(str(self.test_vault))
        self.assertEqual(approval_workflow.pending_approval, self.test_vault / 'Pending_Approval')
        self.assertEqual(approval_workflow.approved, self.test_vault / 'Approved')

    def test_reasoning_loop_plan_creation(self):
        """Test plan creation from action file"""
        reasoning_loop = ClaudeReasoningLoop(str(self.test_vault))

        # Create test action file
        test_file = self.test_vault / 'Needs_Action/test_action.md'
        test_file.write_text("type: email\nsubject: Test Subject\nfrom: test@example.com")

        # Process it
        plans_created = reasoning_loop.process_needs_action()
        self.assertGreater(len(plans_created), 0)

        # Check if plan was created
        plans = list((self.test_vault / 'Plans').glob('*.md'))
        self.assertGreater(len(plans), 0)

    def test_approval_workflow_creation(self):
        """Test approval workflow file creation"""
        approval_workflow = ApprovalWorkflow(str(self.test_vault))

        # Create test approval request
        approval_file = approval_workflow.create_approval_request(
            'email_send',
            {
                'to': 'test@example.com',
                'subject': 'Test Subject',
                'body': 'Test email body'
            }
        )

        self.assertTrue(approval_file.exists())
        self.assertIn('Pending_Approval', str(approval_file))

        # Check content
        content = approval_file.read_text()
        self.assertIn('type: approval_request', content)
        self.assertIn('status: pending', content)

    def test_approval_workflow_parsing(self):
        """Test approval workflow file parsing"""
        approval_workflow = ApprovalWorkflow(str(self.test_vault))

        # Create test approval request
        approval_file = approval_workflow.create_approval_request(
            'payment',
            {
                'amount': 100.00,
                'recipient': 'Vendor A',
                'invoice_id': 'INV-123'
            }
        )

        # Parse it
        action = approval_workflow._parse_approval_file(approval_file)
        self.assertEqual(action['type'], 'payment')
        self.assertIn('amount', action['details'])
        self.assertEqual(action['details']['amount'], 100.00)

    def test_watcher_keywords(self):
        """Test watcher keyword functionality"""
        watcher = WhatsAppWatcher(str(self.test_vault), session_path='/tmp/test_session')

        # Test keyword matching
        test_messages = [
            ('urgent help needed', True),
            ('just checking in', False),
            ('pricing for 100 units', True),
            ('hello how are you', False),
            ('invoice payment due', True)
        ]

        for message, expected in test_messages:
            result = any(kw in message for kw in watcher.keywords)
            self.assertEqual(result, expected, f"Keyword test failed for: {message}")

if __name__ == '__main__':
    unittest.main()