"""Cache service for Redis operations (optional)."""
import json
import logging
from typing import Optional
from flask import current_app

logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache service with graceful degradation."""

    def __init__(self):
        self._redis = None
        self._connected = False

    def _get_redis(self):
        """Get Redis connection lazily."""
        if self._redis is not None:
            return self._redis if self._connected else None

        redis_url = current_app.config.get('REDIS_URL')
        if not redis_url:
            self._connected = False
            return None

        try:
            import redis
            self._redis = redis.from_url(redis_url)
            self._redis.ping()
            self._connected = True
            logger.info("Redis connected successfully")
            return self._redis
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Running without cache.")
            self._connected = False
            return None

    def _make_key(self, domain_name: str, language: str) -> str:
        """Generate cache key."""
        return f"domain:{domain_name}:lang:{language}"

    def get(self, domain_name: str, language: str) -> Optional[dict]:
        """Get cached config data."""
        redis_client = self._get_redis()
        if not redis_client:
            return None

        try:
            key = self._make_key(domain_name, language)
            data = redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    def set(self, domain_name: str, language: str, data: dict,
            ttl: int = None) -> bool:
        """Set cached config data."""
        redis_client = self._get_redis()
        if not redis_client:
            return False

        try:
            key = self._make_key(domain_name, language)
            ttl = ttl or current_app.config.get('REDIS_TTL', 3600)
            redis_client.setex(key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    def invalidate(self, domain_name: str, language: str = None) -> bool:
        """Invalidate cache for domain (optionally specific language)."""
        redis_client = self._get_redis()
        if not redis_client:
            return False

        try:
            if language:
                key = self._make_key(domain_name, language)
                redis_client.delete(key)
            else:
                # Delete all language variants for this domain
                pattern = f"domain:{domain_name}:lang:*"
                keys = redis_client.keys(pattern)
                if keys:
                    redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.warning(f"Cache invalidate error: {e}")
            return False

    def invalidate_all(self) -> bool:
        """Invalidate all cached data."""
        redis_client = self._get_redis()
        if not redis_client:
            return False

        try:
            keys = redis_client.keys("domain:*")
            if keys:
                redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.warning(f"Cache invalidate_all error: {e}")
            return False


# Singleton instance
cache_service = CacheService()
