"""
Search Domain Interfaces

Defines the contracts and interfaces for search domain services.
This establishes clear boundaries between the search domain and other domains.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Standard search result format."""
    id: str
    score: float
    content: str
    title: str
    source_type: str
    metadata: Dict[str, Any]


class ISearchService(ABC):
    """Interface for search services."""
    
    @abstractmethod
    async def semantic_search(
        self,
        query: str,
        limit: int,
        organization_id: str
    ) -> List[SearchResult]:
        """Perform semantic vector search."""
        pass
    
    @abstractmethod
    async def keyword_search(
        self,
        query: str,
        limit: int,
        organization_id: str
    ) -> List[SearchResult]:
        """Perform keyword-based search."""
        pass
    
    @abstractmethod
    async def hybrid_search(
        self,
        query: str,
        limit: int,
        organization_id: str,
        semantic_weight: float = 0.7
    ) -> List[SearchResult]:
        """Perform hybrid semantic + keyword search."""
        pass
    
    @abstractmethod
    async def enhanced_search(
        self,
        query: str,
        search_type: str,
        limit: int,
        organization_id: str
    ) -> List[SearchResult]:
        """Enhanced search with multiple strategies."""
        pass


class IQdrantIndexer(ABC):
    """Interface for vector indexing services."""
    
    @abstractmethod
    async def index_jira_tickets(
        self,
        tickets: List[Dict],
        organization_id: str
    ) -> bool:
        """Index Jira tickets for search."""
        pass
    
    @abstractmethod
    async def index_commits(
        self,
        commits: List[Dict],
        organization_id: str
    ) -> bool:
        """Index git commits for search."""
        pass
    
    @abstractmethod
    async def index_pull_requests(
        self,
        prs: List[Dict],
        organization_id: str
    ) -> bool:
        """Index pull requests for search."""
        pass
    
    @abstractmethod
    async def index_code_files(
        self,
        files: List[Dict],
        organization_id: str
    ) -> bool:
        """Index code files for search."""
        pass
    
    @abstractmethod
    async def index_confluence_docs(
        self,
        docs: List[Dict],
        organization_id: str
    ) -> bool:
        """Index Confluence documents for search."""
        pass
    
    @abstractmethod
    async def search_jira_tickets(
        self,
        query: str,
        organization_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Search indexed Jira tickets."""
        pass
    
    @abstractmethod
    async def search_commits(
        self,
        query: str,
        organization_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Search indexed commits."""
        pass
    
    @abstractmethod
    async def search_code_files(
        self,
        query: str,
        organization_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Search indexed code files."""
        pass