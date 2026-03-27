import os
import time
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

# Try to import anthropic for Claude API integration
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

class ClaudeReasoningLoop:
    def __init__(self, vault_path: str, use_claude_api: bool = True):
        """
        Initialize the Claude Reasoning Loop.

        Args:
            vault_path: Path to the obsidian vault
            use_claude_api: If True and ANTHROPIC_API_KEY is set, uses real Claude API.
                           If False or no API key, uses template-based fallback.
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.plans = self.vault_path / 'Plans'
        self.done = self.vault_path / 'Done'
        self.company_handbook = self.vault_path / 'Company_Handbook.md'
        self.use_claude_api = use_claude_api and ANTHROPIC_AVAILABLE and os.getenv('ANTHROPIC_API_KEY')

        # Initialize Claude client if available
        self.claude_client = None
        if self.use_claude_api:
            try:
                self.claude_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
                self.logger = logging.getLogger('ClaudeReasoningLoop')
                self.logger.info("Claude API integration enabled")
            except Exception as e:
                self.logger.error(f"Failed to initialize Claude client: {e}")
                self.use_claude_api = False

        # Create directories if they don't exist
        self.needs_action.mkdir(exist_ok=True)
        self.plans.mkdir(exist_ok=True)
        self.done.mkdir(exist_ok=True)

    def _get_company_handbook(self) -> str:
        """Read the company handbook for context"""
        if self.company_handbook.exists():
            return self.company_handbook.read_text()
        return "No company handbook available. Follow general business best practices."

    def _call_claude_api(self, action_content: str, action_type: str) -> str:
        """Call Claude API to generate a personalized plan"""
        if not self.claude_client:
            return None

        try:
            handbook = self._get_company_handbook()

            prompt = f"""You are an AI business assistant processing a new task.

# Company Handbook Context:
{handbook[:2000]}  # Limit context length

# New Task Input:
{action_content}

# Task Type: {action_type}

Based on the company handbook and the task above, create a detailed action plan.
Include:
1. Analysis of the situation
2. Specific actionable steps with checkboxes
3. Priority level (High/Medium/Low)
4. Deadline recommendation
5. Any approval requirements
6. Reference to handbook rules if applicable

Format as a markdown plan file with frontmatter:
---
created: <timestamp>
type: {action_type}
status: pending_review
---

Then the plan content with clear checklist steps.

Return ONLY the markdown plan, no additional commentary."""

            response = self.claude_client.messages.create(
                model="claude-4-opus-20250514",
                max_tokens=2000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.content[0].text

        except Exception as e:
            self.logger.error(f"Claude API call failed: {e}")
            return None

    def process_needs_action(self) -> List[str]:
        """Process all files in Needs_Action and create Plan.md files"""
        created_plans = []
        use_claude = self.use_claude_api

        for action_file in self.needs_action.glob('*.md'):
            try:
                self.logger.info(f"Processing: {action_file.name}")

                # Generate plan using Claude API if available, otherwise template
                if use_claude:
                    plan = self._generate_plan_with_claude(action_file)
                else:
                    plan = self._create_plan_from_action(action_file)

                if plan:
                    plan_path = self.plans / f'PLAN_{action_file.stem}.md'
                    plan_path.write_text(plan)
                    created_plans.append(str(plan_path))

                    # Move original to done
                    action_file.rename(self.done / action_file.name)
                    self.logger.info(f"Created plan: {plan_path.name}")

            except Exception as e:
                self.logger.error(f"Error processing {action_file}: {e}")

        return created_plans

    def _generate_plan_with_claude(self, action_file: Path) -> str:
        """Generate a plan using Claude API"""
        content = action_file.read_text()

        # Extract type from frontmatter
        action_type = 'generic'
        if content.startswith('---'):
            try:
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    for line in frontmatter.split('\n'):
                        if line.startswith('type:'):
                            action_type = line.split(':', 1)[1].strip()
                            break
            except:
                pass

        # Call Claude
        plan = self._call_claude_api(content, action_type)

        if plan:
            return plan
        else:
            # Fallback to template-based plan
            self.logger.warning(f"Claude API unavailable for {action_file.name}, using template fallback")
            return self._create_plan_from_action(action_file)

    def _extract_field(self, content: str, field: str) -> str:
        """Extract field from markdown frontmatter or content"""
        # Check frontmatter first (between --- markers)
        if content.startswith('---'):
            try:
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    for line in frontmatter.split('\n'):
                        if line.strip().startswith(f'{field}:'):
                            return line.split(':', 1)[1].strip()
            except:
                pass

        # Fallback: search entire content
        for line in content.split('\n'):
            if line.strip().startswith(f'{field}:'):
                return line.split(':', 1)[1].strip()
        return ''

    def _create_email_plan(self, content: str) -> str:
        """Create plan for email action (template fallback)"""
        subject = self._extract_field(content, 'subject')
        sender = self._extract_field(content, 'from')

        # Try to extract email body snippet
        email_snippet = ""
        if "## Email Content" in content or "### Email Content" in content:
            parts = content.split("## Email Content", 1)
            if len(parts) > 1:
                email_snippet = parts[1].split("##", 1)[0].strip()[:500]

        return f"""---
created: {time.strftime('%Y-%m-%d %H:%M:%S')}
type: email_response
status: pending_review
requires_approval: true
---

