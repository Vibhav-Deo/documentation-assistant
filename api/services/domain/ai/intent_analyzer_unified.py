"""
Unified Intent Analyzer Service

Combines the functionality of intent_analyzer.py and intent_analyzer_enhanced.py
into a single, comprehensive service with feature flags for backward compatibility.

Features:
- Basic decision extraction (from intent_analyzer.py)
- Enhanced confidence scoring (from intent_analyzer_enhanced.py)
- Conflict detection across sources (from intent_analyzer_enhanced.py)
- Decision storage with full-text search (from intent_analyzer_enhanced.py)
- Organization-scoped operations with proper validation

This service extends OrganizationScopedService for consistent patterns.
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from services.shared.base_service import OrganizationScopedService
from services.infrastructure.database.base_repository import OrganizationScopedRepository


class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DecisionElement:
    """Represents a decision element with confidence scoring."""
    content: str
    confidence_score: float  # 0.0 to 1.0
    confidence_level: ConfidenceLevel
    sources: List[str]
    reasoning: str


@dataclass
class ConflictDetection:
    """Represents a detected conflict between sources."""
    element_type: str  # "approach", "constraint", "risk", etc.
    conflicting_sources: List[str]
    conflict_description: str
    severity: str  # "high", "medium", "low"
    resolution_suggestion: str


@dataclass
class BasicDecision:
    """Basic decision structure (original intent_analyzer.py format)."""
    decision_id: str
    ticket_key: str
    decision_summary: str
    problem_statement: str
    alternatives_considered: List[str]
    chosen_approach: str
    constraints: List[str]
    risks: List[Dict[str, str]]
    stakeholders: List[str]
    implementation_commits: List[str]
    related_prs: List[str]
    related_docs: List[str]
    created_at: str
    raw_analysis: str


@dataclass
class EnhancedDecision:
    """Enhanced decision with confidence scoring and conflict detection."""
    decision_id: str
    ticket_key: str
    decision_summary: DecisionElement
    problem_statement: DecisionElement
    alternatives_considered: List[DecisionElement]
    chosen_approach: DecisionElement
    constraints: List[DecisionElement]
    risks: List[DecisionElement]
    stakeholders: List[str]
    conflicts_detected: List[ConflictDetection]
    overall_confidence: float
    implementation_commits: List[str]
    related_prs: List[str]
    related_docs: List[str]
    created_at: str
    raw_analysis: str


class UnifiedIntentAnalyzer(OrganizationScopedService):
    """
    Unified Intent Analyzer combining basic and enhanced capabilities.
    
    Provides both simple decision extraction and advanced confidence scoring
    with conflict detection based on feature flags.
    """
    
    def __init__(self, repository: OrganizationScopedRepository, ai_service):
        super().__init__(repository)
        self.ai = ai_service
    
    # ========================================
    # MAIN ENTRY POINTS
    # ========================================
    
    async def analyze_ticket_decisions(
        self, 
        ticket_key: str, 
        org_id: str, 
        user_org_id: str,
        enhanced: bool = True
    ) -> Union[BasicDecision, EnhancedDecision]:
        """
        Main entry point: Analyze decisions for a specific ticket.
        
        Args:
            ticket_key: Jira ticket key (e.g., "DEMO-001")
            org_id: Organization ID
            user_org_id: User's organization ID for access validation
            enhanced: If True, returns EnhancedDecision with confidence scoring
            
        Returns:
            BasicDecision or EnhancedDecision based on enhanced flag
        """
        # Validate organization access
        await self.validate_organization_access(org_id, user_org_id)
        
        operation_name = f"analyze_ticket_decisions_{ticket_key}"
        
        if enhanced:
            return await self.handle_operation(
                operation_name,
                self._analyze_enhanced_decisions,
                ticket_key, org_id
            )
        else:
            return await self.handle_operation(
                operation_name,
                self._analyze_basic_decisions,
                ticket_key, org_id
            )
    
    async def _analyze_basic_decisions(self, ticket_key: str, org_id: str) -> BasicDecision:
        """Analyze decisions using basic approach (original intent_analyzer.py)."""
        # 1. Get ticket from database
        ticket = await self._get_ticket_by_key(ticket_key, org_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_key} not found")

        # 2. Find related data
        commits = await self._get_commits_for_ticket(ticket_key, org_id)
        prs = await self._get_prs_for_ticket(ticket_key, org_id)
        docs = []  # Placeholder for document search

        # 3. Extract decision rationale
        return await self._extract_basic_decision_rationale(ticket, commits, prs, docs)
    
    async def _analyze_enhanced_decisions(self, ticket_key: str, org_id: str) -> EnhancedDecision:
        """Analyze decisions using enhanced approach with confidence scoring."""
        # 1. Get ticket from database
        ticket = await self._get_ticket_by_key(ticket_key, org_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_key} not found")

        # 2. Find related data
        commits = await self._get_commits_for_ticket(ticket_key, org_id)
        prs = await self._get_prs_for_ticket(ticket_key, org_id)
        docs = []  # Placeholder for document search

        # 3. Extract enhanced decision rationale
        return await self._extract_enhanced_decision_rationale(ticket, commits, prs, docs, org_id)
    
    # ========================================
    # BASIC DECISION EXTRACTION (from intent_analyzer.py)
    # ========================================
    
    async def _extract_basic_decision_rationale(
        self,
        ticket: Dict,
        commits: List[Dict],
        prs: List[Dict],
        docs: List[Dict]
    ) -> BasicDecision:
        """
        Extract decision rationale from multi-source context (basic approach).
        """
        # Build comprehensive context
        context = self._build_decision_context(ticket, commits, prs, docs)

        # Create analysis prompt
        prompt = self._build_basic_decision_prompt(context, ticket)

        # Use AI to analyze and extract decisions
        analysis = await self.ai.generate_response(prompt, model="mistral")

        # Structure the response
        return BasicDecision(
            decision_id=f"decision_{ticket.get('ticket_key', 'unknown')}",
            ticket_key=ticket.get('ticket_key'),
            decision_summary=self._extract_summary(analysis),
            problem_statement=self._extract_section(analysis, "Problem Statement"),
            alternatives_considered=self._extract_alternatives_basic(analysis),
            chosen_approach=self._extract_section(analysis, "Chosen Approach"),
            constraints=self._extract_constraints_basic(analysis),
            risks=self._extract_risks_basic(analysis),
            stakeholders=self._extract_stakeholders(ticket, commits, prs),
            implementation_commits=[c.get('sha') for c in commits],
            related_prs=[pr.get('number') for pr in prs],
            related_docs=[d.get('title') for d in docs],
            created_at=datetime.now().isoformat(),
            raw_analysis=analysis
        )
    
    def _build_basic_decision_prompt(self, context: str, ticket: Dict) -> str:
        """Build AI prompt for basic decision extraction."""
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
    
    # ========================================
    # ENHANCED DECISION EXTRACTION (from intent_analyzer_enhanced.py)
    # ========================================
    
    async def _extract_enhanced_decision_rationale(
        self,
        ticket: Dict,
        commits: List[Dict],
        prs: List[Dict],
        docs: List[Dict],
        org_id: str
    ) -> EnhancedDecision:
        """
        Extract decision rationale with confidence scoring and conflict detection.
        """
        # Build comprehensive context
        context = self._build_decision_context(ticket, commits, prs, docs)

        # Create enhanced analysis prompt
        prompt = self._build_enhanced_decision_prompt(context, ticket)

        # Use AI to analyze and extract decisions
        analysis = await self.ai.generate_response(prompt, model="mistral")

        # Extract elements with confidence scoring
        decision_summary = self._extract_element_with_confidence(
            analysis, "Decision Summary", ["ticket", "analysis"]
        )
        
        problem_statement = self._extract_element_with_confidence(
            analysis, "Problem Statement", ["ticket", "commits", "prs"]
        )
        
        chosen_approach = self._extract_element_with_confidence(
            analysis, "Chosen Approach", ["commits", "prs", "docs"]
        )

        # Extract lists with confidence
        alternatives = self._extract_alternatives_with_confidence(analysis)
        constraints = self._extract_constraints_with_confidence(analysis)
        risks = self._extract_risks_with_confidence(analysis)

        # Detect conflicts
        conflicts = self._detect_conflicts(
            context, alternatives, constraints, risks, chosen_approach
        )

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence([
            decision_summary, problem_statement, chosen_approach
        ] + alternatives + constraints + risks)

        # Store decision in database
        decision_id = f"enhanced_decision_{ticket.get('ticket_key', 'unknown')}_{int(datetime.now().timestamp())}"
        
        enhanced_decision = EnhancedDecision(
            decision_id=decision_id,
            ticket_key=ticket.get('ticket_key'),
            decision_summary=decision_summary,
            problem_statement=problem_statement,
            alternatives_considered=alternatives,
            chosen_approach=chosen_approach,
            constraints=constraints,
            risks=risks,
            stakeholders=self._extract_stakeholders(ticket, commits, prs),
            conflicts_detected=conflicts,
            overall_confidence=overall_confidence,
            implementation_commits=[c.get('sha') for c in commits],
            related_prs=[pr.get('number') for pr in prs],
            related_docs=[d.get('title') for d in docs],
            created_at=datetime.now().isoformat(),
            raw_analysis=analysis
        )

        # Store in database
        await self._store_enhanced_decision(enhanced_decision, org_id)

        return enhanced_decision
    
    def _build_enhanced_decision_prompt(self, context: str, ticket: Dict) -> str:
        """Build enhanced AI prompt for decision extraction with confidence indicators."""
        ticket_key = ticket.get('ticket_key', 'N/A')
        summary = ticket.get('summary', 'N/A')

        prompt = f"""You are an expert software architect analyzing project decisions with confidence assessment.

