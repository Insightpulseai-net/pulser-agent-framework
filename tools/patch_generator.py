#!/usr/bin/env python3
"""
Patch Mode Generator for Docs2Code Pipeline.

Instead of rewriting entire files, generates unified diffs for incremental
updates. This reduces regressions and makes PR review more manageable.

Usage:
    python tools/patch_generator.py --docir docs/docir/docir.json --output patches/
    python tools/patch_generator.py --docir docs/docir/docir.json --apply
"""

import argparse
import difflib
import hashlib
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PatchGenerator')


@dataclass
class FileChange:
    """A single file change."""
    path: str
    action: str  # 'create', 'modify', 'delete'
    old_content: Optional[str]
    new_content: Optional[str]
    old_hash: Optional[str]
    new_hash: Optional[str]


@dataclass
class Patch:
    """A patch containing multiple file changes."""
    id: str
    timestamp: str
    docir_hash: str
    changes: list[FileChange] = field(default_factory=list)
    summary: str = ""


class ContentHasher:
    """Compute content hashes for change detection."""

    @staticmethod
    def hash_content(content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @staticmethod
    def hash_file(path: Path) -> Optional[str]:
        """Compute hash of file content."""
        if not path.exists():
            return None
        try:
            return ContentHasher.hash_content(path.read_text())
        except Exception:
            return None


class DiffGenerator:
    """Generate unified diffs between file versions."""

    @staticmethod
    def generate_diff(
        old_content: Optional[str],
        new_content: Optional[str],
        file_path: str,
    ) -> str:
        """Generate a unified diff between old and new content."""
        old_lines = (old_content or '').splitlines(keepends=True)
        new_lines = (new_content or '').splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f'a/{file_path}',
            tofile=f'b/{file_path}',
            lineterm='',
        )

        return ''.join(diff)

    @staticmethod
    def apply_diff(original: str, diff_text: str) -> str:
        """Apply a unified diff to content. Returns modified content."""
        # Parse the diff
        lines = diff_text.split('\n')
        result_lines = original.split('\n')

        # Simple line-by-line application (for production, use patch command)
        hunks = []
        current_hunk = None

        for line in lines:
            if line.startswith('@@'):
                if current_hunk:
                    hunks.append(current_hunk)
                # Parse hunk header
                parts = line.split('@@')
                if len(parts) >= 2:
                    range_info = parts[1].strip()
                    old_range, new_range = range_info.split(' ')
                    old_start = int(old_range.split(',')[0].lstrip('-'))
                    current_hunk = {
                        'start': old_start - 1,  # 0-indexed
                        'removes': [],
                        'adds': [],
                    }
            elif current_hunk is not None:
                if line.startswith('-') and not line.startswith('---'):
                    current_hunk['removes'].append(line[1:])
                elif line.startswith('+') and not line.startswith('+++'):
                    current_hunk['adds'].append(line[1:])

        if current_hunk:
            hunks.append(current_hunk)

        # Apply hunks in reverse order to preserve line numbers
        for hunk in reversed(hunks):
            start = hunk['start']
            # Remove old lines
            for _ in hunk['removes']:
                if start < len(result_lines):
                    result_lines.pop(start)
            # Add new lines
            for i, add_line in enumerate(hunk['adds']):
                result_lines.insert(start + i, add_line)

        return '\n'.join(result_lines)


