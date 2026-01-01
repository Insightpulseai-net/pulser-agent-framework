"""
Dataset builders for ML training pipelines.

This module provides utilities for building training datasets from various sources:
- docs_to_jsonl: Convert documentation to SFT JSONL format
- code_pairs: Generate code pair datasets for fine-tuning
- conversations: Build conversational datasets
"""

from pathlib import Path

BUILDERS_DIR = Path(__file__).parent
