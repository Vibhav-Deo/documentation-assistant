"""
Streaming Utilities

Provides utilities for Server-Sent Events (SSE) formatting, event management,
and streaming response handling with consistent structure and validation.
"""

import json
import time
import uuid
from typing import Dict, Any, Optional, Union
from models import (
    StreamingEvent, StreamingEventType, SearchMetadata, SearchSource,
    ContentChunk, CompletionMetadata, StreamingError,
    MetadataEvent, SourcesEvent, ContentEvent, CompleteEvent, ErrorEvent
)


class StreamingEventFormatter:
    """
    Utility class for formatting streaming events as Server-Sent Events (SSE).
    
    Provides consistent event formatting, validation, and serialization
    for all streaming response types.
    """
    
    @staticmethod
    def format_sse_event(
        event_type: StreamingEventType,
        data: Union[Dict[str, Any], SearchMetadata, ContentChunk, CompletionMetadata, StreamingError],
        event_id: Optional[str] = None,
        timestamp: Optional[float] = None
    ) -> str:
        """
        Format data as Server-Sent Event with proper structure.
        
        Args:
            event_type: Type of streaming event
            data: Event data (dict or Pydantic model)
            event_id: Optional unique event identifier
            timestamp: Optional timestamp (defaults to current time)
            
        Returns:
            Formatted SSE string
        """
        if timestamp is None:
            timestamp = time.time()
            
        if event_id is None:
            event_id = str(uuid.uuid4())[:8]
        
        # Convert Pydantic models to dict
        if hasattr(data, 'dict'):
            data_dict = data.dict()
        else:
            data_dict = data
        
        event = {
            "type": event_type.value,
            "data": data_dict,
            "timestamp": timestamp,
            "event_id": event_id
        }
        
        return f"data: {json.dumps(event)}\n\n"
    
    @staticmethod
    def format_metadata_event(
        processing_time: float,
        sources_searched: Dict[str, int],
        total_results: int,
        query_id: Optional[str] = None
    ) -> str:
        """Format search metadata event."""
        metadata = SearchMetadata(
            processing_time=processing_time,
            sources_searched=sources_searched,
            total_results=total_results,
            query_id=query_id
        )
        
        return StreamingEventFormatter.format_sse_event(
            StreamingEventType.METADATA,
            metadata
        )
    
    @staticmethod
    def format_sources_event(sources: list) -> str:
        """Format search sources event."""
        # Validate and convert sources to SearchSource models
        validated_sources = []
        for source in sources:
            if isinstance(source, dict):
                validated_sources.append(SearchSource(**source))
            else:
                validated_sources.append(source)
        
        sources_data = {"sources": [s.dict() for s in validated_sources]}
        
        return StreamingEventFormatter.format_sse_event(
            StreamingEventType.SOURCES,
            sources_data
        )
    
    @staticmethod
    def format_content_event(
        chunk: str,
        chunk_id: Optional[int] = None,
        total_chunks: Optional[int] = None
    ) -> str:
        """Format content chunk event."""
        content = ContentChunk(
            chunk=chunk,
            chunk_id=chunk_id,
            total_chunks=total_chunks
        )
        
        return StreamingEventFormatter.format_sse_event(
            StreamingEventType.CONTENT,
            content
        )
    
    @staticmethod
    def format_complete_event(
        total_tokens: int,
        model_used: Optional[str],
        final_processing_time: float,
        query_metadata: Dict[str, Any]
    ) -> str:
        """Format completion event."""
        completion = CompletionMetadata(
            total_tokens=total_tokens,
            model_used=model_used,
            final_processing_time=final_processing_time,
            query_metadata=query_metadata
        )
        
        return StreamingEventFormatter.format_sse_event(
            StreamingEventType.COMPLETE,
            completion
        )
    
    @staticmethod
    def format_error_event(
        error_type: str,
        message: str,
        recoverable: bool = True,
        error_code: Optional[str] = None
    ) -> str:
        """Format error event."""
        error = StreamingError(
            error_type=error_type,
            message=message,
            recoverable=recoverable,
            error_code=error_code
        )
        
        return StreamingEventFormatter.format_sse_event(
            StreamingEventType.ERROR,
            error
        )