class PatchModeGenerator:
    """
    Generate patches instead of full file rewrites.

    This approach:
    1. Compares existing files to what would be generated
    2. Creates unified diffs for only changed portions
    3. Allows review before applying
    4. Reduces merge conflicts
    """

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.changes: list[FileChange] = []

    def add_file(self, relative_path: str, new_content: str) -> FileChange:
        """Add a file creation or modification."""
        full_path = self.target_dir / relative_path

        if full_path.exists():
            old_content = full_path.read_text()
            old_hash = ContentHasher.hash_content(old_content)
        else:
            old_content = None
            old_hash = None

        new_hash = ContentHasher.hash_content(new_content)

        # Determine action
        if old_content is None:
            action = 'create'
        elif old_hash == new_hash:
            action = 'unchanged'
        else:
            action = 'modify'

        change = FileChange(
            path=relative_path,
            action=action,
            old_content=old_content,
            new_content=new_content,
            old_hash=old_hash,
            new_hash=new_hash,
        )
        self.changes.append(change)
        return change

    def delete_file(self, relative_path: str) -> Optional[FileChange]:
        """Mark a file for deletion."""
        full_path = self.target_dir / relative_path

        if not full_path.exists():
            return None

        old_content = full_path.read_text()
        old_hash = ContentHasher.hash_content(old_content)

        change = FileChange(
            path=relative_path,
            action='delete',
            old_content=old_content,
            new_content=None,
            old_hash=old_hash,
            new_hash=None,
        )
        self.changes.append(change)
        return change

    def generate_patch(self, docir_hash: str) -> Patch:
        """Generate a patch from accumulated changes."""
        patch = Patch(
            id=f"patch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.utcnow().isoformat(),
            docir_hash=docir_hash,
            changes=self.changes,
        )

        # Generate summary
        created = sum(1 for c in self.changes if c.action == 'create')
        modified = sum(1 for c in self.changes if c.action == 'modify')
        deleted = sum(1 for c in self.changes if c.action == 'delete')
        unchanged = sum(1 for c in self.changes if c.action == 'unchanged')

        patch.summary = f"Created: {created}, Modified: {modified}, Deleted: {deleted}, Unchanged: {unchanged}"

        return patch

    def write_patch_file(self, patch: Patch, output_path: Path) -> None:
        """Write patch to a file in unified diff format."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            # Write header
            f.write(f"# Patch ID: {patch.id}\n")
            f.write(f"# Timestamp: {patch.timestamp}\n")
            f.write(f"# DocIR Hash: {patch.docir_hash}\n")
            f.write(f"# Summary: {patch.summary}\n")
            f.write("#\n")

            # Write each change as a diff
            for change in patch.changes:
                if change.action == 'unchanged':
                    continue

                f.write(f"# Action: {change.action}\n")
                f.write(f"# File: {change.path}\n")

                if change.action == 'delete':
                    f.write(f"# (file deleted)\n")
                    diff = DiffGenerator.generate_diff(
                        change.old_content,
                        '',
                        change.path,
                    )
                else:
                    diff = DiffGenerator.generate_diff(
                        change.old_content,
                        change.new_content,
                        change.path,
                    )

                f.write(diff)
                f.write("\n\n")

        logger.info(f"Patch written to {output_path}")

    def apply_patch(self, patch: Patch, dry_run: bool = False) -> dict:
        """Apply a patch to the target directory."""
        results = {
            'applied': [],
            'skipped': [],
            'errors': [],
        }

        for change in patch.changes:
            full_path = self.target_dir / change.path

            try:
                if change.action == 'unchanged':
                    results['skipped'].append(change.path)
                    continue

                if change.action == 'create':
                    if dry_run:
                        logger.info(f"[DRY RUN] Would create: {change.path}")
                    else:
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        full_path.write_text(change.new_content)
                        logger.info(f"Created: {change.path}")
                    results['applied'].append(change.path)

                elif change.action == 'modify':
                    # Check if file still matches expected old content
                    if full_path.exists():
                        current_hash = ContentHasher.hash_file(full_path)
                        if current_hash != change.old_hash:
                            logger.warning(
                                f"File modified since patch created: {change.path}"
                            )
                            # Could implement 3-way merge here

                    if dry_run:
                        logger.info(f"[DRY RUN] Would modify: {change.path}")
                    else:
                        full_path.write_text(change.new_content)
                        logger.info(f"Modified: {change.path}")
                    results['applied'].append(change.path)

                elif change.action == 'delete':
                    if dry_run:
                        logger.info(f"[DRY RUN] Would delete: {change.path}")
                    else:
                        if full_path.exists():
                            full_path.unlink()
                            logger.info(f"Deleted: {change.path}")
                    results['applied'].append(change.path)

            except Exception as e:
                logger.error(f"Error applying change to {change.path}: {e}")
                results['errors'].append({'path': change.path, 'error': str(e)})

        return results


def generate_from_docir(docir_path: Path, output_dir: Path, mode: str = 'patch') -> Patch:
    """
    Generate code from DocIR in patch mode.

    This is a wrapper that uses the existing code generator but captures
    output for diff generation instead of direct file writes.
    """
    # Load DocIR
    with open(docir_path) as f:
        docir = json.load(f)

    docir_hash = ContentHasher.hash_content(json.dumps(docir, sort_keys=True))

    # Initialize patch generator
    patch_gen = PatchModeGenerator(output_dir)

    # Get module specs from DocIR
    module_map = docir.get('module_map', {})
    if not module_map:
        # Create default module
        module_map = {
            'ipai_generated': {
                'module_name': 'ipai_generated',
                'display_name': 'Generated Module',
                'category': 'native_odoo',
            }
        }

    # Generate content for each module
    for module_name, module_spec in module_map.items():
        _generate_module_content(
            patch_gen,
            module_name,
            module_spec,
            docir,
        )

    # Generate patch
    patch = patch_gen.generate_patch(docir_hash)
    return patch


def _generate_module_content(
    patch_gen: PatchModeGenerator,
    module_name: str,
    module_spec: dict,
    docir: dict,
) -> None:
    """Generate content for a single module."""
    base_path = f"addons/{module_name}"

    # __manifest__.py
    manifest_content = f'''# -*- coding: utf-8 -*-
"""
{module_spec.get('display_name', module_name)}

