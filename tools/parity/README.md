# Parity Checklist Generator

Track feature parity against enterprise reference implementations (SAP AFC, GRC, Signavio).

## Overview

The parity generator produces:

- **PARITY_CHECKLIST.md** - Human-readable checklist with acceptance criteria
- **parity_matrix.csv** - Importable to Google Sheets/Supabase
- **summary.json** - CI/CD integration (score, counts)
- **spec-kit/*.md** - Spec-driven development documents

## Quick Start

```bash
# Install dependencies
pip install pyyaml

# Generate parity report
python paritygen.py parity.yml profiles/ipai_odoo_ce_18.yml

# Output in out/ directory
ls -la out/
```

## CI/CD Gate

Use `--min-score` to fail builds below threshold:

```bash
python paritygen.py parity.yml profiles/ipai_odoo_ce_18.yml --min-score=0.85
```

## Directory Structure

```
tools/parity/
├── parity.yml                    # Master capability catalog
├── profiles/
│   └── ipai_odoo_ce_18.yml       # Implementation profile (status overrides)
├── paritygen.py                  # Generator script
├── out/                          # Generated artifacts
│   ├── PARITY_CHECKLIST.md
│   ├── parity_matrix.csv
│   ├── summary.json
│   └── spec-kit/
│       ├── constitution.md
│       └── tasks.md
└── README.md
```

## Configuration

### parity.yml

Defines capabilities, frameworks, and acceptance criteria:

```yaml
items:
  - id: close.calendar_state_machine
    group: close_orchestration
    name: "Close calendar state machine"
    priority: core
    frameworks: [sap_afc]
    acceptance:
      - "Multi-company fiscal period tracking"
      - "State transitions enforce business rules"
```

### Profile (profiles/*.yml)

Override status per implementation:

```yaml
target:
  name: "IPAI Odoo CE 18"

overrides:
  close.calendar_state_machine:
    status: done
    notes: "Implemented in v1.0"
    evidence:
      - "models/close_calendar.py"
```

## Scoring

| Priority | Weight | Description |
|----------|--------|-------------|
| core | 3 | Must-have for MVP |
| important | 2 | Required for production |
| nice | 1 | Future enhancement |

| Status | Points | Description |
|--------|--------|-------------|
| done | 1.0 | Fully implemented |
| partial | 0.5 | In progress |
| planned | 0.2 | On roadmap |
| no | 0.0 | Not planned |

**Parity Score** = Σ(weight × points) / Σ(weight × 1.0)

## Frameworks Tracked

- **SAP AFC** - Advanced Financial Closing
- **SAP GRC** - Governance, Risk, Compliance
- **SAP Signavio** - Process Intelligence
- **SOX 404** - Sarbanes-Oxley Internal Controls
- **BIR Compliance** - Philippine Bureau of Internal Revenue

## Capability Groups

1. **Close Orchestration** - Workflow, tasks, dependencies
2. **Finance Controls** - GL validation, reconciliation
3. **Evidence & Audit** - Document tracking, snapshots
4. **Intercompany** - IC settlement, netting
5. **Philippine Localization** - BIR forms, tax engine
6. **Separation of Duties** - RBAC, four-eyes, audit trail
7. **Access Governance** - Reviews, emergency access
8. **RAG AI Copilot** - Knowledge base, context chat
9. **Process Intelligence** - Mining, bottleneck detection
10. **Close Cockpit UI** - Dashboard, compliance view

## GitHub Actions Integration

```yaml
# .github/workflows/parity.yml
name: Parity Check

on: [push, pull_request]

jobs:
  parity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install pyyaml
      - run: |
          python tools/parity/paritygen.py \
            tools/parity/parity.yml \
            tools/parity/profiles/ipai_odoo_ce_18.yml \
            --min-score=0.85
      - uses: actions/upload-artifact@v4
        with:
          name: parity-report
          path: tools/parity/out/
```

## Updating Status

1. Edit `profiles/ipai_odoo_ce_18.yml`
2. Add/update override for the capability
3. Run generator to verify
4. Commit changes

```yaml
# Example: Mark capability as done
overrides:
  sod.conflict_matrix:
    status: done
    notes: "Implemented with 12 critical conflict pairs"
    evidence:
      - "models/sod_conflict.py"
      - "data/critical_conflicts.xml"
```

## Related Documents

- [Testing Framework](../../docs/testing/README.md)
- [SoD Recommendation](../../docs/spectra-pf-sod-recommendation.docx)