Ticket: {ticket_key} - {summary}

Analyze the following context and extract decision-making rationale with confidence indicators:

{context}

For each section, provide:
1. The extracted information
2. Confidence level (HIGH/MEDIUM/LOW) based on:
   - HIGH: Explicitly stated with clear evidence
   - MEDIUM: Reasonably inferred from context
   - LOW: Speculative or minimal evidence
3. Source evidence (which parts of context support this)

Format your response as follows:

## Decision Summary
[CONFIDENCE: HIGH/MEDIUM/LOW]
[SOURCES: ticket/commits/prs/docs]
Brief summary of what was decided.
[REASONING: Why this confidence level]

## Problem Statement
[CONFIDENCE: HIGH/MEDIUM/LOW]
[SOURCES: ticket/commits/prs/docs]
What problem was being solved? What was the business/technical need?
[REASONING: Why this confidence level]

## Alternatives Considered
[CONFIDENCE: HIGH/MEDIUM/LOW]
[SOURCES: ticket/commits/prs/docs]
- Alternative 1: Description
- Alternative 2: Description
[REASONING: Why this confidence level]

## Chosen Approach
[CONFIDENCE: HIGH/MEDIUM/LOW]
[SOURCES: ticket/commits/prs/docs]
Which approach was ultimately chosen? Describe it clearly.
[REASONING: Why this confidence level]

