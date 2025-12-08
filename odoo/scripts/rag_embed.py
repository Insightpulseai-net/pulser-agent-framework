#!/usr/bin/env python3
"""
RAG Embedding Pipeline
======================

Generates embeddings for chunks and stores them in pgvector.

Usage:
    python rag_embed.py                    # Embed all unembedded chunks
    python rag_embed.py --model text-embedding-3-large
    python rag_embed.py --batch-size 100
    python rag_embed.py --dry-run

Environment Variables:
    DATABASE_URL        - PostgreSQL connection string
    OPENAI_API_KEY      - OpenAI API key
    EMBEDDING_MODEL     - Default model (text-embedding-3-large)
    EMBEDDING_BATCH_SIZE - Batch size for API calls
"""

import os
import sys
import argparse
import logging
import time
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

try:
    import psycopg2
    from psycopg2.extras import DictCursor, execute_values
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

# Import our LLM client
try:
    from llm_client import LLMClient, EmbeddingResponse
except ImportError:
    # Fallback if not in path
    sys.path.insert(0, os.path.dirname(__file__))
    from llm_client import LLMClient, EmbeddingResponse

load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "50"))

# Model dimensions
MODEL_DIMENSIONS = {
    "text-embedding-3-large": 3072,  # Can be reduced to 1536
    "text-embedding-3-small": 1536,
    "text-embedding-ada-002": 1536,
    "nomic-embed-text": 768,
}

# Console
console = Console()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("rag_embed.log"),
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ChunkBatch:
    """Batch of chunks for embedding."""
    chunk_ids: List[str]
    tenant_ids: List[str]
    texts: List[str]


