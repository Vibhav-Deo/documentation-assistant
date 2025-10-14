"""
Intent Analyzer Service

Extracts the "WHY" behind decisions from multiple sources:
- Jira ticket descriptions and comments
- Pull request discussions
- Commit messages
- Design documents
- Code comments

Core USP: Answer "why did we make this decision?" questions by analyzing
context across all data sources.
"""

from typing import Dict, List, Optional
import re
from datetime import datetime


class IntentAnalyzer:
    """
    Analyzes intent and extracts decision rationale from multiple sources.

    Key capabilities:
    1. Extract decisions from tickets, PRs, commits, docs
    2. Identify alternative approaches considered
    3. Extract constraints and tradeoffs
    4. Identify risks and mitigations
    5. Link decisions to implementation
    """

    def __init__(self, db_service, ai_service):
        self.db = db_service
        self.ai = ai_service

    async def extract_decision_rationale(
        self,
        ticket: Dict,
        commits: List[Dict],
        prs: List[Dict],
        docs: List[Dict]
    ) -> Dict:
        """
        Extract decision rationale from multi-source context.

        Args:
            ticket: Jira ticket data
            commits: Related commit history
            prs: Related pull requests
            docs: Related documentation

        Returns:
            Dict with:
            - decision_summary: What was decided
            - problem_statement: What problem was being solved
            - alternatives_considered: Other approaches evaluated
            - chosen_approach: Why this specific approach
            - constraints: What limited the decision
            - risks: Identified risks and mitigations
            - stakeholders: Who was involved
        """
        # Build comprehensive context
        context = self._build_decision_context(ticket, commits, prs, docs)

        # Create analysis prompt
        prompt = self._build_decision_prompt(context, ticket)

        # Use AI to analyze and extract decisions
        analysis = self.ai.generate_response(prompt, model="gpt-oss:120b")

        # Structure the response
        return {
            "decision_id": f"decision_{ticket.get('ticket_key', 'unknown')}",
            "ticket_key": ticket.get('ticket_key'),
            "decision_summary": self._extract_summary(analysis),
            "problem_statement": self._extract_section(analysis, "Problem"),
            "alternatives_considered": self._extract_alternatives(analysis),
            "chosen_approach": self._extract_section(analysis, "Chosen Approach"),
            "constraints": self._extract_constraints(analysis),
            "risks": self._extract_risks(analysis),
            "stakeholders": self._extract_stakeholders(ticket, commits, prs),
            "implementation_commits": [c.get('sha') for c in commits],
            "related_prs": [pr.get('number') for pr in prs],
            "related_docs": [d.get('title') for d in docs],
            "created_at": datetime.now().isoformat(),
            "raw_analysis": analysis
        }

    def _build_decision_context(
        self,
        ticket: Dict,
        commits: List[Dict],
        prs: List[Dict],
        docs: List[Dict]
    ) -> str:
        """Build comprehensive context from all sources."""
        context_parts = []

        # 1. Ticket context
        context_parts.append("=== JIRA TICKET ===")
        context_parts.append(f"Key: {ticket.get('ticket_key')}")
        context_parts.append(f"Summary: {ticket.get('summary')}")
        context_parts.append(f"Description:\n{ticket.get('description', '')[:1000]}")

        # Extract comments if available in metadata
        metadata = ticket.get('metadata', {})
        if isinstance(metadata, dict) and metadata.get('comments'):
            context_parts.append("\nComments:")
            for comment in metadata['comments'][:5]:  # Top 5 comments
                author = comment.get('author', 'Unknown')
                body = comment.get('body', '')[:500]
                context_parts.append(f"- {author}: {body}")

        # 2. Commit context
        if commits:
            context_parts.append("\n=== RELATED COMMITS ===")
            for commit in commits[:10]:  # Top 10 commits
                sha = commit.get('sha', '')[:7]
                message = commit.get('message', '')[:200]
                author = commit.get('author_name', 'Unknown')
                context_parts.append(f"\n[{sha}] by {author}")
                context_parts.append(f"{message}")

        # 3. Pull request context
        if prs:
            context_parts.append("\n=== PULL REQUESTS ===")
            for pr in prs[:5]:  # Top 5 PRs
                number = pr.get('number', 'N/A')
                title = pr.get('title', '')
                description = pr.get('description', '')[:500]
                context_parts.append(f"\nPR #{number}: {title}")
                context_parts.append(f"{description}")

        # 4. Documentation context
        if docs:
            context_parts.append("\n=== RELATED DOCUMENTATION ===")
            for doc in docs[:3]:  # Top 3 docs
                title = doc.get('title', 'Untitled')
                text = doc.get('text', '')[:500]
                context_parts.append(f"\n{title}")
                context_parts.append(f"{text}...")

        return "\n".join(context_parts)

    def _build_decision_prompt(self, context: str, ticket: Dict) -> str:
        """Build AI prompt for decision extraction."""
        ticket_key = ticket.get('ticket_key', 'N/A')
        summary = ticket.get('summary', 'N/A')

        prompt = f"""You are an expert software architect analyzing project decisions.

Ticket: {ticket_key} - {summary}

Analyze the following context and extract the decision-making rationale:

{context}

Please provide a comprehensive analysis in the following format:

## Problem Statement
What problem was being solved? What was the business/technical need?

## Alternatives Considered
What other approaches were evaluated? List each alternative.

## Chosen Approach
Which approach was ultimately chosen? Describe it clearly.

## Why This Approach?
Why was this specific approach chosen over alternatives? What were the key factors?

## Constraints
What constraints influenced the decision? (budget, time, technical limitations, etc.)

## Risks & Mitigations
What risks were identified? How were they mitigated?

## Trade-offs
What trade-offs were made? What was gained vs. what was sacrificed?

If any section cannot be determined from the context, write "Not explicitly documented" for that section.

Focus on extracting the "WHY" behind decisions, not just the "WHAT" was implemented.
"""
        return prompt

    def _extract_summary(self, analysis: str) -> str:
        """Extract decision summary from analysis."""
        # Look for chosen approach section as summary
        chosen = self._extract_section(analysis, "Chosen Approach")
        if chosen and chosen != "Not explicitly documented":
            return chosen[:200]  # First 200 chars as summary
        return "Decision extracted from ticket analysis"

    def _extract_section(self, analysis: str, section_name: str) -> str:
        """Extract a specific section from analysis."""
        pattern = rf"##\s*{section_name}.*?\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, analysis, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            return content if content else "Not explicitly documented"
        return "Not explicitly documented"

    def _extract_alternatives(self, analysis: str) -> List[str]:
        """Extract list of alternatives considered."""
        section = self._extract_section(analysis, "Alternatives Considered")
        if section == "Not explicitly documented":
            return []

        # Look for bullet points or numbered lists
        alternatives = []
        for line in section.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or
                        re.match(r'^\d+\.', line)):
                # Remove bullet/number prefix
                alt = re.sub(r'^[-*]\s*|\d+\.\s*', '', line).strip()
                if alt:
                    alternatives.append(alt)

        return alternatives[:5]  # Top 5 alternatives

    def _extract_constraints(self, analysis: str) -> List[str]:
        """Extract list of constraints."""
        section = self._extract_section(analysis, "Constraints")
        if section == "Not explicitly documented":
            return []

        constraints = []
        for line in section.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or
                        re.match(r'^\d+\.', line)):
                constraint = re.sub(r'^[-*]\s*|\d+\.\s*', '', line).strip()
                if constraint:
                    constraints.append(constraint)

        return constraints[:5]

    def _extract_risks(self, analysis: str) -> List[Dict[str, str]]:
        """Extract risks and mitigations."""
        section = self._extract_section(analysis, "Risks & Mitigations")
        if section == "Not explicitly documented":
            return []

        risks = []
        # Simple extraction - could be enhanced with more sophisticated parsing
        for line in section.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*')):
                risk_text = re.sub(r'^[-*]\s*', '', line).strip()
                if risk_text:
                    risks.append({
                        "risk": risk_text,
                        "mitigation": "See analysis details"
                    })

        return risks[:5]

    def _extract_stakeholders(
        self,
        ticket: Dict,
        commits: List[Dict],
        prs: List[Dict]
    ) -> List[str]:
        """Identify stakeholders involved in the decision."""
        stakeholders = set()

        # From ticket
        if ticket.get('reporter'):
            stakeholders.add(ticket['reporter'])
        if ticket.get('assignee'):
            stakeholders.add(ticket['assignee'])

        # From commits
        for commit in commits[:20]:  # Limit to avoid too many
            if commit.get('author_name'):
                stakeholders.add(commit['author_name'])

        # From PRs
        for pr in prs[:10]:
            if pr.get('author'):
                stakeholders.add(pr['author'])

        return list(stakeholders)[:10]  # Top 10 stakeholders

    async def analyze_ticket_decisions(self, ticket_key: str, org_id: str) -> Dict:
        """
        Main entry point: Analyze decisions for a specific ticket.

        Args:
            ticket_key: Jira ticket key (e.g., "DEMO-001")
            org_id: Organization ID

        Returns:
            Decision analysis with rationale
        """
        # 1. Get ticket from database
        ticket = await self.db.get_jira_ticket_by_key(ticket_key, org_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_key} not found")

        # 2. Find related commits
        commits = await self.db.get_commits_for_ticket(ticket_key, org_id)

        # 3. Find related PRs
        prs = await self.db.get_prs_for_ticket(ticket_key, org_id)

        # 4. Find related docs (search for ticket key in documentation)
        # This would need a semantic search or full-text search
        docs = []  # Placeholder - implement doc search

        # 5. Extract decision rationale
        decision = await self.extract_decision_rationale(ticket, commits, prs, docs)

        return decision

    async def find_decision_by_question(self, question: str, org_id: str) -> Dict:
        """
        Find decision based on a natural language question.

        Example: "Why did we choose MongoDB over PostgreSQL?"
        """
        # Use semantic search to find relevant tickets/commits
        # This integrates with existing multi-source search

        # Placeholder - will integrate with qdrant_indexer
        return {
            "question": question,
            "status": "not_implemented",
            "message": "Natural language decision search coming soon"
        }
