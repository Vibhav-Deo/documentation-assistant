"""
Gap Detection Router

Handles gap detection endpoints for finding missing work, orphaned tickets, and undocumented features.
"""

from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from models import User
from services.shared.auth import get_current_user
from dependencies.container import get_gap_detector

router = APIRouter(prefix="/gaps", tags=["gap-detection"])


@router.get("/orphaned-tickets")
async def get_orphaned_tickets(
    days: int = QueryParam(default=90, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    gap_detector = Depends(get_gap_detector)
):
    """
    Find orphaned tickets (tickets without related commits).
    
    Identifies tickets that have been created but have no associated
    development work (commits) within the specified time window.
    """
    try:
        result = await gap_detector.find_orphaned_tickets(
            current_user.organization_id, days
        )
        
        return {
            "orphaned_tickets": result.get("tickets", []),
            "count": result.get("total_orphaned", 0),
            "time_window_days": days,
            "statistics": {
                "by_status": result.get("by_status", {}),
                "by_priority": result.get("by_priority", {}),
                "by_assignee": result.get("by_assignee", {})
            },
            "analysis_metadata": {
                "criteria": f"Tickets created in last {days} days with no related commits",
                "organization_id": current_user.organization_id
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/undocumented")
async def get_undocumented_features(
    current_user: User = Depends(get_current_user),
    gap_detector = Depends(get_gap_detector)
):
    """
    Find undocumented features (commits without ticket references).
    
    Identifies development work that was done but not properly
    tracked through tickets or documentation.
    """
    try:
        result = await gap_detector.find_undocumented_features(
            current_user.organization_id
        )
        
        return {
            "undocumented_commits": result.get("commits", []),
            "count": result.get("total_undocumented", 0),
            "statistics": {
                "by_author": result.get("by_author", {}),
                "by_repository": result.get("by_repository", {}),
                "total_code_changes": result.get("total_code_changes", 0)
            },
            "analysis_metadata": {
                "criteria": "Commits without ticket references or documentation",
                "organization_id": current_user.organization_id
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/missing-decisions")
async def get_missing_decisions(
    current_user: User = Depends(get_current_user),
    gap_detector = Depends(get_gap_detector)
):
    """
    Find tickets that need decision analysis.
    
    Identifies tickets that have implementation but lack
    documented decision rationale.
    """
    try:
        result = await gap_detector.find_missing_decisions(
            current_user.organization_id
        )
        
        return {
            "missing_decisions": result.get("tickets", []),
            "count": result.get("total_missing_decisions", 0),
            "statistics": {
                "by_issue_type": result.get("by_issue_type", {})
            },
            "analysis_metadata": {
                "criteria": "Tickets with implementation but no decision analysis",
                "organization_id": current_user.organization_id
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stale-work")
async def get_stale_work(
    days: int = QueryParam(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    gap_detector = Depends(get_gap_detector)
):
    """
    Find stale work items (tickets not updated recently).
    
    Identifies tickets that are in progress but haven't been
    updated within the specified time window.
    """
    try:
        result = await gap_detector.find_stale_work(
            current_user.organization_id, days
        )
        
        return {
            "stale_tickets": result.get("tickets", []),
            "count": result.get("total_stale", 0),
            "time_window_days": days,
            "statistics": {
                "by_status": result.get("by_status", {}),
                "by_assignee": result.get("by_assignee", {})
            },
            "analysis_metadata": {
                "criteria": f"In-progress tickets not updated in last {days} days",
                "organization_id": current_user.organization_id
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comprehensive")
async def get_comprehensive_gaps(
    current_user: User = Depends(get_current_user),
    gap_detector = Depends(get_gap_detector)
):
    """
    Get a comprehensive gap analysis across all categories.
    
    Provides a complete overview of all types of gaps in the
    development process.
    """
    try:
        # Get comprehensive gaps from detector
        result = await gap_detector.get_comprehensive_gaps(
            current_user.organization_id
        )
        
        return {
            "comprehensive_analysis": {
                "orphaned_tickets": {
                    "items": result["orphaned_tickets"].get("tickets", []),
                    "count": result["orphaned_tickets"].get("total_orphaned", 0),
                    "statistics": {
                        "by_status": result["orphaned_tickets"].get("by_status", {}),
                        "by_priority": result["orphaned_tickets"].get("by_priority", {})
                    }
                },
                "undocumented_commits": {
                    "items": result["undocumented_features"].get("commits", []),
                    "count": result["undocumented_features"].get("total_undocumented", 0),
                    "statistics": {
                        "by_author": result["undocumented_features"].get("by_author", {}),
                        "by_repository": result["undocumented_features"].get("by_repository", {})
                    }
                },
                "missing_decisions": {
                    "items": result["missing_decisions"].get("tickets", []),
                    "count": result["missing_decisions"].get("total_missing_decisions", 0),
                    "statistics": {
                        "by_issue_type": result["missing_decisions"].get("by_issue_type", {})
                    }
                },
                "stale_tickets": {
                    "items": result["stale_work"].get("tickets", []),
                    "count": result["stale_work"].get("total_stale", 0),
                    "statistics": {
                        "by_status": result["stale_work"].get("by_status", {}),
                        "by_assignee": result["stale_work"].get("by_assignee", {})
                    }
                }
            },
            "summary": result.get("summary", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))