"""
Sync Domain

This domain handles all data synchronization functionality including:
- External system integrations (Jira, Confluence, Git)
- Data ingestion and processing
- Real-time sync coordination
- Data validation and transformation
"""

# Import interfaces first
from .interfaces import (
    IJiraService,
    IRepoService,
    IDocumentService,
    SyncResult as ISyncResult
)

# Import domain models
from .models import (
    SyncStatus,
    SourceProvider,
    SyncResult,
    SyncJob,
    JiraConfiguration,
    RepositoryConfiguration,
    ConfluenceConfiguration,
    DataTransformation,
    SyncMapping,
    ExternalEntity,
    SyncConflict,
    WebhookEvent,
    SyncSchedule
)

# Import all sync domain services
from .jira_service import JiraService
from .repo_service import RepositoryService
from .document import DocumentService, chunk_text

__all__ = [
    # Interfaces
    'IJiraService',
    'IRepoService',
    'IDocumentService',
    'ISyncResult',
    # Models
    'SyncStatus',
    'SourceProvider',
    'SyncResult',
    'SyncJob',
    'JiraConfiguration',
    'RepositoryConfiguration',
    'ConfluenceConfiguration',
    'DataTransformation',
    'SyncMapping',
    'ExternalEntity',
    'SyncConflict',
    'WebhookEvent',
    'SyncSchedule',
    # Services
    'JiraService',
    'RepositoryService',
    'DocumentService',
    'chunk_text'
]