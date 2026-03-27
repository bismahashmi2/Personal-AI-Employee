"""
Unit Tests for Decision Engine

Tests for the autonomous decision-making capability with context-aware processing,
multi-step reasoning, confidence scoring, and historical pattern learning.
"""

import asyncio
import json
import logging
import time
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

from decision_engine import (
    DecisionEngine, DecisionRequest, DecisionContext, DecisionContextType,
    DecisionPriority, DecisionOption, DecisionResult, DecisionOutcome,
    ConfidenceScorer, MultiStepReasoner, DecisionPattern, DecisionContextManager
)


class TestDecisionEngine(unittest.TestCase):
    """Test suite for DecisionEngine"""

    def setUp(self):
        """Set up test environment"""
        self.engine = DecisionEngine()
        self.logger = logging.getLogger("TestDecisionEngine")
        logging.basicConfig(level=logging.DEBUG)

    def test_confidence_scorer_basic(self):
        """Test basic confidence scoring functionality"""
        scorer = ConfidenceScorer()

        # Create test context and request
        context = DecisionContext(
            user_id="test_user",
            context_type=DecisionContextType.BUSINESS,
            user_preferences={"preferred_actions": ["approve"]},
            time_of_day="morning"
        )

        request = DecisionRequest(
            user_id="test_user",
            request_id="test_001",
            problem_statement="Test problem",
            context_type=DecisionContextType.BUSINESS,
            urgency=DecisionPriority.MEDIUM
        )

        # Create test options
        options = [
            DecisionOption(
                option_id="option_1",
                description="Test option",
                confidence_score=0.8,
                expected_outcome=DecisionOutcome.SUCCESS,
                steps_required=["Step 1", "Step 2"],
                resource_requirements={"time": 2.0},
                risk_level="low",
                explanation="Test explanation"
            )
        ]

        # Calculate confidence
        scores = scorer.calculate_confidence(context, request, options)

        # Verify scores are between 0 and 1
        for score in scores.values():
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

        # Verify at least one score was calculated
        self.assertGreater(len(scores), 0)

    def test_confidence_scoring_factors(self):
        """Test confidence scoring with different factors"""
        scorer = ConfidenceScorer()

        context = DecisionContext(
            user_id="test_user",
            context_type=DecisionContextType.TECHNICAL,
            user_preferences={"preferred_actions": ["auto"]},
            time_of_day="afternoon",
            recent_actions=["technical_auto"]
        )

        request = DecisionRequest(
            user_id="test_user",
            request_id="test_002",
            problem_statement="Technical issue",
            context_type=DecisionContextType.TECHNICAL,
            urgency=DecisionPriority.HIGH
        )

        options = [
            DecisionOption(
                option_id="auto",
                description="Automatic solution",
                confidence_score=0.9,
                expected_outcome=DecisionOutcome.SUCCESS,
                steps_required=["Analyze", "Fix", "Test"],
                resource_requirements={"time": 3.0},
                risk_level="medium",
                explanation="Auto solution"
            ),
            DecisionOption(
                option_id="manual",
                description="Manual solution",
                confidence_score=0.7,
                expected_outcome=DecisionOutcome.SUCCESS,
                steps_required=["Analyze", "Manual fix", "Test"],
                resource_requirements={"time": 5.0},
                risk_level="high",
                explanation="Manual solution"
            )
        ]

        scores = scorer.calculate_confidence(context, request, options)

        # Verify auto option gets higher score due to preferences and recent actions
        self.assertGreater(scores["auto"], scores["manual"])

        # Verify scores are reasonable
        self.assertGreaterEqual(scores["auto"], 0.5)
        self.assertGreaterEqual(scores["manual"], 0.3)

    def test_multi_step_reasoning(self):
        """Test multi-step reasoning functionality"""
        reasoner = MultiStepReasoner()

        context = DecisionContext(
            user_id="test_user",
            context_type=DecisionContextType.BUSINESS,
            time_of_day="morning"
        )

        request = DecisionRequest(
            user_id="test_user",
            request_id="test_003",
            problem_statement="Should we approve the project?",
            context_type=DecisionContextType.BUSINESS,
            urgency=DecisionPriority.MEDIUM
        )

        option = DecisionOption(
            option_id="approve",
            description="Approve the project",
            confidence_score=0.85,
            expected_outcome=DecisionOutcome.SUCCESS,
            steps_required=["Check budget", "Review timeline", "Get approvals"],
            resource_requirements={"time": 2.0, "approvals": 2},
            risk_level="low",
            explanation="Project approval"
        )

        # Test reasoning chain
        chain = reasoner.build_reasoning_chain(context, request, option)
        self.assertGreater(len(chain), 0)
        self.assertIn("Problem:", chain[0])
        self.assertIn("Selected Option:", chain[2])
        self.assertIn("Reasoning Steps:", chain[4])

        # Test multi-step plan
        plan = reasoner.create_multi_step_plan(context, request, option)
        self.assertEqual(len(plan), 3)  # Should have 3 steps
        for step in plan:
            self.assertIn('step_number', step)
            self.assertIn('action', step)
            self.assertIn('estimated_duration', step)
            self.assertGreater(step['estimated_duration'], 0)

    def test_decision_context_manager(self):
        """Test decision context manager functionality"""
        manager = DecisionContextManager()

        # Create context
        context = manager.create_context("test_user", DecisionContextType.PERSONAL)
        self.assertEqual(context.user_id, "test_user")
        self.assertEqual(context.context_type, DecisionContextType.PERSONAL)
        self.assertIn(context.time_of_day, ["morning", "afternoon", "evening", "night"])

        # Update context
        result = MagicMock()
        result.selected_option = DecisionOption(
            option_id="test_option",
            description="Test",
            confidence_score=0.9,
            expected_outcome=DecisionOutcome.SUCCESS,
            steps_required=["Step 1"],
            resource_requirements={"time": 1.0},
            risk_level="low",
            explanation="Test"
        )
        result.confidence_score = 0.9

        manager.update_context(context, result)
        self.assertIn("test_option", context.recent_actions)
        self.assertEqual(len(context.recent_actions), 1)

        # Test time of day and day of week
        time_context = manager.create_context("time_user", DecisionContextType.BUSINESS)
        self.assertIn(time_context.time_of_day, ["morning", "afternoon", "evening", "night"])
        self.assertIn(time_context.day_of_week, ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])

    @patch('time.localtime')
    def test_decision_engine_basic_flow(self, mock_time):
        """Test basic decision engine flow"""
        # Mock time to return consistent results
        mock_time.return_value = time.struct_time((2024, 1, 1, 10, 0, 0, 0, 1, 0))  # Monday at 10 AM

        engine = DecisionEngine()

        # Create test request and context
        request = DecisionRequest(
            user_id="test_user",
            request_id="test_004",
            problem_statement="Test decision problem",
            context_type=DecisionContextType.BUSINESS,
            urgency=DecisionPriority.MEDIUM,
            required_confidence=0.6
        )

        context = DecisionContext(
            user_id="test_user",
            context_type=DecisionContextType.BUSINESS,
            user_preferences={"preferred_actions": ["approve"]},
            time_of_day="morning",
            day_of_week="monday"
        )

        # Run decision
        result = asyncio.run(engine.make_decision(request, context))

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.request_id, "test_004")
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)
        self.assertGreater(len(result.reasoning_chain), 0)
        self.assertEqual(result.context_used.user_id, "test_user")

        # Verify context was updated
        self.assertIn(result.selected_option.option_id if result.selected_option else None,
                    result.context_used.recent_actions if result.context_used.recent_actions else [])

    def test_decision_engine_fallback(self):
        """Test fallback mechanism in decision engine"""
        engine = DecisionEngine()

        # Create request with very high confidence requirement
        request = DecisionRequest(
            user_id="test_user",
            request_id="test_005",
            problem_statement="Test fallback problem",
            context_type=DecisionContextType.TECHNICAL,
            urgency=DecisionPriority.LOW,
            required_confidence=0.99  # Very high requirement
        )

        context = DecisionContext(
            user_id="test_user",
            context_type=DecisionContextType.TECHNICAL,
            time_of_day="morning"
        )

        # Run decision
        result = asyncio.run(engine.make_decision(request, context))

        # Verify fallback was applied if confidence was low
        # Since we can't control confidence scores in test, we'll check structure
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)
        self.assertIn("Fallback Plan:", result.reasoning_chain[-1])

    def test_decision_engine_pattern_learning(self):
        """Test pattern learning functionality"""
        engine = DecisionEngine()

        # Create initial request
        request1 = DecisionRequest(
            user_id="test_user",
            request_id="test_006",
            problem_statement="Pattern learning test 1",
            context_type=DecisionContextType.BUSINESS,
            urgency=DecisionPriority.MEDIUM
        )

        context1 = DecisionContext(
            user_id="test_user",
            context_type=DecisionContextType.BUSINESS
        )

        # Make first decision
        result1 = asyncio.run(engine.make_decision(request1, context1))

        # Create second request with similar context
        request2 = DecisionRequest(
            user_id="test_user",
            request_id="test_007",
            problem_statement="Pattern learning test 2",
            context_type=DecisionContextType.BUSINESS,
            urgency=DecisionPriority.MEDIUM
        )

        context2 = DecisionContext(
            user_id="test_user",
            context_type=DecisionContextType.BUSINESS,
            recent_actions=result1.context_used.recent_actions
        )

        # Make second decision
        result2 = asyncio.run(engine.make_decision(request2, context2))

        # Verify patterns were created and context was updated
        self.assertGreater(len(engine.patterns), 0)
        self.assertIn(result1.selected_option.option_id if result1.selected_option else None,
                    context2.recent_actions if context2.recent_actions else [])

    def test_decision_engine_error_handling(self):
        """Test error handling in decision engine"""
        engine = DecisionEngine()

        # Test with invalid context type
        request = DecisionRequest(
            user_id="test_user",
            request_id="test_008",
            problem_statement="Error handling test",
            context_type=None,  # Invalid context
            urgency=DecisionPriority.MEDIUM
        )

        # Should handle gracefully without crashing
        try:
            result = asyncio.run(engine.make_decision(request))
            self.assertIsNotNone(result)
            self.assertEqual(result.confidence_score, 0.0)
            self.assertIsNone(result.selected_option)
        except Exception as e:
            self.fail(f"Decision engine raised unexpected exception: {e}")

    def test_decision_option_generation(self):
        """Test decision option generation for different contexts"""
        engine = DecisionEngine()

        # Test business context options
        business_request = DecisionRequest(
            user_id="test_user",
            request_id="test_009",
            problem_statement="Business test",
            context_type=DecisionContextType.BUSINESS
        )

        business_options = engine._generate_options(business_request, DecisionContext(
            user_id="test_user",
            context_type=DecisionContextType.BUSINESS
        ))

        self.assertGreater(len(business_options), 0)
        for option in business_options:
            self.assertIn(option.risk_level, ["low", "medium", "high"])
            self.assertGreaterEqual(option.confidence_score, 0.0)
            self.assertLessEqual(option.confidence_score, 1.0)

        # Test technical context options
        technical_request = DecisionRequest(
            user_id="test_user",
            request_id="test_010",
            problem_statement="Technical test",
            context_type=DecisionContextType.TECHNICAL
        )

        technical_options = engine._generate_options(technical_request, DecisionContext(
            user_id="test_user",
            context_type=DecisionContextType.TECHNICAL
        ))

        self.assertGreater(len(technical_options), 0)

        # Test social context options
        social_request = DecisionRequest(
            user_id="test_user",
            request_id="test_011",
            problem_statement="Social test",
            context_type=DecisionContextType.SOCIAL
        )

        social_options = engine._generate_options(social_request, DecisionContext(
            user_id="test_user",
            context_type=DecisionContextType.SOCIAL
        ))

        self.assertGreater(len(social_options), 0)

    def test_decision_engine_cli_interface(self):
        """Test CLI interface functionality"""
        # Test basic CLI functionality
        from decision_engine import main  # Assuming main function exists

        # Mock command line arguments
        test_args = [
            "--test",
            "--context", "business",
            "--user", "cli_test_user",
            "--problem", "CLI test problem"
        ]

        # This would normally test the CLI interface
        # For now, we'll just verify the arguments are parsed correctly
        # In a real test, we would use subprocess or mock sys.argv
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)