"""
AI Domain Models

Data models specific to the AI domain including:
- AI responses and metadata
- Decision records and analysis
- Auto-tagging results
- Conversation context
"""

from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum


class AIModelType(str, Enum):
    """Supported AI model types."""
    MISTRAL = "mistral"
    LLAMA2 = "llama2"
    CODELLAMA = "codellama"
    GPT4 = "gpt-4"


class PromptType(str, Enum):
    """Types of prompts for different use cases."""
    SIMPLE = "simple"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    ROLE_BASED = "role_based"


class AIResponse(BaseModel):
    """Structured AI response with metadata."""
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


class DecisionRecord(BaseModel):
    """Structured decision record from intent analysis."""
    id: Optional[str] = None
    ticket_key: str
    decision_summary: str
    problem_statement: str
    alternatives_considered: List[Dict[str, Any]]
    chosen_approach: str
    constraints: List[str]
    risks: List[Dict[str, Any]]
    stakeholders: List[str]
    confidence_scores: Dict[str, float]
    conflicts_detected: List[Dict[str, Any]]
    implementation_commits: List[str]
    related_prs: List[int]
    related_docs: List[str]
    created_at: Optional[datetime] = None
    organization_id: str


class ConflictDetection(BaseModel):
    """Detected conflict between data sources."""
    conflict_type: str
    source_a: Dict[str, Any]
    source_b: Dict[str, Any]
    confidence: float
    description: str


class TagSuggestion(BaseModel):
    """Auto-tagging suggestion with confidence."""
    tag: str
    category: str
    confidence: float
    source: str
    reasoning: Optional[str] = None


class CommitClassification(BaseModel):
    """Classification result for a commit."""
    commit_hash: str
    classification: str  # feature, bugfix, refactor, documentation, test, chore
    confidence: float
    keywords_matched: List[str]
    patterns_matched: List[str]


class DocumentTopics(BaseModel):
    """Extracted topics from a document."""
    document_id: str
    topics: List[Dict[str, Any]]
    categories: List[str]
    keywords: List[str]
    confidence_scores: Dict[str, float]


class ConversationContext(BaseModel):
    """Context for maintaining conversation state."""
    session_id: str
    user_id: str
    organization_id: str
    messages: List[Dict[str, Any]]
    context_summary: Optional[str] = None
    last_updated: datetime
    metadata: Dict[str, Any] = {}


class PromptTemplate(BaseModel):
    """Template for generating prompts."""
    name: str
    template_type: PromptType
    template: str
    variables: List[str]
    examples: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = {}


class FeedbackRecord(BaseModel):
    """User feedback for improving AI services."""
    feedback_id: Optional[str] = None
    service_type: str  # "auto_tagging", "decision_extraction", etc.
    item_id: str
    user_id: str
    organization_id: str
    suggested_result: Dict[str, Any]
    actual_result: Dict[str, Any]
    feedback_type: str  # "correction", "approval", "rejection"
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}