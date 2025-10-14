"""
Redis Cache Decorator for Query Optimization

Provides a simple decorator to cache expensive query results in Redis.
"""

import json
import hashlib
from functools import wraps
from typing import Optional, Any
import asyncio


class QueryCache:
    """Redis-based query cache with TTL support"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"qcache:{prefix}:{key_hash}"
    
    def cache(self, prefix: str, ttl: int = 300):
        """
        Cache decorator for async functions
        
        Args:
            prefix: Cache key prefix
            ttl: Time to live in seconds (default 5 minutes)
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self.cache_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                try:
                    cached = await self.redis.get(cache_key)
                    if cached:
                        return json.loads(cached)
                except Exception as e:
                    print(f"Cache read error: {e}")
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Store in cache
                try:
                    await self.redis.setex(
                        cache_key,
                        ttl,
                        json.dumps(result, default=str)
                    )
                except Exception as e:
                    print(f"Cache write error: {e}")
                
                return result
            
            return wrapper
        return decorator
    
    async def invalidate(self, pattern: str):
        """Invalidate cache keys matching pattern"""
        try:
            keys = await self.redis.keys(f"qcache:{pattern}:*")
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            print(f"Cache invalidation error: {e}")
