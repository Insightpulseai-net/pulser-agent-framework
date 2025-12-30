"""
In-memory storage provider.

Simple, fast memory storage for development and testing.
"""

from __future__ import annotations

import fnmatch
from datetime import datetime, timedelta
from typing import Any

from pulser_agents.memory.base import MemoryConfig, MemoryEntry, MemoryProvider


class InMemoryProvider(MemoryProvider):
    """
    In-memory storage provider.

    Fast, ephemeral storage suitable for development, testing,
    and single-instance deployments.

    Features:
    - Automatic expiration
    - LRU eviction when max_entries is reached
    - Pattern-based key listing

    Example:
        >>> provider = InMemoryProvider(
        ...     config=MemoryConfig(
        ...         namespace="chat",
        ...         max_entries=1000,
        ...         ttl=3600,  # 1 hour
        ...     )
        ... )
        >>> await provider.set("session:123", {"user": "alice"})
    """

    def __init__(self, config: MemoryConfig | None = None) -> None:
        super().__init__(config)
        self._store: dict[str, MemoryEntry] = {}

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        now = datetime.utcnow()
        expired_keys = [
            key for key, entry in self._store.items()
            if entry.expires_at and entry.expires_at < now
        ]
        for key in expired_keys:
            del self._store[key]

    def _enforce_max_entries(self) -> None:
        """Enforce max_entries limit using LRU eviction."""
        if self.config.max_entries is None:
            return

        while len(self._store) > self.config.max_entries:
            # Find least recently accessed entry
            lru_key = min(
                self._store.keys(),
                key=lambda k: self._store[k].last_accessed or self._store[k].created_at
            )
            del self._store[lru_key]

    async def get(self, key: str) -> Any | None:
        """Get a value from memory."""
        self._cleanup_expired()

        full_key = self._make_key(key)
        entry = self._store.get(full_key)

        if entry is None:
            return None

        if entry.is_expired():
            del self._store[full_key]
            return None

        entry.touch()
        return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Set a value in memory."""
        self._cleanup_expired()

        full_key = self._make_key(key)
        effective_ttl = ttl if ttl is not None else self.config.ttl

        expires_at = None
        if effective_ttl:
            expires_at = datetime.utcnow() + timedelta(seconds=effective_ttl)

        entry = MemoryEntry(
            key=key,
            value=value,
            metadata=metadata or {},
            expires_at=expires_at,
        )

        self._store[full_key] = entry
        self._enforce_max_entries()

    async def delete(self, key: str) -> bool:
        """Delete a value from memory."""
        full_key = self._make_key(key)
        if full_key in self._store:
            del self._store[full_key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        self._cleanup_expired()
        full_key = self._make_key(key)
        entry = self._store.get(full_key)

        if entry is None:
            return False

        if entry.is_expired():
            del self._store[full_key]
            return False

        return True

    async def clear(self) -> None:
        """Clear all entries in the namespace."""
        prefix = f"{self.config.namespace}:"
        keys_to_delete = [
            key for key in self._store.keys()
            if key.startswith(prefix)
        ]
        for key in keys_to_delete:
            del self._store[key]

    async def keys(self, pattern: str | None = None) -> list[str]:
        """List keys matching a pattern."""
        self._cleanup_expired()

        prefix = f"{self.config.namespace}:"
        prefix_len = len(prefix)

        matching_keys = []
        for full_key in self._store.keys():
            if not full_key.startswith(prefix):
                continue

            key = full_key[prefix_len:]

            if pattern is None or fnmatch.fnmatch(key, pattern):
                matching_keys.append(key)

        return matching_keys

    async def get_entry(self, key: str) -> MemoryEntry | None:
        """Get the full entry including metadata."""
        full_key = self._make_key(key)
        entry = self._store.get(full_key)

        if entry and not entry.is_expired():
            entry.touch()
            return entry

        return None

    async def get_stats(self) -> dict[str, Any]:
        """Get memory provider statistics."""
        self._cleanup_expired()

        total_entries = len(self._store)
        namespace_entries = sum(
            1 for k in self._store.keys()
            if k.startswith(f"{self.config.namespace}:")
        )

        return {
            "total_entries": total_entries,
            "namespace_entries": namespace_entries,
            "namespace": self.config.namespace,
            "max_entries": self.config.max_entries,
            "default_ttl": self.config.ttl,
        }


class ConversationMemory(InMemoryProvider):
    """
    Specialized memory for conversation history.

    Provides convenient methods for managing conversation
    history with automatic summarization support.

    Example:
        >>> memory = ConversationMemory(
        ...     config=MemoryConfig(namespace="conv:user123")
        ... )
        >>> await memory.add_message("user", "Hello!")
        >>> await memory.add_message("assistant", "Hi there!")
        >>> history = await memory.get_history()
    """

    def __init__(
        self,
        config: MemoryConfig | None = None,
        max_messages: int = 100,
    ) -> None:
        super().__init__(config)
        self.max_messages = max_messages

    async def add_message(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a message to conversation history."""
        messages = await self.get("messages") or []
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        })

        # Trim if needed
        if len(messages) > self.max_messages:
            messages = messages[-self.max_messages:]

        await self.set("messages", messages)

    async def get_history(
        self,
        last_n: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get conversation history."""
        messages = await self.get("messages") or []

        if last_n:
            return messages[-last_n:]

        return messages

    async def clear_history(self) -> None:
        """Clear conversation history."""
        await self.delete("messages")

    async def get_summary(self) -> str | None:
        """Get conversation summary if available."""
        return await self.get("summary")

    async def set_summary(self, summary: str) -> None:
        """Set conversation summary."""
        await self.set("summary", summary)
