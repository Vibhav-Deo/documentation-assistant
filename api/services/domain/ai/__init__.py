"""
AI Domain

This domain handles all AI-related functionality including:
- AI response generation and streaming
- Intent analysis and decision extraction
- Prompt engineering and context management
- Multi-model support and fallback logic
"""

# Import interfaces first
from .interfaces import (
    IAIService,
    IIntentAnalyzer,
    IAutoTaggingService,
    AIResponse as IAIResponse,
    DecisionRecord as IDecisionRecord
)

# Import domain models
from .models import (
    AIModelType,
    PromptType,
    AIResponse,
    DecisionRecord,
    ConflictDetection,
    TagSuggestion,
    CommitClassification,
    DocumentTopics,
    ConversationContext,
    PromptTemplate,
    FeedbackRecord
)

# Import all AI domain services for easy access
from .ai_unified import UnifiedAIService, create_ai_service
from .intent_analyzer_unified import UnifiedIntentAnalyzer, create_intent_analyzer
from .auto_tagging import AutoTaggingService
from .conversation import SimpleConversation as ConversationService

# Aliases for backward compatibility
AIService = UnifiedAIService
IntentAnalyzer = UnifiedIntentAnalyzer

__all__ = [
    # Interfaces
    'IAIService',
    'IIntentAnalyzer',
    'IAutoTaggingService',
    'IAIResponse',
    'IDecisionRecord',
    # Models
    'AIModelType',
    'PromptType',
    'AIResponse',
    'DecisionRecord',
    'ConflictDetection',
    'TagSuggestion',
    'CommitClassification',
    'DocumentTopics',
    'ConversationContext',
    'PromptTemplate',
    'FeedbackRecord',
    # Services
    'UnifiedAIService',
    'create_ai_service',
    'UnifiedIntentAnalyzer',
    'create_intent_analyzer',
    'AutoTaggingService',
    'ConversationService',
    # Legacy
    'AIService',
    'IntentAnalyzer'
]