Generated by Docs2Code Pipeline (patch mode)
DocIR Version: {docir.get('version', 'unknown')}
"""
{{
    'name': '{module_spec.get("display_name", module_name)}',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Finance',
    'summary': 'Generated from documentation',
    'author': 'InsightPulseAI',
    'website': 'https://insightpulseai.com',
    'license': 'LGPL-3',
    'depends': {module_spec.get('depends', ['base', 'account'])},
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}}
'''
    patch_gen.add_file(f"{base_path}/__manifest__.py", manifest_content)

    # __init__.py
    init_content = '''# -*- coding: utf-8 -*-
from . import models
'''
    patch_gen.add_file(f"{base_path}/__init__.py", init_content)

    # models/__init__.py
    models = module_spec.get('models', [])
    if models:
        model_imports = '\n'.join(
            f'from . import {m.replace(".", "_")}' for m in models
        )
    else:
        model_imports = '# No models defined'
    patch_gen.add_file(f"{base_path}/models/__init__.py", f"# -*- coding: utf-8 -*-\n{model_imports}\n")

    # Generate model files from DocIR schemas
    for schema_name, schema in docir.get('schemas', {}).items():
        model_content = _generate_model_from_schema(schema_name, schema, docir)
        model_file_name = schema_name.lower().replace(' ', '_')
        patch_gen.add_file(f"{base_path}/models/{model_file_name}.py", model_content)

    # security/ir.model.access.csv
    security_lines = ['id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink']
    for schema_name in docir.get('schemas', {}).keys():
        model_name = schema_name.lower().replace(' ', '_')
        security_lines.append(
            f'access_{model_name}_user,{model_name} user,model_{model_name},base.group_user,1,1,1,1'
        )
    patch_gen.add_file(f"{base_path}/security/ir.model.access.csv", '\n'.join(security_lines) + '\n')

    # tests/__init__.py
    patch_gen.add_file(f"{base_path}/tests/__init__.py", f"# -*- coding: utf-8 -*-\nfrom . import test_{module_name}\n")

    # tests/test_module.py
    test_content = _generate_tests_from_docir(module_name, docir)
    patch_gen.add_file(f"{base_path}/tests/test_{module_name}.py", test_content)


def _generate_model_from_schema(schema_name: str, schema: dict, docir: dict) -> str:
    """Generate a Python model from a JSON schema."""
    class_name = ''.join(word.capitalize() for word in schema_name.split('_'))
    model_name = schema_name.lower().replace('_', '.')

    # Map JSON schema types to Odoo fields
    type_map = {
        'string': 'Char',
        'integer': 'Integer',
        'number': 'Float',
        'boolean': 'Boolean',
        'array': 'One2many',
    }

    fields_code = []
    for prop_name, prop_def in schema.get('properties', {}).items():
        prop_type = prop_def.get('type', 'string')
        odoo_type = type_map.get(prop_type, 'Char')
        required = prop_name in schema.get('required', [])

        # Handle enums as Selection
        if 'enum' in prop_def:
            enum_values = prop_def['enum']
            selection = ', '.join(f"('{v}', '{v.title()}')" for v in enum_values)
            field_line = f"    {prop_name} = fields.Selection([{selection}]"
        elif prop_def.get('format') == 'date':
            field_line = f"    {prop_name} = fields.Date("
        elif prop_def.get('format') == 'date-time':
            field_line = f"    {prop_name} = fields.Datetime("
        else:
            field_line = f"    {prop_name} = fields.{odoo_type}("

        if required:
            field_line += "required=True, "
        field_line = field_line.rstrip(', ') + ")"
        fields_code.append(field_line)

    if not fields_code:
        fields_code = ['    pass']

    # Add compliance references as docstring
    compliance_refs = []
    for rule in docir.get('compliance_rules', []):
        compliance_refs.append(f"    - {rule['id']}: {rule.get('description', '')[:50]}")

    compliance_doc = '\n'.join(compliance_refs) if compliance_refs else '    None'

    return f'''# -*- coding: utf-8 -*-
"""
{schema_name} Model

