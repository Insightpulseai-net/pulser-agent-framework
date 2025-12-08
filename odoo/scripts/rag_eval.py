#!/usr/bin/env python3
"""
RAG Evaluation Pipeline
=======================

Evaluates RAG query performance using RAGAS metrics and stores results.

Usage:
    python rag_eval.py                     # Evaluate all unevaluated queries
    python rag_eval.py --query-id <id>     # Evaluate specific query
    python rag_eval.py --batch-size 50
    python rag_eval.py --dry-run

Metrics:
    - faithfulness: How factually accurate is the answer based on context?
    - answer_relevance: How relevant is the answer to the question?
    - context_relevance: How relevant is the retrieved context?
    - context_precision: Are the most relevant chunks ranked first?
    - context_recall: Does the context contain all needed info?

Environment Variables:
    DATABASE_URL        - PostgreSQL connection string
    OPENAI_API_KEY      - OpenAI API key (for RAGAS)
"""

import os
import sys
import argparse
import logging
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import DictCursor, Json
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
EVAL_BATCH_SIZE = int(os.getenv("EVAL_BATCH_SIZE", "20"))

# Console
console = Console()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("rag_eval.log"),
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class RAGQueryData:
    """Data for a RAG query to evaluate."""
    id: str
    query_text: str
    response_text: str
    retrieved_chunks: List[Dict]
    model: str


@dataclass
class EvaluationResult:
    """Result of evaluation."""
    query_id: str
    evaluator: str
    metrics: Dict[str, float]
    success: bool
    error: Optional[str] = None


class RAGASEvaluator:
    """Evaluates RAG queries using RAGAS metrics."""

    def __init__(self):
        self.ragas_available = False
        self._init_ragas()

    def _init_ragas(self):
        """Initialize RAGAS if available."""
        try:
            from ragas import evaluate
            from ragas.metrics import (
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            )
            self.ragas_available = True
            self.metrics = [
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            ]
            logger.info("RAGAS initialized successfully")
        except ImportError:
            logger.warning("RAGAS not installed, using fallback evaluation")
            self.ragas_available = False

    def evaluate(self, query_data: RAGQueryData) -> EvaluationResult:
        """Evaluate a single RAG query."""
        if self.ragas_available:
            return self._evaluate_ragas(query_data)
        else:
            return self._evaluate_fallback(query_data)

    def _evaluate_ragas(self, query_data: RAGQueryData) -> EvaluationResult:
        """Evaluate using RAGAS library."""
        try:
            from ragas import evaluate
            from datasets import Dataset

            # Prepare data for RAGAS
            contexts = [chunk.get("text", "") for chunk in query_data.retrieved_chunks]

            data = {
                "question": [query_data.query_text],
                "answer": [query_data.response_text],
                "contexts": [contexts],
            }

            dataset = Dataset.from_dict(data)
            results = evaluate(dataset, metrics=self.metrics)

            metrics = {
                "faithfulness": float(results.get("faithfulness", 0)),
                "answer_relevance": float(results.get("answer_relevancy", 0)),
                "context_precision": float(results.get("context_precision", 0)),
                "context_recall": float(results.get("context_recall", 0)),
            }

            return EvaluationResult(
                query_id=query_data.id,
                evaluator="ragas",
                metrics=metrics,
                success=True,
            )

        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {e}")
            return EvaluationResult(
                query_id=query_data.id,
                evaluator="ragas",
                metrics={},
                success=False,
                error=str(e),
            )

    def _evaluate_fallback(self, query_data: RAGQueryData) -> EvaluationResult:
        """Simple heuristic evaluation when RAGAS is not available."""
        metrics = {}

        # Answer length heuristic
        response_len = len(query_data.response_text)
        metrics["answer_length_score"] = min(1.0, response_len / 500)

        # Context usage heuristic
        if query_data.retrieved_chunks:
            # Check if answer seems to use the context
            context_text = " ".join(
                chunk.get("text", "")[:100]
                for chunk in query_data.retrieved_chunks
            ).lower()
            answer_words = set(query_data.response_text.lower().split())
            context_words = set(context_text.split())
            overlap = len(answer_words & context_words)
            metrics["context_overlap"] = min(1.0, overlap / max(len(answer_words), 1))
        else:
            metrics["context_overlap"] = 0.0

        # Query-answer relevance heuristic
        query_words = set(query_data.query_text.lower().split())
        answer_words = set(query_data.response_text.lower().split())
        query_overlap = len(query_words & answer_words)
        metrics["query_answer_overlap"] = min(1.0, query_overlap / max(len(query_words), 1))

        # Composite score
        metrics["composite_score"] = sum(metrics.values()) / len(metrics)

        return EvaluationResult(
            query_id=query_data.id,
            evaluator="heuristic",
            metrics=metrics,
            success=True,
        )


