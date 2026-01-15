"""Simple in-memory caching with TTL support."""

import asyncio
import time
from typing import Any, Optional, Dict, Callable, TypeVar, Tuple
from dataclasses import dataclass
from functools import wraps
import hashlib
import json

T = TypeVar('T')


@dataclass
class CacheEntry:
    """Cache entry with value and expiration time."""
    value: Any
    expires_at: float
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() > self.expires_at


class MemoryCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = asyncio.Lock()
    
    def _make_key(self, *args, **kwargs) -> str:
        """Create cache key from arguments."""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def _cleanup_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
            self._access_times.pop(key, None)
    
    async def _evict_lru(self):
        """Evict least recently used entries if cache is full."""
        while len(self._cache) >= self.max_size:
            # Find least recently used key
            lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
            del self._cache[lru_key]
            del self._access_times[lru_key]
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            await self._cleanup_expired()
            
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                self._access_times.pop(key, None)
                return None
            
            # Update access time
            self._access_times[key] = time.time()
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        if ttl is None:
            ttl = self.default_ttl
        
        expires_at = time.time() + ttl
        entry = CacheEntry(value=value, expires_at=expires_at)
        
        async with self._lock:
            await self._cleanup_expired()
            await self._evict_lru()
            
            self._cache[key] = entry
            self._access_times[key] = time.time()
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._access_times.pop(key, None)
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate cache key for function call."""
        return f"{func_name}:{self._make_key(*args, **kwargs)}"


def cached(ttl: int = 300, cache_instance: Optional[MemoryCache] = None):
    """Decorator to cache function results."""
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        nonlocal cache_instance
        if cache_instance is None:
            cache_instance = MemoryCache(default_ttl=ttl)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = cache_instance.cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache_instance.set(cache_key, result, ttl)
            return result
        
        # Add cache control methods to function
        wrapper.cache_clear = lambda: cache_instance.clear()
        wrapper.cache_delete = lambda *args, **kwargs: cache_instance.delete(
            cache_instance.cache_key(func.__name__, *args, **kwargs)
        )
        
        return wrapper
    
    return decorator


# Global cache instance
global_cache = MemoryCache(default_ttl=300, max_size=1000)