class StreamingEventValidator:
    """
    Utility class for validating streaming events and ensuring data consistency.
    """
    
    @staticmethod
    def validate_event_sequence(events: list) -> Dict[str, Any]:
        """
        Validate that streaming events follow the correct sequence.
        
        Expected sequence: metadata -> sources -> content (multiple) -> complete
        
        Args:
            events: List of streaming events
            
        Returns:
            Validation result with status and details
        """
        if not events:
            return {"valid": False, "error": "No events provided"}
        
        event_types = [event.get("type") for event in events]
        
        # Check for required events
        required_events = [StreamingEventType.METADATA, StreamingEventType.COMPLETE]
        missing_events = [event for event in required_events if event.value not in event_types]
        
        if missing_events:
            return {
                "valid": False,
                "error": f"Missing required events: {missing_events}"
            }
        
        # Check event order
        metadata_index = event_types.index(StreamingEventType.METADATA.value)
        complete_index = event_types.index(StreamingEventType.COMPLETE.value)
        
        if metadata_index != 0:
            return {"valid": False, "error": "Metadata event must be first"}
        
        if complete_index != len(events) - 1:
            return {"valid": False, "error": "Complete event must be last"}
        
        # Check for error events
        error_events = [i for i, event_type in enumerate(event_types) 
                      if event_type == StreamingEventType.ERROR.value]
        
        if error_events:
            # If there are error events, they should be the last event
            if error_events[-1] != len(events) - 1:
                return {"valid": False, "error": "Error event should be the final event"}
        
        return {"valid": True, "event_count": len(events)}
    
    @staticmethod
    def validate_event_data(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate individual event data structure.
        
        Args:
            event: Single streaming event
            
        Returns:
            Validation result
        """
        required_fields = ["type", "data", "timestamp"]
        missing_fields = [field for field in required_fields if field not in event]
        
        if missing_fields:
            return {
                "valid": False,
                "error": f"Missing required fields: {missing_fields}"
            }
        
        # Validate event type
        try:
            event_type = StreamingEventType(event["type"])
        except ValueError:
            return {
                "valid": False,
                "error": f"Invalid event type: {event['type']}"
            }
        
        # Validate timestamp
        if not isinstance(event["timestamp"], (int, float)):
            return {
                "valid": False,
                "error": "Timestamp must be a number"
            }
        
        # Validate data structure based on event type
        data = event["data"]
        
        if event_type == StreamingEventType.METADATA:
            required_data_fields = ["processing_time", "sources_searched", "total_results"]
        elif event_type == StreamingEventType.SOURCES:
            required_data_fields = ["sources"]
        elif event_type == StreamingEventType.CONTENT:
            required_data_fields = ["chunk"]
        elif event_type == StreamingEventType.COMPLETE:
            required_data_fields = ["total_tokens", "final_processing_time", "query_metadata"]
        elif event_type == StreamingEventType.ERROR:
            required_data_fields = ["error_type", "message"]
        else:
            return {"valid": False, "error": f"Unknown event type: {event_type}"}
        
        missing_data_fields = [field for field in required_data_fields if field not in data]
        if missing_data_fields:
            return {
                "valid": False,
                "error": f"Missing data fields for {event_type}: {missing_data_fields}"
            }
        
        return {"valid": True}


class StreamingMetricsCollector:
    """
    Utility class for collecting metrics and performance data from streaming events.
    """
    
    def __init__(self):
        self.events = []
        self.start_time = None
        self.end_time = None
    
    def add_event(self, event: Dict[str, Any]):
        """Add an event to the metrics collection."""
        if self.start_time is None:
            self.start_time = event.get("timestamp", time.time())
        
        self.events.append(event)
        
        if event.get("type") in [StreamingEventType.COMPLETE.value, StreamingEventType.ERROR.value]:
            self.end_time = event.get("timestamp", time.time())
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Calculate and return streaming metrics.
        
        Returns:
            Dictionary containing performance and quality metrics
        """
        if not self.events:
            return {"error": "No events recorded"}
        
        metrics = {
            "total_events": len(self.events),
            "event_types": {},
            "total_duration": None,
            "content_chunks": 0,
            "total_content_length": 0,
            "average_chunk_size": 0,
            "errors": []
        }
        
        # Count event types
        for event in self.events:
            event_type = event.get("type", "unknown")
            metrics["event_types"][event_type] = metrics["event_types"].get(event_type, 0) + 1
        
        # Calculate duration
        if self.start_time and self.end_time:
            metrics["total_duration"] = self.end_time - self.start_time
        
        # Analyze content events
        content_events = [e for e in self.events if e.get("type") == StreamingEventType.CONTENT.value]
        metrics["content_chunks"] = len(content_events)
        
        if content_events:
            total_length = sum(len(e.get("data", {}).get("chunk", "")) for e in content_events)
            metrics["total_content_length"] = total_length
            metrics["average_chunk_size"] = total_length / len(content_events)
        
        # Collect errors
        error_events = [e for e in self.events if e.get("type") == StreamingEventType.ERROR.value]
        metrics["errors"] = [e.get("data", {}) for e in error_events]
        
        # Calculate streaming efficiency
        if metrics["total_duration"] and metrics["content_chunks"]:
            metrics["chunks_per_second"] = metrics["content_chunks"] / metrics["total_duration"]
            metrics["characters_per_second"] = metrics["total_content_length"] / metrics["total_duration"]
        
        return metrics


class StreamingResponseBuilder:
    """
    Utility class for building streaming responses with proper event sequencing.
    """
    
    def __init__(self, query_id: Optional[str] = None):
        self.query_id = query_id or str(uuid.uuid4())[:8]
        self.start_time = time.time()
        self.events_sent = []
        self.metrics_collector = StreamingMetricsCollector()
    
    async def send_metadata(
        self,
        sources_searched: Dict[str, int],
        total_results: int
    ) -> str:
        """Send metadata event."""
        processing_time = time.time() - self.start_time
        
        event = StreamingEventFormatter.format_metadata_event(
            processing_time=processing_time,
            sources_searched=sources_searched,
            total_results=total_results,
            query_id=self.query_id
        )
        
        self.events_sent.append("metadata")
        return event
    
    async def send_sources(self, sources: list) -> str:
        """Send sources event."""
        event = StreamingEventFormatter.format_sources_event(sources)
        self.events_sent.append("sources")
        return event
    
    async def send_content_chunk(
        self,
        chunk: str,
        chunk_id: Optional[int] = None,
        total_chunks: Optional[int] = None
    ) -> str:
        """Send content chunk event."""
        event = StreamingEventFormatter.format_content_event(
            chunk=chunk,
            chunk_id=chunk_id,
            total_chunks=total_chunks
        )
        
        self.events_sent.append("content")
        return event
    
    async def send_completion(
        self,
        total_tokens: int,
        model_used: Optional[str],
        query_metadata: Dict[str, Any]
    ) -> str:
        """Send completion event."""
        final_processing_time = time.time() - self.start_time
        
        event = StreamingEventFormatter.format_complete_event(
            total_tokens=total_tokens,
            model_used=model_used,
            final_processing_time=final_processing_time,
            query_metadata=query_metadata
        )
        
        self.events_sent.append("complete")
        return event
    
    async def send_error(
        self,
        error_type: str,
        message: str,
        recoverable: bool = True,
        error_code: Optional[str] = None
    ) -> str:
        """Send error event."""
        event = StreamingEventFormatter.format_error_event(
            error_type=error_type,
            message=message,
            recoverable=recoverable,
            error_code=error_code
        )
        
        self.events_sent.append("error")
        return event
    
    def get_streaming_metrics(self) -> Dict[str, Any]:
        """Get metrics for this streaming session."""
        return {
            "query_id": self.query_id,
            "events_sent": self.events_sent,
            "total_duration": time.time() - self.start_time,
            "event_count": len(self.events_sent)
        }


# Utility functions for common streaming operations
def create_streaming_headers() -> Dict[str, str]:
    """Create standard headers for streaming responses."""
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Cache-Control"
    }


