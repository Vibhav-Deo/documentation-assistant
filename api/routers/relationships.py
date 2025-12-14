"""
Relationships Router

Handles relationship and knowledge graph endpoints for analyzing connections between tickets, commits, developers, and files.
"""

from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from models import User
from services.shared.auth import get_current_user
from dependencies.container import get_relationship_service

router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.get("/ticket/{ticket_key}")
async def get_ticket_relationships(
    ticket_key: str,
    current_user: User = Depends(get_current_user),
    relationship_service = Depends(get_relationship_service)
):
    """
    Get comprehensive relationship data for a Jira ticket.
    
    Returns related commits, PRs, files, and developers.
    """
    try:
        if not relationship_service:
            raise HTTPException(status_code=503, detail="Relationship service not available")
        
        relationships = await relationship_service.get_ticket_relationships(
            ticket_key, current_user.organization_id
        )
        
        return {
            "ticket_key": ticket_key,
            "relationships": relationships
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/developer/{developer_email}")
async def get_developer_contributions(
    developer_email: str,
    current_user: User = Depends(get_current_user),
    relationship_service = Depends(get_relationship_service)
):
    """
    Get comprehensive contribution data for a developer.
    
    Returns commits, PRs, tickets, and activity timeline.
    """
    try:
        if not relationship_service:
            raise HTTPException(status_code=503, detail="Relationship service not available")
        
        contributions = await relationship_service.get_developer_contributions(
            developer_email, current_user.organization_id
        )
        
        return {
            "developer_email": developer_email,
            "contributions": contributions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file")
async def get_file_history(
    file_path: str,
    current_user: User = Depends(get_current_user),
    relationship_service = Depends(get_relationship_service)
):
    """
    Get change history and relationships for a specific file.
    
    Returns commits that modified the file, related tickets, and contributors.
    """
    try:
        if not relationship_service:
            raise HTTPException(status_code=503, detail="Relationship service not available")
        
        file_history = await relationship_service.get_file_history(
            file_path, current_user.organization_id
        )
        
        return {
            "file_path": file_path,
            "history": file_history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repository/{repo_id}/stats")
async def get_repository_stats(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    relationship_service = Depends(get_relationship_service)
):
    """
    Get comprehensive statistics for a repository.
    
    Returns commit stats, contributor info, file stats, and activity timeline.
    """
    try:
        if not relationship_service:
            raise HTTPException(status_code=503, detail="Relationship service not available")
        
        repo_stats = await relationship_service.get_repository_stats(
            repo_id, current_user.organization_id
        )
        
        return {
            "repository_id": repo_id,
            "stats": repo_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline/{ticket_key}")
async def get_feature_timeline(
    ticket_key: str,
    current_user: User = Depends(get_current_user),
    relationship_service = Depends(get_relationship_service)
):
    """
    Get chronological timeline for a feature/ticket.
    
    Returns timeline of ticket creation, commits, PRs, and completion.
    """
    try:
        if not relationship_service:
            raise HTTPException(status_code=503, detail="Relationship service not available")
        
        timeline = await relationship_service.get_feature_timeline(
            ticket_key, current_user.organization_id
        )
        
        return {
            "ticket_key": ticket_key,
            "timeline": timeline
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_relationships(
    query: str,
    relationship_type: str = QueryParam(default="all"),
    limit: int = QueryParam(default=20, le=100),
    current_user: User = Depends(get_current_user),
    relationship_service = Depends(get_relationship_service)
):
    """
    Search across all relationship data.
    
    Finds tickets, commits, files, and developers matching the query.
    """
    try:
        if not relationship_service:
            raise HTTPException(status_code=503, detail="Relationship service not available")
        
        search_results = await relationship_service.search_relationships(
            query, current_user.organization_id, relationship_type, limit
        )
        
        return {
            "query": query,
            "relationship_type": relationship_type,
            "results": search_results,
            "count": len(search_results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))