"""
Streaming Error Handler

Provides comprehensive error handling and fallback logic for streaming responses.
Includes graceful degradation, automatic fallback, and user-friendly error messages.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, AsyncGenerator
from enum import Enum
from dataclasses import dataclass
from services.shared.streaming_utils import StreamingEventFormatter, StreamingEventType

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    RATE_LIMIT = "rate_limit"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT = "timeout"
    INTERNAL = "internal"
    CLIENT_DISCONNECT = "client_disconnect"


@dataclass
class StreamingError:
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    recoverable: bool
    retry_after: Optional[int] = None
    fallback_available: bool = False
    user_message: Optional[str] = None
    technical_details: Optional[Dict[str, Any]] = None


class StreamingErrorHandler:
    """
    Comprehensive error handling for streaming responses with fallback logic.
    """
    
    def __init__(self):
        self.error_counts = {}
        self.fallback_enabled = True
        
        # Error classification patterns
        self.error_patterns = {
            ErrorCategory.NETWORK: [
                "connection", "network", "timeout", "unreachable", "dns"
            ],
            ErrorCategory.AUTHENTICATION: [
                "unauthorized", "authentication", "token", "forbidden", "401", "403"
            ],
            ErrorCategory.VALIDATION: [
                "validation", "invalid", "malformed", "bad request", "400"
            ],
            ErrorCategory.RATE_LIMIT: [
                "rate limit", "too many requests", "quota", "429"
            ],
            ErrorCategory.SERVICE_UNAVAILABLE: [
                "service unavailable", "502", "503", "504", "maintenance"
            ],
            ErrorCategory.TIMEOUT: [
                "timeout", "deadline", "cancelled", "aborted"
            ],
            ErrorCategory.CLIENT_DISCONNECT: [
                "client disconnect", "connection closed", "cancelled"
            ]
        }
    
    def classify_error(self, error: Exception) -> StreamingError:
        """
        Classify an error and determine appropriate handling strategy.
        
        Args:
            error: The exception that occurred
            
        Returns:
            Classified streaming error with handling metadata
        """
        error_message = str(error).lower()
        error_type = type(error).__name__
        
        # Classify by error patterns
        category = ErrorCategory.INTERNAL  # Default
        for cat, patterns in self.error_patterns.items():
            if any(pattern in error_message for pattern in patterns):
                category = cat
                break
        
        # Determine severity and recoverability
        severity, recoverable = self._determine_severity_and_recoverability(category, error_message)
        
        # Generate user-friendly message
        user_message = self._generate_user_message(category, error_message)
        
        # Determine if fallback is available
        fallback_available = self._has_fallback(category)
        
        # Calculate retry delay for recoverable errors
        retry_after = self._calculate_retry_delay(category) if recoverable else None
        
        return StreamingError(
            category=category,
            severity=severity,
            message=str(error),
            recoverable=recoverable,
            retry_after=retry_after,
            fallback_available=fallback_available,
            user_message=user_message,
            technical_details={
                "error_type": error_type,
                "original_message": str(error)
            }
        )
    
    def _determine_severity_and_recoverability(
        self, 
        category: ErrorCategory, 
        message: str
    ) -> tuple[ErrorSeverity, bool]:
        """Determine error severity and whether it's recoverable."""
        
        severity_map = {
            ErrorCategory.NETWORK: (ErrorSeverity.MEDIUM, True),
            ErrorCategory.AUTHENTICATION: (ErrorSeverity.HIGH, False),
            ErrorCategory.VALIDATION: (ErrorSeverity.MEDIUM, False),
            ErrorCategory.RATE_LIMIT: (ErrorSeverity.MEDIUM, True),
            ErrorCategory.SERVICE_UNAVAILABLE: (ErrorSeverity.HIGH, True),
            ErrorCategory.TIMEOUT: (ErrorSeverity.MEDIUM, True),
            ErrorCategory.CLIENT_DISCONNECT: (ErrorSeverity.LOW, False),
            ErrorCategory.INTERNAL: (ErrorSeverity.HIGH, True)
        }
        
        return severity_map.get(category, (ErrorSeverity.MEDIUM, True))
    
    def _generate_user_message(self, category: ErrorCategory, message: str) -> str:
        """Generate user-friendly error message."""
        
        user_messages = {
            ErrorCategory.NETWORK: "Connection issue detected. Please check your internet connection and try again.",
            ErrorCategory.AUTHENTICATION: "Authentication failed. Please log in again to continue.",
            ErrorCategory.VALIDATION: "Invalid request. Please check your input and try again.",
            ErrorCategory.RATE_LIMIT: "Too many requests. Please wait a moment before trying again.",
            ErrorCategory.SERVICE_UNAVAILABLE: "Service temporarily unavailable. Please try again in a few moments.",
            ErrorCategory.TIMEOUT: "Request timed out. Please try again with a shorter query.",
            ErrorCategory.CLIENT_DISCONNECT: "Connection was interrupted. Please refresh and try again.",
            ErrorCategory.INTERNAL: "An unexpected error occurred. Please try again."
        }
        
        return user_messages.get(category, "An error occurred. Please try again.")
    
    def _has_fallback(self, category: ErrorCategory) -> bool:
        """Determine if fallback is available for this error category."""
        
        # Categories that have fallback options
        fallback_categories = {
            ErrorCategory.NETWORK,
            ErrorCategory.SERVICE_UNAVAILABLE,
            ErrorCategory.TIMEOUT,
            ErrorCategory.INTERNAL
        }
        
        return category in fallback_categories and self.fallback_enabled
    
    def _calculate_retry_delay(self, category: ErrorCategory) -> int:
        """Calculate retry delay in seconds based on error category."""
        
        retry_delays = {
            ErrorCategory.NETWORK: 2,
            ErrorCategory.RATE_LIMIT: 60,
            ErrorCategory.SERVICE_UNAVAILABLE: 30,
            ErrorCategory.TIMEOUT: 5,
            ErrorCategory.INTERNAL: 10
        }
        
        return retry_delays.get(category, 5)
    
    async def handle_streaming_error(
        self,
        error: Exception,
        fallback_handler: Optional[Callable] = None
    ) -> AsyncGenerator[str, None]:
        """
        Handle streaming error with appropriate fallback logic.
        
        Args:
            error: The exception that occurred
            fallback_handler: Optional fallback function to call
            
        Yields:
            Error event or fallback response
        """
        classified_error = self.classify_error(error)
        
        # Log the error
        logger.error(
            f"Streaming error [{classified_error.category.value}]: {classified_error.message}",
            extra=classified_error.technical_details
        )
        
        # Track error for monitoring
        self._track_error(classified_error)
        
        # Try fallback if available and appropriate
        if classified_error.fallback_available and fallback_handler:
            try:
                logger.info("Attempting fallback for streaming error")
                
                # Send error event first
                yield StreamingEventFormatter.format_error_event(
                    error_type=classified_error.category.value,
                    message=f"{classified_error.user_message} Attempting fallback...",
                    recoverable=True,
                    error_code=f"FALLBACK_{classified_error.category.value.upper()}"
                )
                
                # Try fallback
                async for chunk in fallback_handler():
                    yield chunk
                    
                return
                
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                classified_error.user_message = "Both primary and fallback methods failed. Please try again later."
        
        # Send final error event
        yield StreamingEventFormatter.format_error_event(
            error_type=classified_error.category.value,
            message=classified_error.user_message,
            recoverable=classified_error.recoverable,
            error_code=classified_error.category.value.upper()
        )
    
    def _track_error(self, error: StreamingError):
        """Track error for monitoring and analysis."""
        error_key = f"{error.category.value}_{error.severity.value}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            "error_counts": self.error_counts,
            "total_errors": sum(self.error_counts.values()),
            "fallback_enabled": self.fallback_enabled
        }
    
    async def create_fallback_response(
        self,
        query: str,
        error_context: str = "streaming_error"
    ) -> AsyncGenerator[str, None]:
        """
        Create a fallback response when streaming fails.
        
        Args:
            query: Original user query
            error_context: Context about what failed
            
        Yields:
            Fallback response chunks
        """
        fallback_message = f"""I apologize, but I encountered an issue while processing your request about "{query}". 

Here are some suggestions:

1. **Try rephrasing your question** - Sometimes a different wording can help
2. **Check your connection** - Ensure you have a stable internet connection
3. **Try a simpler query** - Break complex questions into smaller parts
4. **Contact support** - If the issue persists, please contact our support team

I'm still learning and improving, so your patience is appreciated. Please try your question again, and I'll do my best to help you."""

        # Send fallback response in chunks to simulate streaming
        words = fallback_message.split()
        chunk_size = 5
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size]) + " "
            yield StreamingEventFormatter.format_content_event(chunk)
            
            # Small delay to simulate natural streaming
            await asyncio.sleep(0.1)


