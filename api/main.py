import time
import traceback
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Import modules
from models import SyncRequest, Query, LoginRequest, RegisterRequest, User, UserRole, Organization
from config import QDRANT_HOST, QDRANT_PORT
from services.cache import SimpleCache
from services.conversation import SimpleConversation
from services.analytics import SimpleAnalytics
from services.search import SearchService
from services.document import DocumentService, chunk_text
from services.ai import AIService
from services.auth import auth_service, get_current_user, require_role
from services.encryption import encryption_service
from models import LoginRequest, RegisterRequest, User, UserRole

# Initialize FastAPI app
app = FastAPI(title="Confluence RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize clients and services
try:
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
except Exception as e:
    raise RuntimeError(f"Failed to initialize clients: {e}")

# Initialize production services
from services.database import db_service
from services.redis_service import redis_service
from services.oauth import oauth_service
from services.monitoring import monitoring_service

# Initialize services
cache_service = SimpleCache()
conversation_service = SimpleConversation()
analytics_service = SimpleAnalytics(qdrant)
search_service = SearchService(qdrant, embedder)
document_service = DocumentService(qdrant, embedder)
ai_service = AIService()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    await db_service.init_pool()

@app.get("/health")
def health_check():
    """Comprehensive health check endpoint"""
    return monitoring_service.get_api_health()

@app.get("/metrics")
def get_metrics():
    """Prometheus metrics endpoint"""
    return monitoring_service.get_system_metrics()

@app.get("/monitoring/alerts")
async def get_alerts(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Get system alerts (admin only)"""
    return monitoring_service.get_alerts()

@app.get("/monitoring/requests")
async def get_request_metrics(hours: int = 24, current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Get request metrics (admin only)"""
    return monitoring_service.get_request_metrics(hours)

@app.get("/monitoring/organization")
async def get_organization_metrics(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Get organization-specific metrics (admin only)"""
    org_data = await db_service.get_organization(current_user.organization_id)
    if not org_data:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Get organization users and their usage
    users = await db_service.get_organization_users(current_user.organization_id)
    total_users = len(users)
    
    # Get usage stats from audit logs
    usage_stats = await db_service.get_organization_usage_stats(current_user.organization_id)
    
    return {
        "organization": {k: str(v) if k == 'id' else v for k, v in org_data.items()},
        "total_users": total_users,
        "users": [{k: str(v) if k in ['id', 'organization_id'] else v for k, v in user.items()} for user in users],
        "usage_stats": usage_stats
    }

@app.get("/analytics")
def get_analytics():
    """Get comprehensive analytics"""
    return {
        "document_stats": analytics_service.get_document_stats(),
        "usage_metrics": analytics_service.get_usage_metrics(),
        "popular_queries": analytics_service.get_popular_queries(),
        "performance_insights": analytics_service.get_performance_insights()
    }

# OAuth endpoints
@app.get("/auth/google")
def google_auth():
    """Get Google OAuth URL"""
    return {"auth_url": oauth_service.get_google_auth_url()}

@app.get("/auth/microsoft")
def microsoft_auth():
    """Get Microsoft OAuth URL"""
    return {"auth_url": oauth_service.get_microsoft_auth_url()}

@app.post("/auth/oauth/callback")
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

# Authentication endpoints
@app.post("/auth/register")
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

@app.post("/auth/login")
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

@app.get("/auth/me")
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

@app.get("/debug/users")
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

@app.post("/debug/create-seed")
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
        import traceback
        traceback.print_exc()
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.post("/debug/test-login")
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
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.post("/clear-cache")
async def clear_cache(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Clear query cache (admin only)"""
    cache_service.clear()
    return {"status": "cache cleared"}

@app.post("/sync")
async def sync_docs(request: SyncRequest, current_user: User = Depends(get_current_user)):
    """Sync documents with dynamic configuration (authenticated)"""
    # Check quota
    if not await db_service.check_and_increment_quota(current_user.organization_id):
        raise HTTPException(status_code=429, detail="Monthly quota exceeded")
    
    document_service.ensure_collection_exists(current_user.organization_id)
    
    if request.source_type == "confluence":
        if not all([request.confluence_base_url, request.confluence_username, request.confluence_api_token]):
            raise HTTPException(status_code=400, detail="Missing Confluence configuration")
        
        pages = document_service.fetch_confluence_pages(
            request.space_key_or_url,
            request.confluence_base_url,
            request.confluence_username,
            request.confluence_api_token
        )
        
        for title, text in pages:
            chunks = chunk_text(text)
            document_service.store_chunks(title, chunks, "confluence", current_user.organization_id)
        
        return {"status": "synced", "pages": len(pages)}
    
    elif request.source_type == "public":
        return document_service.sync_public_url(request.space_key_or_url, current_user.organization_id)
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported source type: {request.source_type}")

@app.post("/ask")
async def ask(query: Query, current_user: User = Depends(get_current_user)):
    start_time = time.time()
    
    # Check quota
    if not await db_service.check_and_increment_quota(current_user.organization_id):
        raise HTTPException(status_code=429, detail="Monthly quota exceeded")
    
    # Log API request for tracking
    await db_service.log_audit(current_user.id, current_user.organization_id, "api_request", "ask", {"question": query.question[:100]})
    
    try:
        # Check cache
        cached_result = cache_service.get(query.question)
        if cached_result:
            return cached_result
        
        # Get conversation context
        context_history = conversation_service.get_context(query.session_id) if query.session_id else ""
        
        # Enhanced search with organization isolation
        try:
            results = search_service.enhanced_search(
                query.question, 
                query.search_type, 
                query.max_results, 
                current_user.organization_id
            )
        except Exception:
            results = []
        
        # Handle case with no documents
        if not results:
            prompt = ai_service.build_prompt(query.question, "", context_history)
            answer = ai_service.generate_response(prompt, query.model)
            
            session_id = query.session_id or conversation_service.create_session()
            conversation_service.add_message(session_id, query.question, answer, [])
            
            response = {
                "answer": answer + "\n\n*Note: This response is based on general knowledge. For more specific answers, consider syncing relevant documentation.*",
                "sources": [],
                "session_id": session_id
            }
            
            cache_service.set(query.question, response)
            analytics_service.log_query(
                query.question, 
                0, 
                time.time() - start_time,
                query.model,
                query.search_type,
                session_id
            )
            
            return response

        # Build context from search results
        context = "\n\n".join(hit.payload["text"] for hit in results)
        prompt = ai_service.build_prompt(query.question, context, context_history)
        answer = ai_service.generate_response(prompt, query.model)
        
        sources = list({hit.payload.get("title", "Unknown source") for hit in results})
        
        # Store conversation
        session_id = query.session_id or conversation_service.create_session()
        conversation_service.add_message(session_id, query.question, answer, sources)
        
        response = {
            "answer": answer, 
            "sources": sources,
            "session_id": session_id
        }
        
        # Cache and log
        cache_service.set(query.question, response)
        analytics_service.log_query(
            query.question, 
            len(results), 
            time.time() - start_time,
            query.model,
            query.search_type,
            session_id
        )
        
        return response

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")