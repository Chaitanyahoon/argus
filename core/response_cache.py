"""
Response caching — cache Gemini responses to reduce API calls
and improve response latency for repeated queries.
"""

import logging
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class ResponseCache:
    """In-memory cache for Gemini responses with TTL and active cleanup."""
    
    def __init__(self, ttl_seconds: int = 3600, cache_dir: Optional[str] = None, cleanup_interval: int = 600):
        """
        Initialize response cache.
        
        Args:
            ttl_seconds: Time-to-live for cached responses (default: 1 hour)
            cache_dir: Optional directory to persist cache to disk
            cleanup_interval: How often to run cleanup task in seconds (default: 10 min)
        """
        self.ttl_seconds = ttl_seconds
        self.cleanup_interval = cleanup_interval
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_persisted_cache()
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query text."""
        return hashlib.md5(query.lower().encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response for query.
        
        Args:
            query: User query/message
            
        Returns:
            Cached response dict or None if not found/expired
        """
        key = self._get_cache_key(query)
        
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry['expires_at']:
                logger.debug(f"✻ Cache HIT for query: {query[:50]}...")
                return entry['response']
            else:
                logger.debug(f"✻ Cache EXPIRED for query: {query[:50]}...")
                del self.cache[key]
        
        return None
    
    def set(self, query: str, response: Dict[str, Any]) -> None:
        """
        Cache response for query.
        
        Args:
            query: User query/message
            response: Response dict (e.g., {'text': '...', 'audio': b'...'})
        """
        key = self._get_cache_key(query)
        self.cache[key] = {
            'query': query,
            'response': response,
            'cached_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=self.ttl_seconds)
        }
        logger.debug(f"✻ Cached response for query: {query[:50]}...")
        
        # Optionally persist to disk
        if self.cache_dir:
            self._save_to_disk(key)
    
    def clear(self) -> None:
        """Clear all cached responses."""
        self.cache.clear()
        logger.info("✻ Cache cleared")
    
    async def start_cleanup_task(self) -> None:
        """Start background task to clean expired entries periodically."""
        if self._cleanup_task and not self._cleanup_task.done():
            logger.warning("Cleanup task already running")
            return
        
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"Cache cleanup task started (interval: {self.cleanup_interval}s)")
    
    async def stop_cleanup_task(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                logger.debug("Cache cleanup task cancelled")
    
    async def _cleanup_loop(self) -> None:
        """Periodically remove expired entries from cache."""
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                self._cleanup_expired()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in cache cleanup loop: {e}")
    
    def _cleanup_expired(self) -> None:
        """Remove all expired entries from cache."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now >= entry['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Cache cleanup: removed {len(expired_keys)} expired entries (cache size: {len(self.cache)})")
    
    def _save_to_disk(self, key: str) -> None:
        """Persist cache entry to disk (async-safe)."""
        if not self.cache_dir:
            return
        
        try:
            entry = self.cache[key]
            cache_file = self.cache_dir / f"{key}.json"
            
            # Prepare serializable data (can't serialize bytes)
            serializable = {
                'query': entry['query'],
                'cached_at': entry['cached_at'].isoformat(),
                'expires_at': entry['expires_at'].isoformat(),
                # Skip binary audio data
            }
            
            with open(cache_file, 'w') as f:
                json.dump(serializable, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to persist cache: {e}")
    
    def _load_persisted_cache(self) -> None:
        """Load persisted cache from disk on startup."""
        if not self.cache_dir:
            return
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    expires_at = datetime.fromisoformat(data['expires_at'])
                    
                    # Skip expired entries
                    if datetime.now() < expires_at:
                        key = cache_file.stem
                        self.cache[key] = {
                            'query': data['query'],
                            'response': {},  # Audio not persisted
                            'cached_at': datetime.fromisoformat(data['cached_at']),
                            'expires_at': expires_at
                        }
            
            logger.info(f"✻ Loaded {len(self.cache)} persisted cache entries")
        except Exception as e:
            logger.warning(f"Failed to load persisted cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        valid_entries = sum(
            1 for e in self.cache.values()
            if datetime.now() < e['expires_at']
        )
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.cache) - valid_entries,
            'ttl_seconds': self.ttl_seconds
        }


# Global cache instance
_global_cache: Optional[ResponseCache] = None

def initialize_cache(ttl_seconds: int = 3600, cache_dir: Optional[str] = None) -> ResponseCache:
    """Initialize global response cache."""
    global _global_cache
    _global_cache = ResponseCache(ttl_seconds=ttl_seconds, cache_dir=cache_dir)
    logger.info("✻ Response cache initialized")
    return _global_cache

def get_cache() -> Optional[ResponseCache]:
    """Get global cache instance."""
    return _global_cache

def cache_response(query: str, response: Dict[str, Any]) -> None:
    """Cache a response globally."""
    if _global_cache:
        _global_cache.set(query, response)

def get_cached_response(query: str) -> Optional[Dict[str, Any]]:
    """Get cached response globally."""
    if _global_cache:
        return _global_cache.get(query)
    return None
