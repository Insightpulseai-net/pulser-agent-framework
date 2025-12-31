#!/usr/bin/env python3
"""
DocumentationParser Agent - Main Entry Point

Extracts structured knowledge from 6 documentation sources and stores
in Supabase pgvector for downstream agent consumption.

Usage:
    python -m pipelines.ingest.parse --source-type sap_s4hana --url "..."

Sources:
    - sap_s4hana: SAP S/4HANA Advanced Financial Closing docs
    - microsoft_learn: Microsoft Azure Architecture Center
    - odoo_core: Odoo 18.0 core modules (GitHub)
    - oca_modules: OCA community modules (GitHub)
    - bir_regulatory: BIR eForms and tax regulations
    - databricks_arch: Databricks Architecture Center
"""

import argparse
import hashlib
import json
import logging
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DocumentationParser')


@dataclass
class ExtractionResult:
    """Result of a documentation extraction."""
    source_type: str
    source_url: str
    extraction_id: str
    documents_extracted: int
    chunks_created: int
    embeddings_queued: int
    extraction_confidence: float
    warnings: list[str]
    errors: list[str]
    duration_seconds: float


@dataclass
class Document:
    """A single extracted document."""
    source_type: str
    source_url: str
    title: str
    content: str
    extraction_confidence: float
    metadata: dict[str, Any]


@dataclass
class Chunk:
    """A document chunk for embedding."""
    doc_id: str
    chunk_index: int
    content: str
    entity_type: Optional[str]
    entity_name: Optional[str]
    regulatory_refs: list[str]
    code_patterns: list[dict]


