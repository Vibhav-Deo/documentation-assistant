"""
Common Utilities Module

Consolidates duplicate imports and common operations found across
multiple service files to eliminate code duplication.

This module provides:
- Common imports and constants
- Shared utility functions
- Common data validation helpers
- Shared formatting utilities
- Common error handling patterns
"""

import re
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from contextlib import asynccontextmanager

# Common third-party imports
import requests
from fastapi import HTTPException

# Common constants
DEFAULT_TIMEOUT = 60
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000
DEFAULT_CONFIDENCE_THRESHOLD = 0.5

# Common regex patterns
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
TICKET_KEY_PATTERN = re.compile(r'^[A-Z]+-\d+$')

logger = logging.getLogger(__name__)


# ========================================
# COMMON DATA CLASSES
# ========================================

@dataclass
class PaginationParams:
    """Standard pagination parameters."""
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE
    offset: int = 0
    
    def __post_init__(self):
        if self.page < 1:
            self.page = 1
        if self.page_size < 1:
            self.page_size = DEFAULT_PAGE_SIZE
        if self.page_size > MAX_PAGE_SIZE:
            self.page_size = MAX_PAGE_SIZE
        self.offset = (self.page - 1) * self.page_size


@dataclass
class PaginatedResponse:
    """Standard paginated response format."""
    items: List[Any]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    @classmethod
    def create(cls, items: List[Any], total_count: int, pagination: PaginationParams):
        total_pages = (total_count + pagination.page_size - 1) // pagination.page_size
        return cls(
            items=items,
            total_count=total_count,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_previous=pagination.page > 1
        )


@dataclass
class OperationResult:
    """Standard operation result format."""
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ========================================
# VALIDATION UTILITIES
# ========================================

def validate_email(email: str) -> bool:
    """Validate email format."""
    return bool(EMAIL_PATTERN.match(email))


def validate_uuid(uuid_str: str) -> bool:
    """Validate UUID format."""
    return bool(UUID_PATTERN.match(uuid_str.lower()))


def validate_ticket_key(ticket_key: str) -> bool:
    """Validate Jira ticket key format (e.g., DEMO-001)."""
    return bool(TICKET_KEY_PATTERN.match(ticket_key))


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validate required fields in data dictionary.
    
    Returns:
        List of missing field names
    """
    return [field for field in required_fields if field not in data or data[field] is None]


def validate_field_types(data: Dict[str, Any], field_types: Dict[str, type]) -> List[str]:
    """
    Validate field types in data dictionary.
    
    Returns:
        List of type validation error messages
    """
    errors = []
    for field, expected_type in field_types.items():
        if field in data and data[field] is not None:
            if not isinstance(data[field], expected_type):
                errors.append(f"{field} must be of type {expected_type.__name__}")
    return errors


def validate_string_lengths(
    data: Dict[str, Any], 
    field_limits: Dict[str, Dict[str, int]]
) -> List[str]:
    """
    Validate string field lengths.
    
    Args:
        data: Data dictionary
        field_limits: Dict mapping field names to {"min": int, "max": int}
    
    Returns:
        List of length validation error messages
    """
    errors = []
    for field, limits in field_limits.items():
        if field in data and isinstance(data[field], str):
            value_length = len(data[field])
            min_length = limits.get("min", 0)
            max_length = limits.get("max", float('inf'))
            
            if value_length < min_length:
                errors.append(f"{field} must be at least {min_length} characters")
            elif value_length > max_length:
                errors.append(f"{field} must be at most {max_length} characters")
    
    return errors


# ========================================
# STRING UTILITIES
# ========================================

def clean_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Input text
        max_length: Maximum length (truncate if longer)
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', text.strip())
    
    # Truncate if needed
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip() + "..."
    
    return cleaned


def extract_ticket_keys(text: str) -> List[str]:
    """Extract Jira ticket keys from text."""
    return TICKET_KEY_PATTERN.findall(text)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove or replace unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = re.sub(r'[^\w\-_\.]', '_', sanitized)
    return sanitized[:255]  # Limit length


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


# ========================================
# DATE/TIME UTILITIES
# ========================================

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse ISO timestamp string to datetime object."""
    try:
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


# ========================================
# COLLECTION UTILITIES
# ========================================

def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size."""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def deduplicate_list(items: List[Any], key_func: Optional[callable] = None) -> List[Any]:
    """
    Remove duplicates from list while preserving order.
    
    Args:
        items: List of items
        key_func: Optional function to extract comparison key
    
    Returns:
        List with duplicates removed
    """
    seen = set()
    result = []
    
    for item in items:
        key = key_func(item) if key_func else item
        if key not in seen:
            seen.add(key)
            result.append(item)
    
    return result


def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with dot notation support."""
    try:
        keys = key.split('.')
        value = dictionary
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError, AttributeError):
        return default


# ========================================
# HTTP UTILITIES
# ========================================

def make_http_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict] = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = 3
) -> requests.Response:
    """
    Make HTTP request with retry logic.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        headers: Optional headers
        data: Optional request data
        timeout: Request timeout in seconds
        retries: Number of retry attempts
    
    Returns:
        Response object
    
    Raises:
        HTTPException: On request failure
    """
    for attempt in range(retries + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=timeout
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.Timeout:
            if attempt == retries:
                raise HTTPException(
                    status_code=504,
                    detail=f"Request timeout after {timeout} seconds"
                )
        except requests.exceptions.ConnectionError:
            if attempt == retries:
                raise HTTPException(
                    status_code=503,
                    detail="Service unavailable - connection failed"
                )
        except requests.exceptions.HTTPError as e:
            if attempt == retries:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"HTTP error: {e.response.text}"
                )
        
        # Wait before retry (exponential backoff)
        if attempt < retries:
            time.sleep(2 ** attempt)


