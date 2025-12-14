"""
Response Formatter Utility

Provides consistent API response formatting across all endpoints.
"""

import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class ResponseFormatter:
    """
    Utility class for creating consistent API responses.
    
    Features:
    - Standardized success/error response formats
    - Metadata inclusion (timing, pagination, etc.)
    - Data transformation helpers
    - Response validation
    """
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Operation completed successfully",
        metadata: Optional[Dict] = None,
        status_code: int = 200
    ) -> Dict[str, Any]:
        """
        Create a standardized success response.
        
        Args:
            data: Response data
            message: Success message
            metadata: Additional metadata
            status_code: HTTP status code
            
        Returns:
            Formatted success response
        """
        response = {
            "success": True,
            "status_code": status_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if data is not None:
            response["data"] = data
        
        if metadata:
            response["metadata"] = metadata
        
        return response
    
    @staticmethod
    def error(
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict] = None,
        status_code: int = 500
    ) -> Dict[str, Any]:
        """
        Create a standardized error response.
        
        Args:
            message: Error message
            error_code: Specific error code
            details: Additional error details
            status_code: HTTP status code
            
        Returns:
            Formatted error response
        """
        response = {
            "success": False,
            "status_code": status_code,
            "error": {
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
        
        if error_code:
            response["error"]["code"] = error_code
        
        if details:
            response["error"]["details"] = details
        
        return response
    
    @staticmethod
    def paginated(
        items: List[Any],
        total: int,
        page: int = 1,
        page_size: int = 20,
        message: str = "Data retrieved successfully"
    ) -> Dict[str, Any]:
        """
        Create a paginated response.
        
        Args:
            items: List of items for current page
            total: Total number of items
            page: Current page number
            page_size: Items per page
            message: Success message
            
        Returns:
            Formatted paginated response
        """
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1
        
        return ResponseFormatter.success(
            data=items,
            message=message,
            metadata={
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_items": total,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_previous": has_prev,
                    "items_on_page": len(items)
                }
            }
        )
    
    @staticmethod
    def search_results(
        query: str,
        results: List[Any],
        total_found: int,
        search_time: float,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a search results response.
        
        Args:
            query: Search query
            results: Search results
            total_found: Total number of results found
            search_time: Time taken for search
            filters: Applied filters
            
        Returns:
            Formatted search response
        """
        return ResponseFormatter.success(
            data=results,
            message=f"Found {total_found} results for query: {query}",
            metadata={
                "search": {
                    "query": query,
                    "total_found": total_found,
                    "results_returned": len(results),
                    "search_time_seconds": round(search_time, 3),
                    "filters": filters or {}
                }
            }
        )
    
    @staticmethod
    def analysis_results(
        analysis_type: str,
        results: Any,
        processing_time: float,
        confidence: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create an analysis results response.
        
        Args:
            analysis_type: Type of analysis performed
            results: Analysis results
            processing_time: Time taken for analysis
            confidence: Confidence score (0-1)
            metadata: Additional metadata
            
        Returns:
            Formatted analysis response
        """
        analysis_metadata = {
            "analysis": {
                "type": analysis_type,
                "processing_time_seconds": round(processing_time, 3),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        if confidence is not None:
            analysis_metadata["analysis"]["confidence"] = confidence
        
        if metadata:
            analysis_metadata.update(metadata)
        
        return ResponseFormatter.success(
            data=results,
            message=f"{analysis_type} analysis completed successfully",
            metadata=analysis_metadata
        )
    
    @staticmethod
    def operation_status(
        operation: str,
        status: str,
        progress: Optional[float] = None,
        details: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create an operation status response.
        
        Args:
            operation: Operation name
            status: Current status
            progress: Progress percentage (0-100)
            details: Additional details
            
        Returns:
            Formatted status response
        """
        status_metadata = {
            "operation": {
                "name": operation,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        if progress is not None:
            status_metadata["operation"]["progress_percent"] = progress
        
        if details:
            status_metadata["operation"]["details"] = details
        
        return ResponseFormatter.success(
            message=f"Operation {operation} is {status}",
            metadata=status_metadata
        )
    
    @staticmethod
    def validation_error(
        field_errors: Dict[str, List[str]],
        message: str = "Validation failed"
    ) -> Dict[str, Any]:
        """
        Create a validation error response.
        
        Args:
            field_errors: Dictionary of field names to error lists
            message: Error message
            
        Returns:
            Formatted validation error response
        """
        return ResponseFormatter.error(
            message=message,
            error_code="VALIDATION_ERROR",
            details={
                "field_errors": field_errors,
                "total_errors": sum(len(errors) for errors in field_errors.values())
            },
            status_code=422
        )
    
    @staticmethod
    def not_found(
        resource: str,
        identifier: str = None
    ) -> Dict[str, Any]:
        """
        Create a not found error response.
        
        Args:
            resource: Resource type that was not found
            identifier: Resource identifier
            
        Returns:
            Formatted not found response
        """
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        
        return ResponseFormatter.error(
            message=message,
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
            status_code=404
        )
    
    @staticmethod
    def unauthorized(
        message: str = "Authentication required"
    ) -> Dict[str, Any]:
        """
        Create an unauthorized error response.
        
        Args:
            message: Error message
            
        Returns:
            Formatted unauthorized response
        """
        return ResponseFormatter.error(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401
        )
    
    @staticmethod
    def forbidden(
        message: str = "Access denied"
    ) -> Dict[str, Any]:
        """
        Create a forbidden error response.
        
        Args:
            message: Error message
            
        Returns:
            Formatted forbidden response
        """
        return ResponseFormatter.error(
            message=message,
            error_code="FORBIDDEN",
            status_code=403
        )
    
    @staticmethod
    def rate_limited(
        retry_after: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a rate limited error response.
        
        Args:
            retry_after: Seconds to wait before retrying
            
        Returns:
            Formatted rate limited response
        """
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        return ResponseFormatter.error(
            message="Rate limit exceeded",
            error_code="RATE_LIMITED",
            details=details,
            status_code=429
        )
    
    @staticmethod
    def service_unavailable(
        service: str,
        message: str = None
    ) -> Dict[str, Any]:
        """
        Create a service unavailable error response.
        
        Args:
            service: Service name that is unavailable
            message: Custom error message
            
        Returns:
            Formatted service unavailable response
        """
        if not message:
            message = f"{service} service is currently unavailable"
        
        return ResponseFormatter.error(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service},
            status_code=503
        )