from cachetools import TTLCache
from functools import wraps
import hashlib
import json
from typing import Any, Callable
from app.config import settings

# Global caches with different TTLs
quote_cache = TTLCache(maxsize=500, ttl=settings.CACHE_TTL_QUOTES)
mover_cache = TTLCache(maxsize=100, ttl=settings.CACHE_TTL_MOVERS)
breadth_cache = TTLCache(maxsize=10, ttl=settings.CACHE_TTL_BREADTH)
sector_cache = TTLCache(maxsize=50, ttl=settings.CACHE_TTL_SECTORS)
macro_cache = TTLCache(maxsize=50, ttl=settings.CACHE_TTL_MACRO)

def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()

def cached(cache: TTLCache):
    """Decorator for caching async function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = cache_key(*args, **kwargs)
            if key in cache:
                return cache[key]
            result = await func(*args, **kwargs)
            cache[key] = result
            return result
        return wrapper
    return decorator
