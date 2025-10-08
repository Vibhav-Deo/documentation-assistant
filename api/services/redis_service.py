import redis
import json
import os
from typing import Optional, Dict, Any
from datetime import timedelta

class RedisService:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.client = redis.from_url(self.redis_url, decode_responses=True)
        self.session_ttl = 86400  # 24 hours
        self.cache_ttl = 3600     # 1 hour
    
    def set_session(self, session_id: str, user_data: Dict, ttl: int = None) -> bool:
        """Store user session"""
        try:
            ttl = ttl or self.session_ttl
            return self.client.setex(
                f"session:{session_id}",
                ttl,
                json.dumps(user_data)
            )
        except Exception:
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get user session"""
        try:
            data = self.client.get(f"session:{session_id}")
            return json.loads(data) if data else None
        except Exception:
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete user session"""
        try:
            return bool(self.client.delete(f"session:{session_id}"))
        except Exception:
            return False
    
    def set_cache(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set cache value"""
        try:
            ttl = ttl or self.cache_ttl
            return self.client.setex(
                f"cache:{key}",
                ttl,
                json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            )
        except Exception:
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value"""
        try:
            data = self.client.get(f"cache:{key}")
            if data:
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return data
            return None
        except Exception:
            return None
    
    def delete_cache(self, key: str) -> bool:
        """Delete cache value"""
        try:
            return bool(self.client.delete(f"cache:{key}"))
        except Exception:
            return False
    
    def clear_cache(self, pattern: str = "cache:*") -> int:
        """Clear cache by pattern"""
        try:
            keys = self.client.keys(pattern)
            return self.client.delete(*keys) if keys else 0
        except Exception:
            return 0
    
    def increment_counter(self, key: str, ttl: int = None) -> int:
        """Increment counter with optional TTL"""
        try:
            pipe = self.client.pipeline()
            pipe.incr(f"counter:{key}")
            if ttl:
                pipe.expire(f"counter:{key}", ttl)
            results = pipe.execute()
            return results[0]
        except Exception:
            return 0
    
    def get_counter(self, key: str) -> int:
        """Get counter value"""
        try:
            value = self.client.get(f"counter:{key}")
            return int(value) if value else 0
        except Exception:
            return 0
    
    def set_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Set rate limit (requests per window)"""
        try:
            current = self.increment_counter(key, window)
            return current <= limit
        except Exception:
            return False

# Global Redis service
redis_service = RedisService()