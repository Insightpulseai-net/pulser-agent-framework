"""
Base memory provider interface.

Defines the contract for all memory backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MemoryConfig(BaseModel):
    """
    Configuration for memory providers.

    Attributes:
        namespace: Namespace for key isolation
        ttl: Default time-to-live in seconds
        max_entries: Maximum entries to store
        metadata: Additional configuration
    """

    namespace: str = "default"
    ttl: int | None = None  # Seconds
    max_entries: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryEntry(BaseModel):
    """
    A single entry in memory.

    Attributes:
        id: Unique entry identifier
        key: Key for retrieval
        value: Stored value
        metadata: Entry metadata
        created_at: Creation timestamp
        expires_at: Optional expiration time
        access_count: Number of times accessed
        last_accessed: Last access timestamp
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    key: str
    value: Any
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    access_count: int = 0
    last_accessed: datetime | None = None

    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def touch(self) -> None:
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()


class MemoryProvider(ABC):
    """
    Abstract base class for memory providers.

    Memory providers handle storage and retrieval of conversation
    history, agent state, and other persistent data.

    Example:
        >>> provider = InMemoryProvider()
        >>> await provider.set("user_preference", {"theme": "dark"})
        >>> prefs = await provider.get("user_preference")
    """

    def __init__(self, config: MemoryConfig | None = None) -> None:
        self.config = config or MemoryConfig()

    def _make_key(self, key: str) -> str:
        """Create namespaced key."""
        return f"{self.config.namespace}:{key}"

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """
        Get a value from memory.

        Args:
            key: The key to retrieve

        Returns:
            The stored value or None if not found
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Set a value in memory.

        Args:
            key: The key to store under
            value: The value to store
            ttl: Time-to-live in seconds (overrides config)
            metadata: Optional metadata for the entry
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from memory.

        Args:
            key: The key to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists.

        Args:
            key: The key to check

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all entries in the namespace."""
        pass

    @abstractmethod
    async def keys(self, pattern: str | None = None) -> list[str]:
        """
        List keys matching a pattern.

        Args:
            pattern: Optional glob pattern for filtering

        Returns:
            List of matching keys
        """
        pass

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values at once.

        Args:
            keys: List of keys to retrieve

        Returns:
            Dictionary of key-value pairs
        """
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(
        self,
        items: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """
        Set multiple values at once.

        Args:
            items: Dictionary of key-value pairs
            ttl: Time-to-live in seconds
        """
        for key, value in items.items():
            await self.set(key, value, ttl=ttl)

    async def delete_many(self, keys: list[str]) -> int:
        """
        Delete multiple keys at once.

        Args:
            keys: List of keys to delete

        Returns:
            Number of keys deleted
        """
        count = 0
        for key in keys:
            if await self.delete(key):
                count += 1
        return count

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a numeric value.

        Args:
            key: The key to increment
            amount: Amount to increment by

        Returns:
            The new value
        """
        current = await self.get(key)
        new_value = (current or 0) + amount
        await self.set(key, new_value)
        return new_value

    async def close(self) -> None:
        """Close the provider and release resources."""
        pass

    async def __aenter__(self) -> MemoryProvider:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
