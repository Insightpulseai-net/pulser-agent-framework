"""
Verified memory provider for cross-agent knowledge sharing.

Inspired by GitHub Copilot's repository-scoped memory system (Jan 2026).
Stores memories with citations (code locations), verified just-in-time
at use-time instead of expensive offline memory curation pipelines.

Key behaviors:
- Memories are hypotheses, not truth - must be verified before use
- Citations link to specific code locations (path, line_start, line_end, sha)
- Verification detects contradictions and triggers correction/refresh
- Recency-based retrieval with status tracking (active/superseded/invalid)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from pulser_agents.memory.base import MemoryConfig, MemoryProvider


@dataclass
class Citation:
    """
    A citation pointing to a specific code location.

    Attributes:
        path: File path relative to repo root
        line_start: Starting line number (1-indexed)
        line_end: Ending line number (1-indexed)
        sha: Optional git SHA for version pinning
        snippet_hash: Optional hash of surrounding context for fuzzy matching
    """

    path: str
    line_start: int
    line_end: int
    sha: str | None = None
    snippet_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "path": self.path,
            "line_start": self.line_start,
            "line_end": self.line_end,
        }
        if self.sha:
            result["sha"] = self.sha
        if self.snippet_hash:
            result["snippet_hash"] = self.snippet_hash
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Citation:
        """Create from dictionary."""
        return cls(
            path=data["path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            sha=data.get("sha"),
            snippet_hash=data.get("snippet_hash"),
        )


@dataclass
class Memory:
    """
    A verified memory with citations.

    Attributes:
        id: Unique memory identifier
        repo: Repository identifier (e.g., 'owner/name')
        subject: Brief topic/category
        fact: The learned convention, invariant, or rule
        citations: Code locations that support this memory
        reason: Why this matters (what problem it prevents)
        refreshed_at: When the memory was last verified/refreshed
        verification_count: Number of times verified
    """

    id: str
    repo: str
    subject: str
    fact: str
    citations: list[Citation]
    reason: str | None = None
    refreshed_at: datetime | None = None
    verification_count: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Memory:
        """Create from dictionary (e.g., from Supabase response)."""
        citations = [
            Citation.from_dict(c) if isinstance(c, dict) else c
            for c in (data.get("citations") or [])
        ]
        refreshed_at = data.get("refreshed_at")
        if isinstance(refreshed_at, str):
            refreshed_at = datetime.fromisoformat(refreshed_at.replace("Z", "+00:00"))

        return cls(
            id=str(data["id"]),
            repo=data.get("repo", ""),
            subject=data["subject"],
            fact=data["fact"],
            citations=citations,
            reason=data.get("reason"),
            refreshed_at=refreshed_at,
            verification_count=data.get("verification_count", 0),
        )


@dataclass
class VerificationResult:
    """
    Result of verifying a memory's citations.

    Attributes:
        valid: Whether all citations are valid
        valid_citations: Citations that were found and valid
        invalid_citations: Citations that were missing or contradicted
        error: Optional error message
    """

    valid: bool
    valid_citations: list[Citation] = field(default_factory=list)
    invalid_citations: list[Citation] = field(default_factory=list)
    error: str | None = None


class VerifiedMemoryConfig(MemoryConfig):
    """Configuration for verified memory provider."""

    supabase_url: str = ""
    supabase_key: str = ""
    github_token: str | None = None
    default_limit: int = 50


class VerifiedMemoryProvider(MemoryProvider):
    """
    Verified memory provider for cross-agent knowledge sharing.

    Uses Supabase as the backend and GitHub API for citation verification.

    Example:
        >>> provider = VerifiedMemoryProvider(
        ...     config=VerifiedMemoryConfig(
        ...         supabase_url="https://xxx.supabase.co",
        ...         supabase_key="your-service-key",
        ...     ),
        ... )
        >>> # Store a memory
        >>> memory_id = await provider.store_memory(
        ...     repo="owner/repo",
        ...     subject="API version synchronization",
        ...     fact="API version must match between client and server",
        ...     citations=[
        ...         Citation("src/client/constants.ts", 12, 12),
        ...         Citation("server/routes/api.go", 8, 8),
        ...     ],
        ...     reason="Prevents integration breakages",
        ... )
        >>> # Get recent memories
        >>> memories = await provider.get_recent_memories("owner/repo")
    """

    def __init__(self, config: VerifiedMemoryConfig | None = None) -> None:
        super().__init__(config)
        self.verified_config = config or VerifiedMemoryConfig()
        self._client: Any | None = None

    async def _get_client(self) -> Any:
        """Get or create Supabase client."""
        if self._client is None:
            try:
                from supabase import create_client
            except ImportError:
                raise ImportError(
                    "supabase package is required. Install with: pip install supabase"
                )

            self._client = create_client(
                self.verified_config.supabase_url,
                self.verified_config.supabase_key,
            )

        return self._client

    async def store_memory(
        self,
        repo: str,
        subject: str,
        fact: str,
        citations: list[Citation],
        reason: str | None = None,
        created_by: str | None = None,
    ) -> str:
        """
        Store a new memory with citations.

        Args:
            repo: Repository identifier (e.g., 'owner/name')
            subject: Brief topic/category
            fact: The learned convention, invariant, or rule
            citations: Code locations that support this memory
            reason: Why this matters (optional)
            created_by: Agent or user ID (optional)

        Returns:
            The memory ID
        """
        client = await self._get_client()

        result = client.rpc(
            "store_memory",
            {
                "p_repo": repo,
                "p_subject": subject,
                "p_fact": fact,
                "p_citations": [c.to_dict() for c in citations],
                "p_reason": reason,
                "p_created_by": created_by,
            },
        ).execute()

        if result.data is None:
            raise RuntimeError("Failed to store memory")

        return str(result.data)

    async def get_recent_memories(
        self,
        repo: str,
        limit: int | None = None,
    ) -> list[Memory]:
        """
        Get recent active memories for a repository.

        Args:
            repo: Repository identifier
            limit: Maximum number of memories (default: config.default_limit)

        Returns:
            List of memories ordered by recency
        """
        client = await self._get_client()

        result = client.rpc(
            "get_recent_memories",
            {
                "p_repo": repo,
                "p_limit": limit or self.verified_config.default_limit,
            },
        ).execute()

        return [Memory.from_dict(m) for m in (result.data or [])]

    async def search_by_path(self, repo: str, path: str) -> list[Memory]:
        """
        Find memories that cite a specific file path.

        Useful when modifying a file to check for relevant conventions.

        Args:
            repo: Repository identifier
            path: File path to search for

        Returns:
            List of memories citing this path
        """
        client = await self._get_client()

        result = client.rpc(
            "search_memories_by_path",
            {
                "p_repo": repo,
                "p_path": path,
            },
        ).execute()

        return [Memory.from_dict(m) for m in (result.data or [])]

    async def refresh_memory(
        self,
        memory_id: str,
        verified_by: str | None = None,
    ) -> bool:
        """
        Refresh a memory timestamp after successful verification.

        Call this when a memory is verified and found to be still valid.
        Keeps useful memories at the top of recency ranking.

        Args:
            memory_id: ID of the memory to refresh
            verified_by: Agent or user ID (optional)

        Returns:
            True if refreshed, False if memory not found
        """
        client = await self._get_client()

        result = client.rpc(
            "refresh_memory",
            {
                "p_memory_id": memory_id,
                "p_verified_by": verified_by,
            },
        ).execute()

        return bool(result.data)

    async def invalidate_memory(
        self,
        memory_id: str,
        reason: str | None = None,
        invalidated_by: str | None = None,
    ) -> bool:
        """
        Mark a memory as invalid after verification finds contradictions.

        Call this when citation verification fails or the fact is no longer true.

        Args:
            memory_id: ID of the memory to invalidate
            reason: Why the memory is invalid (optional)
            invalidated_by: Agent or user ID (optional)

        Returns:
            True if invalidated, False if memory not found
        """
        client = await self._get_client()

        result = client.rpc(
            "invalidate_memory",
            {
                "p_memory_id": memory_id,
                "p_reason": reason,
                "p_invalidated_by": invalidated_by,
            },
        ).execute()

        return bool(result.data)

    async def supersede_memory(
        self,
        old_memory_id: str,
        new_fact: str,
        new_citations: list[Citation] | None = None,
        new_reason: str | None = None,
        created_by: str | None = None,
    ) -> str:
        """
        Replace an incorrect memory with a corrected version.

        Creates a new memory and marks the old one as superseded.
        Maintains chain for traceability.

        Args:
            old_memory_id: ID of the memory to supersede
            new_fact: The corrected fact
            new_citations: Updated citations (optional, keeps old if not provided)
            new_reason: Updated reason (optional)
            created_by: Agent or user ID (optional)

        Returns:
            The new memory ID
        """
        client = await self._get_client()

        result = client.rpc(
            "supersede_memory",
            {
                "p_old_memory_id": old_memory_id,
                "p_new_fact": new_fact,
                "p_new_citations": [c.to_dict() for c in new_citations] if new_citations else None,
                "p_new_reason": new_reason,
                "p_created_by": created_by,
            },
        ).execute()

        if result.data is None:
            raise RuntimeError("Failed to supersede memory")

        return str(result.data)

    async def log_applied(
        self,
        memory_id: str,
        agent_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        """
        Log when a memory is actually used in a task.

        Call this after a memory is applied to track usage.

        Args:
            memory_id: ID of the memory that was applied
            agent_id: Agent that applied the memory (optional)
            session_id: Session/conversation context (optional)
        """
        client = await self._get_client()

        client.rpc(
            "log_memory_applied",
            {
                "p_memory_id": memory_id,
                "p_agent_id": agent_id,
                "p_session_id": session_id,
            },
        ).execute()

    async def verify_citations(
        self,
        repo: str,
        citations: list[Citation],
        ref: str = "HEAD",
    ) -> VerificationResult:
        """
        Verify citations by reading code from GitHub.

        Checks if all cited code locations exist and can be read.

        Args:
            repo: Repository in 'owner/name' format
            citations: Citations to verify
            ref: Git ref to verify against (default: HEAD)

        Returns:
            VerificationResult with valid/invalid citations
        """
        if not self.verified_config.github_token:
            return VerificationResult(
                valid=False,
                error="GitHub token not configured",
            )

        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx package is required for verification. Install with: pip install httpx"
            )

        owner, repo_name = repo.split("/", 1)
        valid_citations = []
        invalid_citations = []

        async with httpx.AsyncClient() as client:
            for citation in citations:
                try:
                    response = await client.get(
                        f"https://api.github.com/repos/{owner}/{repo_name}/contents/{citation.path}",
                        params={"ref": ref},
                        headers={
                            "Authorization": f"Bearer {self.verified_config.github_token}",
                            "Accept": "application/vnd.github.v3+json",
                            "X-GitHub-Api-Version": "2022-11-28",
                        },
                    )

                    if response.status_code == 200:
                        valid_citations.append(citation)
                    else:
                        invalid_citations.append(citation)

                except Exception:
                    invalid_citations.append(citation)

        return VerificationResult(
            valid=len(invalid_citations) == 0,
            valid_citations=valid_citations,
            invalid_citations=invalid_citations,
        )

    # MemoryProvider interface implementation
    async def get(self, key: str) -> Any | None:
        """Get a memory by ID."""
        client = await self._get_client()

        result = (
            client.table("agent_memory")
            .select("*")
            .eq("id", key)
            .eq("status", "active")
            .single()
            .execute()
        )

        if result.data:
            return Memory.from_dict(result.data)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Not directly supported - use store_memory instead."""
        raise NotImplementedError(
            "Use store_memory() to create memories with proper citations"
        )

    async def delete(self, key: str) -> bool:
        """Delete (invalidate) a memory."""
        return await self.invalidate_memory(key)

    async def exists(self, key: str) -> bool:
        """Check if a memory exists and is active."""
        memory = await self.get(key)
        return memory is not None

    async def clear(self) -> None:
        """Not supported for verified memory."""
        raise NotImplementedError(
            "Bulk clearing not supported for verified memory"
        )

    async def keys(self, pattern: str | None = None) -> list[str]:
        """List memory IDs for a repo pattern."""
        client = await self._get_client()

        query = (
            client.table("agent_memory")
            .select("id")
            .eq("status", "active")
        )

        if pattern:
            query = query.ilike("repo", pattern)

        result = query.execute()
        return [str(row["id"]) for row in (result.data or [])]


def format_memories_for_prompt(memories: list[Memory]) -> str:
    """
    Format memories for injection into an agent prompt.

    Creates a concise, readable format for the agent to use.

    Args:
        memories: List of memories to format

    Returns:
        Formatted string for prompt injection
    """
    if not memories:
        return "No repository memories available."

    lines = ["## Repository Memories", ""]
    lines.append(
        "The following are learned conventions for this repository. "
        "You MUST verify each memory before using it by reading the cited locations."
    )
    lines.append("")

    for i, memory in enumerate(memories, 1):
        lines.append(f"### Memory {i}: {memory.subject}")
        lines.append(f"**Fact:** {memory.fact}")
        if memory.reason:
            lines.append(f"**Why:** {memory.reason}")
        lines.append("**Citations:**")
        for citation in memory.citations:
            lines.append(f"  - `{citation.path}` (lines {citation.line_start}-{citation.line_end})")
        lines.append(f"**ID:** `{memory.id}` (for refresh/invalidate)")
        lines.append("")

    return "\n".join(lines)