def validate_streaming_request(query: dict) -> Dict[str, Any]:
    """
    Validate that a request is suitable for streaming.
    
    Args:
        query: Query parameters
        
    Returns:
        Validation result
    """
    if not query.get("stream", False):
        return {"valid": False, "error": "Streaming not requested"}
    
    if not query.get("question"):
        return {"valid": False, "error": "Question is required for streaming"}
    
    # Check for reasonable limits
    max_results = query.get("max_results", 5)
    if max_results > 50:
        return {"valid": False, "error": "max_results too high for streaming (limit: 50)"}
    
    return {"valid": True}


def estimate_streaming_duration(
    query_length: int,
    max_results: int,
    model: str = "mistral"
) -> float:
    """
    Estimate streaming response duration based on query parameters.
    
    Args:
        query_length: Length of the question
        max_results: Maximum search results
        model: AI model being used
        
    Returns:
        Estimated duration in seconds
    """
    # Base time for search and processing
    base_time = 1.0
    
    # Search time based on max_results
    search_time = max_results * 0.1
    
    # AI generation time based on query complexity and model
    model_multipliers = {
        "mistral": 1.0,
        "llama2": 1.2,
        "codellama": 1.1
    }
    
    generation_time = (query_length / 100) * model_multipliers.get(model, 1.0)
    
    return base_time + search_time + generation_time