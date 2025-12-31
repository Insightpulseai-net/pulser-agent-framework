"""
Base extractor class for documentation sources.

All source-specific extractors should inherit from this base class.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExtractedDocument:
    """A single extracted document."""
    source_type: str
    source_url: str
    title: str
    content: str
    extraction_confidence: float
    metadata: dict[str, Any]


class BaseExtractor(ABC):
    """
    Base class for documentation extractors.

    All extractors must implement:
    - extract(): Main extraction method
    - _parse_page(): Parse a single page/document
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.warnings: list[str] = []
        self.errors: list[str] = []

    @abstractmethod
    def extract(
        self,
        url: str,
        max_depth: int = 5,
        timeout_seconds: int = 300,
    ) -> list[ExtractedDocument]:
        """
        Extract documents from the source.

        Args:
            url: Base URL or repository URL
            max_depth: Maximum recursion depth
            timeout_seconds: Timeout per extraction

        Returns:
            List of extracted documents
        """
        pass

    @abstractmethod
    def _parse_page(self, url: str) -> Optional[ExtractedDocument]:
        """
        Parse a single page/document.

        Args:
            url: URL of the page to parse

        Returns:
            ExtractedDocument or None if parsing failed
        """
        pass

    def _calculate_confidence(self, content: str, metadata: dict) -> float:
        """
        Calculate extraction confidence score.

        Args:
            content: Extracted content
            metadata: Extraction metadata

        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 1.0

        # Penalize short content
        if len(content) < 100:
            score -= 0.2

        # Penalize if no metadata
        if not metadata:
            score -= 0.1

        # Penalize if too many errors in parsing
        if self.errors:
            score -= min(0.3, len(self.errors) * 0.05)

        return max(0.0, min(1.0, score))

    def _clean_content(self, content: str) -> str:
        """
        Clean extracted content.

        Args:
            content: Raw content

        Returns:
            Cleaned content
        """
        import re

        # Remove excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r' {2,}', ' ', content)

        # Remove common noise
        content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL)
        content = re.sub(r'<style.*?</style>', '', content, flags=re.DOTALL)

        return content.strip()
