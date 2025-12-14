"""
Enterprise Confluence RAG API - Modular Architecture

This is the main FastAPI application with a clean, modular structure.
All endpoints are organized into domain-specific routers with centralized
error handling, dependency injection, and consistent response formatting.
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from middleware.error_handler import (
    ErrorHandlerMiddleware, 
    RequestLoggingMiddleware,
    create_error_handlers
)
from middleware.logging_config import setup_environment_logging
from middleware.monitoring import (
    MonitoringMiddleware,
    get_metrics_collector,
    get_health_checker,
    register_default_health_checks
)
from dependencies.container import service_lifespan
from routers import (
    auth, monitoring, sync, search, decisions, gaps, 
    admin, data, relationships, demo, ai, predictions, auto_tag
)

setup_environment_logging()
logger = logging.getLogger(__name__)
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with service initialization and monitoring."""
    logger.info("🚀 Starting Enterprise Confluence RAG API v2.0.0")
    
    try:
        async with service_lifespan() as container:
            app.state.container = container
            app.state.metrics_collector = get_metrics_collector()
            app.state.health_checker = get_health_checker()
            register_default_health_checks()
            logger.info("✅ All services initialized successfully")
            yield
    except Exception as e:
        logger.error("❌ Application startup failed", exc_info=True)
        raise
    finally:
        logger.info("🛑 Application shutting down gracefully")


app = FastAPI(
    title="Enterprise Confluence RAG API",
    version="2.0.0",
    description="Modular API for enterprise document analysis and AI-powered insights",
    lifespan=lifespan,
    debug=DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=True
)

app.add_middleware(
    MonitoringMiddleware,
    metrics_collector=get_metrics_collector(),
    health_checker=get_health_checker(),
    collect_detailed_metrics=True
)
app.add_middleware(
    ErrorHandlerMiddleware, 
    debug=DEBUG,
    log_request_body=DEBUG,
    slow_request_threshold=2.0,
    enable_metrics=True
)
if DEBUG or ENVIRONMENT in ["development", "staging"]:
    app.add_middleware(
        RequestLoggingMiddleware, 
        log_body=DEBUG,
        log_response=DEBUG,
        exclude_paths=["/health", "/metrics", "/favicon.ico"]
    )

exception_handlers = create_error_handlers()
for status_code, handler in exception_handlers.items():
    app.add_exception_handler(status_code, handler)
app.add_exception_handler(RequestValidationError, exception_handlers[422])
for router in [auth, monitoring, sync, search, decisions, gaps, admin, data, relationships, demo, ai, predictions, auto_tag]:
    app.include_router(router.router)


@app.get("/")
async def root():
    """API root endpoint with basic information."""
    from services.shared.response_formatter import ResponseFormatter
    
    return ResponseFormatter.success(
        data={
            "message": "Enterprise Confluence RAG API",
            "version": "2.0.0",
            "status": "running",
            "architecture": "modular",
            "environment": ENVIRONMENT,
            "debug_mode": DEBUG
        },
        message="API is running successfully"
    )


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    from services.shared.response_formatter import ResponseFormatter
    
    health_checker = get_health_checker()
    health_status = health_checker.get_health_status()
    
    return ResponseFormatter.success(
        data=health_status,
        message="Service is healthy"
    ) if health_status["status"] == "healthy" else ResponseFormatter.error(
        message="Service is unhealthy",
        error_code="UNHEALTHY",
        details=health_status,
        status_code=503
    )

@app.get("/metrics")
async def metrics():
    """Metrics endpoint for monitoring systems."""
    from services.shared.response_formatter import ResponseFormatter
    from middleware.error_handler import get_error_metrics
    
    metrics_collector = get_metrics_collector()
    return ResponseFormatter.success(
        data={
            "application_metrics": metrics_collector.get_all_metrics(),
            "error_metrics": get_error_metrics(),
            "timestamp": time.time()
        },
        message="Metrics retrieved successfully"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)