# ========================================
# ERROR HANDLING UTILITIES
# ========================================

def create_error_response(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict] = None
) -> HTTPException:
    """Create standardized error response."""
    error_detail = {
        "message": message,
        "timestamp": get_current_timestamp()
    }
    
    if error_code:
        error_detail["error_code"] = error_code
    
    if details:
        error_detail["details"] = details
    
    return HTTPException(status_code=status_code, detail=error_detail)


def handle_database_error(error: Exception, operation: str) -> HTTPException:
    """Convert database errors to appropriate HTTP exceptions."""
    error_msg = str(error).lower()
    
    if "unique constraint" in error_msg or "duplicate key" in error_msg:
        return create_error_response(
            409,
            f"Duplicate entry in {operation}",
            "DUPLICATE_ENTRY"
        )
    elif "foreign key constraint" in error_msg:
        return create_error_response(
            400,
            f"Invalid reference in {operation}",
            "INVALID_REFERENCE"
        )
    elif "not null constraint" in error_msg:
        return create_error_response(
            400,
            f"Missing required field in {operation}",
            "MISSING_REQUIRED_FIELD"
        )
    else:
        logger.error(f"Database error in {operation}: {error}")
        return create_error_response(
            500,
            f"Database error in {operation}",
            "DATABASE_ERROR"
        )


# ========================================
# LOGGING UTILITIES
# ========================================

def log_operation_start(operation: str, **kwargs) -> float:
    """Log operation start and return start time."""
    start_time = time.time()
    logger.info(f"Starting operation: {operation}", extra=kwargs)
    return start_time


def log_operation_end(operation: str, start_time: float, **kwargs) -> None:
    """Log operation completion with duration."""
    duration = time.time() - start_time
    logger.info(
        f"Operation completed: {operation} in {format_duration(duration)}",
        extra={**kwargs, "duration_seconds": duration}
    )


def log_operation_error(operation: str, error: Exception, **kwargs) -> None:
    """Log operation error."""
    logger.error(
        f"Operation failed: {operation}. Error: {str(error)}",
        extra={**kwargs, "error_type": type(error).__name__},
        exc_info=True
    )


# ========================================
# ASYNC UTILITIES
# ========================================

async def run_with_timeout(coro, timeout_seconds: float):
    """Run coroutine with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Operation timed out after {timeout_seconds} seconds"
        )


async def gather_with_limit(coroutines: List, limit: int = 10):
    """Run coroutines concurrently with concurrency limit."""
    semaphore = asyncio.Semaphore(limit)
    
    async def limited_coro(coro):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(*[limited_coro(coro) for coro in coroutines])


# ========================================
# CONFIGURATION UTILITIES
# ========================================

def get_env_var(name: str, default: Any = None, required: bool = False) -> Any:
    """Get environment variable with validation."""
    import os
    
    value = os.getenv(name, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable {name} is not set")
    
    return value


def parse_bool(value: Union[str, bool]) -> bool:
    """Parse boolean value from string or bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return False


def parse_int(value: Union[str, int], default: int = 0) -> int:
    """Parse integer value with fallback."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def parse_float(value: Union[str, float], default: float = 0.0) -> float:
    """Parse float value with fallback."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

# ========================================
# COMMON UTILITIES CLASS
# ========================================

class CommonUtilities:
    """
    Wrapper class for common utility functions.
    Provides a centralized interface for shared operations.
    """
    
    # Validation methods
    @staticmethod
    def validate_email(email: str) -> bool:
        return validate_email(email)
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        return validate_uuid(uuid_str)
    
    @staticmethod
    def validate_ticket_key(ticket_key: str) -> bool:
        return validate_ticket_key(ticket_key)
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        return validate_required_fields(data, required_fields)
    
    # String utilities
    @staticmethod
    def clean_text(text: str, max_length: Optional[int] = None) -> str:
        return clean_text(text, max_length)
    
    @staticmethod
    def extract_ticket_keys(text: str) -> List[str]:
        return extract_ticket_keys(text)
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        return truncate_text(text, max_length, suffix)
    
    # Date/time utilities
    @staticmethod
    def get_current_timestamp() -> str:
        return get_current_timestamp()
    
    @staticmethod
    def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
        return parse_timestamp(timestamp_str)
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        return format_duration(seconds)
    
    # Collection utilities
    @staticmethod
    def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
        return chunk_list(items, chunk_size)
    
    @staticmethod
    def deduplicate_list(items: List[Any], key_func: Optional[callable] = None) -> List[Any]:
        return deduplicate_list(items, key_func)
    
    @staticmethod
    def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
        return safe_get(dictionary, key, default)
    
    # Error handling
    @staticmethod
    def create_error_response(
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> HTTPException:
        return create_error_response(status_code, message, error_code, details)
    
    @staticmethod
    def handle_database_error(error: Exception, operation: str) -> HTTPException:
        return handle_database_error(error, operation)
    
    # Configuration utilities
    @staticmethod
    def get_env_var(name: str, default: Any = None, required: bool = False) -> Any:
        return get_env_var(name, default, required)
    
    @staticmethod
    def parse_bool(value: Union[str, bool]) -> bool:
        return parse_bool(value)
    
    @staticmethod
    def parse_int(value: Union[str, int], default: int = 0) -> int:
        return parse_int(value, default)
    
    @staticmethod
    def parse_float(value: Union[str, float], default: float = 0.0) -> float:
        return parse_float(value, default)