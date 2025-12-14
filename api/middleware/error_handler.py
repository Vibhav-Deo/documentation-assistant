"""
Centralized Error Handling Middleware

Provides consistent error handling across all API endpoints,
eliminating the repetitive try-catch blocks found throughout the codebase.

Enhanced with comprehensive logging, monitoring integration, and
structured error categorization for better observability.
"""

import logging
import traceback
import time
import json
import uuid
from typing import Callable, Dict, Any, Optional, List
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from services.shared.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)

# Error metrics for monitoring (in production, use proper metrics system)
error_metrics = {
    "total_errors": 0,
    "error_categories": {},
    "error_rates": {},
    "slow_requests": 0
}


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware for centralized error handling and logging.
    
    Features:
    - Consistent error response format using ResponseFormatter
    - Comprehensive error logging with structured data
    - Request/response timing and performance monitoring
    - Advanced error categorization and metrics
    - Security-aware error reporting
    - Integration with monitoring systems
    - Request correlation IDs for tracing
    """
    
    def __init__(
        self, 
        app, 
        debug: bool = False,
        log_request_body: bool = False,
        slow_request_threshold: float = 2.0,
        enable_metrics: bool = True
    ):
        super().__init__(app)
        self.debug = debug
        self.log_request_body = log_request_body
        self.slow_request_threshold = slow_request_threshold
        self.enable_metrics = enable_metrics
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with comprehensive error handling and monitoring."""
        start_time = time.time()
        correlation_id = str(uuid.uuid4())
        
        # Add correlation ID to request state
        request.state.correlation_id = correlation_id
        
        # Log request start with structured data
        request_data = await self._extract_request_data(request, correlation_id)
        logger.info("Request started", extra=request_data)
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log successful requests with structured data
            success_data = {
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "processing_time_seconds": round(process_time, 3),
                "user_agent": request.headers.get("user-agent", "unknown"),
                "client_ip": self._get_client_ip(request),
                "response_size": response.headers.get("content-length", "unknown")
            }
            
            # Check for slow requests
            if process_time > self.slow_request_threshold:
                success_data["slow_request"] = True
                logger.warning("Slow request detected", extra=success_data)
                if self.enable_metrics:
                    error_metrics["slow_requests"] += 1
            else:
                logger.info("Request completed successfully", extra=success_data)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            return await self._handle_http_exception(request, e, start_time, correlation_id)
            
        except Exception as e:
            # Handle unexpected exceptions
            return await self._handle_unexpected_exception(request, e, start_time, correlation_id)
    
    async def _handle_http_exception(
        self, 
        request: Request, 
        exc: HTTPException, 
        start_time: float,
        correlation_id: str
    ) -> JSONResponse:
        """Handle FastAPI HTTP exceptions with enhanced logging."""
        process_time = time.time() - start_time
        
        # Create structured log data
        error_data = {
            "correlation_id": correlation_id,
            "error_type": "http_exception",
            "method": request.method,
            "path": request.url.path,
            "status_code": exc.status_code,
            "error_message": str(exc.detail),
            "processing_time_seconds": round(process_time, 3),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "client_ip": self._get_client_ip(request),
            "query_params": dict(request.query_params)
        }
        
        # Log the HTTP exception with structured data
        if exc.status_code >= 500:
            logger.error("HTTP server error", extra=error_data)
        elif exc.status_code >= 400:
            logger.warning("HTTP client error", extra=error_data)
        else:
            logger.info("HTTP exception", extra=error_data)
        
        # Update metrics
        if self.enable_metrics:
            error_metrics["total_errors"] += 1
            status_category = f"{exc.status_code // 100}xx"
            error_metrics["error_categories"][status_category] = (
                error_metrics["error_categories"].get(status_category, 0) + 1
            )
        
        # Create consistent error response using ResponseFormatter
        if exc.status_code == 400:
            error_response = ResponseFormatter.error(
                message=str(exc.detail),
                error_code="BAD_REQUEST",
                status_code=400
            )
        elif exc.status_code == 401:
            error_response = ResponseFormatter.unauthorized(str(exc.detail))
        elif exc.status_code == 403:
            error_response = ResponseFormatter.forbidden(str(exc.detail))
        elif exc.status_code == 404:
            error_response = ResponseFormatter.not_found("Resource", str(exc.detail))
        elif exc.status_code == 422:
            error_response = ResponseFormatter.validation_error(
                field_errors={"general": [str(exc.detail)]},
                message="Validation failed"
            )
        elif exc.status_code == 429:
            error_response = ResponseFormatter.rate_limited()
        else:
            error_response = ResponseFormatter.error(
                message=str(exc.detail),
                error_code=f"HTTP_{exc.status_code}",
                status_code=exc.status_code
            )
        
        # Add correlation ID and debug information
        error_response["correlation_id"] = correlation_id
        
        if self.debug:
            error_response["debug"] = {
                "headers": dict(exc.headers) if exc.headers else None,
                "processing_time_seconds": round(process_time, 3),
                "request_data": await self._extract_request_data(request, correlation_id)
            }
        
        response = JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    
    async def _handle_unexpected_exception(
        self, 
        request: Request, 
        exc: Exception, 
        start_time: float,
        correlation_id: str
    ) -> JSONResponse:
        """Handle unexpected exceptions with comprehensive logging and monitoring."""
        process_time = time.time() - start_time
        
        # Determine error category and severity
        error_category = self._categorize_error(exc)
        error_severity = self._determine_error_severity(exc)
        
        # Create structured log data
        error_data = {
            "correlation_id": correlation_id,
            "error_type": "unexpected_exception",
            "exception_class": type(exc).__name__,
            "exception_message": str(exc),
            "error_category": error_category,
            "error_severity": error_severity,
            "method": request.method,
            "path": request.url.path,
            "processing_time_seconds": round(process_time, 3),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "client_ip": self._get_client_ip(request),
            "query_params": dict(request.query_params),
            "traceback": traceback.format_exc() if self.debug else None
        }
        
        # Log the unexpected exception with full context
        if error_severity == "critical":
            logger.critical("Critical system error", extra=error_data, exc_info=True)
        elif error_severity == "high":
            logger.error("High severity error", extra=error_data, exc_info=True)
        else:
            logger.error("Unexpected exception", extra=error_data, exc_info=True)
        
        # Update metrics
        if self.enable_metrics:
            error_metrics["total_errors"] += 1
            error_metrics["error_categories"][error_category] = (
                error_metrics["error_categories"].get(error_category, 0) + 1
            )
        
        # Create user-friendly error message based on category
        user_message = self._get_user_friendly_message(error_category, exc)
        
        # Create error response using ResponseFormatter
        if error_category == "database_error":
            error_response = ResponseFormatter.service_unavailable(
                service="Database",
                message="Database service is temporarily unavailable"
            )
        elif error_category == "ai_service_error":
            error_response = ResponseFormatter.service_unavailable(
                service="AI",
                message="AI service is temporarily unavailable"
            )
        elif error_category == "network_error":
            error_response = ResponseFormatter.service_unavailable(
                service="External API",
                message="External service is temporarily unavailable"
            )
        else:
            error_response = ResponseFormatter.error(
                message=user_message,
                error_code="INTERNAL_SERVER_ERROR",
                details={"category": error_category} if self.debug else None,
                status_code=500
            )
        
        # Add correlation ID and debug information
        error_response["correlation_id"] = correlation_id
        
        if self.debug:
            error_response["debug"] = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
                "processing_time_seconds": round(process_time, 3),
                "error_category": error_category,
                "error_severity": error_severity,
                "request_data": await self._extract_request_data(request, correlation_id)
            }
        
        response = JSONResponse(
            status_code=500,
            content=error_response
        )
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    
    def _categorize_error(self, exc: Exception) -> str:
        """
        Enhanced error categorization for better debugging and monitoring.
        
        Args:
            exc: The exception to categorize
            
        Returns:
            Error category string
        """
        exc_type = type(exc).__name__.lower()
        exc_message = str(exc).lower()
        
        # Database errors
        if any(keyword in exc_type for keyword in [
            'connection', 'database', 'sql', 'postgres', 'asyncpg', 'psycopg'
        ]) or any(keyword in exc_message for keyword in [
            'connection refused', 'database', 'relation does not exist', 'syntax error'
        ]):
            return "database_error"
        
        # Network/HTTP errors
        if any(keyword in exc_type for keyword in [
            'connection', 'timeout', 'network', 'http', 'aiohttp', 'requests'
        ]) or any(keyword in exc_message for keyword in [
            'connection timeout', 'network unreachable', 'connection refused'
        ]):
            return "network_error"
        
        # Validation errors
        if any(keyword in exc_type for keyword in [
            'validation', 'pydantic', 'schema', 'value'
        ]) or 'validation' in exc_message:
            return "validation_error"
        
        # Authentication/Authorization errors
        if any(keyword in exc_message for keyword in [
            'auth', 'token', 'permission', 'unauthorized', 'forbidden', 'jwt'
        ]) or any(keyword in exc_type for keyword in ['auth', 'permission']):
            return "auth_error"
        
        # AI/ML service errors
        if any(keyword in exc_message for keyword in [
            'ollama', 'qdrant', 'embedding', 'model', 'openai', 'mistral'
        ]) or any(keyword in exc_type for keyword in ['ai', 'model']):
            return "ai_service_error"
        
        # File system errors
        if any(keyword in exc_type for keyword in [
            'file', 'io', 'permission', 'os'
        ]) or any(keyword in exc_message for keyword in [
            'no such file', 'permission denied', 'file not found'
        ]):
            return "filesystem_error"
        
        # Import/module errors
        if any(keyword in exc_type for keyword in [
            'import', 'module', 'attribute'
        ]) or any(keyword in exc_message for keyword in [
            'no module named', 'cannot import', 'has no attribute'
        ]):
            return "import_error"
        
        # Memory errors
        if any(keyword in exc_type for keyword in ['memory', 'overflow']):
            return "memory_error"
        
        # Concurrency errors
        if any(keyword in exc_type for keyword in ['lock', 'deadlock', 'race']):
            return "concurrency_error"
        
        # Configuration errors
        if any(keyword in exc_message for keyword in [
            'config', 'environment', 'setting', 'missing'
        ]):
            return "configuration_error"
        
        # Rate limiting errors
        if any(keyword in exc_message for keyword in ['rate limit', 'quota', 'throttle']):
            return "rate_limit_error"
        
        # Default category
        return "unknown_error"
    
    def _determine_error_severity(self, exc: Exception) -> str:
        """
        Determine error severity level for monitoring and alerting.
        
        Args:
            exc: The exception to analyze
            
        Returns:
            Severity level: "low", "medium", "high", or "critical"
        """
        exc_type = type(exc).__name__.lower()
        exc_message = str(exc).lower()
        
        # Critical errors that require immediate attention
        if any(keyword in exc_type for keyword in [
            'memory', 'overflow', 'deadlock', 'corruption'
        ]) or any(keyword in exc_message for keyword in [
            'out of memory', 'disk full', 'corruption', 'deadlock'
        ]):
            return "critical"
        
        # High severity errors that affect core functionality
        if any(keyword in exc_type for keyword in [
            'database', 'connection', 'auth'
        ]) or any(keyword in exc_message for keyword in [
            'database unavailable', 'authentication failed', 'connection refused'
        ]):
            return "high"
        
        # Medium severity errors that affect some functionality
        if any(keyword in exc_type for keyword in [
            'validation', 'permission', 'timeout'
        ]) or any(keyword in exc_message for keyword in [
            'validation failed', 'timeout', 'service unavailable'
        ]):
            return "medium"
        
        # Low severity errors (expected errors, user errors)
        return "low"
    
    def _get_user_friendly_message(self, error_category: str, exc: Exception) -> str:
        """
        Generate user-friendly error messages based on error category.
        
        Args:
            error_category: The categorized error type
            exc: The original exception
            
        Returns:
            User-friendly error message
        """
        messages = {
            "database_error": "We're experiencing database connectivity issues. Please try again in a few moments.",
            "network_error": "We're having trouble connecting to external services. Please try again later.",
            "validation_error": "The provided data is invalid. Please check your input and try again.",
            "auth_error": "Authentication failed. Please check your credentials and try again.",
            "ai_service_error": "Our AI service is temporarily unavailable. Please try again later.",
            "filesystem_error": "We're experiencing file system issues. Please try again later.",
            "import_error": "A system component is missing. Please contact support if this persists.",
            "memory_error": "The system is experiencing high load. Please try again in a few moments.",
            "concurrency_error": "A system conflict occurred. Please try again.",
            "configuration_error": "A system configuration issue was detected. Please contact support.",
            "rate_limit_error": "You've exceeded the rate limit. Please wait before trying again.",
            "unknown_error": "An unexpected error occurred. Please try again or contact support if this persists."
        }
        
        return messages.get(error_category, messages["unknown_error"])
    
    async def _extract_request_data(self, request: Request, correlation_id: str) -> Dict[str, Any]:
        """
        Extract structured request data for logging.
        
        Args:
            request: The FastAPI request object
            correlation_id: Unique request identifier
            
        Returns:
            Dictionary of request data
        """
        request_data = {
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": {
                key: value for key, value in request.headers.items()
                if key.lower() not in ['authorization', 'cookie', 'x-api-key']  # Exclude sensitive headers
            },
            "user_agent": request.headers.get("user-agent", "unknown"),
            "client_ip": self._get_client_ip(request),
            "content_type": request.headers.get("content-type", "unknown"),
            "content_length": request.headers.get("content-length", "unknown")
        }
        
        # Optionally include request body (be careful with sensitive data)
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Only log body size for security reasons
                    request_data["body_size"] = len(body)
                    
                    # In debug mode, include sanitized body content
                    if self.debug:
                        try:
                            body_text = body.decode('utf-8')[:1000]  # Limit size
                            # Remove sensitive data patterns
                            import re
                            sanitized_body = re.sub(
                                r'("password"|"token"|"secret"|"key")\s*:\s*"[^"]*"',
                                r'\1: "[REDACTED]"',
                                body_text,
                                flags=re.IGNORECASE
                            )
                            request_data["body_preview"] = sanitized_body
                        except Exception:
                            request_data["body_preview"] = "[Unable to decode body]"
            except Exception:
                pass
        
        return request_data
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request, considering proxies.
        
        Args:
            request: The FastAPI request object
            
        Returns:
            Client IP address
        """
        # Check for forwarded headers (common in load balancers/proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware for detailed request/response logging and monitoring.
    
    Provides structured logging with security-aware data handling,
    performance monitoring, and integration with observability systems.
    """
    
    def __init__(
        self, 
        app, 
        log_body: bool = False,
        log_response: bool = False,
        exclude_paths: Optional[List[str]] = None,
        sensitive_headers: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.log_body = log_body
        self.log_response = log_response
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/favicon.ico"]
        self.sensitive_headers = sensitive_headers or [
            "authorization", "cookie", "x-api-key", "x-auth-token"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details with enhanced monitoring."""
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        start_time = time.time()
        correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
        
        # Log request details with structured data
        request_info = await self._build_request_log_data(request, correlation_id, start_time)
        logger.info("HTTP request received", extra=request_info)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Log response details
            process_time = time.time() - start_time
            response_info = await self._build_response_log_data(
                request, response, correlation_id, process_time
            )
            
            # Determine log level based on status code
            if response.status_code >= 500:
                logger.error("HTTP response sent (server error)", extra=response_info)
            elif response.status_code >= 400:
                logger.warning("HTTP response sent (client error)", extra=response_info)
            else:
                logger.info("HTTP response sent (success)", extra=response_info)
            
            return response
            
        except Exception as e:
            # Log exception during request processing
            process_time = time.time() - start_time
            error_info = {
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "processing_time_seconds": round(process_time, 3),
                "exception": str(e),
                "exception_type": type(e).__name__
            }
            logger.error("Exception during request processing", extra=error_info)
            raise
    
    async def _build_request_log_data(
        self, 
        request: Request, 
        correlation_id: str, 
        start_time: float
    ) -> Dict[str, Any]:
        """Build structured request log data."""
        # Filter sensitive headers
        safe_headers = {
            key: "[REDACTED]" if key.lower() in self.sensitive_headers else value
            for key, value in request.headers.items()
        }
        
        request_data = {
            "correlation_id": correlation_id,
            "event_type": "http_request",
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": safe_headers,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length"),
            "timestamp": start_time,
            "request_id": correlation_id
        }
        
        # Optionally include request body information
        if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_data["body_size"] = len(body)
                    
                    # In debug mode, include sanitized body preview
                    try:
                        body_text = body.decode('utf-8')[:500]  # Limit preview size
                        # Sanitize sensitive data
                        import re
                        sanitized_body = re.sub(
                            r'("password"|"token"|"secret"|"key"|"auth")\s*:\s*"[^"]*"',
                            r'\1: "[REDACTED]"',
                            body_text,
                            flags=re.IGNORECASE
                        )
                        request_data["body_preview"] = sanitized_body
                    except Exception:
                        request_data["body_preview"] = "[Unable to decode body]"
            except Exception:
                request_data["body_size"] = "unknown"
        
        return request_data
    
    async def _build_response_log_data(
        self, 
        request: Request, 
        response: Response, 
        correlation_id: str, 
        process_time: float
    ) -> Dict[str, Any]:
        """Build structured response log data."""
        response_data = {
            "correlation_id": correlation_id,
            "event_type": "http_response",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "processing_time_seconds": round(process_time, 3),
            "response_headers": dict(response.headers),
            "content_type": response.headers.get("content-type"),
            "content_length": response.headers.get("content-length"),
            "client_ip": self._get_client_ip(request)
        }
        
        # Optionally include response body information
        if self.log_response and hasattr(response, 'body'):
            try:
                if hasattr(response.body, '__len__'):
                    response_data["response_size"] = len(response.body)
            except Exception:
                pass
        
        # Add performance categorization
        if process_time > 5.0:
            response_data["performance_category"] = "very_slow"
        elif process_time > 2.0:
            response_data["performance_category"] = "slow"
        elif process_time > 1.0:
            response_data["performance_category"] = "moderate"
        else:
            response_data["performance_category"] = "fast"
        
        return response_data
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address considering proxies."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"


def create_error_handlers():
    """
    Create enhanced custom exception handlers for specific error types.
    
    Returns:
        Dictionary of exception handlers with comprehensive logging and monitoring
    """
    
    async def validation_exception_handler(request: Request, exc):
        """Handle Pydantic validation errors with detailed logging."""
        correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
        
        # Extract validation error details
        if hasattr(exc, 'errors'):
            validation_errors = exc.errors()
            field_errors = {}
            
            for error in validation_errors:
                field_path = '.'.join(str(loc) for loc in error['loc'])
                if field_path not in field_errors:
                    field_errors[field_path] = []
                field_errors[field_path].append(error['msg'])
        else:
            field_errors = {"general": [str(exc)]}
        
        # Log validation error with structured data
        error_data = {
            "correlation_id": correlation_id,
            "error_type": "validation_error",
            "method": request.method,
            "path": request.url.path,
            "field_errors": field_errors,
            "client_ip": _get_client_ip_helper(request),
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        logger.warning("Request validation failed", extra=error_data)
        
        # Update metrics
        if error_metrics:
            error_metrics["total_errors"] += 1
            error_metrics["error_categories"]["validation_error"] = (
                error_metrics["error_categories"].get("validation_error", 0) + 1
            )
        
        # Create response using ResponseFormatter
        response_content = ResponseFormatter.validation_error(
            field_errors=field_errors,
            message="Request validation failed"
        )
        response_content["correlation_id"] = correlation_id
        
        response = JSONResponse(
            status_code=422,
            content=response_content
        )
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    
    async def not_found_handler(request: Request, exc):
        """Handle 404 Not Found errors with enhanced logging."""
        correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
        
        # Log not found error
        error_data = {
            "correlation_id": correlation_id,
            "error_type": "not_found",
            "method": request.method,
            "path": request.url.path,
            "client_ip": _get_client_ip_helper(request),
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        logger.info("Endpoint not found", extra=error_data)
        
        # Create response using ResponseFormatter
        response_content = ResponseFormatter.not_found(
            resource="Endpoint",
            identifier=f"{request.method} {request.url.path}"
        )
        response_content["correlation_id"] = correlation_id
        
        response = JSONResponse(
            status_code=404,
            content=response_content
        )
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    
    async def method_not_allowed_handler(request: Request, exc):
        """Handle 405 Method Not Allowed errors with enhanced logging."""
        correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
        
        # Log method not allowed error
        error_data = {
            "correlation_id": correlation_id,
            "error_type": "method_not_allowed",
            "method": request.method,
            "path": request.url.path,
            "client_ip": _get_client_ip_helper(request),
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        logger.warning("Method not allowed", extra=error_data)
        
        # Create response using ResponseFormatter
        response_content = ResponseFormatter.error(
            message=f"Method {request.method} not allowed for {request.url.path}",
            error_code="METHOD_NOT_ALLOWED",
            details={
                "method": request.method,
                "path": request.url.path,
                "allowed_methods": getattr(exc, 'allowed_methods', []) if hasattr(exc, 'allowed_methods') else []
            },
            status_code=405
        )
        response_content["correlation_id"] = correlation_id
        
        response = JSONResponse(
            status_code=405,
            content=response_content
        )
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    
    async def internal_server_error_handler(request: Request, exc):
        """Handle 500 Internal Server Error with comprehensive logging."""
        correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
        
        # Log internal server error
        error_data = {
            "correlation_id": correlation_id,
            "error_type": "internal_server_error",
            "method": request.method,
            "path": request.url.path,
            "exception": str(exc),
            "exception_type": type(exc).__name__,
            "client_ip": _get_client_ip_helper(request),
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        logger.error("Internal server error", extra=error_data, exc_info=True)
        
        # Create response using ResponseFormatter
        response_content = ResponseFormatter.error(
            message="An internal server error occurred",
            error_code="INTERNAL_SERVER_ERROR",
            status_code=500
        )
        response_content["correlation_id"] = correlation_id
        
        response = JSONResponse(
            status_code=500,
            content=response_content
        )
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    
    return {
        422: validation_exception_handler,
        405: method_not_allowed_handler,
        500: internal_server_error_handler
    }


def _get_client_ip_helper(request: Request) -> str:
    """Helper function to extract client IP address."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    if request.client:
        return request.client.host
    
    return "unknown"


def get_error_metrics() -> Dict[str, Any]:
    """
    Get current error metrics for monitoring.
    
    Returns:
        Dictionary of error metrics
    """
    return {
        "total_errors": error_metrics["total_errors"],
        "error_categories": dict(error_metrics["error_categories"]),
        "error_rates": dict(error_metrics["error_rates"]),
        "slow_requests": error_metrics["slow_requests"],
        "timestamp": time.time()
    }


def reset_error_metrics():
    """Reset error metrics (useful for testing or periodic resets)."""
    global error_metrics
    error_metrics = {
        "total_errors": 0,
        "error_categories": {},
        "error_rates": {},
        "slow_requests": 0
    }