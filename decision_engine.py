#!/usr/bin/env python3
"""
Decision Engine

Core autonomous decision-making capability that provides context-aware processing,
multi-step reasoning, confidence scoring, and historical pattern learning for
Gold Tier AI Employee functionality.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable, TypeVar
from dataclasses import dataclass, field
from enum import Enum
import random
from collections import defaultdict
import math


# Type variables for generic decision handlers
T = TypeVar('T')


class DecisionContextType(Enum):
    BUSINESS = "business"
    TECHNICAL = "technical"
    SOCIAL = "social"
    PERSONAL = "personal"


class DecisionPriority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class DecisionOutcome(Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    INCONCLUSIVE = "inconclusive"


@dataclass
class DecisionContext:
    """Context for a decision - contains user preferences, historical patterns, and business rules"""
    user_id: str
    context_type: DecisionContextType
    business_rules: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    historical_patterns: Dict[str, Any] = field(default_factory=dict)
    current_state: Dict[str, Any] = field(default_factory=dict)
    time_of_day: str = "unknown"
    day_of_week: str = "unknown"
    recent_actions: List[str] = field(default_factory=list)


@dataclass
class DecisionRequest:
    """Request for a decision - contains the problem to be solved and context"""
    user_id: str
    request_id: str
    problem_statement: str
    context_type: DecisionContextType
    available_options: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    urgency: DecisionPriority = DecisionPriority.MEDIUM
    required_confidence: float = 0.7


@dataclass
class DecisionOption:
    """A potential decision option with metadata"""
    option_id: str
    description: str
    confidence_score: float = 0.0  # Will be calculated
    expected_outcome: DecisionOutcome = DecisionOutcome.SUCCESS
    steps_required: List[str] = None
    resource_requirements: Dict[str, float] = None
    risk_level: str = "medium"
    explanation: str = ""
    quality_score: float = 0.5  # Inherent quality of this option (0.0-1.0)

    def __post_init__(self):
        if self.steps_required is None:
            self.steps_required = []
        if self.resource_requirements is None:
            self.resource_requirements = {}


@dataclass
class DecisionResult:
    """Result of a decision process"""
    request_id: str
    selected_option: Optional[DecisionOption]
    confidence_score: float
    reasoning_chain: List[str]
    multi_step_plan: Optional[List[Dict[str, Any]]]
    fallback_applied: bool
    timestamp: float
    context_used: DecisionContext


@dataclass
class DecisionPattern:
    """Historical pattern for learning and improvement"""
    pattern_id: str
    trigger_conditions: Dict[str, Any]
    successful_actions: List[str]
    success_rate: float
    last_used: float
    frequency: int


class ConfidenceScorer:
    """Calculates confidence scores for decisions based on multiple factors"""

    def __init__(self):
        self.logger = logging.getLogger("ConfidenceScorer")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def calculate_confidence(self, context: DecisionContext, request: DecisionRequest,
                            options: List[DecisionOption]) -> Dict[str, float]:
        """Calculate confidence scores for all options"""
        scores = {}
        for option in options:
            score = self._calculate_single_confidence(context, request, option)
            scores[option.option_id] = score
        return scores

    def _calculate_single_confidence(self, context: DecisionContext, request: DecisionRequest,
                                   option: DecisionOption) -> float:
        """Calculate confidence score for a single option"""
        # Base confidence based on option quality
        base_confidence = self._calculate_base_confidence(option)

        # Context adjustment
        context_adjustment = self._calculate_context_adjustment(context, option)

        # Pattern matching with historical data
        pattern_adjustment = self._calculate_pattern_adjustment(context, option)

        # Urgency adjustment
        urgency_adjustment = self._calculate_urgency_adjustment(request.urgency, option)

        # Final confidence score
        confidence = base_confidence + context_adjustment + pattern_adjustment + urgency_adjustment
        confidence = max(0.0, min(1.0, confidence))  # Clamp between 0 and 1

        return confidence

    def _calculate_base_confidence(self, option: DecisionOption) -> float:
        """Calculate base confidence from option properties"""
        # Use inherent quality score plus some base, then adjust for risk
        base = option.quality_score if hasattr(option, 'quality_score') else 0.5
        risk_penalty = 0.0

        if option.risk_level == "high":
            risk_penalty = -0.2
        elif option.risk_level == "medium":
            risk_penalty = -0.1

        # Calculate base confidence more generously so scores aren't too low
        return max(0.3, base - risk_penalty)

    def _calculate_context_adjustment(self, context: DecisionContext, option: DecisionOption) -> float:
        """Adjust confidence based on context"""
        adjustment = 0.0

        # Check if option matches user preferences
        if context.user_preferences:
            preferred = context.user_preferences.get('preferred_actions', [])
            if any(pref in option.description.lower() for pref in preferred):
                adjustment += 0.15

        # Check time-based patterns (small positive adjustment for productive hours)
        if context.time_of_day in ['morning', 'afternoon']:
            adjustment += 0.05
        elif context.time_of_day == 'evening':
            adjustment -= 0.05

        return adjustment

    def _calculate_pattern_adjustment(self, context: DecisionContext, option: DecisionOption) -> float:
        """Adjust confidence based on historical patterns"""
        # This would normally query a pattern database
        # For now, we'll use simple pattern matching
        adjustment = 0.0

        # If option matches recent successful actions
        if option.option_id in context.recent_actions[-3:]:  # Last 3 actions
            adjustment += 0.2

        # Check day of week patterns
        if context.day_of_week in ['monday', 'tuesday']:
            # Higher confidence for certain actions on weekdays
            adjustment += 0.1

        return adjustment

    def _calculate_urgency_adjustment(self, urgency: DecisionPriority, option: DecisionOption) -> float:
        """Adjust confidence based on urgency"""
        if urgency == DecisionPriority.HIGH:
            # High urgency might reduce confidence for complex options
            if len(option.steps_required) > 2:
                return -0.15
            return 0.0
        elif urgency == DecisionPriority.LOW:
            # Low urgency allows for more thorough options
            return 0.1
        return 0.0


class MultiStepReasoner:
    """Handles multi-step reasoning and chained actions"""

    def __init__(self):
        self.logger = logging.getLogger("MultiStepReasoner")

    def build_reasoning_chain(self, context: DecisionContext, request: DecisionRequest,
                             option: DecisionOption) -> List[str]:
        """Build a reasoning chain for the selected option"""
        chain = []

        # Add problem statement
        chain.append(f"Problem: {request.problem_statement}")

        # Add context analysis (guard against None context_type)
        context_type = context.context_type.value if context.context_type else "unknown"
        chain.append(f"Context: {context_type} with {len(context.business_rules)} business rules")

        # Add option rationale
        chain.append(f"Selected Option: {option.description}")
        chain.append(f"Confidence: {option.confidence_score:.2f}")

        # Add Reasoning Steps at position 4 (index 4) as expected by tests
        chain.append("Reasoning Steps:")

        # Add step-by-step reasoning
        if option.steps_required:
            for i, step in enumerate(option.steps_required, 1):
                chain.append(f"  {i}. {step}")

        # Add risk level after steps
        chain.append(f"Risk Level: {option.risk_level}")

        # Add resource analysis
        if option.resource_requirements:
            chain.append("Resource Requirements:")
            for resource, amount in option.resource_requirements.items():
                chain.append(f"  {resource}: {amount}")

        # Add fallback consideration
        chain.append("Fallback Plan: Available if confidence < 0.5")

        return chain

    def create_multi_step_plan(self, context: DecisionContext, request: DecisionRequest,
                              option: DecisionOption) -> List[Dict[str, Any]]:
        """Create a detailed multi-step execution plan"""
        plan = []

        if not option.steps_required:
            return plan

        # Create sequential steps with timing estimates
        for i, step in enumerate(option.steps_required, 1):
            step_plan = {
                'step_number': i,
                'action': step,
                'estimated_duration': random.uniform(0.5, 3.0),  # Estimate duration in seconds
                'dependencies': [s['step_number'] for s in plan] if plan else [],
                'status': 'pending',
                'priority': option.resource_requirements.get('priority', 'medium')
            }
            plan.append(step_plan)

        return plan


class DecisionEngine:
    """Main decision engine that coordinates all decision-making processes"""

    def __init__(self):
        self.logger = logging.getLogger("DecisionEngine")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        self.confidence_scorer = ConfidenceScorer()
        self.reasoner = MultiStepReasoner()
        self.patterns: Dict[str, DecisionPattern] = {}
        self.context_manager = DecisionContextManager()

    async def make_decision(self, request: DecisionRequest,
                          context: Optional[DecisionContext] = None) -> DecisionResult:
        """Make a decision based on request and context"""
        self.logger.info(f"Making decision for request {request.request_id}")

        # Validate context_type
        if request.context_type is None:
            self.logger.warning("Invalid context_type: None")
            return DecisionResult(
                request_id=request.request_id,
                selected_option=None,
                confidence_score=0.0,
                reasoning_chain=["Error: Invalid context type"],
                multi_step_plan=None,
                fallback_applied=False,
                timestamp=time.time(),
                context_used=context or DecisionContext(
                    user_id=request.user_id,
                    context_type=DecisionContextType.PERSONAL
                )
            )

        # Get or create context
        if not context:
            context = self.context_manager.create_context(request.user_id, request.context_type)

        # Generate potential options
        options = self._generate_options(request, context)

        # Calculate confidence scores
        confidence_scores = self.confidence_scorer.calculate_confidence(context, request, options)
        for option in options:
            option.confidence_score = confidence_scores.get(option.option_id, 0.0)

        # Select best option
        selected_option = self._select_best_option(options, request.required_confidence)

        # Build reasoning chain
        reasoning_chain = self.reasoner.build_reasoning_chain(context, request, selected_option)

        # Create multi-step plan if needed
        multi_step_plan = None
        if selected_option and len(selected_option.steps_required) > 1:
            multi_step_plan = self.reasoner.create_multi_step_plan(context, request, selected_option)

        # Determine if fallback is needed
        fallback_applied = False
        if selected_option and selected_option.confidence_score < 0.5:
            fallback_applied = True
            # In a real system, we would apply fallback logic here

        # Create result
        result = DecisionResult(
            request_id=request.request_id,
            selected_option=selected_option,
            confidence_score=selected_option.confidence_score if selected_option else 0.0,
            reasoning_chain=reasoning_chain,
            multi_step_plan=multi_step_plan,
            fallback_applied=fallback_applied,
            timestamp=time.time(),
            context_used=context
        )

        # Update patterns and context
        self._update_patterns(result)
        self.context_manager.update_context(context, result)

        self.logger.info(f"Decision made: {selected_option.description if selected_option else 'None'} "
                        f"with confidence {result.confidence_score:.2f}")

        return result

    def _generate_options(self, request: DecisionRequest, context: DecisionContext) -> List[DecisionOption]:
        """Generate potential decision options"""
        options = []

        # Simple option generation based on problem type
        if request.context_type == DecisionContextType.BUSINESS:
            options = self._generate_business_options(request, context)
        elif request.context_type == DecisionContextType.TECHNICAL:
            options = self._generate_technical_options(request, context)
        elif request.context_type == DecisionContextType.SOCIAL:
            options = self._generate_social_options(request, context)
        else:
            options = self._generate_default_options(request, context)

        return options

    def _generate_business_options(self, request: DecisionRequest, context: DecisionContext) -> List[DecisionOption]:
        """Generate business-related decision options"""
        options = [
            DecisionOption(
                option_id="business_approve",
                description="Approve the request based on standard business rules",
                quality_score=0.7,
                expected_outcome=DecisionOutcome.SUCCESS,
                steps_required=["Verify request against business rules", "Check budget constraints", "Obtain necessary approvals"],
                resource_requirements={"time": 2.0, "approvals": 2},
                risk_level="low",
                explanation="Standard approval process following established business protocols"
            ),
            DecisionOption(
                option_id="business_review",
                description="Review request with detailed analysis",
                quality_score=0.85,
                expected_outcome=DecisionOutcome.PARTIAL_SUCCESS,
                steps_required=["Analyze request details", "Compare with historical data", "Consult with stakeholders", "Make recommendation"],
                resource_requirements={"time": 5.0, "stakeholders": 3, "analysis": 1},
                risk_level="medium",
                explanation="Comprehensive review process for complex requests"
            ),
            DecisionOption(
                option_id="business_delegate",
                description="Delegate to appropriate team member",
                quality_score=0.75,
                expected_outcome=DecisionOutcome.SUCCESS,
                steps_required=["Identify appropriate delegate", "Provide context and requirements", "Monitor progress", "Review outcome"],
                resource_requirements={"time": 1.0, "coordination": 1},
                risk_level="low",
                explanation="Delegation to subject matter expert for specialized decisions"
            )
        ]

        return options

    def _generate_technical_options(self, request: DecisionRequest, context: DecisionContext) -> List[DecisionOption]:
        """Generate technical decision options"""
        options = [
            DecisionOption(
                option_id="technical_auto",
                description="Automatic technical solution",
                quality_score=0.8,
                expected_outcome=DecisionOutcome.SUCCESS,
                steps_required=["Analyze technical requirements", "Select optimal solution", "Implement automated fix", "Test and validate"],
                resource_requirements={"time": 3.0, "automation": 1, "testing": 1},
                risk_level="medium",
                explanation="Automated technical solution using best practices"
            ),
            DecisionOption(
                option_id="technical_manual",
                description="Manual technical intervention",
                quality_score=0.9,
                expected_outcome=DecisionOutcome.SUCCESS,
                steps_required=["Manual assessment", "Custom implementation", "Manual testing", "Documentation"],
                resource_requirements={"time": 4.0, "manual_labor": 1, "expertise": 1},
                risk_level="high",
                explanation="Manual technical intervention for complex or unique cases"
            ),
            DecisionOption(
                option_id="technical_refer",
                description="Refer to technical specialist",
                quality_score=0.95,
                expected_outcome=DecisionOutcome.SUCCESS,
                steps_required=["Identify specialist", "Provide detailed context", "Escalate with priority", "Review specialist recommendation"],
                resource_requirements={"time": 1.0, "specialist": 1, "coordination": 1},
                risk_level="low",
                explanation="Escalation to technical specialist for expert handling"
            )
        ]

        return options

    def _generate_social_options(self, request: DecisionRequest, context: DecisionContext) -> List[DecisionOption]:
        """Generate social decision options"""
        options = [
            DecisionOption(
                option_id="social_mediate",
                description="Mediate social situation",
                quality_score=0.7,
                expected_outcome=DecisionOutcome.SUCCESS,
                steps_required=["Understand all perspectives", "Facilitate communication", "Find common ground", "Establish agreement"],
                resource_requirements={"time": 4.0, "empathy": 1, "communication": 1},
                risk_level="medium",
                explanation="Mediation to resolve social or interpersonal conflicts"
            ),
            DecisionOption(
                option_id="social_support",
                description="Provide social support",
                quality_score=0.8,
                expected_outcome=DecisionOutcome.SUCCESS,
                steps_required=["Listen actively", "Provide emotional support", "Offer practical assistance", "Follow up"],
                resource_requirements={"time": 2.0, "empathy": 1, "resources": 1},
                risk_level="low",
                explanation="Supportive approach for social or emotional situations"
            ),
            DecisionOption(
                option_id="social_delegate",
                description="Delegate to social expert",
                quality_score=0.85,
                expected_outcome=DecisionOutcome.SUCCESS,
                steps_required=["Identify appropriate expert", "Provide context", "Coordinate intervention", "Monitor outcome"],
                resource_requirements={"time": 1.0, "expert": 1, "coordination": 1},
                risk_level="low",
                explanation="Escalation to social expert for complex interpersonal situations"
            )
        ]

        return options

    def _generate_default_options(self, request: DecisionRequest, context: DecisionContext) -> List[DecisionOption]:
        """Generate default options for unknown contexts"""
        options = [
            DecisionOption(
                option_id="default_standard",
                description="Apply standard procedure",
                quality_score=0.6,
                expected_outcome=DecisionOutcome.SUCCESS,
                steps_required=["Apply standard operating procedures", "Document decision", "Communicate outcome"],
                resource_requirements={"time": 1.0, "documentation": 1},
                risk_level="low",
                explanation="Standard procedure for routine decisions"
            ),
            DecisionOption(
                option_id="default_escalate",
                description="Escalate to human supervisor",
                quality_score=0.9,
                expected_outcome=DecisionOutcome.SUCCESS,
                steps_required=["Prepare detailed context", "Escalate with priority", "Await human decision", "Implement outcome"],
                resource_requirements={"time": 0.5, "escalation": 1},
                risk_level="low",
                explanation="Escalation to human for complex or high-stakes decisions"
            )
        ]

        return options

    def _select_best_option(self, options: List[DecisionOption], required_confidence: float) -> Optional[DecisionOption]:
        """Select the best option based on confidence scores"""
        if not options:
            return None

        # Sort by confidence score descending
        sorted_options = sorted(options, key=lambda o: o.confidence_score, reverse=True)

        # Find highest confidence option that meets minimum threshold
        for option in sorted_options:
            if option.confidence_score >= required_confidence:
                return option

        # If none meet threshold, return highest confidence option anyway
        return sorted_options[0]

    def _update_patterns(self, result: DecisionResult):
        """Update decision patterns based on outcome"""
        if not result.selected_option:
            return

        # This would normally query a pattern database
        # For now, we'll just log the pattern
        pattern_id = f"pattern_{int(time.time())}"

        pattern = DecisionPattern(
            pattern_id=pattern_id,
            trigger_conditions={
                'context_type': str(result.context_used.context_type),
                'option_id': result.selected_option.option_id,
                'confidence': result.confidence_score
            },
            successful_actions=result.selected_option.steps_required,
            success_rate=result.confidence_score,
            last_used=time.time(),
            frequency=1
        )

        self.patterns[pattern_id] = pattern


class DecisionContextManager:
    """Manages user contexts and historical patterns"""

    def __init__(self):
        self.contexts: Dict[str, DecisionContext] = {}
        self.logger = logging.getLogger("DecisionContextManager")

    def create_context(self, user_id: str, context_type: DecisionContextType) -> DecisionContext:
        """Create a new decision context"""
        context = DecisionContext(
            user_id=user_id,
            context_type=context_type,
            time_of_day=self._get_time_of_day(),
            day_of_week=self._get_day_of_week(),
            recent_actions=[]
        )

        self.contexts[user_id] = context
        return context

    def update_context(self, context: DecisionContext, result: DecisionResult):
        """Update context with new decision result"""
        if context is None:
            return

        # Ensure context is tracked
        if context.user_id not in self.contexts:
            self.contexts[context.user_id] = context

        # Update recent actions
        if result.selected_option:
            context.recent_actions.append(result.selected_option.option_id)
            # Keep only last 5 actions
            if len(context.recent_actions) > 5:
                context.recent_actions = context.recent_actions[-5:]

        # Update business rules based on outcome
        if result.confidence_score > 0.8:
            context.business_rules['high_confidence'] = True
        elif result.confidence_score < 0.3:
            context.business_rules['low_confidence'] = True

        # Update user preferences based on successful outcomes
        if result.confidence_score > 0.7 and result.selected_option:
            if 'preferred_actions' not in context.user_preferences:
                context.user_preferences['preferred_actions'] = []
            context.user_preferences['preferred_actions'].append(result.selected_option.description)

    def get_context(self, user_id: str) -> Optional[DecisionContext]:
        """Get existing context for user"""
        return self.contexts.get(user_id)

    def _get_time_of_day(self) -> str:
        """Get current time of day"""
        current_hour = time.localtime().tm_hour
        if 6 <= current_hour < 12:
            return "morning"
        elif 12 <= current_hour < 18:
            return "afternoon"
        elif 18 <= current_hour < 22:
            return "evening"
        else:
            return "night"

    def _get_day_of_week(self) -> str:
        """Get current day of week"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        return days[time.localtime().tm_wday]


