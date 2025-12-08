"""
Document Chunker - Chunking strategy for knowledge base ingestion.

Chunking strategies:
1. Fixed-size chunks (512 tokens)
2. Semantic chunks (paragraph boundaries)
3. Recursive chunks (hierarchical)
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import tiktoken
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentChunker:
    """Chunk documents for vector search ingestion."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk text using fixed-size strategy with overlap.

        Args:
            text: Text to chunk
            metadata: Metadata to attach to each chunk

        Returns:
            List of chunks with metadata
        """
        # Tokenize text
        tokens = self.encoding.encode(text)

        chunks = []
        start_idx = 0

        while start_idx < len(tokens):
            # Get chunk tokens
            end_idx = min(start_idx + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start_idx:end_idx]

            # Decode tokens back to text
            chunk_text = self.encoding.decode(chunk_tokens)

            # Create chunk with metadata
            chunk = {
                "text": chunk_text,
                "source": metadata.get("source", "unknown"),
                "category": metadata.get("category", "general"),
                "chunk_index": len(chunks),
                "total_tokens": len(chunk_tokens)
            }

            chunks.append(chunk)

            # Move to next chunk with overlap
            start_idx = end_idx - self.chunk_overlap

        logger.info(f"Created {len(chunks)} chunks from document: {metadata.get('source')}")
        return chunks

    def chunk_markdown(self, markdown: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk markdown using semantic boundaries (headers, paragraphs).
        """
        chunks = []
        sections = markdown.split("\n## ")  # Split on H2 headers

        for section in sections:
            if not section.strip():
                continue

            # Each section becomes a chunk
            chunk = {
                "text": section.strip(),
                "source": metadata.get("source", "unknown"),
                "category": metadata.get("category", "general"),
                "chunk_index": len(chunks),
                "total_tokens": len(self.encoding.encode(section))
            }

            # If chunk too large, split further
            if chunk["total_tokens"] > self.chunk_size:
                sub_chunks = self.chunk_text(section, metadata)
                chunks.extend(sub_chunks)
            else:
                chunks.append(chunk)

        logger.info(f"Created {len(chunks)} semantic chunks from markdown: {metadata.get('source')}")
        return chunks

    def process_directory(self, input_dir: Path, output_file: Path, category: str = "general") -> None:
        """
        Process all documents in a directory.

        Args:
            input_dir: Directory containing documents
            output_file: Output JSON file for chunks
            category: Category for all documents
        """
        all_chunks = []

        for file_path in input_dir.rglob("*.md"):
            logger.info(f"Processing: {file_path}")

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            metadata = {
                "source": str(file_path.relative_to(input_dir)),
                "category": category
            }

            chunks = self.chunk_markdown(content, metadata)
            all_chunks.extend(chunks)

        # Save chunks to JSON
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(all_chunks)} chunks to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Chunk documents for vector search")
    parser.add_argument("--input", required=True, help="Input directory with documents")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--category", default="general", help="Document category")
    parser.add_argument("--chunk-size", type=int, default=512, help="Chunk size in tokens")
    parser.add_argument("--overlap", type=int, default=50, help="Chunk overlap in tokens")

    args = parser.parse_args()

    chunker = DocumentChunker(chunk_size=args.chunk_size, chunk_overlap=args.overlap)
    chunker.process_directory(
        input_dir=Path(args.input),
        output_file=Path(args.output),
        category=args.category
    )


if __name__ == "__main__":
    main()


# Example usage:
# python document_chunker.py --input docs/ --output chunks.json --category "finance"
