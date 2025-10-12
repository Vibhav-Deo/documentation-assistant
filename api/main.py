import time
import traceback
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Import modules
from models import SyncRequest, Query, LoginRequest, RegisterRequest, User, UserRole, Organization, JiraSyncRequest, RepositorySyncRequest
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
from services.relationship_service import RelationshipService
from services.qdrant_setup import QdrantSetup, init_qdrant_setup
from services.qdrant_indexer import QdrantIndexer, init_qdrant_indexer

# Initialize services
cache_service = SimpleCache()
conversation_service = SimpleConversation()
analytics_service = SimpleAnalytics(qdrant)
search_service = SearchService(qdrant, embedder)
document_service = DocumentService(qdrant, embedder)
ai_service = AIService()

# Relationship service, Qdrant setup, and indexer will be initialized after database pool is ready
relationship_service = None
qdrant_setup = None
qdrant_indexer = None

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    global relationship_service, qdrant_setup, qdrant_indexer

    # Initialize database pool
    await db_service.init_pool()

    # Initialize relationship service after database pool is ready
    relationship_service = RelationshipService(db_service)

    # Initialize Qdrant collections (Phase 1: Dual Storage)
    qdrant_setup = init_qdrant_setup(qdrant)
    collections_result = await qdrant_setup.create_all_collections()

    # Initialize Qdrant indexer (Phase 2: Dual Storage)
    qdrant_indexer = init_qdrant_indexer(qdrant, embedder)

    # Log collection status
    print("📊 Qdrant Collections Status:")
    for collection, status in collections_result.items():
        print(f"   {collection}: {status}")
    print("✅ Qdrant indexer initialized")

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

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported source type: {request.source_type}. Only 'confluence' is supported.")

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
        
        # Search documentation
        try:
            doc_results = search_service.enhanced_search(
                query.question, 
                query.search_type, 
                query.max_results, 
                current_user.organization_id
            )
        except Exception as e:
            print(f"Error searching docs: {e}")
            doc_results = []
        
        # PHASE 5: MULTI-SOURCE SEMANTIC SEARCH (Qdrant)
        # Search Jira tickets semantically (Phase 2)
        try:
            if qdrant_indexer:
                jira_tickets = await qdrant_indexer.search_jira_tickets(
                    query.question,
                    current_user.organization_id,
                    limit=3
                )
                print(f"🔍 Found {len(jira_tickets)} Jira tickets (semantic) for: {query.question}")
            else:
                # Fallback to PostgreSQL exact search
                jira_tickets = await db_service.search_jira_tickets(
                    query.question,
                    current_user.organization_id,
                    limit=3
                )
                print(f"Found {len(jira_tickets)} Jira tickets (exact) for: {query.question}")
        except Exception as e:
            print(f"Error searching Jira tickets: {e}")
            jira_tickets = []

        # Search commits semantically (Phase 3)
        try:
            if qdrant_indexer:
                commit_results = await qdrant_indexer.search_commits(
                    query.question,
                    current_user.organization_id,
                    limit=3
                )
                print(f"🔍 Found {len(commit_results)} commits (semantic) for: {query.question}")
            else:
                commit_results = []
        except Exception as e:
            print(f"Error searching commits: {e}")
            commit_results = []

        # Search code files semantically (Phase 4)
        try:
            if qdrant_indexer:
                code_files = await qdrant_indexer.search_code_files(
                    query.question,
                    current_user.organization_id,
                    limit=3
                )
                print(f"🔍 Found {len(code_files)} code files (semantic) for: {query.question}")
            else:
                # Fallback to PostgreSQL exact search
                code_files = await db_service.search_code_files(
                    query.question,
                    current_user.organization_id,
                    limit=3
                )
                print(f"Found {len(code_files)} code files (exact) for: {query.question}")
        except Exception as e:
            print(f"Error searching code files: {e}")
            code_files = []

        # Build combined context
        context_parts = []
        sources = []
        
        # Check query type
        import re
        ticket_key_pattern = r'\b([A-Z]{2,10}-\d+)\b'
        has_ticket_key = bool(re.search(ticket_key_pattern, query.question.upper()))
        jira_terms = ['ticket', 'jira', 'bug', 'story', 'task', 'epic', 'sprint']
        is_jira_query = has_ticket_key or any(term in query.question.lower() for term in jira_terms)

        # Check if query is about code
        code_terms = ['function', 'class', 'code', 'implement', 'file', 'module', 'import', 'def ', 'async ', 'const ', 'var ', 'let ']
        is_code_query = any(term in query.question.lower() for term in code_terms)
        
        # Build context with intelligent prioritization
        if code_files and is_code_query:
            # For code-specific queries, prioritize code files
            context_parts.append("=== Code Examples ===")
            for code_file in code_files:
                code_text = f"File: {code_file['file_path']}\n"
                code_text += f"Language: {code_file.get('language', 'unknown')}\n"
                if code_file.get('functions'):
                    code_text += f"Functions: {', '.join(code_file['functions'][:5])}\n"
                if code_file.get('classes'):
                    code_text += f"Classes: {', '.join(code_file['classes'][:5])}\n"
                # Add relevant code snippet
                if code_file.get('content'):
                    code_text += f"\nCode:\n```\n{code_file['content'][:800]}\n```"
                context_parts.append(code_text)
                sources.append(f"Code: {code_file['file_path']}")

            # Add docs as supplementary
            if doc_results:
                relevant_docs = [hit for hit in doc_results if hit.score > 0.7]
                if relevant_docs:
                    context_parts.append("\n=== Related Documentation ===")
                    for hit in relevant_docs[:2]:
                        context_parts.append(hit.payload["text"])
                        sources.append(hit.payload.get("title", "Unknown source"))

        elif jira_tickets and is_jira_query:
            # For Jira-specific queries, prioritize Jira tickets
            context_parts.append("=== Jira Tickets ===")
            for ticket in jira_tickets:
                ticket_text = f"Ticket {ticket['ticket_key']}: {ticket['summary']}\n"
                if ticket.get('description'):
                    ticket_text += f"Description: {ticket['description'][:500]}\n"
                ticket_text += f"Status: {ticket['status']}, Type: {ticket['issue_type']}"
                if ticket.get('assignee'):
                    ticket_text += f", Assignee: {ticket['assignee']}"
                context_parts.append(ticket_text)
                sources.append(f"Jira: {ticket['ticket_key']}")

            # Add docs if highly relevant
            if doc_results:
                relevant_docs = [hit for hit in doc_results if hit.score > 0.7]
                if relevant_docs:
                    context_parts.append("\n=== Related Documentation ===")
                    for hit in relevant_docs[:2]:
                        context_parts.append(hit.payload["text"])
                        sources.append(hit.payload.get("title", "Unknown source"))

        else:
            # For general queries, prioritize documentation
            if doc_results:
                context_parts.append("=== Documentation ===")
                for hit in doc_results:
                    context_parts.append(hit.payload["text"])
                    sources.append(hit.payload.get("title", "Unknown source"))

            # Add code files as supplementary
            if code_files:
                context_parts.append("\n=== Related Code ===")
                for code_file in code_files[:2]:
                    code_text = f"File: {code_file['file_path']} ({code_file.get('language', 'unknown')})"
                    if code_file.get('functions'):
                        code_text += f"\nFunctions: {', '.join(code_file['functions'][:3])}"
                    context_parts.append(code_text)
                    sources.append(f"Code: {code_file['file_path']}")

            # Add Jira tickets as supplementary
            if jira_tickets:
                context_parts.append("\n=== Related Jira Tickets ===")
                for ticket in jira_tickets:
                    ticket_text = f"Ticket {ticket['ticket_key']}: {ticket['summary']}\n"
                    if ticket.get('description'):
                        ticket_text += f"Description: {ticket['description'][:300]}\n"
                    ticket_text += f"Status: {ticket['status']}"
                    context_parts.append(ticket_text)
                    sources.append(f"Jira: {ticket['ticket_key']}")
        
        # Handle case with no data
        if not context_parts:
            prompt = ai_service.build_prompt(query.question, "", context_history)
            answer = ai_service.generate_response(prompt, query.model)
            
            session_id = query.session_id or conversation_service.create_session()
            conversation_service.add_message(session_id, query.question, answer, [])
            
            response = {
                "answer": answer + "\n\n*Note: This response is based on general knowledge. For more specific answers, consider syncing relevant documentation and Jira tickets.*",
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

        # Build multi-source prompt and generate answer (PHASE 5)
        # Format Confluence results for prompt builder
        confluence_results = []
        if doc_results:
            for hit in doc_results:
                confluence_results.append({
                    "title": hit.payload.get("title", "Untitled"),
                    "text": hit.payload.get("text", "")
                })

        # Use new multi-source prompt builder with source attribution
        prompt = ai_service.build_multi_source_prompt(
            query.question,
            confluence_results,
            jira_tickets,
            commit_results,
            code_files
        )
        answer = ai_service.generate_response(prompt, query.model)
        
        # Store conversation
        session_id = query.session_id or conversation_service.create_session()
        conversation_service.add_message(session_id, query.question, answer, sources)
        
        # Build enhanced response with source attribution (PHASE 5)
        source_attribution = {
            "confluence_docs": len(confluence_results),
            "jira_tickets": len(jira_tickets),
            "commits": len(commit_results),
            "code_files": len(code_files),
            "total_sources": len(confluence_results) + len(jira_tickets) + len(commit_results) + len(code_files)
        }

        response = {
            "answer": answer,
            "sources": list(set(sources)),
            "source_attribution": source_attribution,
            "session_id": session_id
        }
        
        # Cache and log
        cache_service.set(query.question, response)
        analytics_service.log_query(
            query.question,
            len(doc_results) + len(jira_tickets) + len(code_files),
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

@app.post("/sync/jira")
async def sync_jira(
    request: JiraSyncRequest,
    current_user: User = Depends(get_current_user)
):
    """Sync Jira project tickets"""
    try:
        # Import Jira service
        from services.integrations.jira_service import JiraService

        # Initialize Jira client
        jira_service = JiraService(
            request.server,
            request.email,
            request.api_token
        )

        # Test connection
        if not jira_service.test_connection():
            raise HTTPException(status_code=401, detail="Failed to connect to Jira. Check credentials.")

        # Sync project tickets
        tickets = jira_service.sync_project(request.project_key)

        # DUAL STORAGE: Store tickets in both PostgreSQL and Qdrant
        tickets_created = 0
        tickets_updated = 0
        tickets_indexed = 0

        for ticket_data in tickets:
            try:
                # 1. Store in PostgreSQL (for relationships and exact queries)
                result = await db_service.create_jira_ticket(ticket_data, current_user.organization_id)
                tickets_created += 1

                # 2. Store in Qdrant (for semantic search) - PHASE 2
                if qdrant_indexer:
                    indexed = await qdrant_indexer.index_jira_ticket(
                        ticket_data,
                        current_user.organization_id
                    )
                    if indexed:
                        tickets_indexed += 1

            except Exception as e:
                print(f"Error storing ticket {ticket_data.get('key')}: {e}")
                continue

        # Log audit event
        await db_service.log_audit(
            current_user.id,
            current_user.organization_id,
            "jira_sync",
            "sync",
            {
                "project": request.project_key,
                "tickets_synced": len(tickets),
                "tickets_indexed_qdrant": tickets_indexed,
                "server": request.server
            }
        )

        return {
            "status": "success",
            "tickets_synced": len(tickets),
            "tickets_indexed": tickets_indexed,
            "project_key": request.project_key,
            "server": request.server,
            "dual_storage": tickets_indexed > 0
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to sync Jira: {str(e)}")

@app.get("/jira/tickets")
async def get_jira_tickets(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Get all Jira tickets for the organization"""
    try:
        tickets = await db_service.get_jira_tickets(current_user.organization_id, limit, offset)
        total_count = await db_service.count_jira_tickets(current_user.organization_id)
        return {
            "tickets": tickets,
            "count": len(tickets),
            "total": total_count,
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync/repository")
async def sync_repository(
    request: RepositorySyncRequest,
    current_user: User = Depends(get_current_user)
):
    """Sync code repository (GitHub, GitLab, Bitbucket)"""
    try:
        from services.integrations.repo_service import RepositoryService

        # Initialize repository service
        repo_service = RepositoryService(
            request.provider,
            request.repo_url,
            request.access_token,
            request.branch
        )

        # Test connection
        if not repo_service.test_connection():
            raise HTTPException(status_code=401, detail="Failed to connect to repository. Check credentials and URL.")

        # Extract repo name
        repo_name = repo_service.repo

        # Sync repository files
        file_data_list = repo_service.sync_repository(max_files=500)

        # Create repository record
        repo_data = {
            'repo_url': request.repo_url,
            'repo_name': repo_name,
            'provider': request.provider,
            'branch': request.branch,
            'file_count': len(file_data_list),
            'metadata': {
                'owner': repo_service.owner,
                'synced_files': len(file_data_list)
            }
        }

        repo_record = await db_service.create_repository(repo_data, current_user.organization_id)

        # DUAL STORAGE: Store code files in PostgreSQL + Qdrant
        files_created = 0
        files_indexed = 0

        for file_data in file_data_list:
            try:
                # 1. Store in PostgreSQL (for relationships and exact queries)
                await db_service.create_code_file(file_data, repo_record['id'], current_user.organization_id)
                files_created += 1

                # 2. Store in Qdrant (for semantic search) - PHASE 4
                if qdrant_indexer:
                    # Add repository_id to file data for indexing
                    file_data['repository_id'] = repo_record['id']
                    indexed = await qdrant_indexer.index_code_file(
                        file_data,
                        current_user.organization_id
                    )
                    if indexed:
                        files_indexed += 1

            except Exception as e:
                print(f"Error storing file {file_data.get('file_path')}: {e}")
                continue

        # DUAL STORAGE: Fetch and store commit history in PostgreSQL + Qdrant
        print(f"Fetching commit history for {repo_name}...")
        commits = repo_service.fetch_commit_history(max_commits=500)
        commits_created = 0
        commits_indexed = 0

        for commit_data in commits:
            try:
                # 1. Store in PostgreSQL (for relationships and exact queries)
                await db_service.create_commit(commit_data, repo_record['id'], current_user.organization_id)
                commits_created += 1

                # 2. Store in Qdrant (for semantic search) - PHASE 3
                if qdrant_indexer:
                    # Add repository_id to commit data for indexing
                    commit_data['repository_id'] = repo_record['id']
                    indexed = await qdrant_indexer.index_commit(
                        commit_data,
                        current_user.organization_id
                    )
                    if indexed:
                        commits_indexed += 1

            except Exception as e:
                print(f"Error storing commit {commit_data.get('sha')}: {e}")
                continue

        # Fetch and store pull requests
        print(f"Fetching pull requests for {repo_name}...")
        prs = repo_service.fetch_pull_requests(max_prs=100)
        prs_created = 0
        for pr_data in prs:
            try:
                await db_service.create_pull_request(pr_data, repo_record['id'], current_user.organization_id)
                prs_created += 1
            except Exception as e:
                print(f"Error storing PR #{pr_data.get('pr_number')}: {e}")
                continue

        # Log audit event
        await db_service.log_audit(
            current_user.id,
            current_user.organization_id,
            "repository_sync",
            "sync",
            {
                "repo_url": request.repo_url,
                "provider": request.provider,
                "files_synced": files_created,
                "files_indexed_qdrant": files_indexed,
                "commits_synced": commits_created,
                "commits_indexed_qdrant": commits_indexed,
                "prs_synced": prs_created,
                "branch": request.branch
            }
        )

        return {
            "status": "success",
            "files_synced": files_created,
            "files_indexed": files_indexed,
            "commits_synced": commits_created,
            "commits_indexed": commits_indexed,
            "prs_synced": prs_created,
            "repo_name": repo_name,
            "repo_url": request.repo_url,
            "provider": request.provider,
            "dual_storage": (files_indexed > 0 and commits_indexed > 0),
            "branch": request.branch
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to sync repository: {str(e)}")

@app.get("/repositories")
async def get_repositories(current_user: User = Depends(get_current_user)):
    """Get all synced repositories for the organization"""
    try:
        repos = await db_service.get_repositories(current_user.organization_id)
        return {
            "repositories": repos,
            "count": len(repos)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/repositories/{repo_id}/files")
async def get_repository_files(
    repo_id: str,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get code files for a specific repository"""
    try:
        files = await db_service.get_code_files(repo_id, current_user.organization_id, limit)
        return {
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Relationship and Knowledge Graph Endpoints
# ============================================

@app.get("/relationships/ticket/{ticket_key}")
async def get_ticket_relationships(
    ticket_key: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get all relationships for a Jira ticket

    Returns:
    - Related commits
    - Related pull requests
    - Related documents
    - Related code files
    - Related developers
    - Complete timeline
    """
    try:
        relationships = await relationship_service.get_ticket_relationships(
            ticket_key,
            current_user.organization_id
        )
        return relationships
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR in get_ticket_relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/relationships/developer/{developer_email}")
async def get_developer_contributions(
    developer_email: str,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """
    Get all contributions by a developer

    Returns:
    - Commits authored
    - Pull requests created
    - Tickets worked on
    - Code files modified
    - Statistics
    """
    try:
        contributions = await relationship_service.get_developer_contributions(
            developer_email,
            current_user.organization_id,
            limit
        )
        return contributions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/relationships/file")
async def get_file_history(
    file_path: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get complete history of a code file

    Returns:
    - All commits that modified the file
    - Developers who worked on it
    - Related tickets
    - Timeline
    """
    try:
        history = await relationship_service.get_file_history(
            file_path,
            current_user.organization_id
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/relationships/repository/{repo_id}/stats")
async def get_repository_stats(
    repo_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive statistics for a repository

    Returns:
    - Commit stats
    - PR stats
    - File stats
    - Top contributors
    - Related tickets
    """
    try:
        stats = await relationship_service.get_repository_stats(
            repo_id,
            current_user.organization_id
        )

        if not stats:
            raise HTTPException(status_code=404, detail="Repository not found")

        return stats
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR in get_repository_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/relationships/timeline/{ticket_key}")
async def get_feature_timeline(
    ticket_key: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get complete chronological timeline for a feature/ticket

    Returns:
    - Ticket creation
    - All commits
    - All pull requests
    - Document updates
    - Sorted chronologically
    """
    try:
        timeline = await relationship_service.get_feature_timeline(
            ticket_key,
            current_user.organization_id
        )
        return {
            "ticket_key": ticket_key,
            "timeline": timeline,
            "count": len(timeline)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/relationships/search")
async def search_relationships(
    query: str,
    entity_types: str = "commits,prs,tickets,files",
    current_user: User = Depends(get_current_user)
):
    """
    Search across all entities and return relationships

    Query parameters:
    - query: Search term
    - entity_types: Comma-separated list (commits,prs,tickets,files,documents)

    Returns:
    - Matching commits
    - Matching pull requests
    - Matching tickets
    - Matching files
    - Matching documents
    """
    try:
        entity_list = [t.strip() for t in entity_types.split(',')]

        results = await relationship_service.search_relationships(
            query,
            current_user.organization_id,
            entity_list
        )
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR in search_relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ADMIN ENDPOINTS: Qdrant Collections Management
# ============================================================================

@app.get("/admin/qdrant/collections")
async def list_qdrant_collections(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """
    List all Qdrant collections with their status and statistics.

    Admin only endpoint to monitor multi-source indexing.
    """
    try:
        if not qdrant_setup:
            raise HTTPException(status_code=503, detail="Qdrant setup not initialized")

        collections_info = await qdrant_setup.get_all_collections_info()
        storage_stats = await qdrant_setup.get_storage_stats()

        return {
            "status": "success",
            "collections": collections_info,
            "storage": storage_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/qdrant/verify")
async def verify_qdrant_setup(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """
    Verify that all required Qdrant collections exist.

    Returns:
    - Status of each required collection
    - Whether setup is complete
    """
    try:
        if not qdrant_setup:
            raise HTTPException(status_code=503, detail="Qdrant setup not initialized")

        verification_results = await qdrant_setup.verify_setup()

        all_exist = all(verification_results.values())

        return {
            "status": "complete" if all_exist else "incomplete",
            "collections": verification_results,
            "missing": [name for name, exists in verification_results.items() if not exists]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/jira")
async def search_jira_tickets_semantic(
    query: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    Search Jira tickets using semantic search (Phase 2: Dual Storage).

    Enables natural language queries like:
    - "authentication issues" → Finds tickets about login, auth, security
    - "payment bugs" → Finds tickets about billing, transactions, checkout
    - "performance problems" → Finds tickets about speed, latency, optimization

    This is the core USP: semantic search across Jira to find related tickets
    even when exact keywords don't match.
    """
    try:
        if not qdrant_indexer:
            raise HTTPException(status_code=503, detail="Qdrant indexer not initialized")

        results = await qdrant_indexer.search_jira_tickets(
            query,
            current_user.organization_id,
            limit
        )

        return {
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results),
            "source": "qdrant_semantic_search"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/commits")
async def search_commits_semantic(
    query: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    Search Git commits using semantic search (Phase 3: Dual Storage).

    Enables natural language queries like:
    - "user authentication" → Finds commits about login, auth, sign-in
    - "payment processing" → Finds commits about billing, checkout, stripe
    - "bug fixes" → Finds commits with bug-related changes
    - "performance improvements" → Finds commits about optimization

    Core USP: Find commits by what they did, not just exact commit message words.
    """
    try:
        if not qdrant_indexer:
            raise HTTPException(status_code=503, detail="Qdrant indexer not initialized")

        results = await qdrant_indexer.search_commits(
            query,
            current_user.organization_id,
            limit
        )

        return {
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results),
            "source": "qdrant_semantic_search"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/code")
async def search_code_files_semantic(
    query: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    Search code files using semantic search (Phase 4: Dual Storage).

    Enables natural language queries like:
    - "authentication service" → Finds auth-related files (auth.py, login.js, etc.)
    - "payment processing" → Finds payment/billing files
    - "database connection" → Finds DB-related files
    - "user management" → Finds user/account management files

    Core USP: Find code files by functionality, not just file names.
    """
    try:
        if not qdrant_indexer:
            raise HTTPException(status_code=503, detail="Qdrant indexer not initialized")

        results = await qdrant_indexer.search_code_files(
            query,
            current_user.organization_id,
            limit
        )

        return {
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results),
            "source": "qdrant_semantic_search"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))