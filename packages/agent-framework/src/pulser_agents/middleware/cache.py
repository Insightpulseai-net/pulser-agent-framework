"""
Caching middleware for agents.

Provides response caching to reduce API calls.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime
from typing import Any

from pulser_agents.core.message import Message
from pulser_agents.core.response import AgentResponse, RunResult
from pulser_agents.memory.base import MemoryProvider
from pulser_agents.memory.in_memory import InMemoryProvider
from pulser_agents.middleware.base import Middleware, MiddlewareContext, NextHandler


class CacheMiddleware(Middleware):
    """
    Middleware for caching agent responses.

    Caches responses based on input message and context,
    returning cached results for identical requests.

    Example:
        >>> middleware = CacheMiddleware(
        ...     ttl=3600,  # 1 hour
        ...     cache_provider=RedisMemoryProvider(),
        ... )
        >>> chain.add(middleware)
    """

    def __init__(
        self,
        cache_provider: MemoryProvider | None = None,
        ttl: int = 3600,
        key_generator: Callable[[MiddlewareContext], str] | None = None,
        should_cache: Callable[[RunResult], bool] | None = None,
    ) -> None:
        """
        Initialize cache middleware.

        Args:
            cache_provider: Memory provider for cache storage
            ttl: Time-to-live for cached entries in seconds
            key_generator: Custom function to generate cache keys
            should_cache: Function to determine if a result should be cached
        """
        self.cache = cache_provider or InMemoryProvider()
        self.ttl = ttl
        self.key_generator = key_generator or self._default_key_generator
        self.should_cache = should_cache or self._default_should_cache

        # Statistics
        self._hits = 0
        self._misses = 0

    def _default_key_generator(self, ctx: MiddlewareContext) -> str:
        """Generate a cache key from the context."""
        key_parts = {
            "agent": ctx.agent_name,
            "input": (
                ctx.input_message
                if isinstance(ctx.input_message, str)
                else ctx.input_message.text if ctx.input_message else ""
            ),
        }

        # Include relevant context variables
        if ctx.context:
            key_parts["user_id"] = ctx.context.user_id
            key_parts["session_id"] = ctx.context.session_id

        key_str = json.dumps(key_parts, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    def _default_should_cache(self, result: RunResult) -> bool:
        """Determine if a result should be cached."""
        # Don't cache if there was an error
        if not result.final_response:
            return False

        # Don't cache empty responses
        if not result.final_response.content:
            return False

        # Don't cache tool call responses
        if result.final_response.has_tool_calls:
            return False

        return True

    def _serialize_result(self, result: RunResult) -> dict[str, Any]:
        """Serialize a RunResult for caching."""
        return {
            "content": result.content,
            "model": result.final_response.model if result.final_response else None,
            "iterations": result.iterations,
            "cached_at": datetime.utcnow().isoformat(),
        }

    def _deserialize_result(self, data: dict[str, Any]) -> RunResult:
        """Deserialize a cached result."""
        result = RunResult()
        response = AgentResponse(
            message=Message.assistant(content=data["content"]),
            model=data.get("model"),
            metadata={"cached": True, "cached_at": data.get("cached_at")},
        )
        result.add_response(response)
        result.complete()
        return result

    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """Check cache or call next handler."""
        cache_key = self.key_generator(ctx)

        # Check cache
        cached = await self.cache.get(cache_key)
        if cached is not None:
            self._hits += 1
            ctx.set_metadata("cache_hit", True)
            ctx.set_metadata("cache_key", cache_key)
            return self._deserialize_result(cached)

        self._misses += 1
        ctx.set_metadata("cache_hit", False)
        ctx.set_metadata("cache_key", cache_key)

        # Call next handler
        result = await next_handler(ctx)

        # Cache if appropriate
        if self.should_cache(result):
            await self.cache.set(
                cache_key,
                self._serialize_result(result),
                ttl=self.ttl,
            )

        return result

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "ttl": self.ttl,
        }

    async def invalidate(self, pattern: str | None = None) -> int:
        """
        Invalidate cache entries.

        Args:
            pattern: Optional glob pattern for keys to invalidate

        Returns:
            Number of entries invalidated
        """
        keys = await self.cache.keys(pattern)
        return await self.cache.delete_many(keys)


class SemanticCacheMiddleware(Middleware):
    """
    Semantic caching using embeddings.

    Caches based on semantic similarity rather than exact match,
    allowing similar queries to benefit from cached results.

    Example:
        >>> middleware = SemanticCacheMiddleware(
        ...     embedding_func=openai_embed,
        ...     similarity_threshold=0.95,
        ... )
    """

    def __init__(
        self,
        embedding_func: Callable[[str], Any],
        similarity_threshold: float = 0.95,
        ttl: int = 3600,
        max_entries: int = 1000,
    ) -> None:
        """
        Initialize semantic cache middleware.

        Args:
            embedding_func: Async function to generate embeddings
            similarity_threshold: Minimum similarity for cache hit
            ttl: Time-to-live for cached entries
            max_entries: Maximum cached entries
        """
        self.embedding_func = embedding_func
        self.similarity_threshold = similarity_threshold
        self.ttl = ttl
        self.max_entries = max_entries

        # In-memory cache with embeddings
        self._cache: list[dict[str, Any]] = []
        self._hits = 0
        self._misses = 0

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity."""
        import math

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """Check semantic cache or call next handler."""
        input_text = (
            ctx.input_message
            if isinstance(ctx.input_message, str)
            else ctx.input_message.text if ctx.input_message else ""
        )

        # Get embedding for input
        input_embedding = await self.embedding_func(input_text)

        # Search cache
        now = datetime.utcnow()
        best_match = None
        best_similarity = 0.0

        for entry in self._cache:
            # Check expiration
            if (now - entry["created_at"]).total_seconds() > self.ttl:
                continue

            similarity = self._cosine_similarity(
                input_embedding,
                entry["embedding"],
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = entry

        if best_match and best_similarity >= self.similarity_threshold:
            self._hits += 1
            ctx.set_metadata("semantic_cache_hit", True)
            ctx.set_metadata("similarity", best_similarity)

            # Reconstruct result
            result = RunResult()
            response = AgentResponse(
                message=Message.assistant(content=best_match["response"]),
                metadata={"cached": True, "similarity": best_similarity},
            )
            result.add_response(response)
            result.complete()
            return result

        self._misses += 1
        ctx.set_metadata("semantic_cache_hit", False)

        # Call next handler
        result = await next_handler(ctx)

        # Add to cache
        if result.final_response and result.final_response.content:
            self._cache.append({
                "input": input_text,
                "embedding": input_embedding,
                "response": result.final_response.content,
                "created_at": now,
            })

            # Evict old entries
            if len(self._cache) > self.max_entries:
                self._cache = self._cache[-self.max_entries:]

        return result
