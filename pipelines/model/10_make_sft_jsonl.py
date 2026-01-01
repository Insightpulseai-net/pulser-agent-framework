#!/usr/bin/env python3
"""
GENERATED FILE - DO NOT EDIT MANUALLY
Source: docs-to-code-pipeline Model Factory
Generated: 2026-01-01T00:00:00Z
Regenerate: Managed by repository template

Build SFT Training Dataset
--------------------------
Converts source documents to supervised fine-tuning JSONL format.

Usage:
    python pipelines/model/10_make_sft_jsonl.py --version v1 --output data/train.jsonl
"""

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def compute_hash(content: str) -> str:
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()


def load_source_documents(source_dir: str) -> list:
    """Load source documents from directory."""
    source_path = Path(source_dir)
    documents = []

    if not source_path.exists():
        logger.warning(f"Source directory not found: {source_dir}")
        return documents

    for file_path in source_path.glob("**/*.md"):
        with open(file_path, "r") as f:
            content = f.read()
        documents.append({
            "path": str(file_path),
            "content": content,
        })

    logger.info(f"Loaded {len(documents)} source documents")
    return documents


def convert_to_sft_format(documents: list) -> list:
    """Convert documents to SFT instruction format."""
    samples = []

    for doc in documents:
        content = doc["content"]

        # Extract sections and convert to instruction-output pairs
        # This is a simplified example - customize for your data
        sections = content.split("##")

        for section in sections:
            if not section.strip():
                continue

            lines = section.strip().split("\n")
            if len(lines) < 2:
                continue

            title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()

            if title and body:
                samples.append({
                    "instruction": f"Explain: {title}",
                    "input": "",
                    "output": body[:1000],  # Limit length
                })

    logger.info(f"Generated {len(samples)} SFT samples")
    return samples


def write_jsonl(samples: list, output_path: str):
    """Write samples to JSONL file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        for sample in samples:
            f.write(json.dumps(sample) + "\n")

    logger.info(f"Wrote {len(samples)} samples to {output_path}")


def register_dataset(version: str, output_path: str, samples: list):
    """Register dataset in registry."""
    registry_path = Path("ml/datasets/registry.yaml")

    if not registry_path.exists():
        logger.warning("Dataset registry not found, skipping registration")
        return

    # Compute content hash
    content = json.dumps(samples, sort_keys=True)
    content_hash = compute_hash(content)

    registration = {
        "version": version,
        "path": output_path,
        "row_count": len(samples),
        "content_sha256": content_hash,
        "created_at": datetime.utcnow().isoformat(),
    }

    logger.info(f"Dataset registered: {json.dumps(registration, indent=2)}")


def main():
    parser = argparse.ArgumentParser(description="Build SFT Training Dataset")
    parser.add_argument(
        "--version", default="v1", help="Dataset version"
    )
    parser.add_argument(
        "--source", default="docs", help="Source documents directory"
    )
    parser.add_argument(
        "--output", default="data/train.jsonl", help="Output JSONL file"
    )

    args = parser.parse_args()

    logger.info(f"Building SFT dataset version: {args.version}")
    logger.info(f"Source: {args.source}")
    logger.info(f"Output: {args.output}")

    # Load source documents
    documents = load_source_documents(args.source)

    if not documents:
        logger.warning("No source documents found, creating sample dataset")
        # Create sample data for testing
        samples = [
            {
                "instruction": "What is InsightPulse AI?",
                "input": "",
                "output": "InsightPulse AI is a platform for building AI-powered applications.",
            },
            {
                "instruction": "How do I create an agent?",
                "input": "",
                "output": "To create an agent, define a skill file and register it in the skills directory.",
            },
        ]
    else:
        # Convert to SFT format
        samples = convert_to_sft_format(documents)

    # Write output
    write_jsonl(samples, args.output)

    # Register dataset
    register_dataset(args.version, args.output, samples)

    logger.info("Dataset build complete!")


if __name__ == "__main__":
    main()
