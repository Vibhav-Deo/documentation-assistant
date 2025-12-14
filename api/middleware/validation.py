"""
Request/Response Validation Decorators

Provides decorators for comprehensive input validation, output validation,
and request/response transformation with consistent error handling.
"""

import functools
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union
from fastapi import HTTPException, Request
from pydantic import BaseModel, ValidationError
from services.shared.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)


def validate_request(
    *,
    required_fields: Optional[List[str]] = None,
    field_types: Optional[Dict[str, Type]] = None,
    field_limits: Optional[Dict[str, Dict[str, Union[int, float]]]] = None,
    custom_validators: Optional[Dict[str, Callable]] = None,
    sanitize_input: bool = True
) -> Callable:
    """
    Decorator for comprehensive request validation.
    
    Args:
        required_fields: List of required field names
        field_types: Dictionary mapping field names to expected types
        field_limits: Dictionary mapping field names to validation limits
        custom_validators: Dictionary mapping field names to custom validation functions
        sanitize_input: Whether to sanitize string inputs
        
    Returns:
        Decorated function with request validation
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request data from function arguments
            request_data = {}
            
            # Look for Pydantic models in kwargs
            for key, value in kwargs.items():
                if isinstance(value, BaseModel):
                    request_data.update(value.dict())
                elif isinstance(value, dict):
                    request_data.update(value)
            
            # Perform validation
            validation_errors = {}
            
            # Check required fields
            if required_fields:
                missing_fields = [
                    field for field in required_fields 
                    if field not in request_data or request_data[field] is None
                ]
                if missing_fields:
                    validation_errors["missing_fields"] = missing_fields
            
            # Check field types
            if field_types:
                type_errors = []
                for field, expected_type in field_types.items():
                    if field in request_data and request_data[field] is not None:
                        if not isinstance(request_data[field], expected_type):
                            type_errors.append(
                                f"{field} must be of type {expected_type.__name__}, "
                                f"got {type(request_data[field]).__name__}"
                            )
                if type_errors:
                    validation_errors["type_errors"] = type_errors
            
            # Check field limits
            if field_limits:
                limit_errors = []
                for field, limits in field_limits.items():
                    if field in request_data and request_data[field] is not None:
                        value = request_data[field]
                        
                        # String length validation
                        if isinstance(value, str):
                            min_length = limits.get("min_length", 0)
                            max_length = limits.get("max_length", float('inf'))
                            
                            if len(value) < min_length:
                                limit_errors.append(f"{field} must be at least {min_length} characters")
                            elif len(value) > max_length:
                                limit_errors.append(f"{field} must be at most {max_length} characters")
                        
                        # Numeric range validation
                        elif isinstance(value, (int, float)):
                            min_value = limits.get("min_value", float('-inf'))
                            max_value = limits.get("max_value", float('inf'))
                            
                            if value < min_value:
                                limit_errors.append(f"{field} must be at least {min_value}")
                            elif value > max_value:
                                limit_errors.append(f"{field} must be at most {max_value}")
                        
                        # List length validation
                        elif isinstance(value, list):
                            min_items = limits.get("min_items", 0)
                            max_items = limits.get("max_items", float('inf'))
                            
                            if len(value) < min_items:
                                limit_errors.append(f"{field} must have at least {min_items} items")
                            elif len(value) > max_items:
                                limit_errors.append(f"{field} must have at most {max_items} items")
                
                if limit_errors:
                    validation_errors["limit_errors"] = limit_errors
            
            # Run custom validators
            if custom_validators:
                custom_errors = []
                for field, validator in custom_validators.items():
                    if field in request_data:
                        try:
                            if not validator(request_data[field]):
                                custom_errors.append(f"{field} failed custom validation")
                        except Exception as e:
                            custom_errors.append(f"{field} validation error: {str(e)}")
                
                if custom_errors:
                    validation_errors["custom_errors"] = custom_errors
            
            # Sanitize input if requested
            if sanitize_input:
                for key, value in request_data.items():
                    if isinstance(value, str):
                        # Basic XSS prevention
                        sanitized = (value
                                   .replace("<script", "&lt;script")
                                   .replace("</script>", "&lt;/script&gt;")
                                   .replace("javascript:", "")
                                   .replace("on", "")  # Remove event handlers
                                   .strip())
                        
                        # Update the original model if it exists
                        for arg_key, arg_value in kwargs.items():
                            if isinstance(arg_value, BaseModel) and hasattr(arg_value, key):
                                setattr(arg_value, key, sanitized)
            
            # If validation errors exist, raise HTTPException
            if validation_errors:
                logger.warning(f"Request validation failed: {validation_errors}")
                raise HTTPException(
                    status_code=422,
                    detail=ResponseFormatter.validation_error(
                        field_errors=validation_errors,
                        message="Request validation failed"
                    )
                )
            
            # Log successful validation
            logger.debug(f"Request validation passed for {func.__name__}")
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_response(
    *,
    response_model: Optional[Type[BaseModel]] = None,
    required_fields: Optional[List[str]] = None,
    transform_response: bool = True
) -> Callable:
    """
    Decorator for response validation and transformation.
    
    Args:
        response_model: Pydantic model for response validation
        required_fields: List of required fields in response
        transform_response: Whether to transform response using ResponseFormatter
        
    Returns:
        Decorated function with response validation
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Call the original function
                result = await func(*args, **kwargs)
                
                # Validate response if model is provided
                if response_model and result is not None:
                    try:
                        if isinstance(result, dict):
                            # Validate dictionary against model
                            validated_result = response_model(**result)
                            result = validated_result.dict()
                        elif not isinstance(result, response_model):
                            # Try to convert to model
                            validated_result = response_model(result)
                            result = validated_result.dict()
                    except ValidationError as e:
                        logger.error(f"Response validation failed for {func.__name__}: {e}")
                        raise HTTPException(
                            status_code=500,
                            detail="Internal server error: Invalid response format"
                        )
                
                # Check required fields
                if required_fields and isinstance(result, dict):
                    missing_fields = [
                        field for field in required_fields 
                        if field not in result or result[field] is None
                    ]
                    if missing_fields:
                        logger.error(f"Response missing required fields: {missing_fields}")
                        raise HTTPException(
                            status_code=500,
                            detail="Internal server error: Incomplete response"
                        )
                
                # Transform response if requested
                if transform_response and not isinstance(result, dict) or "success" not in result:
                    processing_time = time.time() - start_time
                    result = ResponseFormatter.success(
                        data=result,
                        metadata={"processing_time_seconds": round(processing_time, 3)}
                    )
                
                logger.debug(f"Response validation passed for {func.__name__}")
                return result
                
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error occurred"
                )
        
        return wrapper
    return decorator