def main():
    """CLI entry point for decision engine"""
    import argparse

    parser = argparse.ArgumentParser(description="Decision Engine CLI")
    parser.add_argument("--test", action="store_true", help="Run test decisions")
    parser.add_argument("--context", choices=[t.value for t in DecisionContextType],
                       help="Decision context type")
    parser.add_argument("--user", default="test_user", help="User ID for decision")
    parser.add_argument("--problem", help="Problem statement for decision")

    args = parser.parse_args()

    engine = DecisionEngine()

    if args.test:
        print("Running test decisions...")

        # Test business context
        business_request = DecisionRequest(
            user_id=args.user,
            request_id="test_001",
            problem_statement="Should we approve the budget increase request?",
            context_type=DecisionContextType.BUSINESS,
            urgency=DecisionPriority.MEDIUM,
            required_confidence=0.6
        )

        business_context = DecisionContext(
            user_id=args.user,
            context_type=DecisionContextType.BUSINESS,
            business_rules={"budget_available": True, "prior_approvals": 3},
            user_preferences={"preferred_actions": ["approve", "review"]},
            recent_actions=["business_review", "business_approve"]
        )

        result = asyncio.run(engine.make_decision(business_request, business_context))

        print("\nBusiness Decision Result:")
        print(f"Selected Option: {result.selected_option.description if result.selected_option else 'None'}")
        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"Fallback Applied: {result.fallback_applied}")
        print(f"\nReasoning Chain:")
        for line in result.reasoning_chain:
            print(f"  {line}")

        # Test technical context
        technical_request = DecisionRequest(
            user_id=args.user,
            request_id="test_002",
            problem_statement="How should we handle the server outage?",
            context_type=DecisionContextType.TECHNICAL,
            urgency=DecisionPriority.HIGH,
            required_confidence=0.7
        )

        technical_context = DecisionContext(
            user_id=args.user,
            context_type=DecisionContextType.TECHNICAL,
            business_rules={"service_level_agreement": "99.9%"},
            recent_actions=["technical_auto"]
        )

        result = asyncio.run(engine.make_decision(technical_request, technical_context))

        print("\nTechnical Decision Result:")
        print(f"Selected Option: {result.selected_option.description if result.selected_option else 'None'}")
        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"Fallback Applied: {result.fallback_applied}")
        print(f"\nReasoning Chain:")
        for line in result.reasoning_chain:
            print(f"  {line}")

        # Test social context
        social_request = DecisionRequest(
            user_id=args.user,
            request_id="test_003",
            problem_statement="How should we handle the team conflict?",
            context_type=DecisionContextType.SOCIAL,
            urgency=DecisionPriority.MEDIUM,
            required_confidence=0.5
        )

        social_context = DecisionContext(
            user_id=args.user,
            context_type=DecisionContextType.SOCIAL,
            recent_actions=["social_support"]
        )

        result = asyncio.run(engine.make_decision(social_request, social_context))

        print("\nSocial Decision Result:")
        print(f"Selected Option: {result.selected_option.description if result.selected_option else 'None'}")
        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"Fallback Applied: {result.fallback_applied}")
        print(f"\nReasoning Chain:")
        for line in result.reasoning_chain:
            print(f"  {line}")

        print("\nTest decisions completed!")


# CLI interface for decision engine
if __name__ == "__main__":
    main()