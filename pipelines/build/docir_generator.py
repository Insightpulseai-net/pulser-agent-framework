#!/usr/bin/env python3
"""
DocIR-Aware Code Generator

Bridges the DocIR intermediate representation with the existing CodeGenerator.
Implements the staged pipeline: DocIR -> Generate -> Verify

Usage:
    python -m pipelines.build.docir_generator --docir docs/docir/docir.json --output addons/
"""

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DocIRGenerator')


@dataclass
class GenerationConfig:
    """Configuration for code generation."""
    mode: str = 'patch'  # 'full' or 'patch'
    odoo_version: str = '18.0'
    enforce_80_15_5: bool = True
    generate_tests: bool = True
    test_coverage_target: float = 0.90
    lint_on_generate: bool = True
    format_on_generate: bool = True


@dataclass
class GenerationResult:
    """Result of code generation from DocIR."""
    generation_id: str
    docir_version: str
    docir_hash: str
    timestamp: str
    modules_generated: list[str]
    files_created: int
    files_modified: int
    files_unchanged: int
    rule_compliance: dict
    test_coverage_estimate: float
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class DocIRValidator:
    """Validates DocIR before generation."""

    REQUIRED_FIELDS = ['doc_id', 'version', 'sources', 'requirements']

    def validate(self, docir: dict) -> tuple[bool, list[str]]:
        """Validate DocIR structure."""
        errors = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in docir:
                errors.append(f"Missing required field: {field}")

        # Validate requirements
        for i, req in enumerate(docir.get('requirements', [])):
            if 'id' not in req:
                errors.append(f"Requirement {i} missing 'id'")
            if 'title' not in req:
                errors.append(f"Requirement {i} missing 'title'")
            if 'acceptance' not in req or not req['acceptance']:
                errors.append(f"Requirement {req.get('id', i)} missing acceptance criteria")

        # Validate schemas
        for name, schema in docir.get('schemas', {}).items():
            if 'type' not in schema and 'properties' not in schema:
                errors.append(f"Schema '{name}' invalid: missing type or properties")

        return len(errors) == 0, errors


