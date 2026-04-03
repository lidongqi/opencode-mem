"""Memory cache system for intelligent memory queries."""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from collections import OrderedDict
import threading
import hashlib
import logging

logger = logging.getLogger(__name__)


class LRUCache:
    """Thread-safe LRU cache implementation."""

    def __init__(self, max_size: int = 100, max_age_seconds: int = 3600):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of items to cache
            max_age_seconds: Maximum age of cached items in seconds
        """
        self.max_size = max_size
        self.max_age = timedelta(seconds=max_age_seconds)
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        with self.lock:
            if key not in self.cache:
                return None

            item = self.cache[key]
            if datetime.now(timezone.utc) - item['timestamp'] > self.max_age:
                del self.cache[key]
                logger.debug(f"[LRUCache] Expired item: {key}")
                return None

            self.cache.move_to_end(key)
            logger.debug(f"[LRUCache] Cache hit: {key}")
            return item['value']

    def set(self, key: str, value: Any) -> None:
        """Set item in cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]

            self.cache[key] = {
                'value': value,
                'timestamp': datetime.now(timezone.utc)
            }
            self.cache.move_to_end(key)

            while len(self.cache) > self.max_size:
                oldest = next(iter(self.cache))
                del self.cache[oldest]
                logger.debug(f"[LRUCache] Evicted: {oldest}")

    def delete(self, key: str) -> None:
        """Delete item from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]

    def clear(self) -> None:
        """Clear all items from cache."""
        with self.lock:
            self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'max_age_seconds': self.max_age.total_seconds(),
            }


class MemoryCacheSystem:
    """Three-tier cache system for memory queries."""

    def __init__(
        self,
        session_ttl: int = 3600,
        query_cache_ttl: int = 300,
        lru_max_size: int = 100,
        max_session_cache_size: int = 1000,
        max_query_cache_size: int = 500
    ):
        """
        Initialize three-tier cache system.

        Args:
            session_ttl: Session cache TTL in seconds
            query_cache_ttl: Query cache TTL in seconds
            lru_max_size: Maximum size for LRU cache
            max_session_cache_size: Maximum number of sessions to cache
            max_query_cache_size: Maximum number of queries to cache
        """
        self.session_cache: Dict[str, Dict[str, Any]] = {}
        self.session_ttl = session_ttl
        self.max_session_cache_size = max_session_cache_size

        self.query_cache: Dict[str, Dict[str, Any]] = {}
        self.query_cache_ttl = query_cache_ttl
        self.max_query_cache_size = max_query_cache_size

        self.lru_cache = LRUCache(max_size=lru_max_size, max_age_seconds=3600)

        self.lock = threading.Lock()
        logger.info(f"[MemoryCache] Initialized with session_ttl={session_ttl}s, query_ttl={query_cache_ttl}s")

    def _evict_expired_sessions(self) -> None:
        """Evict expired session cache entries."""
        now = datetime.now(timezone.utc)
        expired = [
            sid for sid, item in self.session_cache.items()
            if now - item['timestamp'] > timedelta(seconds=self.session_ttl)
        ]
        for sid in expired:
            del self.session_cache[sid]

    def _evict_expired_queries(self) -> None:
        """Evict expired query cache entries."""
        now = datetime.now(timezone.utc)
        expired = [
            key for key, item in self.query_cache.items()
            if now - item['timestamp'] > timedelta(seconds=self.query_cache_ttl)
        ]
        for key in expired:
            del self.query_cache[key]

    def get_session_memories(self, session_id: str) -> Optional[List[Dict]]:
        """Get cached memories for a session."""
        with self.lock:
            if session_id not in self.session_cache:
                return None

            item = self.session_cache[session_id]
            if datetime.now(timezone.utc) - item['timestamp'] > timedelta(seconds=self.session_ttl):
                del self.session_cache[session_id]
                logger.debug(f"[MemoryCache] Session cache expired: {session_id}")
                return None

            logger.debug(f"[MemoryCache] Session cache hit: {session_id}")
            return item['memories']

    def set_session_memories(self, session_id: str, memories: List[Dict]) -> None:
        """Cache memories for a session."""
        with self.lock:
            if len(self.session_cache) >= self.max_session_cache_size:
                self._evict_expired_sessions()
                if len(self.session_cache) >= self.max_session_cache_size:
                    oldest = next(iter(self.session_cache))
                    del self.session_cache[oldest]
                    logger.debug(f"[MemoryCache] Evicted oldest session: {oldest}")

            self.session_cache[session_id] = {
                'memories': memories,
                'timestamp': datetime.now(timezone.utc)
            }
            logger.debug(f"[MemoryCache] Session cache set: {session_id}, count={len(memories)}")

    def get_query_cache(self, query_hash: str) -> Optional[List[Dict]]:
        """Get cached query result."""
        with self.lock:
            if query_hash not in self.query_cache:
                return None

            item = self.query_cache[query_hash]
            if datetime.now(timezone.utc) - item['timestamp'] > timedelta(seconds=self.query_cache_ttl):
                del self.query_cache[query_hash]
                logger.debug(f"[MemoryCache] Query cache expired: {query_hash}")
                return None

            logger.debug(f"[MemoryCache] Query cache hit: {query_hash}")
            return item['memories']

    def set_query_cache(self, query_hash: str, memories: List[Dict]) -> None:
        """Cache query result."""
        with self.lock:
            if len(self.query_cache) >= self.max_query_cache_size:
                self._evict_expired_queries()
                if len(self.query_cache) >= self.max_query_cache_size:
                    oldest = next(iter(self.query_cache))
                    del self.query_cache[oldest]
                    logger.debug(f"[MemoryCache] Evicted oldest query: {oldest[:8]}")

            self.query_cache[query_hash] = {
                'memories': memories,
                'timestamp': datetime.now(timezone.utc)
            }
            logger.debug(f"[MemoryCache] Query cache set: {query_hash[:8]}, count={len(memories)}")

    def get_hot_memory(self, memory_id: str) -> Optional[Dict]:
        """Get hot memory from LRU cache."""
        return self.lru_cache.get(memory_id)

    def set_hot_memory(self, memory_id: str, memory: Dict) -> None:
        """Set hot memory in LRU cache."""
        self.lru_cache.set(memory_id, memory)

    def invalidate_user_cache(self, user_id: str) -> None:
        """Invalidate all cache for a user."""
        with self.lock:
            keys_to_delete = [
                key for key in self.query_cache.keys()
                if key.startswith(f"{user_id}:")
            ]
            for key in keys_to_delete:
                del self.query_cache[key]

            sessions_to_delete = [
                sid for sid, item in self.session_cache.items()
                if item.get('user_id') == user_id
            ]
            for sid in sessions_to_delete:
                del self.session_cache[sid]

            logger.info(f"[MemoryCache] Invalidated cache for user: {user_id}")

    def clear_all(self) -> None:
        """Clear all caches."""
        with self.lock:
            self.session_cache.clear()
            self.query_cache.clear()
            self.lru_cache.clear()
            logger.info("[MemoryCache] Cleared all caches")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                'session_cache': {
                    'size': len(self.session_cache),
                    'ttl_seconds': self.session_ttl,
                },
                'query_cache': {
                    'size': len(self.query_cache),
                    'ttl_seconds': self.query_cache_ttl,
                },
                'lru_cache': self.lru_cache.get_stats(),
            }

    @staticmethod
    def hash_query(query: str, user_id: str) -> str:
        """Generate hash for query."""
        content = f"{user_id}:{query}"
        return hashlib.md5(content.encode()).hexdigest()
