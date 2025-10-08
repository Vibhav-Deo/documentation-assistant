import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import User, Organization, UserRole, PlanType
import os
import uuid

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

class AuthService:
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.users = {}
        self.organizations = {}
        self.user_sessions = {}
        
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_organization(self, name: str, plan: PlanType = PlanType.FREE) -> Organization:
        """Create new organization"""
        org_id = str(uuid.uuid4())
        quota_map = {
            PlanType.FREE: 100,
            PlanType.PRO: 10000,
            PlanType.ENTERPRISE: -1  # Unlimited
        }
        
        org = Organization(
            id=org_id,
            name=name,
            plan=plan,
            monthly_quota=quota_map[plan],
            created_at=datetime.now()
        )
        self.organizations[org_id] = org
        return org
    
    def create_user(self, email: str, password: str, name: str, organization_id: str, role: UserRole = UserRole.USER) -> User:
        """Create new user"""
        if email in [u.email for u in self.users.values()]:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        user_id = str(uuid.uuid4())
        hashed_password = self.hash_password(password)
        
        user = User(
            id=user_id,
            email=email,
            name=name,
            role=role,
            organization_id=organization_id,
            created_at=datetime.now()
        )
        
        self.users[user_id] = {
            "user": user,
            "password_hash": hashed_password
        }
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        for user_data in self.users.values():
            if user_data["user"].email == email:
                if self.verify_password(password, user_data["password_hash"]):
                    return user_data["user"]
        return None
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        payload = {
            "user_id": user.id,
            "email": user.email,
            "organization_id": user.organization_id,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """Get current authenticated user"""
        payload = self.verify_token(credentials.credentials)
        user_id = payload.get("user_id")
        
        from services.database import db_service
        user_data = await db_service.get_user_by_id(user_id)
        if not user_data:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Convert UUIDs to strings for Pydantic compatibility
        user_dict = {k: str(v) if k in ['id', 'organization_id'] else v for k, v in user_data.items()}
        return User(**user_dict)
    
    def check_quota(self, organization_id: str) -> bool:
        """Check if organization has remaining quota"""
        org = self.organizations.get(organization_id)
        if not org:
            return False
        
        if org.plan == PlanType.ENTERPRISE:
            return True  # Unlimited
        
        return org.used_quota < org.monthly_quota
    
    def increment_usage(self, organization_id: str):
        """Increment organization usage"""
        if organization_id in self.organizations:
            self.organizations[organization_id].used_quota += 1
    
    def get_organization(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        return self.organizations.get(org_id)

# Global auth service instance
auth_service = AuthService()

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    return await auth_service.get_current_user(credentials)

def require_role(required_role: UserRole):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker