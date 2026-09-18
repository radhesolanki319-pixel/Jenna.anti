import asyncio
import redis.asyncio as aioredis
from app.core.config import settings


class RedisClient:
    """Redis connection abstraction for caching, background jobs, realtime state, and rate limiting."""

    def __init__(self):
        self._client: aioredis.Redis | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None
        self._client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None
            self._loop = None

    @property
    def client(self) -> aioredis.Redis:
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if self._client is None or (current_loop is not None and self._loop != current_loop):
            self._loop = current_loop
            self._client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    # --- Caching ---

    async def cache_get(self, key: str) -> str | None:
        """Get a cached value by key."""
        return await self.client.get(key)

    async def cache_set(self, key: str, value: str, ttl: int = 3600) -> None:
        """Set a cached value with TTL in seconds."""
        await self.client.set(key, value, ex=ttl)

    async def cache_delete(self, key: str) -> None:
        """Delete a cached key."""
        await self.client.delete(key)

    # --- Rate Limiting ---

    async def rate_limit_check(self, key: str, max_requests: int, window: int) -> bool:
        """Check rate limit. Returns True if request is allowed."""
        current = await self.client.incr(key)
        if current == 1:
            await self.client.expire(key, window)
        return current <= max_requests

    # --- Pub/Sub (for realtime state) ---

    async def publish(self, channel: str, message: str) -> None:
        """Publish a message to a channel."""
        await self.client.publish(channel, message)

    # --- Background Jobs (simple queue) ---

    async def enqueue(self, queue: str, data: str) -> None:
        """Push data to a queue."""
        await self.client.lpush(queue, data)

    async def dequeue(self, queue: str) -> str | None:
        """Pop data from a queue."""
        return await self.client.rpop(queue)

    # --- Health ---

    async def ping(self) -> bool:
        """Check Redis connectivity."""
        try:
            return await self.client.ping()
        except Exception:
            return False


redis_client = RedisClient()
