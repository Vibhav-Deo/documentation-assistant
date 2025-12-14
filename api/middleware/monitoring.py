"""
Monitoring Integration Middleware

Provides integration with monitoring and observability systems,
including metrics collection, health checks, and alerting.
"""

import time
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Represents a single metric data point."""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Represents a health check configuration."""
    name: str
    check_function: Callable
    timeout: float = 5.0
    critical: bool = True
    interval: float = 30.0
    last_check: Optional[float] = None
    last_result: Optional[bool] = None
    last_error: Optional[str] = None


class MetricsCollector:
    """
    Collects and stores application metrics for monitoring.
    
    In production, this would integrate with systems like Prometheus,
    DataDog, or CloudWatch. This implementation provides a foundation
    that can be extended with proper metric backends.
    """
    
    def __init__(self, max_points: int = 10000):
        self.max_points = max_points
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.start_time = time.time()
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment a counter metric."""
        key = self._build_key(name, labels)
        self.counters[key] += value
        self._add_metric_point(name, self.counters[key], labels)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric value."""
        key = self._build_key(name, labels)
        self.gauges[key] = value
        self._add_metric_point(name, value, labels)
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Add an observation to a histogram metric."""
        key = self._build_key(name, labels)
        self.histograms[key].append(value)
        
        # Keep only recent observations (last 1000)
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
        
        self._add_metric_point(name, value, labels)
    
    def get_counter(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get current counter value."""
        key = self._build_key(name, labels)
        return self.counters.get(key, 0.0)
    
    def get_gauge(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get current gauge value."""
        key = self._build_key(name, labels)
        return self.gauges.get(key, 0.0)
    
    def get_histogram_stats(self, name: str, labels: Dict[str, str] = None) -> Dict[str, float]:
        """Get histogram statistics."""
        key = self._build_key(name, labels)
        values = self.histograms.get(key, [])
        
        if not values:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0, "p50": 0, "p95": 0, "p99": 0}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "sum": sum(sorted_values),
            "avg": sum(sorted_values) / count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p50": self._percentile(sorted_values, 0.5),
            "p95": self._percentile(sorted_values, 0.95),
            "p99": self._percentile(sorted_values, 0.99)
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                key: self.get_histogram_stats("", {"key": key})
                for key in self.histograms.keys()
            },
            "uptime_seconds": time.time() - self.start_time,
            "timestamp": time.time()
        }
    
    def _build_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Build a unique key for the metric."""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def _add_metric_point(self, name: str, value: float, labels: Dict[str, str] = None):
        """Add a metric point to the time series."""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels or {}
        )
        self.metrics[name].append(point)
    
    def _percentile(self, sorted_values: List[float], percentile: float) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        
        index = int(percentile * (len(sorted_values) - 1))
        return sorted_values[index]


