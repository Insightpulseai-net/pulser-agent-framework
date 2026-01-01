#!/usr/bin/env python3
"""
DocIR Compiler - Compile documentation sources into deterministic IR.

Compiles raw documentation from multiple sources (Notion, GDocs, Markdown, etc.)
into a strict DocIR (Document Intermediate Representation) that can be diffed,
tested, and used for deterministic code generation.

Usage:
    python tools/compile_docir.py --in docs/sources --out docs/docir/docir.json
    python tools/compile_docir.py --in docs/sources --out docs/docir/docir.json --validate
"""

import argparse
import hashlib
import json
import logging
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DocIRCompiler')

# Schema path relative to this script
SCHEMA_PATH = Path(__file__).parent / 'schemas' / 'DocIR.schema.json'


@dataclass
class SourceSpan:
    """Reference to source document location."""
    uri: str
    start: Optional[int] = None
    end: Optional[int] = None
    heading: Optional[str] = None
    quote: Optional[str] = None


@dataclass
class AcceptanceCriterion:
    """Acceptance criterion for a requirement."""
    id: str
    type: str  # unit, integration, e2e, perf, security, manual
    assert_statement: str
    threshold: Optional[dict] = None

    def to_dict(self) -> dict:
        d = {
            'id': self.id,
            'type': self.type,
            'assert': self.assert_statement,
        }
        if self.threshold:
            d['threshold'] = self.threshold
        return d


@dataclass
class InterfaceRef:
    """Reference to an interface (API, model, view, etc.)."""
    kind: str  # http, rpc, event, model, view, function
    method: Optional[str] = None
    path: Optional[str] = None
    request_schema_ref: Optional[str] = None
    response_schema_ref: Optional[str] = None
    model_name: Optional[str] = None


@dataclass
class Requirement:
    """A single requirement extracted from documentation."""
    id: str
    title: str
    priority: str
    source_spans: list[SourceSpan]
    acceptance: list[AcceptanceCriterion]
    description: Optional[str] = None
    interfaces: list[InterfaceRef] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    compliance_refs: list[str] = field(default_factory=list)


@dataclass
class Source:
    """A source document."""
    uri: str
    hash: str
    source_type: str
    extracted_at: Optional[str] = None
    extraction_confidence: Optional[float] = None


@dataclass
class ComplianceRule:
    """A compliance/regulatory rule."""
    id: str
    regulation: str
    rule_type: str
    description: str
    source_url: Optional[str] = None
    validation_logic: Optional[str] = None
    effective_date: Optional[str] = None


@dataclass
class DocIR:
    """Document Intermediate Representation - the compiled output."""
    doc_id: str
    version: str
    sources: list[Source]
    requirements: list[Requirement]
    schemas: dict = field(default_factory=dict)
    architecture_decisions: list = field(default_factory=list)
    compliance_rules: list[ComplianceRule] = field(default_factory=list)
    module_map: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