## Constraints
[CONFIDENCE: HIGH/MEDIUM/LOW]
[SOURCES: ticket/commits/prs/docs]
- Constraint 1: Description
- Constraint 2: Description
[REASONING: Why this confidence level]

## Risks & Mitigations
[CONFIDENCE: HIGH/MEDIUM/LOW]
[SOURCES: ticket/commits/prs/docs]
- Risk 1: Description and mitigation
- Risk 2: Description and mitigation
[REASONING: Why this confidence level]

## Conflicts Detected
Identify any contradictions or inconsistencies between sources:
- Conflict 1: Description of contradiction
- Conflict 2: Description of contradiction

If any section cannot be determined, write "Not explicitly documented" and set confidence to LOW.
"""
        return prompt
    
    # ========================================
    # SHARED UTILITY METHODS
    # ========================================
    
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

    def _extract_alternatives_basic(self, analysis: str) -> List[str]:
        """Extract list of alternatives considered (basic format)."""
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

    def _extract_constraints_basic(self, analysis: str) -> List[str]:
        """Extract list of constraints (basic format)."""
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

    def _extract_risks_basic(self, analysis: str) -> List[Dict[str, str]]:
        """Extract risks and mitigations (basic format)."""
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
    
    # ========================================
    # ENHANCED CONFIDENCE SCORING METHODS
    # ========================================
    
    def _extract_element_with_confidence(
        self, 
        analysis: str, 
        section_name: str, 
        expected_sources: List[str]
    ) -> DecisionElement:
        """Extract a decision element with confidence scoring."""
        
        # Extract section content
        section_content = self._extract_section(analysis, section_name)
        
        if section_content == "Not explicitly documented":
            return DecisionElement(
                content="Not explicitly documented",
                confidence_score=0.1,
                confidence_level=ConfidenceLevel.LOW,
                sources=[],
                reasoning="No evidence found in available sources"
            )

        # Extract confidence level
        confidence_match = re.search(r'\[CONFIDENCE:\s*(HIGH|MEDIUM|LOW)\]', section_content, re.IGNORECASE)
        confidence_str = confidence_match.group(1).upper() if confidence_match else "LOW"
        
        # Extract sources
        sources_match = re.search(r'\[SOURCES:\s*([^\]]+)\]', section_content, re.IGNORECASE)
        sources = []
        if sources_match:
            sources = [s.strip() for s in sources_match.group(1).split('/')]

        # Extract reasoning
        reasoning_match = re.search(r'\[REASONING:\s*([^\]]+)\]', section_content, re.IGNORECASE)
        reasoning = reasoning_match.group(1) if reasoning_match else "No reasoning provided"

        # Clean content (remove metadata tags)
        clean_content = re.sub(r'\[CONFIDENCE:.*?\]', '', section_content)
        clean_content = re.sub(r'\[SOURCES:.*?\]', '', clean_content)
        clean_content = re.sub(r'\[REASONING:.*?\]', '', clean_content)
        clean_content = clean_content.strip()

        # Map confidence level to score
        confidence_mapping = {
            "HIGH": (0.8, ConfidenceLevel.HIGH),
            "MEDIUM": (0.6, ConfidenceLevel.MEDIUM),
            "LOW": (0.3, ConfidenceLevel.LOW)
        }
        
        confidence_score, confidence_level = confidence_mapping.get(
            confidence_str, (0.3, ConfidenceLevel.LOW)
        )

        return DecisionElement(
            content=clean_content,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            sources=sources,
            reasoning=reasoning
        )

    def _extract_alternatives_with_confidence(self, analysis: str) -> List[DecisionElement]:
        """Extract alternatives with confidence scoring."""
        base_element = self._extract_element_with_confidence(
            analysis, "Alternatives Considered", ["ticket", "prs", "docs"]
        )
        
        if base_element.content == "Not explicitly documented":
            return [base_element]

        # Parse individual alternatives
        alternatives = []
        for line in base_element.content.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or re.match(r'^\d+\.', line)):
                alt_text = re.sub(r'^[-*]\s*|\d+\.\s*', '', line).strip()
                if alt_text:
                    alternatives.append(DecisionElement(
                        content=alt_text,
                        confidence_score=base_element.confidence_score,
                        confidence_level=base_element.confidence_level,
                        sources=base_element.sources,
                        reasoning=base_element.reasoning
                    ))

        return alternatives[:5] if alternatives else [base_element]

    def _extract_constraints_with_confidence(self, analysis: str) -> List[DecisionElement]:
        """Extract constraints with confidence scoring."""
        base_element = self._extract_element_with_confidence(
            analysis, "Constraints", ["ticket", "commits", "prs"]
        )
        
        if base_element.content == "Not explicitly documented":
            return [base_element]

        # Parse individual constraints
        constraints = []
        for line in base_element.content.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or re.match(r'^\d+\.', line)):
                constraint_text = re.sub(r'^[-*]\s*|\d+\.\s*', '', line).strip()
                if constraint_text:
                    constraints.append(DecisionElement(
                        content=constraint_text,
                        confidence_score=base_element.confidence_score,
                        confidence_level=base_element.confidence_level,
                        sources=base_element.sources,
                        reasoning=base_element.reasoning
                    ))

        return constraints[:5] if constraints else [base_element]

    def _extract_risks_with_confidence(self, analysis: str) -> List[DecisionElement]:
        """Extract risks with confidence scoring."""
        base_element = self._extract_element_with_confidence(
            analysis, "Risks & Mitigations", ["ticket", "prs", "docs"]
        )
        
        if base_element.content == "Not explicitly documented":
            return [base_element]

        # Parse individual risks
        risks = []
        for line in base_element.content.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or re.match(r'^\d+\.', line)):
                risk_text = re.sub(r'^[-*]\s*|\d+\.\s*', '', line).strip()
                if risk_text:
                    risks.append(DecisionElement(
                        content=risk_text,
                        confidence_score=base_element.confidence_score,
                        confidence_level=base_element.confidence_level,
                        sources=base_element.sources,
                        reasoning=base_element.reasoning
                    ))

        return risks[:5] if risks else [base_element]

    def _detect_conflicts(
        self,
        context: str,
        alternatives: List[DecisionElement],
        constraints: List[DecisionElement],
        risks: List[DecisionElement],
        chosen_approach: DecisionElement
    ) -> List[ConflictDetection]:
        """Detect conflicts between different sources."""
        conflicts = []

        # Look for explicit conflicts in the analysis
        conflicts_section = self._extract_section(context, "Conflicts Detected")
        
        if conflicts_section != "Not explicitly documented":
            for line in conflicts_section.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('*')):
                    conflict_text = re.sub(r'^[-*]\s*', '', line).strip()
                    if conflict_text:
                        conflicts.append(ConflictDetection(
                            element_type="general",
                            conflicting_sources=["multiple"],
                            conflict_description=conflict_text,
                            severity="medium",
                            resolution_suggestion="Review source materials for clarification"
                        ))

        # Detect confidence conflicts (same element with different confidence from different sources)
        all_elements = alternatives + constraints + risks + [chosen_approach]
        low_confidence_elements = [e for e in all_elements if e.confidence_level == ConfidenceLevel.LOW]
        
        if len(low_confidence_elements) > len(all_elements) * 0.5:  # More than 50% low confidence
            conflicts.append(ConflictDetection(
                element_type="confidence",
                conflicting_sources=["analysis"],
                conflict_description="Multiple elements have low confidence, indicating insufficient documentation",
                severity="high",
                resolution_suggestion="Gather additional documentation or stakeholder input"
            ))

        return conflicts

    def _calculate_overall_confidence(self, elements: List[DecisionElement]) -> float:
        """Calculate overall confidence score for the decision."""
        if not elements:
            return 0.1

        # Weight different elements differently
        weights = {
            "decision_summary": 0.3,
            "problem_statement": 0.2,
            "chosen_approach": 0.3,
            "alternatives": 0.1,
            "constraints": 0.05,
            "risks": 0.05
        }

        total_score = 0.0
        total_weight = 0.0

        for i, element in enumerate(elements):
            # Assign weights based on position (rough heuristic)
            if i == 0:  # decision_summary
                weight = weights["decision_summary"]
            elif i == 1:  # problem_statement
                weight = weights["problem_statement"]
            elif i == 2:  # chosen_approach
                weight = weights["chosen_approach"]
            else:  # others
                weight = weights["alternatives"] / max(1, len(elements) - 3)

            total_score += element.confidence_score * weight
            total_weight += weight

        return min(1.0, total_score / total_weight if total_weight > 0 else 0.1)
    
    # ========================================
    # DATABASE OPERATIONS
    # ========================================
    
    async def _get_ticket_by_key(self, ticket_key: str, org_id: str) -> Optional[Dict]:
        """Get ticket from database by key."""
        tickets = await self.org_repository.select_by_org(
            "jira_tickets",
            org_id,
            "*",
            "ticket_key = $2",
            "",
            None,
            None,
            ticket_key
        )
        return tickets[0] if tickets else None
    
    async def _get_commits_for_ticket(self, ticket_key: str, org_id: str) -> List[Dict]:
        """Get commits related to a ticket."""
        # This would need to be implemented based on your database schema
        # For now, return empty list as placeholder
        return []
    
    async def _get_prs_for_ticket(self, ticket_key: str, org_id: str) -> List[Dict]:
        """Get pull requests related to a ticket."""
        # This would need to be implemented based on your database schema
        # For now, return empty list as placeholder
        return []
    
    async def _store_enhanced_decision(self, decision: EnhancedDecision, org_id: str) -> None:
        """Store enhanced decision in database with full-text search support."""
        
        # Convert to dictionary with JSON strings for nested objects
        decision_data = {
            "decision_id": decision.decision_id,
            "ticket_key": decision.ticket_key,
            "decision_summary": json.dumps({
                "content": decision.decision_summary.content,
                "confidence_score": decision.decision_summary.confidence_score,
                "confidence_level": decision.decision_summary.confidence_level.value,
                "sources": decision.decision_summary.sources,
                "reasoning": decision.decision_summary.reasoning
            }),
            "problem_statement": json.dumps({
                "content": decision.problem_statement.content,
                "confidence_score": decision.problem_statement.confidence_score,
                "confidence_level": decision.problem_statement.confidence_level.value,
                "sources": decision.problem_statement.sources,
                "reasoning": decision.problem_statement.reasoning
            }),
            "chosen_approach": json.dumps({
                "content": decision.chosen_approach.content,
                "confidence_score": decision.chosen_approach.confidence_score,
                "confidence_level": decision.chosen_approach.confidence_level.value,
                "sources": decision.chosen_approach.sources,
                "reasoning": decision.chosen_approach.reasoning
            }),
            "alternatives_considered": json.dumps([
                {
                    "content": alt.content,
                    "confidence_score": alt.confidence_score,
                    "confidence_level": alt.confidence_level.value,
                    "sources": alt.sources,
                    "reasoning": alt.reasoning
                } for alt in decision.alternatives_considered
            ]),
            "constraints": json.dumps([
                {
                    "content": constraint.content,
                    "confidence_score": constraint.confidence_score,
                    "confidence_level": constraint.confidence_level.value,
                    "sources": constraint.sources,
                    "reasoning": constraint.reasoning
                } for constraint in decision.constraints
            ]),
            "risks": json.dumps([
                {
                    "content": risk.content,
                    "confidence_score": risk.confidence_score,
                    "confidence_level": risk.confidence_level.value,
                    "sources": risk.sources,
                    "reasoning": risk.reasoning
                } for risk in decision.risks
            ]),
            "conflicts_detected": json.dumps([
                {
                    "element_type": conflict.element_type,
                    "conflicting_sources": conflict.conflicting_sources,
                    "conflict_description": conflict.conflict_description,
                    "severity": conflict.severity,
                    "resolution_suggestion": conflict.resolution_suggestion
                } for conflict in decision.conflicts_detected
            ]),
            "stakeholders": decision.stakeholders,
            "overall_confidence": decision.overall_confidence,
            "implementation_commits": decision.implementation_commits,
            "related_prs": decision.related_prs,
            "related_docs": decision.related_docs,
            "created_at": datetime.now(),
            "raw_analysis": decision.raw_analysis
        }

        # Store in enhanced_decisions table (would need to create this table)
        await self.org_repository.insert_with_org(
            table="enhanced_decisions",
            data=decision_data,
            org_id=org_id
        )
    
    # ========================================
    # SEARCH AND RETRIEVAL METHODS
    # ========================================
    
    async def search_decisions(
        self, 
        query: str, 
        org_id: str, 
        user_org_id: str,
        confidence_threshold: float = 0.5
    ) -> List[Dict]:
        """
        Search decisions using full-text search with confidence filtering.
        """
        await self.validate_organization_access(org_id, user_org_id)
        
        # This would need to be implemented with proper full-text search
        # For now, return empty list as placeholder
        return []

    async def get_decision_conflicts(self, org_id: str, user_org_id: str) -> List[Dict]:
        """Get all decisions with detected conflicts."""
        await self.validate_organization_access(org_id, user_org_id)
        
        # This would need to be implemented based on database schema
        # For now, return empty list as placeholder
        return []
    
    async def find_decision_by_question(self, question: str, org_id: str, user_org_id: str) -> Dict:
        """
        Find decision based on a natural language question.

        Example: "Why did we choose MongoDB over PostgreSQL?"
        """
        await self.validate_organization_access(org_id, user_org_id)
        
        # Use semantic search to find relevant tickets/commits
        # This integrates with existing multi-source search

        # Placeholder - will integrate with qdrant_indexer
        return {
            "question": question,
            "status": "not_implemented",
            "message": "Natural language decision search coming soon"
        }
    
    # ========================================
    # BACKWARD COMPATIBILITY METHODS
    # ========================================
    
    async def extract_decision_rationale(
        self,
        ticket: Dict,
        commits: List[Dict],
        prs: List[Dict],
        docs: List[Dict]
    ) -> Dict:
        """
        Backward compatibility method for basic decision extraction.
        
        Returns basic decision in dictionary format for compatibility
        with existing code that uses intent_analyzer.py
        """
        basic_decision = await self._extract_basic_decision_rationale(ticket, commits, prs, docs)
        
        # Convert to dictionary format
        return {
            "decision_id": basic_decision.decision_id,
            "ticket_key": basic_decision.ticket_key,
            "decision_summary": basic_decision.decision_summary,
            "problem_statement": basic_decision.problem_statement,
            "alternatives_considered": basic_decision.alternatives_considered,
            "chosen_approach": basic_decision.chosen_approach,
            "constraints": basic_decision.constraints,
            "risks": basic_decision.risks,
            "stakeholders": basic_decision.stakeholders,
            "implementation_commits": basic_decision.implementation_commits,
            "related_prs": basic_decision.related_prs,
            "related_docs": basic_decision.related_docs,
            "created_at": basic_decision.created_at,
            "raw_analysis": basic_decision.raw_analysis
        }


# ========================================
# FACTORY FUNCTIONS FOR EASY MIGRATION
# ========================================

def create_intent_analyzer(repository: OrganizationScopedRepository, ai_service, enhanced: bool = True) -> UnifiedIntentAnalyzer:
    """
    Factory function to create intent analyzer instance.
    
    Args:
        repository: Database repository instance
        ai_service: AI service instance
        enhanced: Whether to enable enhanced features by default
        
    Returns:
        UnifiedIntentAnalyzer instance
    """
    analyzer = UnifiedIntentAnalyzer(repository, ai_service)
    analyzer._enhanced_by_default = enhanced
    return analyzer