"""
Sync Domain Interfaces

Defines the contracts and interfaces for sync domain services.
This establishes clear boundaries between the sync domain and other domains.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    success: bool
    items_synced: int
    items_failed: int
    errors: List[str]
    sync_time: datetime
    metadata: Dict[str, Any]


class IJiraService(ABC):
    """Interface for Jira integration services."""
    
    @abstractmethod
    async def sync_tickets(
        self,
        organization_id: str,
        project_keys: List[str] = None
    ) -> SyncResult:
        """Sync Jira tickets for an organization."""
        pass
    
    @abstractmethod
    async def get_ticket(
        self,
        ticket_key: str,
        organization_id: str
    ) -> Optional[Dict]:
        """Get a specific Jira ticket."""
        pass
    
    @abstractmethod
    async def search_tickets(
        self,
        jql: str,
        organization_id: str,
        max_results: int = 100
    ) -> List[Dict]:
        """Search Jira tickets using JQL."""
        pass


class IRepoService(ABC):
    """Interface for repository integration services."""
    
    @abstractmethod
    async def sync_repository(
        self,
        repo_url: str,
        organization_id: str,
        branch: str = "main"
    ) -> SyncResult:
        """Sync repository data for an organization."""
        pass
    
    @abstractmethod
    async def get_commits(
        self,
        repo_id: str,
        organization_id: str,
        since: Optional[datetime] = None
    ) -> List[Dict]:
        """Get commits from a repository."""
        pass
    
    @abstractmethod
    async def get_pull_requests(
        self,
        repo_id: str,
        organization_id: str,
        state: str = "all"
    ) -> List[Dict]:
        """Get pull requests from a repository."""
        pass
    
    @abstractmethod
    async def get_file_content(
        self,
        repo_id: str,
        file_path: str,
        organization_id: str,
        ref: str = "main"
    ) -> Optional[str]:
        """Get content of a specific file."""
        pass


class IDocumentService(ABC):
    """Interface for document processing services."""
    
    @abstractmethod
    async def process_document(
        self,
        document: Dict,
        organization_id: str
    ) -> Dict[str, Any]:
        """Process and extract information from a document."""
        pass
    
    @abstractmethod
    async def chunk_document(
        self,
        content: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[str]:
        """Split document content into chunks."""
        pass
    
    @abstractmethod
    async def extract_metadata(
        self,
        document: Dict
    ) -> Dict[str, Any]:
        """Extract metadata from a document."""
        pass
    
    @abstractmethod
    async def sync_confluence_docs(
        self,
        organization_id: str,
        space_keys: List[str] = None
    ) -> SyncResult:
        """Sync Confluence documents for an organization."""
        pass