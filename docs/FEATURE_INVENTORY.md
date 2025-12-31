# Feature Inventory v2.0.0
## Docs2Code Enterprise Platform + Odoo 18/OCA + Supabase + n8n + Bounded Agents

**Last Updated:** 2025-12-31
**Version:** 2.0.0
**Status:** Production-Ready Specification
**Architecture:** Docs→Spec→Build→Deploy pipeline aligned with GitHub Spec-Kit + deterministic QA

---

## Table of Contents

- [A) Platform Foundation](#a-platform-foundation)
- [B) Docs → Spec (Ingestion + Parsing)](#b-docs--spec-ingestion--parsing)
- [C) Spec → Build (CodeGen)](#c-spec--build-codegen)
- [D) Compliance & Controls](#d-compliance--controls)
- [E) Automation Layer](#e-automation-layer)
- [F) Intelligence Layer](#f-intelligence-layer)
- [G) Quality Gates](#g-quality-gates)
- [H) Production Operations](#h-production-operations)
- [Implementation Priority](#implementation-priority)

---

## A) Platform Foundation

### A1. Monorepo Structure

**Purpose:** Canonical single source of truth for all platform artifacts.

```
pulser-agent-framework/
├── apps/                      # DigitalOcean App specs + Odoo modules
│   └── odoo-saas-platform/
├── services/                  # Deployable microservices
│   ├── ocr-service/
│   └── mcp-coordinator/
├── infra/                     # Infrastructure-as-Code
│   ├── do/                    # DigitalOcean configs
│   └── nginx/
├── docs/
│   ├── ops/conversations/     # Day-0 ops threads (indexed)
│   └── feature-inventory/
├── scripts/
│   └── prove_docs2code.sh     # E2E proof harness
├── tools/
│   └── knowledge/             # RAG + ingestion pipeline
├── .github/workflows/
└── stack.yaml                 # Technology stack manifest
```

### A2. DigitalOcean State Inventory

**Purpose:** Machine-readable catalog of all DO resources.

- Export snapshots: apps, droplets, domains, DNS records, firewalls
- Format: `inventory/runs/<timestamp>/` with symlink to `latest`
- Drift detection: CI job compares current vs. Git specs

### A3. Naming Conventions

| Type | Format | Example |
|------|--------|---------|
| DO App | `{slug}-{env}` | `odoo-prod` |
| Odoo Module | `{vendor}_{feature}` | `ipai_birkx_filing` |
| Supabase Table | `{layer}_{entity}` | `silver_customer` |
| Agent Skill | `{domain}_{action}` | `tax_compute` |
| n8n Workflow | `{domain}-{trigger}-{action}` | `invoice-webhook-email` |

---

## B) Docs → Spec (Ingestion + Parsing)

### B1. Recursive Document Ingestion

**Input Types:**
- Pasted text, Markdown, PDFs
- Web captures (SAP Help, Microsoft Learn, etc.)

**Output:** Structured Spec Objects (YAML/JSON)

```yaml
spec:
  title: "BIR Form 1700"
  source: "https://www.bir.gov.ph/ebirforms"
  entities:
    - name: "taxable_income"
      type: "decimal"
      validations: ["required", "positive"]
  workflows:
    - name: "file_form_1700"
      steps: [validate_data, compute_tax, generate_xml, submit_to_bir]
```

### B2. DocumentationParser Agent

**Skill:** Extract structured information from unstructured documents

**Bounded Outputs:**
- `spec/catalog.yaml`: Entity definitions
- `spec/schema.yaml`: Data types + constraints
- `spec/workflows.yaml`: Process definitions
- `spec/forms.yaml`: UI forms + field mappings

### B3. Conversation-to-Artifact Indexing

**Purpose:** Convert operational conversations into indexed artifacts for RAG.

```yaml
conversation:
  id: "conv_2025-12-28_001"
  title: "BIR Form 1700 Compliance"
  decisions:
    - decision: "Use Form 1700 for individual annual filing"
      authority: "BIR requirement"
  outputs:
    - spec/birkx_form_1700.yaml
  tags: ["compliance", "birkx", "critical_path"]
```

---

## C) Spec → Build (CodeGen)

### C1. Odoo Module Generation (80/15/5 Rule)

**Core Principle:**
- **80%** Odoo 18 CE native modules
- **15%** OCA (Odoo Community Association) modules
- **5%** Custom modules only for genuine gaps

**Generated Artifact:**
```
addons/ipai_birkx_filing/
├── __manifest__.py
├── models/
│   └── bir_form.py
├── views/
│   └── bir_form_views.xml
├── data/
│   └── bir_tax_rates_2024.xml
└── tests/
    └── test_bir_computation.py
```

### C2. Supabase Backend Build

**Stack:**
- PostgreSQL 16 + pgvector
- Row-Level Security (RLS) first
- Medallion pattern (Bronze/Silver/Gold)

**Generated Schema:**
```sql
-- Bronze layer (raw imports)
CREATE TABLE bronze_invoices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  payload JSONB NOT NULL,
  tenant_id UUID NOT NULL
);

-- Silver layer (cleaned, typed)
CREATE TABLE silver_invoices (
  id UUID PRIMARY KEY,
  invoice_number TEXT NOT NULL,
  amount_total DECIMAL(18,2) NOT NULL,
  tenant_id UUID NOT NULL
);
ALTER TABLE silver_invoices ENABLE ROW LEVEL SECURITY;

-- Gold layer (metrics)
CREATE TABLE gold_invoice_metrics (
  period_month DATE NOT NULL,
  total_invoiced DECIMAL(18,2) NOT NULL,
  tenant_id UUID NOT NULL
);
```

### C3. UI Build Hooks (Optional)

**Triggered by:** PR to `apps/*/spec.yaml`

**Output:** React/Tailwind components with RLS-aware guards

---

## D) Compliance & Controls

### D1. Separation of Duties (SoD / Four-Eyes)

**Policy Definition:**
```yaml
sod_policies:
  - workflow: "invoice_approval"
    steps:
      - step: "create"
        role: "preparer"
      - step: "review"
        role: "reviewer"
        constraint: "user_id ≠ preparer_user_id"
      - step: "approve"
        role: "approver"
        constraint: "user_id ≠ preparer AND ≠ reviewer"
```

**Enforcement:** Database triggers + Odoo workflow constraints

### D2. Immutable Audit Trails (SOX-Style)

```sql
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  table_name TEXT NOT NULL,
  operation VARCHAR(10) NOT NULL,
  old_values JSONB,
  new_values JSONB,
  actor_id UUID NOT NULL,
  changed_at TIMESTAMPTZ DEFAULT NOW()
);

-- IMMUTABLE: no UPDATE/DELETE allowed
CREATE TRIGGER audit_lock
BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW EXECUTE FUNCTION fail('Audit logs are immutable');
```

### D3. Regulatory Packs (Philippines - BIR/DOLE)

**BIR Forms Coverage:**
- Form 1700: Individual Annual Income Tax
- Form 1601-C: Monthly Withholding Tax
- Form 2550-Q: Quarterly VAT
- All 36 official eBIRForms

**Validator Agent:** Checks spec + code against BIR rules

---

## E) Automation Layer

### E1. Docs → GitHub Sync

**Pipeline:**
1. Capture doc/text
2. Parse to YAML spec
3. Create Git commit
4. Open PR with spec changes
5. Run CI checks
6. Auto-merge if passing

### E2. Event-Driven Automation

**Common Workflows:**
- PR Merge → Deploy
- Month-End Close → Tax Filing
- E-Filing → BIR Submission

### E3. Rollback + Drift Detection

**Hourly Job:**
```bash
./scripts/detect-drift.sh
# Compares DO state vs. Git specs
# Alerts on divergence
```

---

## F) Intelligence Layer

### F1. 3-Stage Bounded Pipeline

**Hard separation:**
1. **Planning:** Decompose spec → atomic steps
2. **Analysis:** Dependencies, risks, resources
3. **CodeGen:** Generate validated code

**Guardrails:**
- Only cite indexed specs
- Reject missing context
- Code must pass CI

### F2. Memory + Retrieval

**Long-Term Memory:**
- Indexed conversations
- Decision logs
- Specs + ADRs

**Constraints:**
- Only approved sources
- Confidence threshold ≥ 0.7

### F3. Tool Execution Surface

**Odoo Tools:**
- `upgrade_odoo_module(module_name)`
- `run_odoo_tests(module_name)`

**Supabase Tools:**
- `execute_supabase_rpc(function_name, params)` — read-only
- `query_supabase(sql)` — SELECT only

**GitHub Tools:**
- `create_github_issue(title, body, labels)`
- `trigger_github_workflow(workflow, inputs)`

---

## G) Quality Gates

### G1. Test Discipline

**Targets:**
- Unit test coverage: ≥ 90%
- Integration coverage: ≥ 80%
- SQL lint: 100% pass
- Code style: 100% pass

### G2. Deterministic Scorers

```python
def score_compliance(spec: SpecObject) -> bool:
    """Pass/Fail only. No subjective judgment."""
    return all([
        has_all_bir_forms(spec),
        all_validations_defined(spec),
        penalties_computable(spec),
    ])

def score_sql_safety(sql: str) -> bool:
    """No DROP/DELETE/TRUNCATE. RLS required."""
    return all([
        not has_destructive_ops(sql),
        rls_enabled_on_all_tables(sql),
        audit_triggers_present(sql),
    ])
```

### G3. AgentBench Loop

**Workflow:**
1. Agent generates code
2. Code fails compliance check
3. Collect failure as training data
4. Build chosen/rejected pairs
5. DPO optimization
6. Regression tests block merges if >5% regression

---

## H) Production Operations

### H1. Odoo Production Hardening

**Asset Cache Repair:**
```bash
#!/bin/bash
# scripts/repair-odoo-assets.sh
systemctl stop odoo
psql -U odoo -d odoo_prod -c "DELETE FROM ir_attachment WHERE url LIKE '/web/content/%'"
rm -rf /var/lib/odoo/.cache/*
systemctl start odoo
```

**Dependency Determinism:**
- Manifest `depends` fully specified
- Pinned pip versions

### H2. Observability

**Alerts on:**
- Asset build errors
- Repeated auth failures
- Module install/uninstall
- Cron failures
- 5xx spikes

### H3. Backups + Restore Drills

- DB + filestore snapshots (daily)
- Automated restore test job (weekly)
- Point-in-time recovery (30 days)

---

## Implementation Priority

### NOW (Must-Have)

| Feature | Section | Status |
|---------|---------|--------|
| Monorepo structure | A1 | ✅ Done |
| Conversation indexing | B3 | ✅ Done |
| Odoo module generation | C1 | 🔄 In Progress |
| Docs→GitHub sync | E1 | ✅ Done |
| Test discipline | G1 | ✅ Done |
| Asset stabilization | H1 | 🔄 In Progress |

### NEXT

| Feature | Section | Priority |
|---------|---------|----------|
| Full ingestion pipeline | B1/B2 | High |
| Supabase medallion + RLS | C2 | High |
| SoD enforcement | D1/D2 | High |
| Deterministic scorers | G2 | High |

### LATER

| Feature | Section | Priority |
|---------|---------|----------|
| Full tool surface | F3 | Medium |
| AgentBench/DPO loop | G3 | Medium |
| Complete PH regulatory pack | D3 | Medium |
| Full ops automation | H2/H3 | Low |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2025-12-31 | Complete restructure aligned with Spec-Kit + bounded agents |
| 1.0.0 | 2025-12-28 | Initial feature inventory |

---

*This document lives at: `docs/FEATURE_INVENTORY.md`*
*Versioned copies at: `docs/feature-inventory/v2.0.0.md`*
