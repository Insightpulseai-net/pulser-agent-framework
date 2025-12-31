# Docs2Code Automation Pipeline - Implementation Plan

**Version**: 1.0.0
**Status**: Active
**Last Updated**: 2025-01-01

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DOCS2CODE AUTOMATION PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   LAYER 1: INGESTION                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  DocumentationParser Agent                                          │  │
│   │  ├── SAP S/4HANA AFC Docs    ───┐                                   │  │
│   │  ├── Microsoft Learn Azure   ───┤                                   │  │
│   │  ├── Odoo Core (18.0)        ───┼──→ Supabase pgvector             │  │
│   │  ├── OCA Modules             ───┤    (docs_raw, docs_chunks,       │  │
│   │  ├── BIR Forms (bir.gov.ph)  ───┤     docs_embeddings)             │  │
│   │  └── Databricks Arch         ───┘                                   │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│   LAYER 2: BUILD                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  ComplianceValidator ──→ CodeGenerator ──→ SQLAgent ──→ Validation │  │
│   │                                                                     │  │
│   │  ├── BIR 36 Forms        ├── Odoo 18 CE     ├── Medallion      │  │
│   │  ├── PFRS/IAS            ├── OCA refs       │   Architecture    │  │
│   │  ├── DOLE Labor          ├── FastAPI        ├── RLS Policies    │  │
│   │  └── 2024 Tax Brackets   └── 80/15/5 Rule   └── p99 <2s        │  │
│   │                                                                     │  │
│   │  Quality Gates: Unit ≥90% │ Integration ≥80% │ Security Scan    │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│   LAYER 3: RELEASE                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  DeploymentOrchestrator                                             │  │
│   │  ├── Blue/Green Deploy (DigitalOcean)                               │  │
│   │  ├── Health Checks → Auto-Rollback                                  │  │
│   │  └── Failure → DPO/ORPO Pairs → ipai-agentbench → Agent Hardening  │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Knowledge Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| Primary Database | Supabase (PostgreSQL 16) | Knowledge storage |
| Vector Search | pgvector extension | Semantic embeddings |
| Multi-tenancy | Row-Level Security | Tenant isolation |
| Caching | Redis | Extraction cache |

### Agent Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| Parser | Python (BeautifulSoup, PyMuPDF) | Documentation extraction |
| Compliance | Python (custom validators) | Regulatory checks |
| CodeGen | Python (Jinja2 templates) | Code generation |
| SQL | Python (SQLAlchemy, psycopg2) | Database operations |
| Validation | Python (pytest, coverage) | Test generation |
| Deploy | Python (DigitalOcean SDK) | Deployment orchestration |

### Orchestration Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| Workflow Engine | n8n | Pipeline orchestration |
| Queue | Redis | Job queuing |
| Scheduler | n8n Cron | Scheduled runs |
| Webhooks | n8n HTTP | Event triggers |

### Infrastructure Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| Compute | DigitalOcean App Platform | Production hosting |
| Containers | Docker / Kubernetes | Packaging |
| Observability | Prometheus + Grafana | Monitoring |
| Logging | ELK Stack | Centralized logs |

## Data Models

### Bronze Layer (Raw)

```sql
docs_raw
├── id (BIGSERIAL)
├── source_type (TEXT)  -- 'sap', 'microsoft', 'odoo', 'oca', 'bir', 'databricks'
├── source_url (TEXT)
├── document_title (TEXT)
├── document_content (TEXT)
├── extracted_at (TIMESTAMPTZ)
├── extraction_confidence (DECIMAL)
└── raw_metadata (JSONB)
```

### Silver Layer (Processed)

```sql
docs_chunks
├── id (BIGSERIAL)
├── docs_raw_id (BIGINT FK)
├── chunk_index (INT)
├── chunk_content (TEXT)
├── entity_type (TEXT)  -- 'workflow', 'table', 'rule', 'api_endpoint'
├── entity_name (TEXT)
├── relationships (JSONB)
├── code_patterns (JSONB)
└── regulatory_refs (TEXT[])  -- ['BIR_1700', 'PFRS_16']
```

### Gold Layer (Semantic)

```sql
docs_embeddings
├── id (BIGSERIAL)
├── docs_chunks_id (BIGINT FK)
├── chunk_text (TEXT)
├── embedding (VECTOR(1536))
├── search_keywords (TEXT[])
├── entity_type (TEXT)
└── regulatory_tags (TEXT[])
```

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)

