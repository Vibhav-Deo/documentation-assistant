"""
Data Synchronization Router

Handles synchronization with external systems like Confluence, Jira, and Git repositories.
"""

import time
from fastapi import APIRouter, HTTPException, Depends
from models import SyncRequest, JiraSyncRequest, RepositorySyncRequest, User
from services.shared.auth import get_current_user
from services.infrastructure.database import db_service
from services.domain.sync import DocumentService, chunk_text
from services.domain.sync import JiraService
from services.domain.sync import RepositoryService
from services.domain.search import qdrant_indexer

router = APIRouter(prefix="/sync", tags=["synchronization"])


@router.post("/")
async def sync_docs(request: SyncRequest, current_user: User = Depends(get_current_user)):
    """Sync documents with dynamic configuration (authenticated)"""
    # Check quota
    if not await db_service.check_and_increment_quota(current_user.organization_id):
        raise HTTPException(status_code=429, detail="Monthly quota exceeded")
    
    from services.document import document_service
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


@router.post("/jira")
async def sync_jira(
    request: JiraSyncRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Sync Jira tickets for the authenticated user's organization.
    
    This endpoint connects to Jira, fetches tickets, and indexes them
    for semantic search and analysis.
    """
    try:
        # Check quota
        if not await db_service.check_and_increment_quota(current_user.organization_id):
            raise HTTPException(status_code=429, detail="Monthly quota exceeded")
        
        # Initialize Jira service
        jira_service = JiraService(
            server=request.server,
            email=request.email,
            api_token=request.api_token
        )
        
        # Fetch tickets from Jira
        print(f"🔄 Fetching Jira tickets from {request.server} for project {request.project_key}")
        tickets = await jira_service.fetch_tickets(request.project_key)
        print(f"📥 Fetched {len(tickets)} tickets from Jira")
        
        # Store tickets in database
        stored_count = 0
        for ticket in tickets:
            try:
                await db_service.store_jira_ticket(ticket, current_user.organization_id)
                stored_count += 1
            except Exception as e:
                print(f"⚠️  Failed to store ticket {ticket.get('key', 'unknown')}: {e}")
                continue
        
        print(f"💾 Stored {stored_count} tickets in database")
        
        # Index tickets in Qdrant for semantic search
        if qdrant_indexer:
            indexed_count = await qdrant_indexer.index_jira_tickets(
                current_user.organization_id,
                tickets
            )
            print(f"🔍 Indexed {indexed_count} tickets in Qdrant")
        else:
            print("⚠️  Qdrant indexer not available, skipping semantic indexing")
            indexed_count = 0
        
        # Log audit event
        await db_service.log_audit(
            current_user.id,
            current_user.organization_id,
            "jira_sync",
            "sync",
            {
                "project_key": request.project_key,
                "tickets_fetched": len(tickets),
                "tickets_stored": stored_count,
                "tickets_indexed": indexed_count
            }
        )
        
        return {
            "status": "success",
            "message": f"Successfully synced {stored_count} Jira tickets",
            "tickets_fetched": len(tickets),
            "tickets_stored": stored_count,
            "tickets_indexed": indexed_count,
            "project_key": request.project_key
        }
        
    except Exception as e:
        print(f"❌ Jira sync failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to sync Jira: {str(e)}")


@router.post("/repository")
async def sync_repository(
    request: RepositorySyncRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Sync Git repository for the authenticated user's organization.
    
    This endpoint connects to a Git repository, fetches commits and files,
    and indexes them for semantic search and analysis.
    """
    try:
        # Check quota
        if not await db_service.check_and_increment_quota(current_user.organization_id):
            raise HTTPException(status_code=429, detail="Monthly quota exceeded")
        
        # Initialize repository service
        repo_service = RepoService(
            provider=request.provider,
            access_token=request.access_token
        )
        
        # Parse repository info
        repo_info = repo_service.parse_repo_url(request.repo_url)
        print(f"🔄 Syncing repository: {repo_info['owner']}/{repo_info['repo']}")
        
        # Store repository metadata
        repo_data = await db_service.store_repository(
            org_id=current_user.organization_id,
            repo_url=request.repo_url,
            repo_name=repo_info['repo'],
            provider=request.provider,
            branch=request.branch
        )
        repo_id = repo_data['id']
        
        # Fetch commits
        print(f"📥 Fetching commits from {request.branch} branch...")
        commits = await repo_service.fetch_commits(
            repo_info['owner'],
            repo_info['repo'],
            branch=request.branch,
            limit=100  # Limit for demo purposes
        )
        print(f"📥 Fetched {len(commits)} commits")
        
        # Store commits in database
        stored_commits = 0
        for commit in commits:
            try:
                await db_service.store_commit(commit, repo_id, current_user.organization_id)
                stored_commits += 1
            except Exception as e:
                print(f"⚠️  Failed to store commit {commit.get('sha', 'unknown')}: {e}")
                continue
        
        print(f"💾 Stored {stored_commits} commits in database")
        
        # Fetch repository files
        print(f"📁 Fetching repository files...")
        files = await repo_service.fetch_files(
            repo_info['owner'],
            repo_info['repo'],
            branch=request.branch,
            max_files=50  # Limit for demo purposes
        )
        print(f"📁 Fetched {len(files)} files")
        
        # Store files in database
        stored_files = 0
        for file_data in files:
            try:
                await db_service.store_code_file(file_data, repo_id, current_user.organization_id)
                stored_files += 1
            except Exception as e:
                print(f"⚠️  Failed to store file {file_data.get('path', 'unknown')}: {e}")
                continue
        
        print(f"💾 Stored {stored_files} files in database")
        
        # Index in Qdrant for semantic search
        indexed_commits = 0
        indexed_files = 0
        
        if qdrant_indexer:
            # Index commits
            indexed_commits = await qdrant_indexer.index_commits(
                current_user.organization_id,
                commits
            )
            
            # Index files
            indexed_files = await qdrant_indexer.index_code_files(
                current_user.organization_id,
                files
            )
            
            print(f"🔍 Indexed {indexed_commits} commits and {indexed_files} files in Qdrant")
        else:
            print("⚠️  Qdrant indexer not available, skipping semantic indexing")
        
        # Log audit event
        await db_service.log_audit(
            current_user.id,
            current_user.organization_id,
            "repository_sync",
            "sync",
            {
                "repo_url": request.repo_url,
                "provider": request.provider,
                "branch": request.branch,
                "commits_stored": stored_commits,
                "files_stored": stored_files,
                "commits_indexed": indexed_commits,
                "files_indexed": indexed_files
            }
        )
        
        return {
            "status": "success",
            "message": f"Successfully synced repository {repo_info['repo']}",
            "repository": {
                "id": str(repo_id),
                "name": repo_info['repo'],
                "url": request.repo_url,
                "provider": request.provider,
                "branch": request.branch
            },
            "commits_stored": stored_commits,
            "files_stored": stored_files,
            "commits_indexed": indexed_commits,
            "files_indexed": indexed_files
        }
        
    except Exception as e:
        print(f"❌ Repository sync failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to sync repository: {str(e)}")