class DocumentationParser:
    """
    Main parser agent for documentation extraction.

    Implements the DocumentationParser.SKILL.md specification:
    - Extracts from 6 sources
    - Creates JSON ASTs
    - Stores in Supabase (Bronze/Silver layers)
    - Queues embeddings for Gold layer
    """

    VALID_SOURCE_TYPES = [
        'sap_s4hana',
        'microsoft_learn',
        'odoo_core',
        'oca_modules',
        'bir_regulatory',
        'databricks_arch',
        'figma_design',
    ]

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        extraction_id: Optional[str] = None,
    ):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.extraction_id = extraction_id or f"ext_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.warnings: list[str] = []
        self.errors: list[str] = []

    def extract(
        self,
        source_type: str,
        url: str,
        max_depth: int = 5,
        timeout_seconds: int = 300,
    ) -> ExtractionResult:
        """
        Extract documentation from a source.

        Args:
            source_type: Type of source (sap_s4hana, microsoft_learn, etc.)
            url: Base URL or repo URL to extract from
            max_depth: Maximum recursion depth (1-50)
            timeout_seconds: Timeout per extraction (max 300)

        Returns:
            ExtractionResult with extraction statistics
        """
        import time
        start_time = time.time()

        # Validate source type
        if source_type not in self.VALID_SOURCE_TYPES:
            raise ValueError(f"Invalid source_type: {source_type}. Must be one of {self.VALID_SOURCE_TYPES}")

        # Validate constraints
        max_depth = min(max(1, max_depth), 50)  # Clamp 1-50
        timeout_seconds = min(max(30, timeout_seconds), 300)  # Clamp 30-300

        logger.info(f"Starting extraction from {source_type}: {url}")
        logger.info(f"Extraction ID: {self.extraction_id}")
        logger.info(f"Max depth: {max_depth}, Timeout: {timeout_seconds}s")

        # Get the appropriate extractor
        extractor = self._get_extractor(source_type)

        # Run extraction
        try:
            documents = extractor.extract(url, max_depth, timeout_seconds)
            logger.info(f"Extracted {len(documents)} documents")
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            self.errors.append(str(e))
            documents = []

        # Create chunks
        chunks = []
        for doc in documents:
            doc_chunks = self._create_chunks(doc)
            chunks.extend(doc_chunks)

        logger.info(f"Created {len(chunks)} chunks")

        # Calculate duration
        duration = time.time() - start_time

        # Calculate confidence
        if documents:
            avg_confidence = sum(d.extraction_confidence for d in documents) / len(documents)
        else:
            avg_confidence = 0.0

        return ExtractionResult(
            source_type=source_type,
            source_url=url,
            extraction_id=self.extraction_id,
            documents_extracted=len(documents),
            chunks_created=len(chunks),
            embeddings_queued=len(chunks),  # All chunks queued for embedding
            extraction_confidence=avg_confidence,
            warnings=self.warnings.copy(),
            errors=self.errors.copy(),
            duration_seconds=duration,
        )

    def _get_extractor(self, source_type: str):
        """Get the appropriate extractor for a source type."""
        # Import extractors dynamically
        if source_type == 'sap_s4hana':
            from pipelines.ingest.extractors.sap_extractor import SAPExtractor
            return SAPExtractor()
        elif source_type == 'microsoft_learn':
            from pipelines.ingest.extractors.microsoft_extractor import MicrosoftExtractor
            return MicrosoftExtractor()
        elif source_type == 'odoo_core':
            from pipelines.ingest.extractors.odoo_extractor import OdooExtractor
            return OdooExtractor()
        elif source_type == 'oca_modules':
            from pipelines.ingest.extractors.oca_extractor import OCAExtractor
            return OCAExtractor()
        elif source_type == 'bir_regulatory':
            from pipelines.ingest.extractors.bir_extractor import BIRExtractor
            return BIRExtractor()
        elif source_type == 'databricks_arch':
            from pipelines.ingest.extractors.databricks_extractor import DatabricksExtractor
            return DatabricksExtractor()
        else:
            raise ValueError(f"No extractor for source type: {source_type}")

    def _create_chunks(self, doc: Document, chunk_size: int = 1000) -> list[Chunk]:
        """Split document into chunks for embedding."""
        chunks = []
        content = doc.content
        doc_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Simple chunking by character count (can be improved with semantic chunking)
        for i in range(0, len(content), chunk_size):
            chunk_content = content[i:i + chunk_size]

            # Extract regulatory references from chunk
            regulatory_refs = self._extract_regulatory_refs(chunk_content)

            # Extract code patterns
            code_patterns = self._extract_code_patterns(chunk_content)

            # Determine entity type
            entity_type = self._determine_entity_type(chunk_content)

            chunks.append(Chunk(
                doc_id=doc_hash,
                chunk_index=i // chunk_size,
                content=chunk_content,
                entity_type=entity_type,
                entity_name=doc.title,
                regulatory_refs=regulatory_refs,
                code_patterns=code_patterns,
            ))

        return chunks

    def _extract_regulatory_refs(self, text: str) -> list[str]:
        """Extract regulatory references from text."""
        import re

        refs = set()

        # BIR forms
        bir_pattern = r'BIR[- ]?(\d{4}[A-Z]?)'
        for match in re.finditer(bir_pattern, text, re.IGNORECASE):
            refs.add(f"BIR_{match.group(1)}")

        # PFRS standards
        pfrs_pattern = r'PFRS[- ]?(\d+)'
        for match in re.finditer(pfrs_pattern, text, re.IGNORECASE):
            refs.add(f"PFRS_{match.group(1)}")

        # PAS standards
        pas_pattern = r'PAS[- ]?(\d+)'
        for match in re.finditer(pas_pattern, text, re.IGNORECASE):
            refs.add(f"PAS_{match.group(1)}")

        return list(refs)

    def _extract_code_patterns(self, text: str) -> list[dict]:
        """Extract code patterns from text."""
        import re

        patterns = []

        # Look for code blocks
        code_block_pattern = r'```(\w+)?\n(.*?)```'
        for match in re.finditer(code_block_pattern, text, re.DOTALL):
            language = match.group(1) or 'unknown'
            code = match.group(2).strip()
            patterns.append({
                'language': language,
                'code': code[:500],  # Truncate long code
            })

        return patterns

    def _determine_entity_type(self, text: str) -> Optional[str]:
        """Determine the entity type from content."""
        text_lower = text.lower()

        if 'api' in text_lower or 'endpoint' in text_lower:
            return 'api_endpoint'
        elif 'workflow' in text_lower or 'process' in text_lower:
            return 'workflow'
        elif 'table' in text_lower or 'schema' in text_lower:
            return 'table'
        elif 'form' in text_lower or 'bir' in text_lower:
            return 'form'
        elif 'rule' in text_lower or 'policy' in text_lower:
            return 'rule'
        elif 'config' in text_lower or 'setting' in text_lower:
            return 'config'

        return None


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='DocumentationParser Agent - Extract docs to Supabase'
    )
    parser.add_argument(
        '--source-type',
        required=True,
        choices=DocumentationParser.VALID_SOURCE_TYPES,
        help='Type of documentation source'
    )
    parser.add_argument(
        '--url',
        required=True,
        help='Base URL or repository URL to extract from'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output file path for extraction results (JSONL)'
    )
    parser.add_argument(
        '--extraction-id',
        help='Extraction ID (auto-generated if not provided)'
    )
    parser.add_argument(
        '--supabase-url',
        required=True,
        help='Supabase project URL'
    )
    parser.add_argument(
        '--supabase-key',
        required=True,
        help='Supabase anon key'
    )
    parser.add_argument(
        '--max-depth',
        type=int,
        default=5,
        help='Maximum recursion depth (1-50)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Timeout in seconds (30-300)'
    )

    args = parser.parse_args()

    # Create parser
    doc_parser = DocumentationParser(
        supabase_url=args.supabase_url,
        supabase_key=args.supabase_key,
        extraction_id=args.extraction_id,
    )

    # Run extraction
    try:
        result = doc_parser.extract(
            source_type=args.source_type,
            url=args.url,
            max_depth=args.max_depth,
            timeout_seconds=args.timeout,
        )

        # Output result
        result_dict = asdict(result)
        result_json = json.dumps(result_dict, indent=2)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w') as f:
                f.write(result_json)
            logger.info(f"Results written to {args.output}")
        else:
            print(result_json)

        # Exit with error if extraction failed
        if result.errors:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