# Email Response Plan

## Original Message
**From:** {sender}
**Subject:** {subject}

## Content Preview
{email_snippet if email_snippet else '(see original email in Done folder)'}

## Analysis
Business email requiring professional response. Check Company Handbook for tone guidelines.

## Action Steps
- [ ] Read full email content in Done folder
- [ ] Check if this is a new contact (requires approval)
- [ ] Draft response referencing relevant business services
- [ ] Review against Company Handbook rules
- [ ] Submit for approval if new recipient or sensitive content
- [ ] Send response via email MCP once approved

## Priority
High - Business communication

## Deadline
Within 24 hours (check handbook for response time SLAs)

## Approval Requirements
- New email recipients: **YES** (approval required)
- Amounts > $100: **YES**
- Sensitive topics: **YES**

## Notes from Handbook
- Always be professional and helpful
- Include your standard signature
- Response time: < 24 hours for business inquiries
"""

    def _create_whatsapp_plan(self, content: str) -> str:
        """Create plan for WhatsApp message (template fallback)"""
        message = self._extract_field(content, 'message') or self._extract_field(content, 'text') or '(no message content)'
        sender = self._extract_field(content, 'from') or 'Unknown'

        return f"""---
created: {time.strftime('%Y-%m-%d %H:%M:%S')}
type: whatsapp_response
status: pending_review
requires_approval: false
---

# WhatsApp Response Plan

## Message Details
**From:** {sender}
**Message:** {message[:200]}...

## Analysis
Customer inquiry via WhatsApp requiring prompt response.

## Action Steps
- [ ] Check Company Handbook for communication guidelines
- [ ] Determine if this is sales inquiry or support request
- [ ] Draft concise, helpful response
- [ ] Avoid sharing sensitive information
- [ ] Send via WhatsApp Web within 2 hours
- [ ] Log interaction if business-related

## Priority
High if contains keywords: invoice, payment, urgent, asap
Medium otherwise

## Deadline
{self._get_urgency_deadline(message)}

## Notes
- Keep responses under 3 messages
- Move to /Done after response sent
- For sales: direct to email for detailed proposals
"""

    def _get_urgency_deadline(self, message: str) -> str:
        """Determine deadline based on message urgency keywords"""
        urgent_words = ['urgent', 'asap', 'emergency', 'help', 'now']
        if any(word in message.lower() for word in urgent_words):
            return "Within 1 hour (URGENT)"
        return "Within 2 hours (standard)"

    def _create_linkedin_plan(self, content: str) -> str:
        """Create plan for LinkedIn opportunity (template fallback)"""
        opportunity = self._extract_field(content, 'opportunity') or '(trending topic)'
        score = self._extract_field(content, 'trend_score') or 'N/A'

        return f"""---
created: {time.strftime('%Y-%m-%d %H:%M:%S')}
type: linkedin_post
status: pending_review
requires_approval: true
---

# LinkedIn Content Plan

## Opportunity
**Topic:** {opportunity}
**Relevance Score:** {score}

## Business Angle
How does this trend relate to our AI Employee services?

## Content Strategy
1. Hook: Start with an insight about the trend
2. Value: Explain how businesses can leverage this
3. CTA: Invite discussion or offer consultation

## Draft Post Template
> "{opportunity}" is trending. This presents an opportunity for SMBs to...

## Hashtags to Include
#AIAutomation #BusinessTips #DigitalTransformation

## Action Steps
- [ ] Research topic thoroughly (use Company Handbook for positioning)
- [ ] Write draft post (3-5 paragraphs)
- [ ] Add 3-5 relevant hashtags
- [ ] Get approval (business content requires approval)
- [ ] Post at optimal time (9 AM or 12 PM local time)
- [ ] Monitor engagement for 24 hours

## Requirement
LinkedIn posting requires HUMAN APPROVAL via /Pending_Approval folder.

## Notes
- Real LinkedIn API posting not implemented (see README)
- Manually copy draft to LinkedIn or implement LinkedIn MCP server
"""

    def _create_generic_plan(self, content: str) -> str:
        """Create generic plan for unknown action types"""
        # Extract some context from content
        first_lines = '\n'.join(content.split('\n')[:5])

        return f"""---
created: {time.strftime('%Y-%m-%d %H:%M:%S')}
type: generic_task
status: pending_review
requires_approval: true
---

# Generic Task Plan

## Task Input
```markdown
{first_lines}
```

## Analysis
This task type is not automatically recognized. Manual review required.

## Recommended Steps
1. [ ] Review full task content in Done folder
2. [ ] Categorize task (email, social, finance, etc.)
3. [ ] Check Company Handbook for relevant guidelines
4. [ ] Create appropriate workflow template
5. [ ] Get approval before proceeding
6. [ ] Execute and log completion

## Priority
Review required to determine priority

## Deadline
To be determined after categorization

## Notes
- Unknown task types trigger manual review
- Consider adding handler to claude_reasoning_loop.py
- Update _create_plan_from_action() method

## Action for Human/AI
Review this task type and determine appropriate response strategy.
"""

# Example usage:
# reasoning_loop = ClaudeReasoningLoop('/path/to/vault')
# plans_created = reasoning_loop.process_needs_action()
# print(f'Created {len(plans_created)} plans')