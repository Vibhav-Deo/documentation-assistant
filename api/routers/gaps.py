"""
Gap Detection Router

Handles gap detection endpoints for finding missing work, orphaned tickets, and undocumented features.
"""

from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from models import User
from services.shared.auth import get_current_user

router = APIRouter(prefix="/gaps", tags=["gap-detection"])


@router.get("/orphaned-tickets")
async def get_orphaned_tickets(
    days: int = QueryParam(default=90, ge=1, le=365),
    current_user: User = Depends(get_current_user)
):
    """
    Find orphaned tickets (tickets without related commits).
    
    Identifies tickets that have been created but have no associated
    development work (commits) within the specified time window.
    """
    try:
        from services.domain.analytics import gap_detector
        
        if not gap_detector:
            raise HTTPException(status_code=503, detail="Gap detector not available")
        
        orphaned_tickets = await gap_detector.find_orphaned_tickets(
            current_user.organization_id, days
        )
        
        return {
            "orphaned_tickets": orphaned_tickets,
            "count": len(orphaned_tickets),
            "time_window_days": days,
            "analysis_metadata": {
                "criteria": f"Tickets created in last {days} days with no related commits",
                "organization_id": current_user.organization_id
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/undocumented")
async def get_undocumented_features(
    current_user: User = Depends(get_current_user)
):
    """
    Find undocumented features (commits without ticket references).
    
    Identifies development work that was done but not properly
    tracked through tickets or documentation.
    """
    try:
        from services.domain.analytics import gap_detector
        
        if not gap_detector:
            raise HTTPException(status_code=503, detail="Gap detector not available")
        
        undocumented_commits = await gap_detector.find_undocumented_commits(
            current_user.organization_id
        )
        
        return {
            "undocumented_commits": undocumented_commits,
            "count": len(undocumented_commits),
            "analysis_metadata": {
                "criteria": "Commits without ticket references or documentation",
                "organization_id": current_user.organization_id
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/missing-decisions")
async def get_missing_decisions(
    current_user: User = Depends(get_current_user)
):
    """
    Find tickets that need decision analysis.
    
    Identifies tickets that have implementation but lack
    documented decision rationale.
    """
    try:
        from services.domain.analytics import gap_detector
        
        if not gap_detector:
            raise HTTPException(status_code=503, detail="Gap detector not available")
        
        missing_decisions = await gap_detector.find_missing_decisions(
            current_user.organization_id
        )
        
        return {
            "missing_decisions": missing_decisions,
            "count": len(missing_decisions),
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
    current_user: User = Depends(get_current_user)
):
    """
    Find stale work items (tickets not updated recently).
    
    Identifies tickets that are in progress but haven't been
    updated within the specified time window.
    """
    try:
        from services.domain.analytics import gap_detector
        
        if not gap_detector:
            raise HTTPException(status_code=503, detail="Gap detector not available")
        
        stale_tickets = await gap_detector.find_stale_tickets(
            current_user.organization_id, days
        )
        
        return {
            "stale_tickets": stale_tickets,
            "count": len(stale_tickets),
            "time_window_days": days,
            "analysis_metadata": {
                "criteria": f"In-progress tickets not updated in last {days} days",
                "organization_id": current_user.organization_id
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comprehensive")
async def get_comprehensive_gaps(
    current_user: User = Depends(get_current_user)
):
    """
    Get a comprehensive gap analysis across all categories.
    
    Provides a complete overview of all types of gaps in the
    development process.
    """
    try:
        from services.domain.analytics import gap_detector
        
        if not gap_detector:
            raise HTTPException(status_code=503, detail="Gap detector not available")
        
        # Get all types of gaps
        orphaned_tickets = await gap_detector.find_orphaned_tickets(
            current_user.organization_id, 90
        )
        
        undocumented_commits = await gap_detector.find_undocumented_commits(
            current_user.organization_id
        )
        
        missing_decisions = await gap_detector.find_missing_decisions(
            current_user.organization_id
        )
        
        stale_tickets = await gap_detector.find_stale_tickets(
            current_user.organization_id, 30
        )
        
        # Calculate summary statistics
        total_gaps = (
            len(orphaned_tickets) + 
            len(undocumented_commits) + 
            len(missing_decisions) + 
            len(stale_tickets)
        )
        
        return {
            "comprehensive_analysis": {
                "orphaned_tickets": {
                    "items": orphaned_tickets,
                    "count": len(orphaned_tickets)
                },
                "undocumented_commits": {
                    "items": undocumented_commits,
                    "count": len(undocumented_commits)
                },
                "missing_decisions": {
                    "items": missing_decisions,
                    "count": len(missing_decisions)
                },
                "stale_tickets": {
                    "items": stale_tickets,
                    "count": len(stale_tickets)
                }
            },
            "summary": {
                "total_gaps": total_gaps,
                "gap_categories": 4,
                "organization_id": current_user.organization_id,
                "analysis_timestamp": "now"  # Would use actual timestamp
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))