class HealthChecker:
    """
    Manages health checks for various system components.
    """
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.overall_health = True
        self.last_check_time = None
    
    def register_check(
        self,
        name: str,
        check_function: Callable,
        timeout: float = 5.0,
        critical: bool = True,
        interval: float = 30.0
    ):
        """Register a new health check."""
        self.checks[name] = HealthCheck(
            name=name,
            check_function=check_function,
            timeout=timeout,
            critical=critical,
            interval=interval
        )
        logger.info(f"Registered health check: {name}")
    
    async def run_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check."""
        if name not in self.checks:
            return {"status": "error", "message": f"Health check '{name}' not found"}
        
        check = self.checks[name]
        start_time = time.time()
        
        try:
            # Run the check with timeout
            result = await asyncio.wait_for(
                check.check_function(),
                timeout=check.timeout
            )
            
            duration = time.time() - start_time
            check.last_check = time.time()
            check.last_result = True
            check.last_error = None
            
            return {
                "status": "healthy",
                "duration_seconds": round(duration, 3),
                "timestamp": check.last_check,
                "details": result if isinstance(result, dict) else {}
            }
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            check.last_check = time.time()
            check.last_result = False
            check.last_error = f"Health check timed out after {check.timeout}s"
            
            return {
                "status": "unhealthy",
                "error": check.last_error,
                "duration_seconds": round(duration, 3),
                "timestamp": check.last_check
            }
            
        except Exception as e:
            duration = time.time() - start_time
            check.last_check = time.time()
            check.last_result = False
            check.last_error = str(e)
            
            logger.error(f"Health check '{name}' failed: {e}")
            
            return {
                "status": "unhealthy",
                "error": check.last_error,
                "duration_seconds": round(duration, 3),
                "timestamp": check.last_check
            }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks."""
        results = {}
        overall_healthy = True
        
        for name in self.checks.keys():
            result = await self.run_check(name)
            results[name] = result
            
            # Check if this is a critical check that failed
            if (self.checks[name].critical and 
                result["status"] != "healthy"):
                overall_healthy = False
        
        self.overall_health = overall_healthy
        self.last_check_time = time.time()
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": self.last_check_time,
            "checks": results,
            "summary": {
                "total_checks": len(self.checks),
                "healthy_checks": len([r for r in results.values() if r["status"] == "healthy"]),
                "unhealthy_checks": len([r for r in results.values() if r["status"] == "unhealthy"])
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status without running checks."""
        return {
            "status": "healthy" if self.overall_health else "unhealthy",
            "last_check": self.last_check_time,
            "checks_registered": len(self.checks),
            "checks": {
                name: {
                    "last_result": check.last_result,
                    "last_check": check.last_check,
                    "last_error": check.last_error,
                    "critical": check.critical
                }
                for name, check in self.checks.items()
            }
        }


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting application metrics and monitoring data.
    """
    
    def __init__(
        self,
        app,
        metrics_collector: MetricsCollector,
        health_checker: HealthChecker,
        collect_detailed_metrics: bool = True
    ):
        super().__init__(app)
        self.metrics = metrics_collector
        self.health_checker = health_checker
        self.collect_detailed_metrics = collect_detailed_metrics
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect metrics for each request."""
        start_time = time.time()
        
        # Extract request labels
        labels = {
            "method": request.method,
            "endpoint": self._normalize_path(request.url.path)
        }
        
        # Increment request counter
        self.metrics.increment_counter("http_requests_total", labels=labels)
        
        # Track concurrent requests
        self.metrics.increment_counter("http_requests_in_progress")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Add status code to labels
            labels["status_code"] = str(response.status_code)
            labels["status_class"] = f"{response.status_code // 100}xx"
            
            # Record metrics
            self.metrics.observe_histogram("http_request_duration_seconds", duration, labels)
            self.metrics.increment_counter("http_responses_total", labels=labels)
            
            # Track response size if available
            if "content-length" in response.headers:
                try:
                    size = int(response.headers["content-length"])
                    self.metrics.observe_histogram("http_response_size_bytes", size, labels)
                except ValueError:
                    pass
            
            # Collect detailed metrics if enabled
            if self.collect_detailed_metrics:
                self._collect_detailed_metrics(request, response, duration)
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            labels["status_code"] = "500"
            labels["status_class"] = "5xx"
            labels["exception"] = type(e).__name__
            
            self.metrics.increment_counter("http_requests_failed_total", labels=labels)
            self.metrics.observe_histogram("http_request_duration_seconds", duration, labels)
            
            raise
            
        finally:
            # Decrement concurrent requests
            self.metrics.increment_counter("http_requests_in_progress", value=-1)
    
    def _normalize_path(self, path: str) -> str:
        """Normalize URL path for metrics (remove IDs, etc.)."""
        # Replace UUIDs and numeric IDs with placeholders
        import re
        
        # Replace UUIDs
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{uuid}',
            path,
            flags=re.IGNORECASE
        )
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace other common patterns
        path = re.sub(r'/[a-zA-Z0-9_-]{20,}', '/{token}', path)
        
        return path
    
    def _collect_detailed_metrics(self, request: Request, response: Response, duration: float):
        """Collect additional detailed metrics."""
        # Track slow requests
        if duration > 2.0:
            self.metrics.increment_counter("http_slow_requests_total", labels={
                "method": request.method,
                "endpoint": self._normalize_path(request.url.path)
            })
        
        # Track error rates by endpoint
        if response.status_code >= 400:
            self.metrics.increment_counter("http_errors_by_endpoint", labels={
                "endpoint": self._normalize_path(request.url.path),
                "status_code": str(response.status_code)
            })
        
        # Track user agent patterns (for bot detection, etc.)
        user_agent = request.headers.get("user-agent", "unknown")
        if "bot" in user_agent.lower() or "crawler" in user_agent.lower():
            self.metrics.increment_counter("http_bot_requests_total")


# Global instances (in production, these would be properly injected)
metrics_collector = MetricsCollector()
health_checker = HealthChecker()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return metrics_collector


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    return health_checker


# Common health check functions
async def database_health_check() -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        from services.infrastructure.database import db_service
        
        # Simple query to check database connectivity
        result = await db_service.execute_query("SELECT 1 as health_check")
        
        return {
            "database_connected": True,
            "query_result": result[0] if result else None
        }
    except Exception as e:
        raise Exception(f"Database health check failed: {str(e)}")


async def redis_health_check() -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        from services.infrastructure.redis_service import redis_service
        
        # Simple ping to check Redis connectivity
        await redis_service.ping()
        
        return {
            "redis_connected": True,
            "ping_successful": True
        }
    except Exception as e:
        raise Exception(f"Redis health check failed: {str(e)}")


async def qdrant_health_check() -> Dict[str, Any]:
    """Check Qdrant connectivity."""
    try:
        from services.domain.search.qdrant_indexer import qdrant_indexer
        
        if qdrant_indexer and hasattr(qdrant_indexer, 'client'):
            # Check if Qdrant is accessible
            collections = await qdrant_indexer.client.get_collections()
            
            return {
                "qdrant_connected": True,
                "collections_count": len(collections.collections) if collections else 0
            }
        else:
            return {
                "qdrant_connected": False,
                "message": "Qdrant indexer not initialized"
            }
    except Exception as e:
        raise Exception(f"Qdrant health check failed: {str(e)}")


async def ai_service_health_check() -> Dict[str, Any]:
    """Check AI service connectivity."""
    try:
        from services.domain.ai import UnifiedAIService
        # Create a simple test instance
        ai_service = UnifiedAIService(None)
        
        # Simple test query to check AI service
        test_response = ai_service.generate_response("Health check test", "mistral")
        
        return {
            "ai_service_connected": True,
            "test_response_length": len(test_response) if test_response else 0
        }
    except Exception as e:
        raise Exception(f"AI service health check failed: {str(e)}")


def register_default_health_checks():
    """Register default health checks for common services."""
    health_checker.register_check(
        "database",
        database_health_check,
        timeout=5.0,
        critical=True,
        interval=30.0
    )
    
    health_checker.register_check(
        "redis",
        redis_health_check,
        timeout=3.0,
        critical=False,
        interval=30.0
    )
    
    health_checker.register_check(
        "qdrant",
        qdrant_health_check,
        timeout=5.0,
        critical=False,
        interval=60.0
    )
    
    health_checker.register_check(
        "ai_service",
        ai_service_health_check,
        timeout=10.0,
        critical=False,
        interval=120.0
    )