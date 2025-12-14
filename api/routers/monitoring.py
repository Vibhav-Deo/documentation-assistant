"""
Monitoring and Health Check Router

Handles system health, metrics, alerts, and monitoring endpoints.
Enhanced with comprehensive error handling, validation, and structured responses.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from models import User, UserRole
from services.shared.auth import require_role
from services.infrastructure.monitoring import monitoring_service
from services.infrastructure.database import db_service
from services.shared.response_formatter import ResponseFormatter
from middleware.validation import (
    validate_request,
    validate_response,
    log_performance,
    require_permissions
)

router = APIRouter(tags=["monitoring"])
logger = logging.getLogger(__name__)


@router.get("/health")
@validate_response(transform_response=True)
@log_performance(log_level=logging.DEBUG)
async def health_check():
    """Comprehensive health check endpoint with enhanced monitoring."""
    from middleware.monitoring import get_health_checker
    
    try:
        # Get basic health status
        health_checker = get_health_checker()
        health_status = health_checker.get_health_status()
        
        # Also get legacy monitoring service health if available
        try:
            legacy_health = monitoring_service.get_api_health()
            health_status["legacy_monitoring"] = legacy_health
        except Exception as e:
            logger.warning(f"Legacy monitoring service unavailable: {e}")
            health_status["legacy_monitoring"] = {"status": "unavailable", "error": str(e)}
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=ResponseFormatter.service_unavailable(
                service="Health Check",
                message="Health check system is unavailable"
            )
        )


@router.get("/metrics")
@validate_response(transform_response=True)
@log_performance(log_level=logging.DEBUG)
async def get_metrics():
    """Enhanced metrics endpoint with comprehensive system metrics."""
    from middleware.monitoring import get_metrics_collector
    from middleware.error_handler import get_error_metrics
    
    try:
        # Get new metrics
        metrics_collector = get_metrics_collector()
        application_metrics = metrics_collector.get_all_metrics()
        error_metrics = get_error_metrics()
        
        # Get legacy metrics if available
        try:
            legacy_metrics = monitoring_service.get_system_metrics()
        except Exception as e:
            logger.warning(f"Legacy metrics unavailable: {e}")
            legacy_metrics = {"status": "unavailable", "error": str(e)}
        
        return {
            "application_metrics": application_metrics,
            "error_metrics": error_metrics,
            "legacy_metrics": legacy_metrics,
            "metrics_format": "enhanced"
        }
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ResponseFormatter.error(
                message="Failed to collect system metrics",
                error_code="METRICS_ERROR",
                details={"error": str(e)}
            )
        )


@router.get("/monitoring/alerts")
@require_permissions(required_roles=[UserRole.ADMIN])
@validate_response(transform_response=True)
@log_performance(log_level=logging.INFO)
async def get_alerts(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Get system alerts with enhanced error handling (admin only)."""
    try:
        alerts = monitoring_service.get_alerts()
        
        return ResponseFormatter.success(
            data=alerts,
            message="System alerts retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve alerts: {e}", extra={
            "user_id": current_user.id,
            "organization_id": current_user.organization_id
        })
        raise HTTPException(
            status_code=500,
            detail=ResponseFormatter.error(
                message="Failed to retrieve system alerts",
                error_code="ALERTS_ERROR",
                details={"error": str(e)}
            )
        )


