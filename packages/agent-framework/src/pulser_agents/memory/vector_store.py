"""
Vector store memory provider.

Provides semantic search capabilities using embeddings.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pulser_agents.memory.base import MemoryConfig, MemoryProvider


@dataclass
class VectorSearchResult:
    """Result from a vector similarity search."""

    id: str
    content: str
    score: float
    metadata: dict[str, Any]


class VectorMemoryConfig(MemoryConfig):
    """Configuration for vector memory."""

    embedding_dim: int = 1536  # OpenAI ada-002 default
    index_type: str = "flat"  # flat, hnsw
    distance_metric: str = "cosine"  # cosine, euclidean, dot


class VectorMemoryProvider(MemoryProvider):
    """
    Vector store for semantic similarity search.

    Stores documents with embeddings and enables similarity-based
    retrieval. Useful for RAG (Retrieval Augmented Generation) patterns.

    Features:
    - Multiple embedding backends (OpenAI, local)
    - Configurable similarity metrics
    - Metadata filtering

    Example:
        >>> provider = VectorMemoryProvider(
        ...     embedding_func=openai_embed,
        ... )
        >>> await provider.add_document(
        ...     "doc1",
        ...     "The quick brown fox jumps over the lazy dog",
        ... )
        >>> results = await provider.search("fast fox jumping", k=5)
    """

    def __init__(
        self,
        config: VectorMemoryConfig | None = None,
        embedding_func: Callable[[str], list[float]] | None = None,
        embedding_func_async: Callable[[str], Any] | None = None,
    ) -> None:
        super().__init__(config or VectorMemoryConfig())
        self.vector_config = config or VectorMemoryConfig()
        self.embedding_func = embedding_func
        self.embedding_func_async = embedding_func_async

        # In-memory storage for simple implementation
        self._documents: dict[str, dict[str, Any]] = {}
        self._vectors: dict[str, list[float]] = {}

    async def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text."""
        if self.embedding_func_async:
            return await self.embedding_func_async(text)
        elif self.embedding_func:
            return self.embedding_func(text)
        else:
            raise ValueError("No embedding function configured")

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import math

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def _euclidean_distance(self, a: list[float], b: list[float]) -> float:
        """Compute Euclidean distance between two vectors."""
        import math

        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    def _compute_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute similarity based on configured metric."""
        if self.vector_config.distance_metric == "cosine":
            return self._cosine_similarity(a, b)
        elif self.vector_config.distance_metric == "euclidean":
            # Convert distance to similarity (smaller distance = higher similarity)
            distance = self._euclidean_distance(a, b)
            return 1.0 / (1.0 + distance)
        elif self.vector_config.distance_metric == "dot":
            return sum(x * y for x, y in zip(a, b))
        else:
            return self._cosine_similarity(a, b)

    async def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a document to the vector store.

        Args:
            doc_id: Unique document identifier
            content: Document text content
            metadata: Optional document metadata
        """
        embedding = await self._get_embedding(content)

        self._documents[doc_id] = {
            "content": content,
            "metadata": metadata or {},
        }
        self._vectors[doc_id] = embedding

    async def add_documents(
        self,
        documents: list[tuple[str, str, dict[str, Any] | None]],
    ) -> None:
        """
        Add multiple documents.

        Args:
            documents: List of (doc_id, content, metadata) tuples
        """
        for doc_id, content, metadata in documents:
            await self.add_document(doc_id, content, metadata)

    async def search(
        self,
        query: str,
        k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
        min_score: float = 0.0,
    ) -> list[VectorSearchResult]:
        """
        Search for similar documents.

        Args:
            query: Query text
            k: Maximum number of results
            filter_metadata: Optional metadata filters
            min_score: Minimum similarity score

        Returns:
            List of search results ordered by similarity
        """
        query_embedding = await self._get_embedding(query)

        # Compute similarities
        results = []
        for doc_id, embedding in self._vectors.items():
            doc = self._documents[doc_id]

            # Apply metadata filter
            if filter_metadata:
                match = all(
                    doc["metadata"].get(k) == v
                    for k, v in filter_metadata.items()
                )
                if not match:
                    continue

            score = self._compute_similarity(query_embedding, embedding)

            if score >= min_score:
                results.append(VectorSearchResult(
                    id=doc_id,
                    content=doc["content"],
                    score=score,
                    metadata=doc["metadata"],
                ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)

        return results[:k]

    async def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """Get a document by ID."""
        return self._documents.get(doc_id)

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document."""
        if doc_id in self._documents:
            del self._documents[doc_id]
            del self._vectors[doc_id]
            return True
        return False

    async def update_metadata(
        self,
        doc_id: str,
        metadata: dict[str, Any],
    ) -> bool:
        """Update document metadata."""
        if doc_id in self._documents:
            self._documents[doc_id]["metadata"].update(metadata)
            return True
        return False

    # MemoryProvider interface implementation
    async def get(self, key: str) -> Any | None:
        """Get a document."""
        return self._documents.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Set a document (value should be a string for embedding)."""
        if isinstance(value, str):
            await self.add_document(key, value, metadata)
        else:
            # Store as regular document without embedding
            self._documents[key] = {
                "content": str(value),
                "metadata": metadata or {},
            }

    async def delete(self, key: str) -> bool:
        """Delete a document."""
        return await self.delete_document(key)

    async def exists(self, key: str) -> bool:
        """Check if a document exists."""
        return key in self._documents

    async def clear(self) -> None:
        """Clear all documents."""
        self._documents.clear()
        self._vectors.clear()

    async def keys(self, pattern: str | None = None) -> list[str]:
        """List document IDs."""
        import fnmatch

        if pattern:
            return [k for k in self._documents.keys() if fnmatch.fnmatch(k, pattern)]
        return list(self._documents.keys())

    def document_count(self) -> int:
        """Get the number of documents."""
        return len(self._documents)


def create_openai_embedding_func(
    api_key: str | None = None,
    model: str = "text-embedding-ada-002",
) -> Callable[[str], Any]:
    """
    Create an async embedding function using OpenAI.

    Args:
        api_key: OpenAI API key (uses env var if not provided)
        model: Embedding model to use

    Returns:
        Async function that takes text and returns embeddings
    """
    async def embed(text: str) -> list[float]:
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError(
                "openai package is required. Install with: pip install openai"
            )

        client = AsyncOpenAI(api_key=api_key)
        response = await client.embeddings.create(
            input=text,
            model=model,
        )
        return response.data[0].embedding

    return embed
