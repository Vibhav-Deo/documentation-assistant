"""
Admin Router

Handles administrative endpoints for system management, debugging, and admin-only operations.
"""

import traceback
from fastapi import APIRouter, HTTPException, Depends
from models import LoginRequest, User, UserRole
from services.shared.auth import require_role
from services.shared.auth import auth_service
from services.infrastructure.database import db_service
from services.infrastructure.cache import SimpleCache

router = APIRouter(tags=["admin"])

# Initialize cache service
cache_service = SimpleCache()


@router.get("/admin/qdrant/collections")
async def list_qdrant_collections(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """
    List all Qdrant collections and their status (admin only).
    
    Provides information about vector collections used for semantic search.
    """
    try:
        from services.qdrant_setup import qdrant_setup
        
        if not qdrant_setup:
            raise HTTPException(status_code=503, detail="Qdrant setup service not available")
        
        collections_info = await qdrant_setup.get_collections_info()
        
        return {
            "collections": collections_info,
            "total_collections": len(collections_info)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/qdrant/verify")
async def verify_qdrant_setup(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """
    Verify Qdrant setup and collection health (admin only).
    
    Checks if all required collections exist and are properly configured.
    """
    try:
        from services.qdrant_setup import qdrant_setup
        
        if not qdrant_setup:
            raise HTTPException(status_code=503, detail="Qdrant setup service not available")
        
        verification_result = await qdrant_setup.verify_setup()
        
        return verification_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/backfill/qdrant")
async def backfill_qdrant(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """
    Backfill Qdrant with existing data from PostgreSQL (admin only).
    
    Re-indexes all existing data into Qdrant collections for semantic search.
    This is useful after system updates or data recovery.
    """
    try:
        from services.domain.search import qdrant_indexer
        
        if not qdrant_indexer:
            raise HTTPException(status_code=503, detail="Qdrant indexer not available")
        
        # Get organization data to backfill
        org_id = current_user.organization_id
        
        # Backfill Jira tickets
        jira_tickets = await db_service.get_all_jira_tickets(org_id)
        jira_indexed = await qdrant_indexer.index_jira_tickets(org_id, jira_tickets)
        
        # Backfill commits
        commits = await db_service.get_all_commits(org_id)
        commits_indexed = await qdrant_indexer.index_commits(org_id, commits)
        
        # Backfill code files
        code_files = await db_service.get_all_code_files(org_id)
        files_indexed = await qdrant_indexer.index_code_files(org_id, code_files)
        
        return {
            "status": "success",
            "backfill_results": {
                "jira_tickets_indexed": jira_indexed,
                "commits_indexed": commits_indexed,
                "code_files_indexed": files_indexed
            },
            "organization_id": org_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-cache")
async def clear_cache(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Clear query cache (admin only)"""
    cache_service.clear()
    return {"status": "cache cleared"}


# Debug endpoints
@router.get("/debug/users")
async def debug_users():
    """Debug endpoint to check users in database"""
    try:
        # Check if we can connect to database
        if not db_service.pool:
            return {"error": "Database pool not initialized"}
        
        async with db_service.pool.acquire() as conn:
            users = await conn.fetch("SELECT email, name, role FROM users LIMIT 10")
            orgs = await conn.fetch("SELECT name, plan FROM organizations LIMIT 10")
            
            return {
                "database_connected": True,
                "users": [dict(user) for user in users],
                "organizations": [dict(org) for org in orgs]
            }
    except Exception as e:
        return {"error": str(e), "database_connected": False}


@router.post("/debug/create-seed")
async def create_seed_data():
    """Create seed data via API endpoint"""
    try:
        import bcrypt
        
        # Create Demo Organization
        demo_org_data = await db_service.create_organization("Demo Organization", "enterprise")
        
        # Create Acme Corp Organization  
        acme_org_data = await db_service.create_organization("Acme Corp", "pro")
        
        # Hash passwords
        demo_password = bcrypt.hashpw("demo123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user_password = bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create users
        demo_user = await db_service.create_user(
            "demo@example.com", demo_password, "Demo User", demo_org_data["id"], "user"
        )
        
        admin_user = await db_service.create_user(
            "admin@acmecorp.com", admin_password, "John Admin", acme_org_data["id"], "admin"
        )
        
        regular_user = await db_service.create_user(
            "user@acmecorp.com", user_password, "Jane User", acme_org_data["id"], "user"
        )
        
        return {
            "status": "success",
            "message": "Seed data created",
            "organizations": [demo_org_data, acme_org_data],
            "users": [demo_user, admin_user, regular_user]
        }
        
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@router.post("/debug/test-login")
async def test_login(request: LoginRequest):
    """Debug login process step by step"""
    try:
        email = request.email
        password = request.password
        print(f"Testing login for: {email}")
        
        # Step 1: Check if user exists
        user_data = await db_service.get_user_by_email(email)
        if not user_data:
            return {"error": "User not found", "step": "user_lookup"}
        
        print(f"User found: {user_data['name']}")
        
        # Step 2: Test password verification
        stored_hash = user_data["password_hash"]
        password_valid = auth_service.verify_password(password, stored_hash)
        
        print(f"Password verification: {password_valid}")
        
        if not password_valid:
            return {
                "error": "Password verification failed", 
                "step": "password_verification",
                "stored_hash_length": len(stored_hash)
            }
        
        # Step 3: Create user object (convert UUIDs to strings)
        user_dict = {k: str(v) if k in ['id', 'organization_id'] else v 
                    for k, v in user_data.items() if k != "password_hash"}
        user = User(**user_dict)
        
        # Step 4: Get organization
        org_data = await db_service.get_organization(user.organization_id)
        if not org_data:
            return {"error": "Organization not found", "step": "org_lookup"}
        
        # Step 5: Create token
        token = auth_service.create_access_token(user)
        
        return {
            "success": True,
            "user": user.dict(),
            "organization": org_data,
            "token_created": bool(token)
        }
        
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}