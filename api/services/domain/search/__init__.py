"""
Search Domain

This domain handles all search-related functionality including:
- Semantic and keyword search
- Vector indexing and retrieval
- Search result ranking and filtering
- Multi-source search coordination
"""

# Import interfaces first
from .interfaces import (
    ISearchService,
    IQdrantIndexer,
    SearchResult as ISearchResult
)

# Import domain models
from .models import (
    SearchType,
    SourceType,
    SearchResult,
    SearchQuery,
    SearchResponse,
    IndexingJob,
    VectorEmbedding,
    SearchIndex,
    SearchRanking,
    SearchAnalytics,
    CollectionInfo
)

# Import all search domain services
from .search import SearchService
from .qdrant_indexer import QdrantIndexer, init_qdrant_indexer
from .qdrant_setup import QdrantSetup, init_qdrant_setup

__all__ = [
    # Interfaces
    'ISearchService',
    'IQdrantIndexer',
    'ISearchResult',
    # Models
    'SearchType',
    'SourceType',
    'SearchResult',
    'SearchQuery',
    'SearchResponse',
    'IndexingJob',
    'VectorEmbedding',
    'SearchIndex',
    'SearchRanking',
    'SearchAnalytics',
    'CollectionInfo',
    # Services
    'SearchService',
    'QdrantIndexer',
    'init_qdrant_indexer',
    'QdrantSetup',
    'init_qdrant_setup'
]