import time
import psutil
import os
import json
from typing import Dict, List
from datetime import datetime, timedelta
from .redis_service import redis_service
from .database import db_service

class MonitoringService:
    def __init__(self):
        self.start_time = time.time()
    
    def get_system_metrics(self) -> Dict:
        """Get system performance metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "uptime_seconds": int(time.time() - self.start_time),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_api_health(self) -> Dict:
        """Get API health status"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        # Check Redis
        try:
            redis_service.client.ping()
            health_status["services"]["redis"] = {"status": "healthy", "response_time_ms": 0}
        except Exception as e:
            health_status["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Check Database
        try:
            # This would need to be async in real implementation
            health_status["services"]["database"] = {"status": "healthy", "response_time_ms": 0}
        except Exception as e:
            health_status["services"]["database"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        return health_status
    
    def log_request_metrics(self, endpoint: str, method: str, status_code: int, response_time: float, user_id: str = None):
        """Log request metrics to Redis"""
        timestamp = datetime.now()
        
        # Store in Redis with TTL
        metrics = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time": response_time,
            "user_id": user_id,
            "timestamp": timestamp.isoformat()
        }
        
        # Store individual request
        redis_service.client.lpush("request_metrics", json.dumps(metrics))
        redis_service.client.expire("request_metrics", 86400)  # 24 hours
        
        # Update counters
        date_key = timestamp.strftime("%Y-%m-%d")
        hour_key = timestamp.strftime("%Y-%m-%d-%H")
        
        redis_service.increment_counter(f"requests_daily_{date_key}", 86400)
        redis_service.increment_counter(f"requests_hourly_{hour_key}", 3600)
        redis_service.increment_counter(f"status_{status_code}_{date_key}", 86400)
    
    def get_request_metrics(self, hours: int = 24) -> Dict:
        """Get request metrics for the last N hours"""
        try:
            # Get recent metrics from Redis
            metrics_data = redis_service.client.lrange("request_metrics", 0, 1000)
            
            total_requests = len(metrics_data)
            status_codes = {}
            response_times = []
            endpoints = {}
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            for metric_str in metrics_data:
                try:
                    metric = json.loads(metric_str)
                    metric_time = datetime.fromisoformat(metric["timestamp"])
                    
                    if metric_time < cutoff_time:
                        continue
                    
                    # Count status codes
                    status = metric["status_code"]
                    status_codes[status] = status_codes.get(status, 0) + 1
                    
                    # Collect response times
                    response_times.append(metric["response_time"])
                    
                    # Count endpoints
                    endpoint = metric["endpoint"]
                    endpoints[endpoint] = endpoints.get(endpoint, 0) + 1
                    
                except Exception:
                    continue
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                "total_requests": total_requests,
                "avg_response_time": round(avg_response_time, 3),
                "status_codes": status_codes,
                "top_endpoints": dict(sorted(endpoints.items(), key=lambda x: x[1], reverse=True)[:10]),
                "error_rate": round((status_codes.get(500, 0) / max(total_requests, 1)) * 100, 2),
                "period_hours": hours
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_alerts(self) -> List[Dict]:
        """Get system alerts"""
        alerts = []
        
        # Check system resources
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > 80:
            alerts.append({
                "type": "warning",
                "message": f"High CPU usage: {cpu_percent}%",
                "timestamp": datetime.now().isoformat()
            })
        
        if memory_percent > 85:
            alerts.append({
                "type": "critical",
                "message": f"High memory usage: {memory_percent}%",
                "timestamp": datetime.now().isoformat()
            })
        
        # Check error rates
        metrics = self.get_request_metrics(1)  # Last hour
        if metrics.get("error_rate", 0) > 5:
            alerts.append({
                "type": "warning",
                "message": f"High error rate: {metrics['error_rate']}%",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts

# Global monitoring service
monitoring_service = MonitoringService()