Generated by Docs2Code Pipeline (patch mode)

Compliance References:
{compliance_doc}
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class {class_name}(models.Model):
    """
    {schema_name}

    Auto-generated from DocIR schema definition.
    """
    _name = '{model_name}'
    _description = '{schema_name}'

{chr(10).join(fields_code)}
'''


def _generate_tests_from_docir(module_name: str, docir: dict) -> str:
    """Generate test cases from DocIR acceptance criteria."""
    test_methods = []

    for req in docir.get('requirements', []):
        for ac in req.get('acceptance', []):
            if ac['type'] in ['unit', 'integration']:
                method_name = f"test_{ac['id'].lower().replace('-', '_')}"
                assertion = ac.get('assert', 'Verify requirement')

                test_methods.append(f'''
    def {method_name}(self):
        """
        Requirement: {req['id']} - {req['title']}
        Acceptance: {ac['id']} - {assertion}
        """
        # TODO: Implement test
        # Assertion: {assertion}
        self.assertTrue(True, "Test not yet implemented")
''')

    if not test_methods:
        test_methods = ['''
    def test_placeholder(self):
        """Placeholder test."""
        self.assertTrue(True)
''']

    return f'''# -*- coding: utf-8 -*-
"""
Unit tests for {module_name}

Generated by Docs2Code Pipeline (patch mode)
Based on DocIR acceptance criteria
Target coverage: ≥90%
"""

from odoo.tests import TransactionCase


class Test{module_name.title().replace("_", "")}(TransactionCase):
    """Test cases generated from DocIR requirements."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        super().setUpClass()
{''.join(test_methods)}
'''


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate code patches from DocIR'
    )
    parser.add_argument(
        '--docir',
        type=Path,
        required=True,
        help='Path to DocIR JSON file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('patches'),
        help='Output directory for patches (or target dir for --apply)'
    )
    parser.add_argument(
        '--target',
        type=Path,
        help='Target directory for code generation (default: current dir)'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply patches directly to target directory'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making changes'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate DocIR exists
    if not args.docir.exists():
        logger.error(f"DocIR file not found: {args.docir}")
        sys.exit(1)

    # Determine target directory
    target_dir = args.target or Path.cwd()

    # Generate patch
    patch = generate_from_docir(args.docir, target_dir)

    logger.info(f"Generated patch: {patch.id}")
    logger.info(f"Summary: {patch.summary}")

    if args.apply or args.dry_run:
        # Apply patches
        patch_gen = PatchModeGenerator(target_dir)
        patch_gen.changes = patch.changes
        results = patch_gen.apply_patch(patch, dry_run=args.dry_run)

        print(f"\nResults:")
        print(f"  Applied: {len(results['applied'])}")
        print(f"  Skipped: {len(results['skipped'])}")
        print(f"  Errors: {len(results['errors'])}")

        if results['errors']:
            for err in results['errors']:
                print(f"    - {err['path']}: {err['error']}")
            sys.exit(1)
    else:
        # Write patch file
        patch_file = args.output / f"{patch.id}.patch"
        PatchModeGenerator(target_dir).write_patch_file(patch, patch_file)

        # Also write JSON version for programmatic use
        json_file = args.output / f"{patch.id}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'id': patch.id,
                'timestamp': patch.timestamp,
                'docir_hash': patch.docir_hash,
                'summary': patch.summary,
                'changes': [
                    {
                        'path': c.path,
                        'action': c.action,
                        'old_hash': c.old_hash,
                        'new_hash': c.new_hash,
                    }
                    for c in patch.changes
                ],
            }, f, indent=2)

        print(f"\nPatch files written:")
        print(f"  - {patch_file}")
        print(f"  - {json_file}")


if __name__ == '__main__':
    main()
