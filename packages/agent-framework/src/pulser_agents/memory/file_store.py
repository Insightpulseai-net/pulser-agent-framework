"""
File-based memory provider.

Persistent storage using the local filesystem.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from pulser_agents.memory.base import MemoryConfig, MemoryEntry, MemoryProvider


class FileMemoryProvider(MemoryProvider):
    """
    File-based memory provider.

    Persists data to the local filesystem as JSON files.
    Suitable for simple deployments without external dependencies.

    Features:
    - JSON file storage
    - Automatic directory creation
    - TTL support with lazy expiration
    - Atomic writes

    Example:
        >>> provider = FileMemoryProvider(
        ...     base_path="./data/memory",
        ...     config=MemoryConfig(namespace="agents"),
        ... )
        >>> await provider.set("config:agent1", {"model": "gpt-4"})
    """

    def __init__(
        self,
        base_path: str = "./memory_store",
        config: MemoryConfig | None = None,
    ) -> None:
        super().__init__(config)
        self.base_path = Path(base_path)
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure the storage directory exists."""
        namespace_dir = self.base_path / self.config.namespace
        namespace_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        """Get the file path for a key."""
        # Sanitize key for filesystem
        safe_key = key.replace("/", "_").replace("\\", "_").replace(":", "_")
        return self.base_path / self.config.namespace / f"{safe_key}.json"

    def _read_entry(self, path: Path) -> MemoryEntry | None:
        """Read an entry from a file."""
        if not path.exists():
            return None

        try:
            with open(path) as f:
                data = json.load(f)

            entry = MemoryEntry(**data)

            # Check expiration
            if entry.is_expired():
                path.unlink()
                return None

            return entry

        except (json.JSONDecodeError, OSError):
            return None

    def _write_entry(self, path: Path, entry: MemoryEntry) -> None:
        """Write an entry to a file atomically."""
        # Write to temp file first
        temp_path = path.with_suffix(".tmp")

        data = entry.model_dump()
        # Convert datetime to ISO format for JSON
        data["created_at"] = data["created_at"].isoformat()
        if data["expires_at"]:
            data["expires_at"] = data["expires_at"].isoformat()
        if data["last_accessed"]:
            data["last_accessed"] = data["last_accessed"].isoformat()

        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        # Atomic rename
        temp_path.rename(path)

    async def get(self, key: str) -> Any | None:
        """Get a value from file storage."""
        path = self._get_file_path(key)
        entry = self._read_entry(path)

        if entry is None:
            return None

        entry.touch()
        self._write_entry(path, entry)

        return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Set a value in file storage."""
        path = self._get_file_path(key)
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

        self._write_entry(path, entry)

    async def delete(self, key: str) -> bool:
        """Delete a file."""
        path = self._get_file_path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a file exists and is not expired."""
        path = self._get_file_path(key)
        entry = self._read_entry(path)
        return entry is not None

    async def clear(self) -> None:
        """Clear all files in the namespace."""
        namespace_dir = self.base_path / self.config.namespace
        if namespace_dir.exists():
            for file in namespace_dir.glob("*.json"):
                file.unlink()

    async def keys(self, pattern: str | None = None) -> list[str]:
        """List keys matching a pattern."""
        import fnmatch

        namespace_dir = self.base_path / self.config.namespace
        keys = []

        for file in namespace_dir.glob("*.json"):
            key = file.stem
            entry = self._read_entry(file)

            if entry is None:
                continue

            if pattern is None or fnmatch.fnmatch(key, pattern):
                keys.append(key)

        return keys

    async def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        namespace_dir = self.base_path / self.config.namespace
        removed = 0

        for file in namespace_dir.glob("*.json"):
            entry = self._read_entry(file)
            if entry is None:
                # Already removed by _read_entry
                removed += 1

        return removed

    async def get_stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        namespace_dir = self.base_path / self.config.namespace
        file_count = sum(1 for _ in namespace_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in namespace_dir.glob("*.json"))

        return {
            "file_count": file_count,
            "total_size_bytes": total_size,
            "namespace": self.config.namespace,
            "base_path": str(self.base_path),
        }


class JSONLMemoryProvider(MemoryProvider):
    """
    Append-only memory using JSONL format.

    Stores entries as JSON lines, useful for event logs
    and audit trails.

    Example:
        >>> provider = JSONLMemoryProvider(
        ...     file_path="./logs/agent_events.jsonl",
        ... )
        >>> await provider.append({"event": "run_started", "agent": "agent1"})
    """

    def __init__(
        self,
        file_path: str = "./memory.jsonl",
        config: MemoryConfig | None = None,
    ) -> None:
        super().__init__(config)
        self.file_path = Path(file_path)
        self._ensure_file()
        self._cache: dict[str, Any] = {}

    def _ensure_file(self) -> None:
        """Ensure the file and parent directory exist."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.touch()

    def _load_cache(self) -> None:
        """Load all entries into cache."""
        self._cache = {}
        with open(self.file_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        if "key" in entry:
                            self._cache[entry["key"]] = entry.get("value")
                    except json.JSONDecodeError:
                        continue

    async def append(self, data: dict[str, Any]) -> None:
        """Append a record to the log."""
        data["timestamp"] = datetime.utcnow().isoformat()

        with open(self.file_path, "a") as f:
            f.write(json.dumps(data, default=str) + "\n")

    async def get(self, key: str) -> Any | None:
        """Get a value (loads from file if not cached)."""
        if not self._cache:
            self._load_cache()
        return self._cache.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Set a value by appending to the log."""
        await self.append({
            "key": key,
            "value": value,
            "metadata": metadata or {},
        })
        self._cache[key] = value

    async def delete(self, key: str) -> bool:
        """Mark a key as deleted in the log."""
        if key in self._cache:
            await self.append({
                "key": key,
                "deleted": True,
            })
            del self._cache[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        if not self._cache:
            self._load_cache()
        return key in self._cache

    async def clear(self) -> None:
        """Clear the log file."""
        with open(self.file_path, "w") as f:
            f.write("")
        self._cache = {}

    async def keys(self, pattern: str | None = None) -> list[str]:
        """List all keys."""
        import fnmatch

        if not self._cache:
            self._load_cache()

        if pattern:
            return [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]
        return list(self._cache.keys())

    async def iter_records(self) -> list[dict[str, Any]]:
        """Iterate over all records in the log."""
        records = []
        with open(self.file_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records