class RAGEmbedder:
    """Generates and stores embeddings for RAG chunks."""

    def __init__(
        self,
        db_url: str = DATABASE_URL,
        model: str = EMBEDDING_MODEL,
        batch_size: int = EMBEDDING_BATCH_SIZE,
        provider: str = "openai",
    ):
        self.db_url = db_url
        self.model = model
        self.batch_size = batch_size
        self.provider = provider
        self.dimensions = MODEL_DIMENSIONS.get(model, 1536)
        self.conn = None
        self.llm_client = None

    def connect(self) -> bool:
        """Connect to database and initialize LLM client."""
        if not self.db_url:
            console.print("[red]DATABASE_URL not set[/red]")
            return False

        try:
            self.conn = psycopg2.connect(self.db_url)
            console.print("[green]Connected to database[/green]")

            # Initialize LLM client
            self.llm_client = LLMClient(provider=self.provider)
            console.print(f"[green]Initialized {self.provider} client with model {self.model}[/green]")

            return True
        except Exception as e:
            console.print(f"[red]Connection failed: {e}[/red]")
            return False

    def close(self):
        """Close connections."""
        if self.conn:
            self.conn.close()

    def get_unembedded_chunks(self, limit: int = 1000) -> List[Dict]:
        """Get chunks that don't have embeddings yet."""
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT c.id, c.tenant_id, c.text
                FROM rag_chunks c
                LEFT JOIN rag_embeddings e ON c.id = e.chunk_id AND e.model = %s
                WHERE e.id IS NULL
                ORDER BY c.created_at
                LIMIT %s
            """, (self.model, limit))
            return [dict(row) for row in cur.fetchall()]

    def get_embedding_stats(self) -> Dict:
        """Get statistics about embeddings."""
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT
                    COUNT(DISTINCT c.id) as total_chunks,
                    COUNT(DISTINCT e.chunk_id) as embedded_chunks,
                    COUNT(DISTINCT e.model) as models_used
                FROM rag_chunks c
                LEFT JOIN rag_embeddings e ON c.id = e.chunk_id
            """)
            row = cur.fetchone()
            return dict(row)

    def create_batches(self, chunks: List[Dict]) -> List[ChunkBatch]:
        """Split chunks into batches."""
        batches = []
        for i in range(0, len(chunks), self.batch_size):
            batch_chunks = chunks[i:i + self.batch_size]
            batches.append(ChunkBatch(
                chunk_ids=[c["id"] for c in batch_chunks],
                tenant_ids=[c["tenant_id"] for c in batch_chunks],
                texts=[c["text"] for c in batch_chunks],
            ))
        return batches

    def embed_batch(self, batch: ChunkBatch, dry_run: bool = False) -> Tuple[int, float]:
        """Generate embeddings for a batch of texts."""
        if dry_run:
            return len(batch.texts), 0.0

        try:
            # Call embedding API
            responses = self.llm_client.embed(batch.texts, model=self.model)

            # Handle single response case
            if isinstance(responses, EmbeddingResponse):
                responses = [responses]

            # Store embeddings
            self._store_embeddings(batch, responses)

            total_cost = sum(r.cost_usd for r in responses)
            return len(responses), total_cost

        except Exception as e:
            logger.error(f"Embedding batch failed: {e}")
            raise

    def _store_embeddings(self, batch: ChunkBatch, responses: List[EmbeddingResponse]):
        """Store embeddings in database."""
        with self.conn.cursor() as cur:
            # Prepare values for bulk insert
            values = []
            for i, (chunk_id, tenant_id, response) in enumerate(
                zip(batch.chunk_ids, batch.tenant_ids, responses)
            ):
                # Format vector for pgvector
                embedding_str = "[" + ",".join(str(x) for x in response.embedding) + "]"

                values.append((
                    tenant_id,
                    chunk_id,
                    self.model,
                    response.dimensions,
                    embedding_str,
                ))

            # Bulk insert
            execute_values(
                cur,
                """
                INSERT INTO rag_embeddings (tenant_id, chunk_id, model, dimensions, embedding)
                VALUES %s
                ON CONFLICT (chunk_id, model) DO UPDATE
                SET embedding = EXCLUDED.embedding, created_at = NOW()
                """,
                values,
                template="(%s, %s, %s, %s, %s::vector)"
            )

        self.conn.commit()

    def run(self, limit: int = None, dry_run: bool = False) -> Dict:
        """Run the embedding pipeline."""
        results = {
            "total_chunks": 0,
            "embedded": 0,
            "failed": 0,
            "total_cost": 0.0,
        }

        # Get stats first
        stats = self.get_embedding_stats()
        console.print(f"Total chunks: {stats['total_chunks']}, Already embedded: {stats['embedded_chunks']}")

        # Get unembedded chunks
        chunks = self.get_unembedded_chunks(limit=limit or 10000)
        results["total_chunks"] = len(chunks)

        if not chunks:
            console.print("[green]All chunks already embedded![/green]")
            return results

        console.print(f"Found {len(chunks)} chunks to embed")

        # Create batches
        batches = self.create_batches(chunks)
        console.print(f"Created {len(batches)} batches of up to {self.batch_size} chunks")

        # Process batches
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Embedding chunks...", total=len(batches))

            for batch in batches:
                try:
                    progress.update(task, description=f"Embedding batch ({len(batch.texts)} chunks)...")

                    embedded, cost = self.embed_batch(batch, dry_run)
                    results["embedded"] += embedded
                    results["total_cost"] += cost

                    # Rate limiting
                    if not dry_run:
                        time.sleep(0.1)  # Small delay between batches

                except Exception as e:
                    logger.error(f"Batch failed: {e}")
                    results["failed"] += len(batch.texts)

                progress.advance(task)

        return results


def main():
    parser = argparse.ArgumentParser(description="RAG Embedding Pipeline")
    parser.add_argument("--model", "-m", default=EMBEDDING_MODEL, help="Embedding model")
    parser.add_argument("--batch-size", "-b", type=int, default=EMBEDDING_BATCH_SIZE, help="Batch size")
    parser.add_argument("--limit", "-l", type=int, help="Max chunks to process")
    parser.add_argument("--provider", "-p", default="openai", help="LLM provider")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be done")
    parser.add_argument("--db", default=DATABASE_URL, help="Database URL")

    args = parser.parse_args()

    embedder = RAGEmbedder(
        db_url=args.db,
        model=args.model,
        batch_size=args.batch_size,
        provider=args.provider,
    )

    if not embedder.connect():
        sys.exit(1)

    try:
        results = embedder.run(limit=args.limit, dry_run=args.dry_run)

        console.print("\n[bold]Embedding Results[/bold]")
        console.print(f"  Total chunks: {results['total_chunks']}")
        console.print(f"  Embedded: {results['embedded']}")
        console.print(f"  Failed: {results['failed']}")
        console.print(f"  Total cost: ${results['total_cost']:.4f}")

        if results["failed"] > 0:
            sys.exit(1)
    finally:
        embedder.close()


if __name__ == "__main__":
    main()
