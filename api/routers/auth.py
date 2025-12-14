"""
Authentication and Authorization Router

Handles user authentication, registration, OAuth, and user management endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from models import LoginRequest, RegisterRequest, User, UserRole, Organization
from services.shared.auth import auth_service, get_current_user, require_role
from services.infrastructure.database import db_service
from services.shared.oauth import oauth_service
import traceback

router = APIRouter(prefix="/auth", tags=["authentication"])


# OAuth endpoints
@router.get("/google")
def google_auth():
    """Get Google OAuth URL"""
    return {"auth_url": oauth_service.get_google_auth_url()}


@router.get("/microsoft")
def microsoft_auth():
    """Get Microsoft OAuth URL"""
    return {"auth_url": oauth_service.get_microsoft_auth_url()}


@router.post("/oauth/callback")
async def oauth_callback(provider: str, code: str):
    """Handle OAuth callback"""
    if provider == "google":
        user_data = await oauth_service.exchange_google_code(code)
    elif provider == "microsoft":
        user_data = await oauth_service.exchange_microsoft_code(code)
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    if not user_data:
        raise HTTPException(status_code=400, detail="OAuth authentication failed")
    
    # Check if user exists or create new one
    existing_user = await db_service.get_user_by_email(user_data["email"])
    
    if existing_user:
        user = User(**existing_user)
        org = await db_service.get_organization(user.organization_id)
    else:
        # Create new organization and user
        org_data = await db_service.create_organization(f"{user_data['name']}'s Organization")
        user_data_db = await db_service.create_user(
            user_data["email"],
            "",  # No password for OAuth users
            user_data["name"],
            org_data["id"],
            "admin"
        )
        # Convert UUIDs to strings
        user_dict = {k: str(v) if k in ['id', 'organization_id'] else v for k, v in user_data_db.items()}
        org_dict = {k: str(v) if k == 'id' else v for k, v in org_data.items()}
        user = User(**user_dict)
        org = Organization(**org_dict)
    
    token = auth_service.create_access_token(user)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
        "organization": org
    }


@router.post("/register")
async def register(request: RegisterRequest):
    """Register new user and organization"""
    try:
        # Create organization in database
        org_data = await db_service.create_organization(request.organization_name)
        
        # Hash password and create user
        password_hash = auth_service.hash_password(request.password)
        user_data = await db_service.create_user(
            request.email,
            password_hash,
            request.name,
            org_data["id"],
            "admin"
        )
        
        # Convert UUIDs to strings
        user_dict = {k: str(v) if k in ['id', 'organization_id'] else v for k, v in user_data.items()}
        org_dict = {k: str(v) if k == 'id' else v for k, v in org_data.items()}
        user = User(**user_dict)
        org = Organization(**org_dict)
        
        # Generate token
        token = auth_service.create_access_token(user)
        
        # Log audit event
        await db_service.log_audit(user.id, org.id, "user_registered", "user", {"email": user.email})
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user,
            "organization": org
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(request: LoginRequest):
    """Login user"""
    print(f"Login attempt for email: {request.email}")
    
    user_data = await db_service.get_user_by_email(request.email)
    print(f"User data found: {user_data is not None}")
    
    if not user_data:
        print("User not found in database")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    password_valid = auth_service.verify_password(request.password, user_data["password_hash"])
    print(f"Password valid: {password_valid}")
    
    if not password_valid:
        print("Password verification failed")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Convert UUIDs to strings for Pydantic compatibility
    user_dict = {k: str(v) if k in ['id', 'organization_id'] else v 
                for k, v in user_data.items() if k != "password_hash"}
    user = User(**user_dict)
    org_data = await db_service.get_organization(user.organization_id)
    # Convert UUIDs to strings for Organization model
    org_dict = {k: str(v) if k == 'id' else v for k, v in org_data.items()}
    org = Organization(**org_dict)
    
    token = auth_service.create_access_token(user)
    
    # Log audit event
    await db_service.log_audit(user.id, org.id, "user_login", "user", {"email": user.email})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
        "organization": org
    }


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    org_data = await db_service.get_organization(current_user.organization_id)
    # Convert UUIDs to strings
    org_dict = {k: str(v) if k == 'id' else v for k, v in org_data.items()} if org_data else None
    org = Organization(**org_dict) if org_dict else None
    return {
        "user": current_user,
        "organization": org
    }