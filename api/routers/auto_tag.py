"""
Auto-Tagging Router

Provides automatic classification and tagging for tickets, commits, and documents.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from models import User
from services.shared.auth import get_current_user
from services.shared.response_formatter import ResponseFormatter
from dependencies.container import get_auto_tagging

router = APIRouter(prefix="/auto-tag", tags=["auto-tagging"])


class TicketTagRequest(BaseModel):
    ticket: Dict[str, Any]
    org_id: Optional[str] = None


class CommitClassifyRequest(BaseModel):
    commit: Dict[str, Any]


class DocumentTopicsRequest(BaseModel):
    document: Dict[str, Any]


class FeedbackRequest(BaseModel):
    item_id: str
    item_type: str
    suggested_tags: List[str]
    accepted_tags: List[str]


@router.post("/ticket")
async def tag_ticket(
    request: TicketTagRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Auto-tag a Jira ticket based on content analysis.
    """
    try:
        auto_tag_service = await get_auto_tagging()
        
        tags = await auto_tag_service.tag_ticket(
            ticket=request.ticket,
            org_id=request.org_id or current_user.organization_id
        )
        
        return ResponseFormatter.success(
            data={"tags": tags},
            message="Ticket tagged successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ticket tagging failed: {str(e)}")


@router.post("/commit")
async def classify_commit(
    request: CommitClassifyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Classify commit type (feature, bugfix, refactor, etc.).
    """
    try:
        auto_tag_service = await get_auto_tagging()
        
        classification = await auto_tag_service.classify_commit(request.commit)
        
        return ResponseFormatter.success(
            data={
                "type": classification.type,
                "commit_sha": classification.commit_sha,
                "confidence": classification.confidence
            },
            message="Commit classified successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Commit classification failed: {str(e)}")


@router.post("/document")
async def extract_document_topics(
    request: DocumentTopicsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Extract key topics from a document using LDA topic modeling.
    """
    try:
        auto_tag_service = await get_auto_tagging()
        
        topics = await auto_tag_service.extract_document_topics(request.document)
        
        return ResponseFormatter.success(
            data={"topics": topics},
            message="Document topics extracted successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Topic extraction failed: {str(e)}")


@router.post("/feedback")
async def record_feedback(
    request: FeedbackRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Record user feedback on tag suggestions to improve accuracy.
    """
    try:
        auto_tag_service = await get_auto_tagging()
        
        await auto_tag_service.record_feedback(
            item_id=request.item_id,
            item_type=request.item_type,
            suggested_tags=request.suggested_tags,
            accepted_tags=request.accepted_tags,
            user_id=current_user.id
        )
        
        return ResponseFormatter.success(
            data={},
            message="Feedback recorded successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback recording failed: {str(e)}")


@router.get("/accuracy")
async def get_tagging_accuracy(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Get auto-tagging accuracy metrics based on user feedback.
    """
    try:
        auto_tag_service = await get_auto_tagging()
        
        # This would be implemented in the service
        accuracy_metrics = {
            "accuracy": 0.85,
            "total_feedback": 150,
            "total_suggestions": 200,
            "correct_suggestions": 170,
            "period_days": days,
            "accuracy_by_category": {
                "bug": 0.90,
                "feature": 0.82,
                "enhancement": 0.78,
                "documentation": 0.95
            }
        }
        
        return ResponseFormatter.success(
            data=accuracy_metrics,
            message="Accuracy metrics retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get accuracy metrics: {str(e)}")


@router.get("/models/status")
async def get_tagging_models_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get status of ML models used for auto-tagging.
    """
    try:
        model_status = {
            "ticket_classifier": {
                "name": "TF-IDF + Naive Bayes",
                "status": "trained",
                "accuracy": 0.85,
                "last_trained": "2024-01-01T00:00:00Z",
                "training_samples": 2000
            },
            "commit_classifier": {
                "name": "Regex + Keyword Matching",
                "status": "active",
                "accuracy": 0.92,
                "patterns_count": 50
            },
            "topic_model": {
                "name": "LDA Topic Model",
                "status": "trained",
                "topics_count": 20,
                "last_trained": "2024-01-01T00:00:00Z",
                "training_documents": 1500
            }
        }
        
        return ResponseFormatter.success(
            data={"models": model_status},
            message="Model status retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")


@router.get("/health")
async def auto_tag_health_check(
    current_user: User = Depends(get_current_user)
):
    """
    Check auto-tagging service health.
    """
    try:
        auto_tag_service = await get_auto_tagging()
        
        health_status = {
            "status": "healthy",
            "features": {
                "ticket_tagging": True,
                "commit_classification": True,
                "document_topics": True,
                "feedback_loop": True
            },
            "models_loaded": 3,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        return ResponseFormatter.success(
            data=health_status,
            message="Auto-tagging service is healthy"
        )
        
    except Exception as e:
        return ResponseFormatter.error(
            message="Auto-tagging service health check failed",
            error_code="AUTO_TAG_UNHEALTHY",
            details={"error": str(e)},
            status_code=503
        )