class RAGEvalPipeline:
    """Evaluation pipeline for RAG queries."""

    def __init__(self, db_url: str = DATABASE_URL, batch_size: int = EVAL_BATCH_SIZE):
        self.db_url = db_url
        self.batch_size = batch_size
        self.conn = None
        self.evaluator = RAGASEvaluator()

    def connect(self) -> bool:
        """Connect to database."""
        if not self.db_url:
            console.print("[red]DATABASE_URL not set[/red]")
            return False

        try:
            self.conn = psycopg2.connect(self.db_url)
            console.print("[green]Connected to database[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Connection failed: {e}[/red]")
            return False

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def get_unevaluated_queries(self, limit: int = None) -> List[RAGQueryData]:
        """Get queries that haven't been evaluated yet."""
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT q.id, q.query_text, q.response_text, q.retrieved_chunks, q.model
                FROM rag_queries q
                LEFT JOIN rag_evaluations e ON q.id = e.rag_query_id
                WHERE e.id IS NULL
                  AND q.success = true
                  AND q.response_text IS NOT NULL
                ORDER BY q.created_at
                LIMIT %s
            """, (limit or self.batch_size,))

            queries = []
            for row in cur.fetchall():
                queries.append(RAGQueryData(
                    id=str(row["id"]),
                    query_text=row["query_text"],
                    response_text=row["response_text"] or "",
                    retrieved_chunks=row["retrieved_chunks"] or [],
                    model=row["model"],
                ))
            return queries

    def get_query_by_id(self, query_id: str) -> Optional[RAGQueryData]:
        """Get a specific query by ID."""
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT id, query_text, response_text, retrieved_chunks, model
                FROM rag_queries
                WHERE id = %s
            """, (query_id,))
            row = cur.fetchone()
            if row:
                return RAGQueryData(
                    id=str(row["id"]),
                    query_text=row["query_text"],
                    response_text=row["response_text"] or "",
                    retrieved_chunks=row["retrieved_chunks"] or [],
                    model=row["model"],
                )
            return None

    def store_evaluation(self, result: EvaluationResult):
        """Store evaluation result in database."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO rag_evaluations (rag_query_id, evaluator, metrics)
                VALUES (%s, %s, %s)
            """, (
                result.query_id,
                result.evaluator,
                Json(result.metrics),
            ))
        self.conn.commit()

    def evaluate_query(self, query: RAGQueryData, dry_run: bool = False) -> EvaluationResult:
        """Evaluate a single query."""
        result = self.evaluator.evaluate(query)

        if not dry_run and result.success:
            self.store_evaluation(result)

        return result

    def get_evaluation_stats(self) -> Dict:
        """Get evaluation statistics."""
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total_evaluations,
                    AVG((metrics->>'faithfulness')::float) as avg_faithfulness,
                    AVG((metrics->>'answer_relevance')::float) as avg_answer_relevance,
                    AVG((metrics->>'context_precision')::float) as avg_context_precision,
                    AVG((metrics->>'context_recall')::float) as avg_context_recall,
                    AVG((metrics->>'composite_score')::float) as avg_composite
                FROM rag_evaluations
                WHERE metrics IS NOT NULL
            """)
            row = cur.fetchone()
            return dict(row) if row else {}

    def run(self, query_id: str = None, limit: int = None, dry_run: bool = False) -> Dict:
        """Run the evaluation pipeline."""
        results = {
            "evaluated": 0,
            "failed": 0,
            "metrics_summary": {},
        }

        if query_id:
            queries = [self.get_query_by_id(query_id)]
            queries = [q for q in queries if q]
        else:
            queries = self.get_unevaluated_queries(limit=limit)

        if not queries:
            console.print("[yellow]No queries to evaluate[/yellow]")
            return results

        console.print(f"Found {len(queries)} queries to evaluate")

        all_metrics = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Evaluating queries...", total=len(queries))

            for query in queries:
                progress.update(task, description=f"Evaluating query {query.id[:8]}...")

                try:
                    result = self.evaluate_query(query, dry_run)

                    if result.success:
                        results["evaluated"] += 1
                        all_metrics.append(result.metrics)
                    else:
                        results["failed"] += 1
                        console.print(f"  [yellow]Failed: {result.error}[/yellow]")

                except Exception as e:
                    logger.error(f"Evaluation failed for query {query.id}: {e}")
                    results["failed"] += 1

                progress.advance(task)

        # Compute average metrics
        if all_metrics:
            metric_keys = all_metrics[0].keys()
            for key in metric_keys:
                values = [m.get(key, 0) for m in all_metrics if key in m]
                if values:
                    results["metrics_summary"][key] = sum(values) / len(values)

        return results


def print_stats(stats: Dict):
    """Print evaluation statistics in a nice table."""
    table = Table(title="RAG Evaluation Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Average", justify="right", style="green")

    for key, value in stats.items():
        if value is not None and key != "total_evaluations":
            table.add_row(key, f"{value:.4f}" if isinstance(value, float) else str(value))

    if "total_evaluations" in stats:
        console.print(f"\nTotal evaluations: {stats['total_evaluations']}")

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="RAG Evaluation Pipeline")
    parser.add_argument("--query-id", "-q", help="Specific query ID to evaluate")
    parser.add_argument("--limit", "-l", type=int, default=EVAL_BATCH_SIZE, help="Max queries to evaluate")
    parser.add_argument("--stats", action="store_true", help="Show evaluation statistics")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be done")
    parser.add_argument("--db", default=DATABASE_URL, help="Database URL")

    args = parser.parse_args()

    pipeline = RAGEvalPipeline(db_url=args.db, batch_size=args.limit)

    if not pipeline.connect():
        sys.exit(1)

    try:
        if args.stats:
            stats = pipeline.get_evaluation_stats()
            print_stats(stats)
            return

        results = pipeline.run(
            query_id=args.query_id,
            limit=args.limit,
            dry_run=args.dry_run,
        )

        console.print("\n[bold]Evaluation Results[/bold]")
        console.print(f"  Evaluated: {results['evaluated']}")
        console.print(f"  Failed: {results['failed']}")

        if results["metrics_summary"]:
            console.print("\n[bold]Average Metrics[/bold]")
            for key, value in results["metrics_summary"].items():
                console.print(f"  {key}: {value:.4f}")

        if results["failed"] > 0:
            sys.exit(1)

    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
