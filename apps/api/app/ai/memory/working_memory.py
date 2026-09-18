"""Short-term working memory manager for active session context and fast temporary state."""

import json
import logging
import time
from typing import Any
from app.core.redis import redis_client

logger = logging.getLogger("jenna.ai.memory.working")


class WorkingMemoryManager:
    """Manages ephemeral working memory with TTL, backed by Redis with in-memory fallback."""

    def __init__(self) -> None:
        # In-memory fallback: dict of key -> (value, expiry_timestamp)
        self._local_cache: dict[str, tuple[Any, float]] = {}

    def _make_key(self, user_id: str, key: str, conversation_id: str | None = None) -> str:
        scope = f"conv:{conversation_id}" if conversation_id else "global"
        return f"jenna:wm:{user_id}:{scope}:{key}"

    def _make_prefix(self, user_id: str, conversation_id: str | None = None) -> str:
        scope = f"conv:{conversation_id}" if conversation_id else "global"
        return f"jenna:wm:{user_id}:{scope}:"

    async def set_item(
        self,
        user_id: str,
        key: str,
        value: Any,
        ttl_seconds: int = 86400,  # 24 hours default
        conversation_id: str | None = None,
    ) -> None:
        """Store a working memory item."""
        full_key = self._make_key(user_id, key, conversation_id)
        payload = json.dumps({"value": value, "saved_at": time.time()})

        try:
            await redis_client.cache_set(full_key, payload, ttl=ttl_seconds)
        except Exception as exc:
            logger.debug("Redis unavailable for working memory, using local fallback: %s", exc)
            self._local_cache[full_key] = (payload, time.time() + ttl_seconds)

    async def get_item(
        self,
        user_id: str,
        key: str,
        conversation_id: str | None = None,
    ) -> Any | None:
        """Retrieve a working memory item."""
        full_key = self._make_key(user_id, key, conversation_id)

        try:
            cached = await redis_client.cache_get(full_key)
            if cached:
                data = json.loads(cached)
                return data.get("value")
        except Exception:
            pass

        # Check local fallback
        if full_key in self._local_cache:
            payload, expiry = self._local_cache[full_key]
            if time.time() < expiry:
                data = json.loads(payload)
                return data.get("value")
            else:
                del self._local_cache[full_key]

        return None

    async def delete_item(
        self,
        user_id: str,
        key: str,
        conversation_id: str | None = None,
    ) -> bool:
        """Delete a working memory item."""
        full_key = self._make_key(user_id, key, conversation_id)
        deleted = False

        try:
            await redis_client.cache_delete(full_key)
            deleted = True
        except Exception:
            pass

        if full_key in self._local_cache:
            del self._local_cache[full_key]
            deleted = True

        return deleted

    async def list_items(
        self,
        user_id: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """List all working memory items for the user / conversation scope."""
        prefix = self._make_prefix(user_id, conversation_id)
        items: dict[str, Any] = {}

        # 1. Try Redis scanning
        try:
            client = redis_client.client
            keys = await client.keys(f"{prefix}*")
            if keys:
                for k in keys:
                    val_str = await client.get(k)
                    if val_str:
                        item_key = k[len(prefix):]
                        items[item_key] = json.loads(val_str).get("value")
                return items
        except Exception:
            pass

        # 2. Local fallback
        now = time.time()
        expired_keys = []
        for k, (payload, expiry) in self._local_cache.items():
            if k.startswith(prefix):
                if now < expiry:
                    item_key = k[len(prefix):]
                    items[item_key] = json.loads(payload).get("value")
                else:
                    expired_keys.append(k)

        for k in expired_keys:
            del self._local_cache[k]

        return items

    async def clear(
        self,
        user_id: str,
        conversation_id: str | None = None,
    ) -> None:
        """Clear all working memory items for scope."""
        prefix = self._make_prefix(user_id, conversation_id)
        try:
            client = redis_client.client
            keys = await client.keys(f"{prefix}*")
            if keys:
                for k in keys:
                    await client.delete(k)
        except Exception:
            pass

        to_del = [k for k in self._local_cache if k.startswith(prefix)]
        for k in to_del:
            del self._local_cache[k]


working_memory_manager = WorkingMemoryManager()