def rate_limit(
    *,
    max_requests: int = 100,
    window_seconds: int = 3600,
    key_func: Optional[Callable] = None
) -> Callable:
    """
    Decorator for rate limiting API endpoints.
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
        key_func: Function to generate rate limit key (default: user ID)
        
    Returns:
        Decorated function with rate limiting
    """
    # Simple in-memory rate limiting (in production, use Redis)
    request_counts = {}
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract rate limit key
            rate_limit_key = "default"
            
            if key_func:
                try:
                    rate_limit_key = key_func(*args, **kwargs)
                except Exception:
                    pass
            else:
                # Try to extract user ID from kwargs
                for value in kwargs.values():
                    if hasattr(value, 'id'):
                        rate_limit_key = str(value.id)
                        break
                    elif hasattr(value, 'organization_id'):
                        rate_limit_key = str(value.organization_id)
                        break
            
            # Check rate limit
            current_time = time.time()
            window_start = current_time - window_seconds
            
            # Clean old entries
            if rate_limit_key in request_counts:
                request_counts[rate_limit_key] = [
                    timestamp for timestamp in request_counts[rate_limit_key]
                    if timestamp > window_start
                ]
            else:
                request_counts[rate_limit_key] = []
            
            # Check if limit exceeded
            if len(request_counts[rate_limit_key]) >= max_requests:
                logger.warning(f"Rate limit exceeded for key: {rate_limit_key}")
                raise HTTPException(
                    status_code=429,
                    detail=ResponseFormatter.rate_limited(
                        retry_after=int(window_seconds - (current_time - min(request_counts[rate_limit_key])))
                    )
                )
            
            # Add current request
            request_counts[rate_limit_key].append(current_time)
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_performance(
    *,
    log_level: int = logging.INFO,
    include_args: bool = False,
    slow_threshold_seconds: float = 1.0
) -> Callable:
    """
    Decorator for performance logging.
    
    Args:
        log_level: Logging level to use
        include_args: Whether to include function arguments in logs
        slow_threshold_seconds: Threshold for logging slow requests
        
    Returns:
        Decorated function with performance logging
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Log function start
            log_data = {
                "function": func.__name__,
                "start_time": start_time
            }
            
            if include_args:
                # Sanitize arguments for logging (remove sensitive data)
                safe_kwargs = {}
                for key, value in kwargs.items():
                    if any(sensitive in key.lower() for sensitive in ['password', 'token', 'secret', 'key']):
                        safe_kwargs[key] = "[REDACTED]"
                    elif isinstance(value, BaseModel):
                        safe_kwargs[key] = f"<{type(value).__name__}>"
                    else:
                        safe_kwargs[key] = str(value)[:100]  # Truncate long values
                
                log_data["arguments"] = safe_kwargs
            
            logger.log(log_level, f"Function started: {log_data}")
            
            try:
                # Call the original function
                result = await func(*args, **kwargs)
                
                # Calculate execution time
                execution_time = time.time() - start_time
                
                # Log completion
                completion_data = {
                    "function": func.__name__,
                    "execution_time_seconds": round(execution_time, 3),
                    "status": "success"
                }
                
                # Log as warning if slow
                if execution_time > slow_threshold_seconds:
                    logger.warning(f"Slow function execution: {completion_data}")
                else:
                    logger.log(log_level, f"Function completed: {completion_data}")
                
                return result
                
            except Exception as e:
                # Log error
                execution_time = time.time() - start_time
                error_data = {
                    "function": func.__name__,
                    "execution_time_seconds": round(execution_time, 3),
                    "status": "error",
                    "error": str(e)
                }
                
                logger.error(f"Function failed: {error_data}")
                raise
        
        return wrapper
    return decorator


def require_permissions(
    *,
    required_roles: Optional[List[str]] = None,
    require_org_access: bool = True,
    custom_check: Optional[Callable] = None
) -> Callable:
    """
    Decorator for authorization and permission checking.
    
    Args:
        required_roles: List of required user roles
        require_org_access: Whether to check organization access
        custom_check: Custom authorization function
        
    Returns:
        Decorated function with authorization
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs
            current_user = None
            org_id = None
            
            for key, value in kwargs.items():
                if hasattr(value, 'role') and hasattr(value, 'organization_id'):
                    current_user = value
                elif key == 'org_id':
                    org_id = value
            
            if not current_user:
                logger.warning("Authorization check failed: No user found")
                raise HTTPException(
                    status_code=401,
                    detail=ResponseFormatter.unauthorized("Authentication required")
                )
            
            # Check required roles
            if required_roles and current_user.role not in required_roles:
                logger.warning(f"Authorization failed: User role {current_user.role} not in {required_roles}")
                raise HTTPException(
                    status_code=403,
                    detail=ResponseFormatter.forbidden("Insufficient permissions")
                )
            
            # Check organization access
            if require_org_access and org_id and org_id != current_user.organization_id:
                logger.warning(f"Organization access denied: User org {current_user.organization_id}, requested {org_id}")
                raise HTTPException(
                    status_code=403,
                    detail=ResponseFormatter.forbidden("Access denied to organization data")
                )
            
            # Run custom authorization check
            if custom_check:
                try:
                    if not await custom_check(current_user, *args, **kwargs):
                        logger.warning("Custom authorization check failed")
                        raise HTTPException(
                            status_code=403,
                            detail=ResponseFormatter.forbidden("Custom authorization failed")
                        )
                except Exception as e:
                    logger.error(f"Custom authorization check error: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail="Authorization check failed"
                    )
            
            logger.debug(f"Authorization passed for user {current_user.id}")
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Utility functions for common validation patterns

def validate_email(email: str) -> bool:
    """Validate email format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    import re
    pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    return bool(re.match(pattern, url))


def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format."""
    import re
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_string.lower()))


def validate_json(json_string: str) -> bool:
    """Validate JSON format."""
    import json
    try:
        json.loads(json_string)
        return True
    except (ValueError, TypeError):
        return False


def sanitize_sql_input(input_string: str) -> str:
    """Sanitize input to prevent SQL injection."""
    # Remove or escape dangerous SQL characters
    dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
    sanitized = input_string
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()


def sanitize_html_input(input_string: str) -> str:
    """Sanitize HTML input to prevent XSS."""
    import html
    # Escape HTML entities
    sanitized = html.escape(input_string)
    
    # Remove dangerous tags and attributes
    dangerous_patterns = [
        r'<script.*?</script>',
        r'<iframe.*?</iframe>',
        r'<object.*?</object>',
        r'<embed.*?>',
        r'on\w+\s*=',  # Event handlers
        r'javascript:',
        r'vbscript:',
        r'data:text/html'
    ]
    
    import re
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    return sanitized.strip()