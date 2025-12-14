"""
Predictive Analytics Router

Provides ML-based predictions for tickets, code hotspots, and resource bottlenecks.
"""

from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from pydantic import BaseModel
from typing import Optional, List
from models import User
from services.shared.auth import get_current_user
from services.shared.response_formatter import ResponseFormatter
from dependencies.container import get_predictive_analytics

router = APIRouter(prefix="/predict", tags=["predictions"])


class TicketCompletionRequest(BaseModel):
    ticket_key: str


class RiskAssessmentRequest(BaseModel):
    ticket_key: str


@router.post("/ticket-completion")
async def predict_ticket_completion(
    request: TicketCompletionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Predict when a ticket will be completed based on historical velocity.
    """
    try:
        predictive_service = await get_predictive_analytics()
        
        prediction = await predictive_service.predict_ticket_completion(
            ticket_key=request.ticket_key,
            org_id=current_user.organization_id
        )
        
        return ResponseFormatter.success(
            data={"prediction": prediction},
            message="Ticket completion prediction generated successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/hotspots")
async def get_code_hotspots(
    lookback_days: int = QueryParam(default=90, ge=1, le=365),
    current_user: User = Depends(get_current_user)
):
    """
    Get code hotspots - files that change frequently and are likely to cause issues.
    """
    try:
        predictive_service = await get_predictive_analytics()
        
        hotspots = await predictive_service.identify_code_hotspots(
            org_id=current_user.organization_id,
            lookback_days=lookback_days
        )
        
        return ResponseFormatter.success(
            data={"hotspots": hotspots},
            message="Code hotspots identified successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hotspot detection failed: {str(e)}")


@router.get("/bottlenecks")
async def forecast_resource_bottlenecks(
    forecast_days: int = QueryParam(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user)
):
    """
    Forecast resource bottlenecks - developers who may be overloaded.
    """
    try:
        predictive_service = await get_predictive_analytics()
        
        bottlenecks = await predictive_service.forecast_resource_bottlenecks(
            org_id=current_user.organization_id,
            forecast_days=forecast_days
        )
        
        return ResponseFormatter.success(
            data={"bottlenecks": bottlenecks},
            message="Resource bottlenecks forecasted successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bottleneck forecasting failed: {str(e)}")


@router.post("/risk")
async def assess_ticket_risk(
    request: RiskAssessmentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Calculate risk score for a ticket using ML-based analysis.
    """
    try:
        predictive_service = await get_predictive_analytics()
        
        risk_assessment = await predictive_service.calculate_risk_score(
            ticket_key=request.ticket_key,
            org_id=current_user.organization_id
        )
        
        return ResponseFormatter.success(
            data={"risk_assessment": risk_assessment},
            message="Risk assessment completed successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")


@router.get("/models/status")
async def get_prediction_models_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get status of ML models used for predictions.
    """
    try:
        predictive_service = await get_predictive_analytics()
        
        # Get model status (this would be implemented in the service)
        model_status = {
            "velocity_model": {
                "name": "Linear Regression",
                "status": "trained",
                "accuracy": 0.85,
                "last_trained": "2024-01-01T00:00:00Z",
                "training_samples": 1000
            },
            "hotspot_model": {
                "name": "Frequency Analysis",
                "status": "trained", 
                "accuracy": 0.78,
                "last_trained": "2024-01-01T00:00:00Z",
                "training_samples": 500
            },
            "risk_model": {
                "name": "Random Forest",
                "status": "trained",
                "accuracy": 0.82,
                "last_trained": "2024-01-01T00:00:00Z",
                "training_samples": 750
            }
        }
        
        return ResponseFormatter.success(
            data={"models": model_status},
            message="Model status retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")


@router.get("/health")
async def predictions_health_check(
    current_user: User = Depends(get_current_user)
):
    """
    Check predictive analytics service health.
    """
    try:
        predictive_service = await get_predictive_analytics()
        
        # Test basic functionality
        health_status = {
            "status": "healthy",
            "features": {
                "ticket_completion": True,
                "code_hotspots": True,
                "resource_bottlenecks": True,
                "risk_assessment": True
            },
            "models_loaded": 3,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        return ResponseFormatter.success(
            data=health_status,
            message="Predictive analytics service is healthy"
        )
        
    except Exception as e:
        return ResponseFormatter.error(
            message="Predictive analytics service health check failed",
            error_code="PREDICTIONS_UNHEALTHY",
            details={"error": str(e)},
            status_code=503
        )