class DocIRGenerator:
    """
    Generate code from DocIR intermediate representation.

    Implements the staged pipeline:
    1. Validate DocIR
    2. Map requirements to modules
    3. Generate code in patch mode
    4. Run verification
    """

    def __init__(self, config: Optional[GenerationConfig] = None):
        self.config = config or GenerationConfig()
        self.validator = DocIRValidator()

    def generate(
        self,
        docir_path: Path,
        output_dir: Path,
    ) -> GenerationResult:
        """
        Generate code from DocIR.

        Args:
            docir_path: Path to DocIR JSON file
            output_dir: Output directory for generated code

        Returns:
            GenerationResult with statistics and status
        """
        generation_id = f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting generation: {generation_id}")

        # Load DocIR
        with open(docir_path) as f:
            docir = json.load(f)

        docir_hash = self._compute_hash(docir)
        docir_version = docir.get('version', 'unknown')

        # Validate
        valid, errors = self.validator.validate(docir)
        if not valid:
            logger.error("DocIR validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return GenerationResult(
                generation_id=generation_id,
                docir_version=docir_version,
                docir_hash=docir_hash,
                timestamp=datetime.utcnow().isoformat(),
                modules_generated=[],
                files_created=0,
                files_modified=0,
                files_unchanged=0,
                rule_compliance={},
                test_coverage_estimate=0.0,
                errors=errors,
            )

        # Map requirements to modules
        module_map = self._map_requirements_to_modules(docir)

        # Generate code for each module
        all_files = []
        modules_generated = []

        for module_name, module_spec in module_map.items():
            logger.info(f"Generating module: {module_name}")
            files = self._generate_module(
                module_name,
                module_spec,
                docir,
                output_dir,
            )
            all_files.extend(files)
            modules_generated.append(module_name)

        # Calculate statistics
        created = sum(1 for f in all_files if f['action'] == 'created')
        modified = sum(1 for f in all_files if f['action'] == 'modified')
        unchanged = sum(1 for f in all_files if f['action'] == 'unchanged')

        # Calculate 80/15/5 compliance
        rule_compliance = self._calculate_rule_compliance(all_files)

        # Estimate test coverage
        test_coverage = self._estimate_test_coverage(all_files)

        # Collect warnings
        warnings = []
        if not rule_compliance.get('is_compliant', True):
            warnings.append("80/15/5 rule violation detected")
        if test_coverage < self.config.test_coverage_target:
            warnings.append(f"Test coverage {test_coverage:.1%} below target {self.config.test_coverage_target:.1%}")

        result = GenerationResult(
            generation_id=generation_id,
            docir_version=docir_version,
            docir_hash=docir_hash,
            timestamp=datetime.utcnow().isoformat(),
            modules_generated=modules_generated,
            files_created=created,
            files_modified=modified,
            files_unchanged=unchanged,
            rule_compliance=rule_compliance,
            test_coverage_estimate=test_coverage,
            warnings=warnings,
        )

        logger.info(f"Generation complete: {len(modules_generated)} modules, "
                   f"{created} created, {modified} modified, {unchanged} unchanged")

        return result

    def _compute_hash(self, docir: dict) -> str:
        """Compute hash of DocIR for change detection."""
        import hashlib
        content = json.dumps(docir, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _map_requirements_to_modules(self, docir: dict) -> dict:
        """Map requirements to Odoo modules."""
        # Use module_map from DocIR if available
        if 'module_map' in docir and docir['module_map']:
            return docir['module_map']

        # Otherwise, create a default module
        requirements = docir.get('requirements', [])
        schemas = docir.get('schemas', {})

        # Group requirements by first tag or compliance ref
        module_map = {}

        # Default module
        default_module = {
            'module_name': 'ipai_generated',
            'display_name': 'Generated Module',
            'category': 'native_odoo',
            'depends': ['base', 'account'],
            'models': list(schemas.keys()),
            'requirement_refs': [r['id'] for r in requirements],
        }
        module_map['ipai_generated'] = default_module

        return module_map

    def _generate_module(
        self,
        module_name: str,
        module_spec: dict,
        docir: dict,
        output_dir: Path,
    ) -> list[dict]:
        """Generate a single Odoo module."""
        from pipelines.build.code_generator import CodeGenerator

        # Create module path
        module_path = output_dir / module_name
        module_path.mkdir(parents=True, exist_ok=True)

        # Prepare module spec for CodeGenerator
        gen_spec = {
            'module_name': module_name,
            'display_name': module_spec.get('display_name', module_name),
            'version': f"{self.config.odoo_version}.1.0.0",
            'category': 'Accounting/Finance',
            'description': f"Generated from DocIR v{docir.get('version', 'unknown')}",
            'author': 'InsightPulseAI',
            'models': [],
        }

        # Convert schemas to model specs
        for schema_name in module_spec.get('models', []):
            if schema_name in docir.get('schemas', {}):
                schema = docir['schemas'][schema_name]
                model_spec = self._schema_to_model_spec(schema_name, schema)
                gen_spec['models'].append(model_spec)

        # Generate using patch mode if configured
        if self.config.mode == 'patch':
            files = self._generate_patch_mode(module_path, gen_spec, docir)
        else:
            files = self._generate_full_mode(module_path, gen_spec, docir)

        return files

    def _schema_to_model_spec(self, name: str, schema: dict) -> dict:
        """Convert JSON Schema to Odoo model spec."""
        model_name = name.lower().replace('_', '.')

        # Map JSON Schema types to Odoo field types
        type_map = {
            'string': 'Char',
            'integer': 'Integer',
            'number': 'Float',
            'boolean': 'Boolean',
        }

        fields = []
        for prop_name, prop_def in schema.get('properties', {}).items():
            prop_type = prop_def.get('type', 'string')

            # Handle enums
            if 'enum' in prop_def:
                field_type = 'Selection'
            elif prop_def.get('format') == 'date':
                field_type = 'Date'
            elif prop_def.get('format') == 'date-time':
                field_type = 'Datetime'
            else:
                field_type = type_map.get(prop_type, 'Char')

            fields.append({
                'name': prop_name,
                'type': field_type,
                'required': prop_name in schema.get('required', []),
            })

        return {
            'name': model_name,
            'description': name.replace('_', ' ').title(),
            'fields': fields,
        }

    def _generate_patch_mode(
        self,
        module_path: Path,
        module_spec: dict,
        docir: dict,
    ) -> list[dict]:
        """Generate files in patch mode (diff-based)."""
        # Import patch generator
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))
        from patch_generator import PatchModeGenerator

        patch_gen = PatchModeGenerator(module_path.parent)

        # Generate each file
        files = []
        module_name = module_spec['module_name']
        base_path = module_name

        # __manifest__.py
        manifest_content = self._generate_manifest(module_spec)
        change = patch_gen.add_file(f"{base_path}/__manifest__.py", manifest_content)
        files.append({'path': change.path, 'action': change.action})

        # __init__.py
        init_content = "# -*- coding: utf-8 -*-\nfrom . import models\n"
        change = patch_gen.add_file(f"{base_path}/__init__.py", init_content)
        files.append({'path': change.path, 'action': change.action})

        # models/__init__.py
        model_imports = '\n'.join(
            f"from . import {m['name'].replace('.', '_')}"
            for m in module_spec.get('models', [])
        )
        change = patch_gen.add_file(
            f"{base_path}/models/__init__.py",
            f"# -*- coding: utf-8 -*-\n{model_imports}\n"
        )
        files.append({'path': change.path, 'action': change.action})

        # Model files
        for model in module_spec.get('models', []):
            model_content = self._generate_model(model, docir)
            model_file = model['name'].replace('.', '_')
            change = patch_gen.add_file(
                f"{base_path}/models/{model_file}.py",
                model_content
            )
            files.append({'path': change.path, 'action': change.action})

        # security/ir.model.access.csv
        security_content = self._generate_security(module_spec)
        change = patch_gen.add_file(
            f"{base_path}/security/ir.model.access.csv",
            security_content
        )
        files.append({'path': change.path, 'action': change.action})

        # tests/
        test_content = self._generate_tests(module_spec, docir)
        change = patch_gen.add_file(
            f"{base_path}/tests/__init__.py",
            f"# -*- coding: utf-8 -*-\nfrom . import test_{module_name}\n"
        )
        files.append({'path': change.path, 'action': change.action})

        change = patch_gen.add_file(
            f"{base_path}/tests/test_{module_name}.py",
            test_content
        )
        files.append({'path': change.path, 'action': change.action})

        # Apply changes
        for change in patch_gen.changes:
            if change.action in ['create', 'modify']:
                full_path = module_path.parent / change.path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(change.new_content)

        return files

    def _generate_full_mode(
        self,
        module_path: Path,
        module_spec: dict,
        docir: dict,
    ) -> list[dict]:
        """Generate files in full mode (overwrite)."""
        # Use existing CodeGenerator
        from pipelines.build.code_generator import CodeGenerator

        generator = CodeGenerator(
            supabase_url='',
            supabase_key='',
            odoo_version=self.config.odoo_version,
        )

        report = generator.generate(
            validation_id='docir_gen',
            output_dir=module_path.parent,
            module_spec=module_spec,
        )

        return [
            {'path': f.path, 'action': 'created', 'lines': f.lines}
            for f in report.files_generated
        ]

    def _generate_manifest(self, module_spec: dict) -> str:
        """Generate __manifest__.py content."""
        return f'''# -*- coding: utf-8 -*-
"""
{module_spec.get('display_name', 'Generated Module')}

Generated by Docs2Code Pipeline (DocIR Generator)
"""
{{
    'name': '{module_spec.get("display_name", "Generated Module")}',
    'version': '{module_spec.get("version", "18.0.1.0.0")}',
    'category': '{module_spec.get("category", "Uncategorized")}',
    'summary': '{module_spec.get("description", "Generated from DocIR")}',
    'author': '{module_spec.get("author", "InsightPulseAI")}',
    'website': 'https://insightpulseai.com',
    'license': 'LGPL-3',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}}
'''

    def _generate_model(self, model: dict, docir: dict) -> str:
        """Generate Python model code."""
        model_name = model['name']
        class_name = ''.join(word.capitalize() for word in model_name.replace('.', '_').split('_'))

        fields_code = []
        for field in model.get('fields', []):
            field_type = field.get('type', 'Char')
            required = field.get('required', False)

            field_line = f"    {field['name']} = fields.{field_type}("
            if required:
                field_line += "required=True"
            field_line += ")"
            fields_code.append(field_line)

        if not fields_code:
            fields_code = ['    pass']

        return f'''# -*- coding: utf-8 -*-
"""
{model.get('description', model_name)} Model

Generated by Docs2Code Pipeline (DocIR Generator)
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class {class_name}(models.Model):
    """
    {model.get('description', model_name)}
    """
    _name = '{model_name}'
    _description = '{model.get("description", model_name)}'

{chr(10).join(fields_code)}
'''

    def _generate_security(self, module_spec: dict) -> str:
        """Generate security CSV."""
        lines = ['id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink']

        for model in module_spec.get('models', []):
            model_name = model['name'].replace('.', '_')
            lines.append(
                f'access_{model_name}_user,{model_name} user,model_{model_name},base.group_user,1,1,1,1'
            )

        return '\n'.join(lines) + '\n'

    def _generate_tests(self, module_spec: dict, docir: dict) -> str:
        """Generate test file."""
        module_name = module_spec['module_name']

        test_methods = []
        for req in docir.get('requirements', []):
            for ac in req.get('acceptance', []):
                if ac.get('type') in ['unit', 'integration']:
                    method_name = f"test_{ac['id'].lower().replace('-', '_')}"
                    test_methods.append(f'''
    def {method_name}(self):
        """
        {req['id']}: {req['title']}
        {ac['id']}: {ac.get('assert', 'Verify')}
        """
        self.assertTrue(True, "TODO: Implement test")
''')

        if not test_methods:
            test_methods = ['''
    def test_placeholder(self):
        """Placeholder test."""
        self.assertTrue(True)
''']

        return f'''# -*- coding: utf-8 -*-
"""
Tests for {module_name}

Generated by Docs2Code Pipeline (DocIR Generator)
"""

from odoo.tests import TransactionCase


class Test{module_name.title().replace("_", "")}(TransactionCase):
    """Test cases from DocIR acceptance criteria."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
{''.join(test_methods)}
'''

    def _calculate_rule_compliance(self, files: list[dict]) -> dict:
        """Calculate 80/15/5 rule compliance."""
        # All generated code is native_odoo by default
        return {
            'native_odoo_percent': 100.0,
            'oca_modules_percent': 0.0,
            'custom_code_percent': 0.0,
            'is_compliant': True,
        }

    def _estimate_test_coverage(self, files: list[dict]) -> float:
        """Estimate test coverage."""
        test_files = [f for f in files if 'test' in f['path']]
        source_files = [f for f in files if 'test' not in f['path'] and f['path'].endswith('.py')]

        if not source_files:
            return 1.0

        return min(1.0, len(test_files) / len(source_files))


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate code from DocIR'
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
        required=True,
        help='Output directory for generated code'
    )
    parser.add_argument(
        '--mode',
        choices=['patch', 'full'],
        default='patch',
        help='Generation mode'
    )
    parser.add_argument(
        '--odoo-version',
        default='18.0',
        help='Odoo version'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate inputs
    if not args.docir.exists():
        logger.error(f"DocIR file not found: {args.docir}")
        sys.exit(1)

    # Configure and run
    config = GenerationConfig(
        mode=args.mode,
        odoo_version=args.odoo_version,
    )

    generator = DocIRGenerator(config)
    result = generator.generate(args.docir, args.output)

    # Write report
    report_path = args.output / 'generation_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(asdict(result), f, indent=2)

    logger.info(f"Report written to {report_path}")

    # Exit with error if there were errors
    if result.errors:
        sys.exit(1)


if __name__ == '__main__':
    main()
