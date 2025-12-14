"""
Data Access Router

Handles basic data retrieval endpoints for Jira tickets, repositories, and relationships.
"""

from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from models import User
from services.shared.auth import get_current_user
from services.infrastructure.database import db_service

router = APIRouter(tags=["data"])


# Jira endpoints
@router.get("/jira/tickets")
async def get_jira_tickets(
    limit: int = QueryParam(default=100, le=500),
    offset: int = QueryParam(default=0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get Jira tickets for the organization"""
    try:
        tickets = await db_service.get_jira_tickets(
            current_user.organization_id,
            limit=limit,
            offset=offset
        )
        
        return {
            "tickets": tickets,
            "count": len(tickets),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Repository endpoints
@router.get("/repositories")
async def get_repositories(current_user: User = Depends(get_current_user)):
    """Get all synced repositories for the organization"""
    try:
        repositories = await db_service.get_repositories(current_user.organization_id)
        
        return {
            "repositories": repositories,
            "count": len(repositories)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repositories/{repo_id}/files")
async def get_repository_files(
    repo_id: str,
    limit: int = QueryParam(default=100, le=500),
    current_user: User = Depends(get_current_user)
):
    """Get files for a specific repository"""
    try:
        files = await db_service.get_repository_files(
            repo_id,
            current_user.organization_id,
            limit=limit
        )
        
        return {
            "repository_id": repo_id,
            "files": files,
            "count": len(files)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))