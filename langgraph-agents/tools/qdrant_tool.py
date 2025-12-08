"""
Qdrant Tool - Vector search from agents.
"""

import logging
from typing import Dict, List, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import openai
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QdrantTool:
    """Execute vector searches against Qdrant."""

    def __init__(self, url: str):
        self.client = QdrantClient(url=url)
        self.openai_client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info(f"Initialized Qdrant client: {url}")

    async def search(
        self,
        collection_name: str,
        query_text: str,
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            collection_name: Qdrant collection name
            query_text: Query text
            limit: Max results
            score_threshold: Minimum similarity score

        Returns:
            List of matching documents with scores
        """
        try:
            # Generate embedding for query
            embedding = await self._generate_embedding(query_text)

            # Search Qdrant
            results = self.client.search(
                collection_name=collection_name,
                query_vector=embedding,
                limit=limit,
                score_threshold=score_threshold
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "text": result.payload.get("text", ""),
                    "source": result.payload.get("source", ""),
                    "category": result.payload.get("category", "")
                })

            logger.info(f"Found {len(formatted_results)} results for query: {query_text[:50]}...")
            return formatted_results

        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            raise

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding for text."""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    async def upsert_documents(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]]
    ) -> None:
        """
        Insert or update documents in Qdrant.

        Args:
            collection_name: Qdrant collection name
            documents: List of documents with text and metadata
        """
        try:
            points = []
            for i, doc in enumerate(documents):
                embedding = await self._generate_embedding(doc["text"])

                point = PointStruct(
                    id=doc.get("id", i),
                    vector=embedding,
                    payload={
                        "text": doc["text"],
                        "source": doc.get("source", ""),
                        "category": doc.get("category", ""),
                        "created_at": doc.get("created_at", 0)
                    }
                )
                points.append(point)

            self.client.upsert(
                collection_name=collection_name,
                points=points
            )

            logger.info(f"Upserted {len(points)} documents to {collection_name}")

        except Exception as e:
            logger.error(f"Qdrant upsert failed: {e}")
            raise
