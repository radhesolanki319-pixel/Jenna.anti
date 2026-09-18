from app.core.logging import logger
from app.core.redis import redis_client
from app.schemas.health import ServiceStatus


class RedisService:
    """Reusable Redis service providing core key-value and connectivity operations."""

    def __init__(self, client=redis_client):
        self.client = client

    async def get(self, key: str) -> str | None:
        """Retrieve a value by key from Redis."""
        try:
            return await self.client.cache_get(key)
        except Exception as e:
            logger.error(f"Redis get failed for key '{key}': {e}", extra={"key": key})
            return None

    async def set(self, key: str, value: str, ttl: int | None = None) -> bool:
        """Store a value in Redis with optional TTL in seconds."""
        try:
            await self.client.cache_set(key, value, ttl=ttl or 3600)
            return True
        except Exception as e:
            logger.error(f"Redis set failed for key '{key}': {e}", extra={"key": key})
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        try:
            await self.client.cache_delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete failed for key '{key}': {e}", extra={"key": key})
            return False

    async def health_check(self) -> ServiceStatus:
        """Check Redis connectivity."""
        try:
            is_healthy = await self.client.ping()
            if is_healthy:
                return ServiceStatus(name="redis", status="healthy")
            return ServiceStatus(name="redis", status="unhealthy", detail="Ping returned False")
        except Exception as e:
            return ServiceStatus(name="redis", status="unhealthy", detail=str(e))


redis_service = RedisService()