@router.get("/monitoring/requests")
@require_permissions(required_roles=[UserRole.ADMIN])
@validate_request(
    field_limits={"hours": {"min_value": 1, "max_value": 168}}  # 1 hour to 1 week
)
@validate_response(transform_response=True)
@log_performance(log_level=logging.INFO)
async def get_request_metrics(
    hours: int = 24, 
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Get request metrics with validation and enhanced error handling (admin only)."""
    try:
        # Get legacy request metrics
        legacy_metrics = monitoring_service.get_request_metrics(hours)
        
        # Get enhanced metrics from new system
        from middleware.monitoring import get_metrics_collector
        metrics_collector = get_metrics_collector()
        
        enhanced_metrics = {
            "request_duration_stats": metrics_collector.get_histogram_stats("http_request_duration_seconds"),
            "request_count": metrics_collector.get_counter("http_requests_total"),
            "error_count": metrics_collector.get_counter("http_requests_failed_total"),
            "slow_request_count": metrics_collector.get_counter("http_slow_requests_total")
        }
        
        return ResponseFormatter.success(
            data={
                "time_window_hours": hours,
                "legacy_metrics": legacy_metrics,
                "enhanced_metrics": enhanced_metrics
            },
            message=f"Request metrics for last {hours} hours retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve request metrics: {e}", extra={
            "user_id": current_user.id,
            "organization_id": current_user.organization_id,
            "hours": hours
        })
        raise HTTPException(
            status_code=500,
            detail=ResponseFormatter.error(
                message="Failed to retrieve request metrics",
                error_code="REQUEST_METRICS_ERROR",
                details={"error": str(e), "hours": hours}
            )
        )


@router.get("/monitoring/organization")
@require_permissions(required_roles=[UserRole.ADMIN], require_org_access=True)
@validate_response(transform_response=True)
@log_performance(log_level=logging.INFO)
async def get_organization_metrics(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Get organization-specific metrics with enhanced error handling (admin only)."""
    try:
        # Get organization data
        org_data = await db_service.get_organization(current_user.organization_id)
        if not org_data:
            raise HTTPException(
                status_code=404,
                detail=ResponseFormatter.not_found(
                    resource="Organization",
                    identifier=current_user.organization_id
                )
            )
        
        # Get organization users and their usage
        users = await db_service.get_organization_users(current_user.organization_id)
        total_users = len(users)
        
        # Get usage stats from audit logs
        usage_stats = await db_service.get_organization_usage_stats(current_user.organization_id)
        
        # Sanitize data for response
        sanitized_org = {k: str(v) if k == 'id' else v for k, v in org_data.items()}
        sanitized_users = [
            {k: str(v) if k in ['id', 'organization_id'] else v for k, v in user.items()} 
            for user in users
        ]
        
        return ResponseFormatter.success(
            data={
                "organization": sanitized_org,
                "total_users": total_users,
                "users": sanitized_users,
                "usage_stats": usage_stats
            },
            message="Organization metrics retrieved successfully"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve organization metrics: {e}", extra={
            "user_id": current_user.id,
            "organization_id": current_user.organization_id
        })
        raise HTTPException(
            status_code=500,
            detail=ResponseFormatter.error(
                message="Failed to retrieve organization metrics",
                error_code="ORG_METRICS_ERROR",
                details={"error": str(e)}
            )
        )


@router.get("/analytics")
@validate_response(transform_response=True)
@log_performance(log_level=logging.INFO)
async def get_analytics():
    """Get comprehensive analytics with enhanced error handling."""
    try:
        from dependencies.container import get_analytics_service
        analytics_service = await get_analytics_service()
        
        # Collect analytics data
        analytics_data = {
            "document_stats": analytics_service.get_document_stats(),
            "usage_metrics": analytics_service.get_usage_metrics(),
            "popular_queries": analytics_service.get_popular_queries(),
            "performance_insights": analytics_service.get_performance_insights()
        }
        
        return ResponseFormatter.success(
            data=analytics_data,
            message="Analytics data retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=ResponseFormatter.error(
                message="Failed to retrieve analytics data",
                error_code="ANALYTICS_ERROR",
                details={"error": str(e)}
            )
        )


# New enhanced endpoints
@router.get("/health/detailed")
@validate_response(transform_response=True)
@log_performance(log_level=logging.INFO)
async def detailed_health_check():
    """Detailed health check that runs all registered checks."""
    from middleware.monitoring import get_health_checker
    
    try:
        health_checker = get_health_checker()
        health_results = await health_checker.run_all_checks()
        
        if health_results["status"] == "healthy":
            return ResponseFormatter.success(
                data=health_results,
                message="All health checks passed"
            )
        else:
            return ResponseFormatter.error(
                message="Some health checks failed",
                error_code="HEALTH_CHECK_FAILED",
                details=health_results,
                status_code=503
            )
    except Exception as e:
        logger.error(f"Health check execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ResponseFormatter.error(
                message="Health check execution failed",
                error_code="HEALTH_CHECK_ERROR",
                details={"error": str(e)}
            )
        )


@router.get("/monitoring/errors")
@require_permissions(required_roles=[UserRole.ADMIN])
@validate_response(transform_response=True)
@log_performance(log_level=logging.INFO)
async def get_error_metrics(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Get detailed error metrics and statistics (admin only)."""
    try:
        from middleware.error_handler import get_error_metrics
        
        error_metrics = get_error_metrics()
        
        return ResponseFormatter.success(
            data=error_metrics,
            message="Error metrics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve error metrics: {e}", extra={
            "user_id": current_user.id,
            "organization_id": current_user.organization_id
        })
        raise HTTPException(
            status_code=500,
            detail=ResponseFormatter.error(
                message="Failed to retrieve error metrics",
                error_code="ERROR_METRICS_ERROR",
                details={"error": str(e)}
            )
        )