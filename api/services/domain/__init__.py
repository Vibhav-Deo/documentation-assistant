"""
Domain Layer

Implements Domain-Driven Design (DDD) principles for the Enterprise Confluence RAG system.

Domains:
- AI: AI response generation, intent analysis, auto-tagging
- Analytics: Predictive analytics, gap detection, impact analysis, relationships
- Search: Semantic search, vector indexing, search coordination
- Sync: Data synchronization, external integrations
- Infrastructure: Database, caching, monitoring, security
- Shared: Cross-cutting concerns, authentication, utilities

Each domain has:
- Clear interfaces defining contracts
- Service implementations
- Domain-specific models
- Proper separation of concerns
"""

# Import domain registry for service management
from .registry import (
    domain_registry,
    AIServices,
    AnalyticsServices,
    SearchServices,
    SyncServices,
    InfrastructureServices,
    SharedServices
)

# Import domain modules
from . import ai
from . import analytics
from . import search
from . import sync

__all__ = [
    # Registry
    'domain_registry',
    'AIServices',
    'AnalyticsServices',
    'SearchServices',
    'SyncServices',
    'InfrastructureServices',
    'SharedServices',
    # Domains
    'ai',
    'analytics',
    'search',
    'sync'
]