"""
Documentation extractors for the Docs2Code pipeline.

Each extractor implements source-specific extraction logic:
- SAPExtractor: SAP S/4HANA AFC documentation
- MicrosoftExtractor: Microsoft Learn / Azure Architecture
- OdooExtractor: Odoo core modules (GitHub)
- OCAExtractor: OCA community modules (GitHub)
- BIRExtractor: Philippine BIR tax forms (PDF + OCR)
- DatabricksExtractor: Databricks Architecture Center
"""

from .base_extractor import BaseExtractor

__all__ = ['BaseExtractor']
