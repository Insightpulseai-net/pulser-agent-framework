"""
Redis-based memory provider.

Persistent, distributed memory storage using Redis.
"""

from __future__ import annotations

import json
from typing import Any

from pulser_agents.memory.base import MemoryConfig, MemoryProvider


class RedisMemoryProvider(MemoryProvider):
    """
    Redis-based memory provider.

    Provides persistent, distributed memory storage suitable
    for production deployments with multiple instances.

    Features:
    - Automatic serialization/deserialization
    - TTL support
    - Pattern-based key listing
    - Atomic operations

    Example:
        >>> provider = RedisMemoryProvider(
        ...     url="redis://localhost:6379",
        ...     config=MemoryConfig(namespace="agents"),
        ... )
        >>> await provider.set("state:agent1", {"status": "active"})
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        config: MemoryConfig | None = None,
        db: int = 0,
    ) -> None:
        super().__init__(config)
        self.url = url
        self.db = db
        self._client: Any | None = None

    async def _get_client(self) -> Any:
        """Get or create Redis client."""
        if self._client is None:
            try:
                import redis.asyncio as redis
            except ImportError:
                raise ImportError(
                    "redis package is required. Install with: pip install redis"
                )

            self._client = redis.from_url(
                self.url,
                db=self.db,
                decode_responses=True,
            )

        return self._client

    def _serialize(self, value: Any) -> str:
        """Serialize value for storage."""
        return json.dumps(value, default=str)

    def _deserialize(self, value: str | None) -> Any:
        """Deserialize value from storage."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def get(self, key: str) -> Any | None:
        """Get a value from Redis."""
        client = await self._get_client()
        full_key = self._make_key(key)
        value = await client.get(full_key)
        return self._deserialize(value)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Set a value in Redis."""
        client = await self._get_client()
        full_key = self._make_key(key)
        effective_ttl = ttl if ttl is not None else self.config.ttl

        # Store value
        serialized = self._serialize(value)

        if effective_ttl:
            await client.setex(full_key, effective_ttl, serialized)
        else:
            await client.set(full_key, serialized)

        # Store metadata if provided
        if metadata:
            meta_key = f"{full_key}:__meta__"
            meta_serialized = self._serialize(metadata)
            if effective_ttl:
                await client.setex(meta_key, effective_ttl, meta_serialized)
            else:
                await client.set(meta_key, meta_serialized)

    async def delete(self, key: str) -> bool:
        """Delete a value from Redis."""
        client = await self._get_client()
        full_key = self._make_key(key)
        meta_key = f"{full_key}:__meta__"

        result = await client.delete(full_key, meta_key)
        return result > 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        client = await self._get_client()
        full_key = self._make_key(key)
        return await client.exists(full_key) > 0

    async def clear(self) -> None:
        """Clear all entries in the namespace."""
        client = await self._get_client()
        pattern = f"{self.config.namespace}:*"

        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break

    async def keys(self, pattern: str | None = None) -> list[str]:
        """List keys matching a pattern."""
        client = await self._get_client()

        if pattern:
            full_pattern = f"{self.config.namespace}:{pattern}"
        else:
            full_pattern = f"{self.config.namespace}:*"

        prefix_len = len(f"{self.config.namespace}:")
        matching_keys = []

        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor, match=full_pattern, count=100)
            for key in keys:
                # Filter out metadata keys
                if not key.endswith(":__meta__"):
                    matching_keys.append(key[prefix_len:])
            if cursor == 0:
                break

        return matching_keys

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values at once using MGET."""
        if not keys:
            return {}

        client = await self._get_client()
        full_keys = [self._make_key(k) for k in keys]
        values = await client.mget(full_keys)

        return {
            key: self._deserialize(value)
            for key, value in zip(keys, values)
            if value is not None
        }

    async def set_many(
        self,
        items: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Set multiple values at once using pipeline."""
        if not items:
            return

        client = await self._get_client()
        effective_ttl = ttl if ttl is not None else self.config.ttl

        async with client.pipeline(transaction=True) as pipe:
            for key, value in items.items():
                full_key = self._make_key(key)
                serialized = self._serialize(value)

                if effective_ttl:
                    pipe.setex(full_key, effective_ttl, serialized)
                else:
                    pipe.set(full_key, serialized)

            await pipe.execute()

    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomically increment a value."""
        client = await self._get_client()
        full_key = self._make_key(key)
        return await client.incrby(full_key, amount)

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on an existing key."""
        client = await self._get_client()
        full_key = self._make_key(key)
        return await client.expire(full_key, ttl)

    async def ttl(self, key: str) -> int:
        """Get remaining TTL for a key."""
        client = await self._get_client()
        full_key = self._make_key(key)
        return await client.ttl(full_key)

    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to a list (left)."""
        client = await self._get_client()
        full_key = self._make_key(key)
        serialized = [self._serialize(v) for v in values]
        return await client.lpush(full_key, *serialized)

    async def rpush(self, key: str, *values: Any) -> int:
        """Push values to a list (right)."""
        client = await self._get_client()
        full_key = self._make_key(key)
        serialized = [self._serialize(v) for v in values]
        return await client.rpush(full_key, *serialized)

    async def lrange(
        self,
        key: str,
        start: int = 0,
        end: int = -1,
    ) -> list[Any]:
        """Get list range."""
        client = await self._get_client()
        full_key = self._make_key(key)
        values = await client.lrange(full_key, start, end)
        return [self._deserialize(v) for v in values]

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