class StreamingFallbackManager:
    """
    Manages fallback strategies for streaming failures.
    """
    
    def __init__(self):
        self.fallback_strategies = {}
        self.error_handler = StreamingErrorHandler()
    
    def register_fallback(
        self,
        error_category: ErrorCategory,
        fallback_func: Callable
    ):
        """Register a fallback function for a specific error category."""
        self.fallback_strategies[error_category] = fallback_func
    
    async def execute_with_fallback(
        self,
        primary_func: Callable,
        query: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Execute primary function with automatic fallback on error.
        
        Args:
            primary_func: Primary streaming function to execute
            query: User query for fallback context
            **kwargs: Arguments for primary function
            
        Yields:
            Streaming response or fallback response
        """
        try:
            async for chunk in primary_func(**kwargs):
                yield chunk
                
        except Exception as error:
            classified_error = self.error_handler.classify_error(error)
            
            # Try registered fallback for this error category
            fallback_func = self.fallback_strategies.get(classified_error.category)
            
            if fallback_func:
                async for chunk in self.error_handler.handle_streaming_error(
                    error, 
                    lambda: fallback_func(query, **kwargs)
                ):
                    yield chunk
            else:
                # Use default fallback
                async for chunk in self.error_handler.handle_streaming_error(
                    error,
                    lambda: self.error_handler.create_fallback_response(query, str(error))
                ):
                    yield chunk


# Global instances
streaming_error_handler = StreamingErrorHandler()
streaming_fallback_manager = StreamingFallbackManager()


# Utility functions
def handle_streaming_error(error: Exception) -> StreamingError:
    """Convenience function to classify streaming errors."""
    return streaming_error_handler.classify_error(error)


async def create_error_response(
    error: Exception,
    query: str = "",
    fallback_handler: Optional[Callable] = None
) -> AsyncGenerator[str, None]:
    """Convenience function to create error responses."""
    async for chunk in streaming_error_handler.handle_streaming_error(
        error, fallback_handler
    ):
        yield chunk