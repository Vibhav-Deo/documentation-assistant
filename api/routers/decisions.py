"""
Decision Analysis Router

Handles decision extraction, analysis, and management endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from models import User
from services.shared.auth import get_current_user
from services.infrastructure.database import db_service

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post("/analyze/{ticket_key}")
async def analyze_ticket_decision(
    ticket_key: str,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze a Jira ticket to extract decision rationale.
    
    Uses the Intent Analyzer to extract decisions from tickets,
    related commits, PRs, and documentation.
    """
    try:
        # Get the intent analyzer
        from dependencies.container import get_unified_intent_analyzer
        intent_analyzer = await get_unified_intent_analyzer()
        
        if not intent_analyzer:
            raise HTTPException(status_code=503, detail="Intent analyzer not available")
        
        # Get ticket data
        ticket = await db_service.get_jira_ticket_by_key(ticket_key, current_user.organization_id)
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_key} not found")
        
        # Get related commits
        commits = await db_service.get_commits_for_ticket(ticket_key, current_user.organization_id)
        
        # Get related PRs (if method exists, otherwise empty list)
        try:
            prs = await db_service.get_prs_for_ticket(ticket_key, current_user.organization_id)
        except AttributeError:
            prs = []
        
        # Get related documents (placeholder - would need document linking)
        docs = []
        
        # Extract decision rationale
        decision = await intent_analyzer.extract_decision_rationale(
            ticket, commits, prs, docs
        )
        
        return {
            "ticket_key": ticket_key,
            "decision": decision,
            "analysis_metadata": {
                "related_commits": len(commits),
                "related_prs": len(prs),
                "related_docs": len(docs)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{decision_id}")
async def get_decision(
    decision_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific decision by ID"""
    try:
        decision = await db_service.get_decision(decision_id, current_user.organization_id)
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        return decision
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticket/{ticket_key}")
async def get_decisions_by_ticket(
    ticket_key: str,
    current_user: User = Depends(get_current_user)
):
    """Get all decisions related to a specific ticket"""
    try:
        decisions = await db_service.get_decisions_by_ticket(ticket_key, current_user.organization_id)
        
        return {
            "ticket_key": ticket_key,
            "decisions": decisions,
            "count": len(decisions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_decisions(
    query: str,
    limit: int = QueryParam(default=10, le=50),
    current_user: User = Depends(get_current_user)
):
    """Search decisions using full-text search"""
    try:
        decisions = await db_service.search_decisions(query, current_user.organization_id, limit)
        
        return {
            "query": query,
            "decisions": decisions,
            "count": len(decisions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_decisions(
    limit: int = QueryParam(default=100, le=500),
    offset: int = QueryParam(default=0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """List all decisions for the organization"""
    try:
        decisions = await db_service.get_all_decisions(
            current_user.organization_id,
            limit=limit
        )
        
        return {
            "decisions": decisions,
            "count": len(decisions),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Enhanced decision analysis endpoints
@router.post("/analyze-enhanced/{ticket_key}")
async def analyze_ticket_decision_enhanced(
    ticket_key: str,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze a Jira ticket using enhanced decision extraction with confidence scoring.
    
    Uses the Enhanced Intent Analyzer to extract decisions with confidence scores
    and conflict detection.
    """
    try:
        # Get the unified intent analyzer (using enhanced mode)
        from dependencies.container import get_unified_intent_analyzer
        from dataclasses import asdict
        unified_analyzer = await get_unified_intent_analyzer()
        
        # Analyze ticket decisions using enhanced mode
        enhanced_decision = await unified_analyzer.analyze_ticket_decisions(
            ticket_key=ticket_key,
            org_id=current_user.organization_id,
            user_org_id=current_user.organization_id,
            enhanced=True  # Use enhanced mode for confidence scoring and conflict detection
        )
        
        # Convert dataclass to dict for JSON serialization
        decision_dict = asdict(enhanced_decision)
        
        return {
            "decision_id": decision_dict.get("decision_id", ""),
            "ticket_key": ticket_key,
            "enhanced_decision": decision_dict,
            "conflicts_detected": decision_dict.get("conflicts_detected", []),
            "overall_confidence": decision_dict.get("overall_confidence", 0.0),
            "analysis_metadata": {
                "related_commits": len(decision_dict.get("implementation_commits", [])),
                "related_prs": len(decision_dict.get("related_prs", [])),
                "related_docs": 0,
                "conflicts_count": len(decision_dict.get("conflicts_detected", []))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enhanced/search")
async def search_enhanced_decisions(
    query: str,
    limit: int = QueryParam(default=10, le=50),
    current_user: User = Depends(get_current_user)
):
    """Search enhanced decisions with full-text search"""
    try:
        decisions = await db_service.search_enhanced_decisions(
            query, current_user.organization_id, limit
        )
        
        return {
            "query": query,
            "decisions": decisions,
            "count": len(decisions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enhanced/conflicts")
async def get_decision_conflicts(
    current_user: User = Depends(get_current_user)
):
    """Get all decisions with detected conflicts"""
    try:
        conflicts = await db_service.get_decisions_with_conflicts(current_user.organization_id)
        
        return {
            "conflicts": conflicts,
            "count": len(conflicts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enhanced/low-confidence")
async def get_low_confidence_decisions(
    confidence_threshold: float = QueryParam(default=0.6, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user)
):
    """Get decisions with low confidence scores for review"""
    try:
        decisions = await db_service.get_low_confidence_decisions(
            current_user.organization_id, confidence_threshold
        )
        
        return {
            "confidence_threshold": confidence_threshold,
            "decisions": decisions,
            "count": len(decisions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))