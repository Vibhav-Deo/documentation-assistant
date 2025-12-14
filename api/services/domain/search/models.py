"""
Search Domain Models

Data models specific to the search domain including:
- Search results and rankings
- Indexing metadata
- Search configurations
"""

from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class SearchType(str, Enum):
    """Types of search operations."""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    ENHANCED = "enhanced"


class SourceType(str, Enum):
    """Types of data sources for search."""
    JIRA_TICKET = "jira_ticket"
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    CODE_FILE = "code_file"
    CONFLUENCE_DOC = "confluence_doc"
    DECISION_RECORD = "decision_record"


class SearchResult(BaseModel):
    """Standard search result format."""
    id: str
    score: float
    content: str
    title: str
    source_type: SourceType
    metadata: Dict[str, Any]
    highlights: Optional[List[str]] = None
    url: Optional[str] = None


class SearchQuery(BaseModel):
    """Search query with parameters."""
    question: str
    search_type: SearchType = SearchType.SEMANTIC
    max_results: int = 5
    filters: Optional[Dict[str, Any]] = None
    organization_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class SearchResponse(BaseModel):
    """Complete search response."""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: int
    search_type: SearchType
    metadata: Dict[str, Any] = {}


class IndexingJob(BaseModel):
    """Indexing job status and metadata."""
    job_id: str
    organization_id: str
    source_type: SourceType
    status: str  # "pending", "running", "completed", "failed"
    items_total: int
    items_processed: int
    items_failed: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}


class VectorEmbedding(BaseModel):
    """Vector embedding for a document."""
    document_id: str
    embedding: List[float]
    model_used: str
    created_at: datetime
    metadata: Dict[str, Any] = {}


class SearchIndex(BaseModel):
    """Search index configuration."""
    index_name: str
    organization_id: str
    source_types: List[SourceType]
    vector_dimension: int
    distance_metric: str
    created_at: datetime
    last_updated: datetime
    document_count: int
    metadata: Dict[str, Any] = {}


class SearchRanking(BaseModel):
    """Search result ranking information."""
    result_id: str
    query: str
    rank_position: int
    relevance_score: float
    click_through: bool = False
    user_feedback: Optional[str] = None
    timestamp: datetime


class SearchAnalytics(BaseModel):
    """Analytics for search operations."""
    organization_id: str
    total_searches: int
    unique_users: int
    avg_response_time_ms: float
    top_queries: List[Dict[str, Any]]
    search_type_distribution: Dict[str, int]
    result_click_rates: Dict[str, float]
    period_start: datetime
    period_end: datetime


class CollectionInfo(BaseModel):
    """Information about a Qdrant collection."""
    collection_name: str
    organization_id: str
    vector_count: int
    indexed_at: datetime
    config: Dict[str, Any]
    status: str  # "active", "indexing", "error"