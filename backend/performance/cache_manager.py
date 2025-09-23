"""
Performance Cache Manager
Advanced caching system with Redis backend, memory fallback, and intelligent cache warming
"""

import asyncio
import json
import pickle
import time
import hashlib
import logging
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import redis.asyncio as redis
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    TTL = "ttl"  # Time-to-live
    LRU = "lru"  # Least recently used
    FIFO = "fifo"  # First in, first out
    WRITE_THROUGH = "write_through"  # Write to cache and storage
    WRITE_BEHIND = "write_behind"  # Write to cache, async to storage

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None
    access_count: int = 0
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if not self.ttl:
            return False
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)

    def update_access(self):
        """Update access metadata"""
        self.accessed_at = datetime.now()
        self.access_count += 1

class PerformanceCacheManager:
    """High-performance cache manager with multiple backends and strategies"""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        memory_limit: int = 512 * 1024 * 1024,  # 512MB
        default_ttl: int = 3600,  # 1 hour
        default_strategy: CacheStrategy = CacheStrategy.LRU
    ):
        self.redis_url = redis_url
        self.memory_limit = memory_limit
        self.default_ttl = default_ttl
        self.default_strategy = default_strategy

        # Redis connection
        self.redis_client: Optional[redis.Redis] = None

        # Memory cache
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.memory_usage = 0

        # Performance metrics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'errors': 0,
            'total_requests': 0
        }

        # Cache warming tasks
        self.warming_tasks: Dict[str, asyncio.Task] = {}

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize cache manager"""
        try:
            if self.redis_url:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=False,
                    max_connections=20,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30
                )
                # Test Redis connection
                await self.redis_client.ping()
                logger.info("Redis cache backend initialized")
            else:
                logger.info("Redis not configured, using memory cache only")

        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}, falling back to memory cache")
            self.redis_client = None

    async def get(
        self,
        key: str,
        default: Any = None,
        deserializer: Optional[Callable] = None
    ) -> Any:
        """Get value from cache with performance optimizations"""
        self.stats['total_requests'] += 1

        try:
            # Try Redis first (if available)
            if self.redis_client:
                try:
                    value = await self.redis_client.get(key)
                    if value is not None:
                        self.stats['hits'] += 1
                        if deserializer:
                            return deserializer(value)
                        try:
                            return pickle.loads(value)
                        except:
                            return json.loads(value.decode('utf-8'))
                except Exception as e:
                    logger.warning(f"Redis get error for key {key}: {e}")

            # Try memory cache
            async with self._lock:
                if key in self.memory_cache:
                    entry = self.memory_cache[key]
                    if not entry.is_expired():
                        entry.update_access()
                        self.stats['hits'] += 1
                        return entry.value
                    else:
                        # Remove expired entry
                        self._remove_from_memory(key)

            # Cache miss
            self.stats['misses'] += 1
            return default

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache get error for key {key}: {e}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        strategy: Optional[CacheStrategy] = None,
        tags: Optional[List[str]] = None,
        serializer: Optional[Callable] = None
    ) -> bool:
        """Set value in cache with performance optimizations"""
        ttl = ttl or self.default_ttl
        strategy = strategy or self.default_strategy
        tags = tags or []

        try:
            # Serialize value
            if serializer:
                serialized_value = serializer(value)
            else:
                try:
                    serialized_value = pickle.dumps(value)
                except:
                    serialized_value = json.dumps(value).encode('utf-8')

            size_bytes = len(serialized_value) if isinstance(serialized_value, bytes) else len(str(serialized_value))

            # Set in Redis (if available)
            if self.redis_client:
                try:
                    await self.redis_client.setex(key, ttl, serialized_value)
                    # Set tags in Redis
                    if tags:
                        for tag in tags:
                            await self.redis_client.sadd(f"tag:{tag}", key)
                            await self.redis_client.expire(f"tag:{tag}", ttl)
                except Exception as e:
                    logger.warning(f"Redis set error for key {key}: {e}")

            # Set in memory cache
            async with self._lock:
                # Check memory limit and evict if necessary
                await self._ensure_memory_limit(size_bytes)

                entry = CacheEntry(
                    key=key,
                    value=value,
                    ttl=ttl,
                    size_bytes=size_bytes,
                    tags=tags
                )

                self.memory_cache[key] = entry
                self.memory_usage += size_bytes

            return True

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            deleted = False

            # Delete from Redis
            if self.redis_client:
                try:
                    result = await self.redis_client.delete(key)
                    deleted = result > 0
                except Exception as e:
                    logger.warning(f"Redis delete error for key {key}: {e}")

            # Delete from memory cache
            async with self._lock:
                if key in self.memory_cache:
                    self._remove_from_memory(key)
                    deleted = True

            return deleted

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_by_tag(self, tag: str) -> int:
        """Delete all keys with a specific tag"""
        deleted_count = 0

        try:
            # Get keys by tag from Redis
            if self.redis_client:
                try:
                    keys = await self.redis_client.smembers(f"tag:{tag}")
                    if keys:
                        deleted_count += await self.redis_client.delete(*keys)
                        await self.redis_client.delete(f"tag:{tag}")
                except Exception as e:
                    logger.warning(f"Redis delete by tag error for tag {tag}: {e}")

            # Delete from memory cache
            async with self._lock:
                keys_to_delete = [
                    key for key, entry in self.memory_cache.items()
                    if tag in entry.tags
                ]
                for key in keys_to_delete:
                    self._remove_from_memory(key)
                    deleted_count += 1

            return deleted_count

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache delete by tag error for tag {tag}: {e}")
            return 0

    async def clear(self) -> bool:
        """Clear all cache entries"""
        try:
            # Clear Redis
            if self.redis_client:
                try:
                    await self.redis_client.flushdb()
                except Exception as e:
                    logger.warning(f"Redis clear error: {e}")

            # Clear memory cache
            async with self._lock:
                self.memory_cache.clear()
                self.memory_usage = 0

            return True

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache clear error: {e}")
            return False

    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[int] = None,
        **kwargs
    ) -> Any:
        """Get value from cache or set it using factory function"""
        value = await self.get(key)

        if value is None:
            # Generate value using factory
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()

            # Set in cache
            await self.set(key, value, ttl, **kwargs)

        return value

    async def warm_cache(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[int] = None,
        interval: int = 300  # 5 minutes
    ):
        """Warm cache by periodically refreshing a key"""
        async def warm_task():
            while True:
                try:
                    if asyncio.iscoroutinefunction(factory):
                        value = await factory()
                    else:
                        value = factory()

                    await self.set(key, value, ttl)
                    await asyncio.sleep(interval)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Cache warming error for key {key}: {e}")
                    await asyncio.sleep(interval)

        # Cancel existing warming task
        if key in self.warming_tasks:
            self.warming_tasks[key].cancel()

        # Start new warming task
        self.warming_tasks[key] = asyncio.create_task(warm_task())

    def _remove_from_memory(self, key: str):
        """Remove entry from memory cache (not thread-safe)"""
        if key in self.memory_cache:
            entry = self.memory_cache.pop(key)
            self.memory_usage -= entry.size_bytes

    async def _ensure_memory_limit(self, incoming_size: int):
        """Ensure memory usage stays within limits"""
        if self.memory_usage + incoming_size <= self.memory_limit:
            return

        # Need to evict entries
        target_usage = self.memory_limit - incoming_size

        if self.default_strategy == CacheStrategy.LRU:
            # Sort by access time (least recently used first)
            sorted_entries = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].accessed_at
            )
        elif self.default_strategy == CacheStrategy.FIFO:
            # Sort by creation time (first in, first out)
            sorted_entries = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].created_at
            )
        else:
            # Default to LRU
            sorted_entries = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].accessed_at
            )

        # Evict entries until we're under the target
        for key, entry in sorted_entries:
            if self.memory_usage <= target_usage:
                break

            self._remove_from_memory(key)
            self.stats['evictions'] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        hit_rate = 0
        if self.stats['total_requests'] > 0:
            hit_rate = self.stats['hits'] / self.stats['total_requests']

        return {
            'hit_rate': hit_rate,
            'memory_usage': self.memory_usage,
            'memory_limit': self.memory_limit,
            'memory_utilization': self.memory_usage / self.memory_limit,
            'entry_count': len(self.memory_cache),
            'redis_available': self.redis_client is not None,
            **self.stats
        }

    async def cleanup(self):
        """Cleanup cache manager"""
        # Cancel warming tasks
        for task in self.warming_tasks.values():
            task.cancel()

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()


# Global cache manager instance
cache_manager = PerformanceCacheManager()

# Decorator for caching function results
def cached(
    ttl: int = 3600,
    key_prefix: str = "",
    tags: Optional[List[str]] = None
):
    """Decorator for caching function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = f"{key_prefix}:{func.__name__}:{args}:{sorted(kwargs.items())}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()

            # Try to get from cache
            result = await cache_manager.get(cache_key)
            if result is not None:
                return result

            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Store in cache
            await cache_manager.set(cache_key, result, ttl, tags=tags)
            return result

        return wrapper
    return decorator