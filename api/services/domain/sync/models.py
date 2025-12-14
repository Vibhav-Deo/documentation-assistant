"""
Sync Domain Models

Data models specific to the sync domain including:
- Synchronization results and status
- External system configurations
- Data transformation models
"""

from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class SyncStatus(str, Enum):
    """Status of synchronization operations."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SourceProvider(str, Enum):
    """External data source providers."""
    JIRA = "jira"
    CONFLUENCE = "confluence"
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class SyncResult(BaseModel):
    """Result of a synchronization operation."""
    success: bool
    items_synced: int
    items_failed: int
    errors: List[str]
    sync_time: datetime
    metadata: Dict[str, Any] = {}


class SyncJob(BaseModel):
    """Synchronization job tracking."""
    job_id: str
    organization_id: str
    source_provider: SourceProvider
    source_config: Dict[str, Any]
    status: SyncStatus
    progress_percentage: float
    items_total: Optional[int] = None
    items_processed: int = 0
    items_failed: int = 0
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}


class JiraConfiguration(BaseModel):
    """Jira integration configuration."""
    server: str  # e.g., "https://your-domain.atlassian.net"
    email: EmailStr
    api_token: str
    project_keys: List[str]
    sync_frequency: Optional[str] = "daily"
    last_sync: Optional[datetime] = None


class RepositoryConfiguration(BaseModel):
    """Repository integration configuration."""
    provider: SourceProvider
    repo_url: str
    access_token: str
    branch: str = "main"
    sync_frequency: Optional[str] = "hourly"
    last_sync: Optional[datetime] = None
    webhook_url: Optional[str] = None


class ConfluenceConfiguration(BaseModel):
    """Confluence integration configuration."""
    base_url: str
    username: str
    api_token: str
    space_keys: List[str]
    sync_frequency: Optional[str] = "daily"
    last_sync: Optional[datetime] = None


class DataTransformation(BaseModel):
    """Data transformation rules for sync."""
    source_field: str
    target_field: str
    transformation_type: str  # "direct", "mapping", "function"
    transformation_config: Dict[str, Any] = {}


class SyncMapping(BaseModel):
    """Mapping configuration for data synchronization."""
    source_provider: SourceProvider
    source_type: str  # "ticket", "commit", "document"
    target_schema: str
    field_mappings: List[DataTransformation]
    validation_rules: List[Dict[str, Any]] = []


class ExternalEntity(BaseModel):
    """External entity from synchronized data."""
    external_id: str
    entity_type: str
    source_provider: SourceProvider
    organization_id: str
    raw_data: Dict[str, Any]
    processed_data: Dict[str, Any]
    sync_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class SyncConflict(BaseModel):
    """Conflict detected during synchronization."""
    conflict_id: str
    entity_id: str
    conflict_type: str  # "duplicate", "schema_mismatch", "validation_error"
    description: str
    local_data: Dict[str, Any]
    remote_data: Dict[str, Any]
    resolution_strategy: Optional[str] = None
    resolved: bool = False
    created_at: datetime


class WebhookEvent(BaseModel):
    """Webhook event from external systems."""
    event_id: str
    source_provider: SourceProvider
    event_type: str
    payload: Dict[str, Any]
    organization_id: str
    processed: bool = False
    received_at: datetime
    processed_at: Optional[datetime] = None


class SyncSchedule(BaseModel):
    """Synchronization schedule configuration."""
    schedule_id: str
    organization_id: str
    source_provider: SourceProvider
    cron_expression: str
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    metadata: Dict[str, Any] = {}