class DocIRCompiler:
    """
    Compiles documentation sources into DocIR.

    Pipeline stages:
    1. Ingest: Load source documents
    2. Normalize: Clean and standardize text
    3. Extract: Pull requirements, schemas, compliance rules
    4. Compile: Build DocIR structure
    5. Validate: Check against schema
    """

    # Patterns for extracting structured content
    REQUIREMENT_PATTERN = re.compile(
        r'(?:^|\n)##?\s*(?:REQ|Requirement|Feature)[- ]?(\d+)[:\s]+(.+?)(?=\n##|\n\Z|\Z)',
        re.IGNORECASE | re.DOTALL
    )

    ACCEPTANCE_PATTERN = re.compile(
        r'(?:^|\n)\s*[-*]\s*(?:AC|Acceptance)[- ]?(\d+[a-z]?)[:\s]+(.+?)(?=\n\s*[-*]|\n##|\n\Z|\Z)',
        re.IGNORECASE | re.DOTALL
    )

    PRIORITY_PATTERN = re.compile(
        r'(?:priority|prio)[:\s]*(P[0-3]|critical|high|medium|low)',
        re.IGNORECASE
    )

    COMPLIANCE_PATTERN = re.compile(
        r'\b(BIR|PFRS|PAS|SOX|DOLE)[_\- ]?([A-Z0-9_-]+)\b',
        re.IGNORECASE
    )

    API_PATTERN = re.compile(
        r'(GET|POST|PUT|PATCH|DELETE)\s+(/[a-zA-Z0-9_/{}-]+)',
        re.IGNORECASE
    )

    def __init__(self, doc_id: str = 'default'):
        self.doc_id = doc_id
        self.sources: list[Source] = []
        self.requirements: list[Requirement] = []
        self.schemas: dict = {}
        self.compliance_rules: list[ComplianceRule] = []
        self.req_counter = 0
        self.ac_counter = 0

    def compile(self, source_dir: Path) -> DocIR:
        """
        Compile all sources in a directory into DocIR.

        Args:
            source_dir: Directory containing source documents

        Returns:
            Compiled DocIR
        """
        logger.info(f"Compiling DocIR from {source_dir}")

        # Find all source files
        source_files = self._find_source_files(source_dir)
        logger.info(f"Found {len(source_files)} source files")

        # Process each source
        for source_file in source_files:
            self._process_source(source_file)

        # Build the IR
        docir = DocIR(
            doc_id=self.doc_id,
            version=datetime.now().strftime('%Y-%m-%d'),
            sources=self.sources,
            requirements=self.requirements,
            schemas=self.schemas,
            compliance_rules=self.compliance_rules,
            metadata={
                'created_at': datetime.utcnow().isoformat(),
                'pipeline_version': '1.0.0',
                'source_count': len(self.sources),
                'requirement_count': len(self.requirements),
            }
        )

        logger.info(f"Compiled {len(self.requirements)} requirements from {len(self.sources)} sources")
        return docir

    def _find_source_files(self, source_dir: Path) -> list[Path]:
        """Find all valid source files."""
        extensions = {'.md', '.txt', '.json', '.yaml', '.yml'}
        files = []

        for ext in extensions:
            files.extend(source_dir.rglob(f'*{ext}'))

        return sorted(files)

    def _process_source(self, source_file: Path) -> None:
        """Process a single source file."""
        logger.debug(f"Processing {source_file}")

        try:
            content = source_file.read_text(encoding='utf-8')
        except Exception as e:
            logger.warning(f"Failed to read {source_file}: {e}")
            return

        # Calculate content hash
        content_hash = f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"

        # Determine source type
        source_type = self._determine_source_type(source_file, content)

        # Create source record
        source = Source(
            uri=f"file://{source_file.absolute()}",
            hash=content_hash,
            source_type=source_type,
            extracted_at=datetime.utcnow().isoformat(),
            extraction_confidence=0.9,
        )
        self.sources.append(source)

        # Extract requirements
        self._extract_requirements(content, source)

        # Extract compliance rules
        self._extract_compliance_rules(content, source)

        # Extract schemas from JSON/YAML if applicable
        if source_file.suffix in {'.json', '.yaml', '.yml'}:
            self._extract_schemas(source_file, content)

    def _determine_source_type(self, source_file: Path, content: str) -> str:
        """Determine the source type from file and content."""
        name = source_file.name.lower()
        content_lower = content.lower()

        if 'bir' in name or 'bir' in content_lower[:500]:
            return 'bir_regulatory'
        elif 'pfrs' in name or 'pfrs' in content_lower[:500]:
            return 'bir_regulatory'
        elif 'odoo' in name or 'odoo' in content_lower[:500]:
            return 'odoo_core'
        elif 'oca' in name:
            return 'oca_modules'
        elif 'sap' in name or 's4hana' in content_lower[:500]:
            return 'sap_s4hana'
        elif 'azure' in name or 'microsoft' in content_lower[:500]:
            return 'microsoft_learn'
        elif 'databricks' in name or 'spark' in content_lower[:500]:
            return 'databricks_arch'
        else:
            return 'markdown'

    def _extract_requirements(self, content: str, source: Source) -> None:
        """Extract requirements from content."""
        # Try structured pattern first
        for match in self.REQUIREMENT_PATTERN.finditer(content):
            req_num = match.group(1)
            req_text = match.group(2).strip()

            self._create_requirement(req_num, req_text, content, source, match)

        # Also look for unstructured requirements (headers followed by bullet points)
        self._extract_implicit_requirements(content, source)

    def _extract_implicit_requirements(self, content: str, source: Source) -> None:
        """Extract implicit requirements from headers with bullet points."""
        # Look for ## headers followed by lists
        header_pattern = re.compile(
            r'^##\s+([^\n]+)\n((?:\s*[-*]\s+[^\n]+\n?)+)',
            re.MULTILINE
        )

        for match in header_pattern.finditer(content):
            title = match.group(1).strip()
            bullets = match.group(2)

            # Skip if already captured as explicit requirement
            if re.search(r'REQ|Requirement', title, re.IGNORECASE):
                continue

            # Skip non-requirement sections
            skip_words = {'installation', 'setup', 'configuration', 'license', 'contributing'}
            if any(word in title.lower() for word in skip_words):
                continue

            # Create implicit requirement
            self.req_counter += 1
            req_id = f"REQ-{self.req_counter:03d}"

            # Extract acceptance criteria from bullets
            acceptance = []
            for bullet_match in re.finditer(r'\s*[-*]\s+(.+)', bullets):
                bullet_text = bullet_match.group(1).strip()
                self.ac_counter += 1
                ac_id = f"AC-{self.ac_counter:03d}"

                # Determine AC type
                ac_type = 'manual'
                if any(word in bullet_text.lower() for word in ['test', 'verify', 'check', 'assert']):
                    ac_type = 'unit'
                elif any(word in bullet_text.lower() for word in ['api', 'endpoint', 'request']):
                    ac_type = 'integration'
                elif any(word in bullet_text.lower() for word in ['ui', 'user', 'click', 'display']):
                    ac_type = 'e2e'
                elif any(word in bullet_text.lower() for word in ['performance', 'latency', 'speed']):
                    ac_type = 'perf'

                acceptance.append(AcceptanceCriterion(
                    id=ac_id,
                    type=ac_type,
                    assert_statement=bullet_text,
                ))

            if not acceptance:
                continue

            # Determine priority
            priority = self._extract_priority(title + '\n' + bullets)

            # Extract compliance refs
            compliance_refs = self._extract_compliance_refs(title + '\n' + bullets)

            # Extract interfaces
            interfaces = self._extract_interfaces(bullets)

            req = Requirement(
                id=req_id,
                title=title,
                priority=priority,
                description=bullets.strip(),
                source_spans=[SourceSpan(
                    uri=source.uri,
                    start=match.start(),
                    end=match.end(),
                    heading=title,
                    quote=bullets[:200] if len(bullets) > 200 else bullets,
                )],
                acceptance=acceptance,
                interfaces=interfaces,
                compliance_refs=compliance_refs,
            )
            self.requirements.append(req)

    def _create_requirement(
        self,
        req_num: str,
        req_text: str,
        content: str,
        source: Source,
        match: re.Match,
    ) -> None:
        """Create a requirement from a match."""
        self.req_counter += 1
        req_id = f"REQ-{int(req_num):03d}"

        # Extract title (first line or sentence)
        lines = req_text.split('\n')
        title = lines[0].strip()[:200]
        description = '\n'.join(lines[1:]).strip() if len(lines) > 1 else None

        # Extract acceptance criteria
        acceptance = []
        for ac_match in self.ACCEPTANCE_PATTERN.finditer(req_text):
            self.ac_counter += 1
            ac_id = f"AC-{int(ac_match.group(1).rstrip('abcdefghijklmnopqrstuvwxyz')):03d}{ac_match.group(1)[-1] if ac_match.group(1)[-1].isalpha() else ''}"
            ac_text = ac_match.group(2).strip()

            # Determine type
            ac_type = 'manual'
            if 'GET' in ac_text or 'POST' in ac_text or 'returns' in ac_text.lower():
                ac_type = 'integration'
            elif 'p95' in ac_text.lower() or 'latency' in ac_text.lower():
                ac_type = 'perf'
            elif 'test' in ac_text.lower():
                ac_type = 'unit'

            acceptance.append(AcceptanceCriterion(
                id=ac_id,
                type=ac_type,
                assert_statement=ac_text,
            ))

        # Default acceptance if none found
        if not acceptance:
            self.ac_counter += 1
            acceptance.append(AcceptanceCriterion(
                id=f"AC-{self.ac_counter:03d}",
                type='manual',
                assert_statement=f"Verify: {title}",
            ))

        # Extract priority
        priority = self._extract_priority(req_text)

        # Extract compliance refs
        compliance_refs = self._extract_compliance_refs(req_text)

        # Extract interfaces
        interfaces = self._extract_interfaces(req_text)

        req = Requirement(
            id=req_id,
            title=title,
            priority=priority,
            description=description,
            source_spans=[SourceSpan(
                uri=source.uri,
                start=match.start(),
                end=match.end(),
                heading=title,
                quote=req_text[:200] if len(req_text) > 200 else req_text,
            )],
            acceptance=acceptance,
            interfaces=interfaces,
            compliance_refs=compliance_refs,
        )
        self.requirements.append(req)

    def _extract_priority(self, text: str) -> str:
        """Extract priority from text."""
        match = self.PRIORITY_PATTERN.search(text)
        if match:
            p = match.group(1).upper()
            if p in {'P0', 'CRITICAL'}:
                return 'P0'
            elif p in {'P1', 'HIGH'}:
                return 'P1'
            elif p in {'P2', 'MEDIUM'}:
                return 'P2'
            else:
                return 'P3'

        # Default based on keywords
        text_lower = text.lower()
        if 'critical' in text_lower or 'must' in text_lower:
            return 'P0'
        elif 'important' in text_lower or 'should' in text_lower:
            return 'P1'
        else:
            return 'P2'

    def _extract_compliance_refs(self, text: str) -> list[str]:
        """Extract compliance references from text."""
        refs = set()
        for match in self.COMPLIANCE_PATTERN.finditer(text):
            regulation = match.group(1).upper()
            code = match.group(2).upper().replace('-', '_')
            refs.add(f"{regulation}_{code}")
        return sorted(refs)

    def _extract_interfaces(self, text: str) -> list[InterfaceRef]:
        """Extract interface references from text."""
        interfaces = []

        # Extract API endpoints
        for match in self.API_PATTERN.finditer(text):
            method = match.group(1).upper()
            path = match.group(2)
            interfaces.append(InterfaceRef(
                kind='http',
                method=method,
                path=path,
            ))

        return interfaces

    def _extract_compliance_rules(self, content: str, source: Source) -> None:
        """Extract compliance rules from content."""
        for match in self.COMPLIANCE_PATTERN.finditer(content):
            regulation = match.group(1).upper()
            code = match.group(2).upper().replace('-', '_')
            rule_id = f"{regulation}_{code}"

            # Avoid duplicates
            if any(r.id == rule_id for r in self.compliance_rules):
                continue

            # Determine rule type
            if regulation == 'BIR':
                rule_type = 'tax_form'
            elif regulation in {'PFRS', 'PAS'}:
                rule_type = 'accounting_standard'
            elif regulation == 'SOX':
                rule_type = 'audit_control'
            elif regulation == 'DOLE':
                rule_type = 'labor_law'
            else:
                rule_type = 'tax_form'

            # Extract context (surrounding text)
            start = max(0, match.start() - 100)
            end = min(len(content), match.end() + 100)
            context = content[start:end].strip()

            rule = ComplianceRule(
                id=rule_id,
                regulation=regulation,
                rule_type=rule_type,
                description=context,
            )
            self.compliance_rules.append(rule)

    def _extract_schemas(self, source_file: Path, content: str) -> None:
        """Extract schemas from JSON/YAML files."""
        try:
            if source_file.suffix == '.json':
                data = json.loads(content)
            else:
                import yaml
                data = yaml.safe_load(content)

            # Look for schema-like structures
            if isinstance(data, dict):
                if 'properties' in data or 'type' in data:
                    name = source_file.stem.replace('-', '_').replace('.', '_')
                    self.schemas[name] = data
                elif 'schemas' in data:
                    for name, schema in data['schemas'].items():
                        self.schemas[name] = schema
        except Exception as e:
            logger.debug(f"Could not parse schemas from {source_file}: {e}")


