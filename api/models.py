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