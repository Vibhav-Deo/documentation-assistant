from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum
from datetime import datetime

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class User(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    name: str
    role: UserRole = UserRole.USER
    organization_id: str
    is_active: bool = True
    created_at: Optional[datetime] = None

class Organization(BaseModel):
    id: Optional[str] = None
    name: str
    plan: PlanType = PlanType.FREE
    monthly_quota: int = 100
    used_quota: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    organization_name: str

class SyncRequest(BaseModel):
    source_type: str
    space_key_or_url: str
    confluence_base_url: Optional[str] = None
    confluence_username: Optional[str] = None
    confluence_api_token: Optional[str] = None

class Query(BaseModel):
    question: str
    session_id: Optional[str] = None
    model: Optional[str] = "mistral"
    max_results: Optional[int] = 5
    search_type: Optional[str] = "semantic"
    stream: Optional[bool] = False

class JiraSyncRequest(BaseModel):
    server: str  # e.g., "https://your-domain.atlassian.net"
    email: EmailStr
    api_token: str
    project_key: str  # e.g., "PROJ"

class RepositorySyncRequest(BaseModel):
    provider: str  # "github", "gitlab", "bitbucket"
    repo_url: str  # e.g., "https://github.com/owner/repo"
    access_token: str  # Personal access token
    branch: Optional[str] = "main"


# Streaming Event Models
class StreamingEventType(str, Enum):
    METADATA = "metadata"
    SOURCES = "sources"
    CONTENT = "content"
    COMPLETE = "complete"
    ERROR = "error"


class SearchMetadata(BaseModel):
    processing_time: float
    sources_searched: dict
    total_results: int
    query_id: Optional[str] = None


class SearchSource(BaseModel):
    type: str  # "documentation", "jira_ticket", "commit", "code_file"
    title: str
    content: str
    score: float
    metadata: Optional[dict] = None


class ContentChunk(BaseModel):
    chunk: str
    chunk_id: Optional[int] = None
    total_chunks: Optional[int] = None


class CompletionMetadata(BaseModel):
    total_tokens: int
    model_used: Optional[str] = None
    final_processing_time: float
    query_metadata: dict


class StreamingError(BaseModel):
    error_type: str
    message: str
    recoverable: bool = True
    error_code: Optional[str] = None


class StreamingEvent(BaseModel):
    type: StreamingEventType
    data: dict
    timestamp: float
    event_id: Optional[str] = None


# Specific streaming event models
class MetadataEvent(BaseModel):
    type: StreamingEventType = StreamingEventType.METADATA
    data: SearchMetadata
    timestamp: float
    event_id: Optional[str] = None


class SourcesEvent(BaseModel):
    type: StreamingEventType = StreamingEventType.SOURCES
    data: dict  # {"sources": List[SearchSource]}
    timestamp: float
    event_id: Optional[str] = None


class ContentEvent(BaseModel):
    type: StreamingEventType = StreamingEventType.CONTENT
    data: ContentChunk
    timestamp: float
    event_id: Optional[str] = None


class CompleteEvent(BaseModel):
    type: StreamingEventType = StreamingEventType.COMPLETE
    data: CompletionMetadata
    timestamp: float
    event_id: Optional[str] = None


class ErrorEvent(BaseModel):
    type: StreamingEventType = StreamingEventType.ERROR
    data: StreamingError
    timestamp: float
    event_id: Optional[str] = None