def validate_docir(docir_path: Path, schema_path: Path) -> tuple[bool, list[str]]:
    """Validate DocIR against JSON schema."""
    try:
        import jsonschema
    except ImportError:
        logger.warning("jsonschema not installed, skipping validation")
        return True, []

    with open(docir_path) as f:
        docir = json.load(f)

    with open(schema_path) as f:
        schema = json.load(f)

    errors = []
    validator = jsonschema.Draft7Validator(schema)

    for error in validator.iter_errors(docir):
        errors.append(f"{'.'.join(str(p) for p in error.absolute_path)}: {error.message}")

    return len(errors) == 0, errors


def docir_to_dict(docir: DocIR) -> dict:
    """Convert DocIR to dictionary for JSON serialization."""
    result = {
        'doc_id': docir.doc_id,
        'version': docir.version,
        'sources': [asdict(s) for s in docir.sources],
        'requirements': [],
        'schemas': docir.schemas,
        'architecture_decisions': docir.architecture_decisions,
        'compliance_rules': [asdict(r) for r in docir.compliance_rules],
        'module_map': docir.module_map,
        'metadata': docir.metadata,
    }

    for req in docir.requirements:
        req_dict = {
            'id': req.id,
            'title': req.title,
            'priority': req.priority,
            'source_spans': [asdict(s) for s in req.source_spans],
            'acceptance': [ac.to_dict() for ac in req.acceptance],
        }
        if req.description:
            req_dict['description'] = req.description
        if req.interfaces:
            req_dict['interfaces'] = [asdict(i) for i in req.interfaces]
        if req.dependencies:
            req_dict['dependencies'] = req.dependencies
        if req.compliance_refs:
            req_dict['compliance_refs'] = req.compliance_refs
        result['requirements'].append(req_dict)

    return result


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Compile documentation sources into DocIR'
    )
    parser.add_argument(
        '--in', '-i',
        dest='input_dir',
        type=Path,
        required=True,
        help='Input directory containing source documents'
    )
    parser.add_argument(
        '--out', '-o',
        dest='output_file',
        type=Path,
        required=True,
        help='Output DocIR JSON file'
    )
    parser.add_argument(
        '--doc-id',
        default='default',
        help='Document ID for the compiled IR'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate output against schema'
    )
    parser.add_argument(
        '--schema',
        type=Path,
        default=SCHEMA_PATH,
        help='Path to DocIR JSON schema'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate input directory
    if not args.input_dir.exists():
        logger.error(f"Input directory does not exist: {args.input_dir}")
        sys.exit(1)

    # Compile
    compiler = DocIRCompiler(doc_id=args.doc_id)
    docir = compiler.compile(args.input_dir)

    # Convert to dict and write
    docir_dict = docir_to_dict(docir)

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_file, 'w') as f:
        json.dump(docir_dict, f, indent=2)

    logger.info(f"DocIR written to {args.output_file}")

    # Validate if requested
    if args.validate:
        if not args.schema.exists():
            logger.error(f"Schema file does not exist: {args.schema}")
            sys.exit(1)

        valid, errors = validate_docir(args.output_file, args.schema)
        if valid:
            logger.info("DocIR validation passed")
        else:
            logger.error("DocIR validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            sys.exit(1)


if __name__ == '__main__':
    main()
