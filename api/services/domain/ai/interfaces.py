"""
AI Domain Interfaces

Defines the contracts and interfaces for AI domain services.
This establishes clear boundaries between the AI domain and other domains.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AIResponse:
    """Standard AI response format across all AI services."""
    content: str
    model_used: str
    tokens_consumed: int
    prompt_tokens: int
    completion_tokens: int
    confidence_score: float
    processing_time_ms: int
    fallback_used: bool
    context_truncated: bool
    metadata: Dict[str, Any]


@dataclass
class DecisionRecord:
    """Structured decision record from intent analysis."""
    id: str
    ticket_key: str
    decision_summary: str
    problem_statement: str
    alternatives_considered: List[Dict]
    chosen_approach: str
    constraints: List[str]
    risks: List[Dict]
    stakeholders: List[str]
    confidence_scores: Dict[str, float]
    conflicts_detected: List[Dict]
    implementation_commits: List[str]
    related_prs: List[int]
    related_docs: List[str]
    created_at: datetime
    organization_id: str


class IAIService(ABC):
    """Interface for AI response generation services."""
    
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        model: str = "mistral",
        temperature: float = 0.7
    ) -> AIResponse:
        """Generate AI response for a given prompt."""
        pass
    
    @abstractmethod
    async def generate_streaming_response(
        self,
        prompt: str,
        model: str = "mistral",
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Generate streaming AI response."""
        pass
    
    @abstractmethod
    async def generate_with_fallback(
        self,
        prompt: str,
        models: List[str] = None
    ) -> AIResponse:
        """Generate response with automatic model fallback."""
        pass


class IIntentAnalyzer(ABC):
    """Interface for intent analysis and decision extraction."""
    
    @abstractmethod
    async def extract_decision(
        self,
        ticket: Dict,
        commits: List[Dict],
        prs: List[Dict],
        docs: List[Dict]
    ) -> DecisionRecord:
        """Extract decision record from multiple sources."""
        pass
    
    @abstractmethod
    async def detect_conflicts(
        self,
        sources: List[Dict]
    ) -> List[Dict]:
        """Detect conflicts across data sources."""
        pass
    
    @abstractmethod
    async def store_decision(
        self,
        decision: DecisionRecord,
        org_id: str
    ) -> str:
        """Store decision with full-text search indexing."""
        pass


class IAutoTaggingService(ABC):
    """Interface for automatic tagging and classification."""
    
    @abstractmethod
    async def tag_ticket(
        self,
        ticket: Dict,
        org_id: str
    ) -> List[Dict]:
        """Auto-tag Jira ticket based on content."""
        pass
    
    @abstractmethod
    async def classify_commit(
        self,
        commit: Dict
    ) -> str:
        """Classify commit type (feature/bugfix/refactor/docs)."""
        pass
    
    @abstractmethod
    async def extract_document_topics(
        self,
        document: Dict
    ) -> List[Dict]:
        """Extract key topics from documentation."""
        pass
    
    @abstractmethod
    async def record_feedback(
        self,
        item_id: str,
        suggested_tags: List[str],
        accepted_tags: List[str],
        user_id: str
    ):
        """Record user feedback to improve accuracy."""
        pass