**Objective**: Establish Supabase schema and basic ingestion

Deliverables:
- [ ] Supabase migrations for Bronze/Silver/Gold layers
- [ ] RLS policies for multi-tenant isolation
- [ ] DocumentationParser agent skeleton
- [ ] Basic web scraping for 2 sources (SAP, Odoo)
- [ ] pgvector embedding pipeline

### Phase 2: Full Ingestion (Weeks 3-4)

**Objective**: Complete all 6 documentation sources

Deliverables:
- [ ] Microsoft Learn extractor
- [ ] OCA GitHub extractor
- [ ] BIR PDF+OCR extractor
- [ ] Databricks extractor
- [ ] Citation/lineage tracking
- [ ] n8n workflow for scheduled ingestion

### Phase 3: Compliance & CodeGen (Weeks 5-6)

**Objective**: Build compliance validation and code generation

Deliverables:
- [ ] ComplianceValidator with BIR 36 forms
- [ ] 2024 tax bracket enforcement
- [ ] PFRS/IAS validation rules
- [ ] CodeGenerator with Odoo 18 templates
- [ ] 80/15/5 rule enforcement
- [ ] SQLAgent with medallion migrations

### Phase 4: Quality & Deploy (Weeks 7-8)

**Objective**: Complete quality gates and deployment

Deliverables:
- [ ] ValidationAgent with pytest generation
- [ ] Coverage enforcement (90%/80%)
- [ ] DeploymentOrchestrator blue/green
- [ ] Health check and rollback logic
- [ ] ipai-agentbench DPO integration
- [ ] Production hardening

## Directory Structure

```
pulser-agent-framework/
├── spec/docs2code/
│   ├── constitution.md
│   ├── prd.md
│   ├── plan.md
│   └── tasks.md
├── agents/
│   ├── DocumentationParser.SKILL.md
│   ├── ComplianceValidator.SKILL.md
│   ├── CodeGenerator.SKILL.md
│   ├── SQLAgent.SKILL.md
│   ├── ValidationAgent.SKILL.md
│   └── DeploymentOrchestrator.SKILL.md
├── pipelines/
│   ├── ingest/
│   │   ├── parse.py
│   │   ├── extractors/
│   │   │   ├── sap_extractor.py
│   │   │   ├── microsoft_extractor.py
│   │   │   ├── odoo_extractor.py
│   │   │   ├── oca_extractor.py
│   │   │   ├── bir_extractor.py
│   │   │   └── databricks_extractor.py
│   │   └── supabase_store.py
│   ├── build/
│   │   ├── compliance_validator.py
│   │   ├── code_generator.py
│   │   ├── sql_agent.py
│   │   └── validation_agent.py
│   └── release/
│       ├── deploy_orchestrator.py
│       └── agentbench_hardener.py
├── supabase/
│   └── migrations/
│       ├── 001_docs2code_schema.sql
│       └── 002_compliance_rules.sql
├── n8n/
│   └── workflows/
│       └── docs2code-orchestrator.json
├── scripts/
│   └── docs2code
└── config/
    └── docs2code.yaml
```

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| BIR website structure changes | Medium | High | Version-locked extractors, alerts on failure |
| Compliance rules misinterpretation | Low | Critical | Human review gate, dual-validation |
| Odoo 18 breaking changes | Medium | Medium | Pin version, OCA compatibility layer |
| pgvector embedding drift | Low | Medium | Periodic reindexing, version tracking |
| DigitalOcean outage | Low | High | Multi-region, automated failover |

## Success Criteria

### Phase 1 Complete When:
- Supabase migrations applied
- 2 extractors working (SAP, Odoo)
- pgvector embeddings stored
- Basic semantic search functional

### Phase 2 Complete When:
- All 6 extractors working
- Lineage tracking operational
- n8n scheduled ingestion running
- >95% extraction accuracy

### Phase 3 Complete When:
- Compliance blocks non-compliant code
- CodeGenerator produces valid Odoo modules
- 80/15/5 rule enforced
- SQLAgent migrations work

### Phase 4 Complete When:
- 90%+ unit coverage enforced
- 80%+ integration coverage enforced
- Blue/green deploys working
- Rollback tested
- DPO pairs generating on failures
