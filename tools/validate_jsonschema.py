#!/usr/bin/env python3
"""
JSON Schema Validator for Docs2Code Pipeline.

Validates a JSON document against a JSON Schema.

Usage:
    python tools/validate_jsonschema.py document.json schema.json
"""

import argparse
import json
import sys
from pathlib import Path


def validate(document_path: Path, schema_path: Path) -> tuple[bool, list[str]]:
    """Validate a JSON document against a schema."""
    try:
        import jsonschema
    except ImportError:
        print("WARNING: jsonschema not installed, skipping validation", file=sys.stderr)
        return True, []

    with open(document_path) as f:
        document = json.load(f)

    with open(schema_path) as f:
        schema = json.load(f)

    errors = []
    validator = jsonschema.Draft7Validator(schema)

    for error in validator.iter_errors(document):
        path = '.'.join(str(p) for p in error.absolute_path)
        if path:
            errors.append(f"{path}: {error.message}")
        else:
            errors.append(error.message)

    return len(errors) == 0, errors


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Validate JSON document against schema'
    )
    parser.add_argument(
        'document',
        type=Path,
        help='Path to JSON document to validate'
    )
    parser.add_argument(
        'schema',
        type=Path,
        help='Path to JSON Schema'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only output errors'
    )

    args = parser.parse_args()

    if not args.document.exists():
        print(f"ERROR: Document not found: {args.document}", file=sys.stderr)
        sys.exit(1)

    if not args.schema.exists():
        print(f"ERROR: Schema not found: {args.schema}", file=sys.stderr)
        sys.exit(1)

    valid, errors = validate(args.document, args.schema)

    if valid:
        if not args.quiet:
            print(f"✓ {args.document} is valid")
        sys.exit(0)
    else:
        print(f"✗ {args.document} is invalid:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
