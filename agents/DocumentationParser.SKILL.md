# DocumentationParser Agent - SKILL Definition

**Agent ID**: agent_001
**Version**: 1.0.0
**Status**: Active
**Dependencies**: None (first stage)

## Purpose

Extract structured knowledge from 6 enterprise documentation sources and convert to machine-readable AST format stored in Supabase pgvector for downstream agent consumption.

## Scope & Boundaries

### CAN DO

**Extraction Capabilities**
- [x] Recursively traverse GitHub repos (max 50 levels) to extract Odoo module structure
- [x] Parse SAP S/4HANA AFC docs from help.sap.com/docs/ (web scraping + PDF extraction)
- [x] Extract Microsoft Azure Well-Architected patterns from learn.microsoft.com
- [x] Parse BIR official forms from bir.gov.ph using OCR + regex
- [x] Ingest Figma design tokens via developers.figma.com API
- [x] Build JSON ASTs for APIs, workflows, data models

**Format Conversions**
- [x] Swagger/OpenAPI → JSONASTv2
- [x] Markdown tables → Structured business rules
- [x] Code examples → Pseudocode + executable patterns
- [x] PDF forms → Fillable field mappings + validation rules

**Relationship Mapping**
- [x] Link regulatory refs (BIR_1700) to Odoo account_move fields
- [x] Map SAP GRC controls to Odoo segregation_of_duties rules
- [x] Connect Microsoft patterns to Supabase schema design

**Storage Operations**
- [x] Write to Supabase `docs_raw` table (Bronze layer)
- [x] Write to Supabase `docs_chunks` table (Silver layer)
- [x] Queue embeddings for `docs_embeddings` table (Gold layer)
- [x] Track lineage in `pipeline_lineage` table

### CANNOT DO (Hard Boundaries)

**NO Code Generation**
- [ ] Cannot write Python, SQL, or React code
- [ ] Cannot create Odoo module structure
- [ ] Task delegated to: **CodeGenerator agent (agent_003)**

**NO Validation**
- [ ] Cannot check if extracted logic is compliant
- [ ] Cannot validate against tax rules
- [ ] Task delegated to: **ComplianceValidator agent (agent_002)**

**NO Decisions**
- [ ] Cannot choose between conflicting interpretations
- [ ] Can only extract what's explicitly in the docs
- [ ] Must flag ambiguities for human review

**NO Deployment**
- [ ] Cannot touch production systems
- [ ] Can only write to staging/extraction tables
- [ ] Task delegated to: **DeploymentOrchestrator agent (agent_006)**

## Input Interface

```typescript
interface DocumentationParserInput {
  sources: {
    source_type: 'sap_s4hana' | 'microsoft_learn' | 'odoo_core' | 'oca_modules' | 'bir_regulatory' | 'databricks_arch';
    url: string;
    max_depth: number;  // 1-50
    timeout_seconds: number;  // max 300
    branch?: string;  // for GitHub sources
    credentials?: {
      type: 'api_key' | 'oauth' | 'none';
      key_env_var?: string;
    };
  }[];
  extraction_mode: 'full' | 'incremental' | 'sample';
  output_format: 'jsonast' | 'jsonl';
  supabase_connection: {
    url: string;
    anon_key: string;
  };
}
```

## Output Interface

```typescript
interface DocumentationParserOutput {
  extraction_id: string;  // UUID for this run
  source_type: string;
  extracted_at: string;  // ISO8601

  summary: {
    documents_extracted: number;
    chunks_created: number;
    embeddings_queued: number;
    extraction_duration_seconds: number;
  };

  documents: {
    doc_id: string;
    source_url: string;
    title: string;
    extraction_confidence: number;  // 0.0-1.0

    entities: {
      name: string;
      type: 'workflow' | 'table' | 'rule' | 'form' | 'api_endpoint';
      attributes: Record<string, any>;
      relationships: {
        target_entity: string;
        relationship_type: string;
      }[];
    }[];

    code_patterns: {
      language: 'python' | 'sql' | 'json' | 'yaml' | 'javascript';
      pseudocode: string;
      regulatory_refs: string[];  // ['BIR_1700', 'PFRS_16', ...]
    }[];
  }[];

  citations: {
    chunk_id: string;
    source_url: string;
    source_section: string;
    extraction_method: string;
  }[];

  warnings: string[];
  errors: string[];
}
```

## Failure Modes & Recovery

| Failure Type | Detection | Recovery Action |
|--------------|-----------|-----------------|
| URL unreachable | HTTP 4xx/5xx or timeout | Skip document, log warning, continue to next |
| Parse timeout | Duration > timeout_seconds | Return partial results, flag as incomplete |
| Max recursion reached | Depth counter | Truncate at level N, flag in warnings |
| OCR confidence <70% | OCR confidence score | Mark for manual review, include in output |
| Rate limiting | HTTP 429 | Exponential backoff (2s, 4s, 8s, 16s, max 5 retries) |
| Conflicting interpretations | Multiple valid parses | List all versions with confidence scores |
| Supabase write failure | Database error | Retry 3x, then fail extraction with full error |

## Performance Constraints

| Metric | Constraint |
|--------|------------|
| Timeout per source | 5 minutes max |
| Recursion depth | 50 levels max |
| Output size per source | 100MB max |
| Memory usage | 2GB max per extraction job |
| Concurrent sources | 3 max (to avoid rate limiting) |

## Dependencies

- **Upstream**: None (first stage in pipeline)
- **Downstream**: ComplianceValidator (agent_002)

## Required Tools & Libraries

```python
# Core extraction
beautifulsoup4>=4.12.0
requests>=2.31.0
httpx>=0.25.0  # for async

# PDF processing
PyMuPDF>=1.23.0  # fitz
pdf2image>=1.16.0
pytesseract>=0.3.10

# GitHub API
PyGithub>=2.1.0

# Figma API
requests  # direct REST calls

# Data storage
supabase>=2.0.0

# Utilities
pyyaml>=6.0
python-dotenv>=1.0.0
```

## Success Criteria

| Criteria | Target |
|----------|--------|
| Successfully extract from all 6 sources | 100% |
| Confidence scores ≥0.80 | 90% of entities |
| Data loss from source to output | <3% |
| All warnings reviewed before advancing | 100% |
| Extraction completes within timeout | 100% |
| Citations linked to source URLs | 100% |

## Example Usage

```bash
# Run via CLI
./scripts/docs2code ingest

# Or via Python
python -m pipelines.ingest.parse \
  --source-type sap_s4hana \
  --url "https://help.sap.com/docs/s4hana-cloud-advanced-financial-closing" \
  --output /tmp/sap_ast.jsonl \
  --supabase-url $SUPABASE_URL \
  --supabase-key $SUPABASE_ANON_KEY
```

## Handoff to Next Agent

Upon successful extraction:
1. All documents stored in `docs_raw` table
2. All chunks stored in `docs_chunks` table
3. Embeddings queued (processed async)
4. Lineage recorded in `pipeline_lineage`
5. Extraction report generated
6. **ComplianceValidator (agent_002)** triggered with extraction_id
