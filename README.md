# Pulser Agent Framework

A comprehensive platform for specification-driven code generation, ML model training, and data engineering workbench operations.

## What's in This Repo

```
pulser-agent-framework/
├── .github/workflows/        # CI/CD pipelines
├── agents/                   # Agent skill definitions
├── apps/workbench-api/       # FastAPI backend for workbench
├── config/                   # Generator configurations (OpenAPI, Buf)
├── db/migrations/            # SQL migrations for workbench schema
├── docs/                     # Documentation and checklists
├── generated/                # Auto-generated SDK clients (gitignored)
├── infra/                    # Docker Compose, nginx, runners
├── migrations/               # Alembic migrations
├── ml/                       # Model Factory (train, eval, serve)
├── n8n/workflows/            # n8n automation templates
├── notebooks/                # Jupyter notebooks
├── odoo/addons/              # ipai_* Odoo modules
├── ops/                      # Operations runbooks
├── packages/agent-framework/ # Python agent framework package
├── pipelines/                # Data and model pipelines
├── prompts/                  # AI system prompts
├── scripts/                  # Utility scripts
├── skills/                   # Agent skill configs (YAML)
├── spec/                     # Spec Kit (PRDs, plans, tasks)
├── specs/                    # API specifications (OpenAPI, Protobuf, AsyncAPI)
├── supabase/migrations/      # Supabase migrations
├── templates/                # Custom generator templates
├── tests/                    # Test suites (unit, integration, API, performance)
├── tools/                    # CLI tools (knowledge, parity)
├── uat/                      # User acceptance tests
└── workflows/                # n8n workflow exports
```

## Quickstart

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 20+ (for code generation)
- Make

### Local Development

```bash
# Clone and setup
git clone https://github.com/Insightpulseai-net/pulser-agent-framework.git
cd pulser-agent-framework

# Initialize Python environment
make init

# Start workbench services
make stack-up

# Validate specifications
make spec-validate

# Generate SDK clients
make generate-all
```

### Environment Configuration

```bash
cp .env.template .env
cp infra/.env.workbench.example infra/.env.workbench
# Edit files with your values
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT PIPELINE                         │
│                                                                 │
│   Specs           Workbench         Pipelines       Deploy      │
│   ─────           ─────────         ─────────       ──────      │
│                                                                 │
│   OpenAPI    →    Notebooks    →    Build/Test  →  Production   │
│   AsyncAPI        API/Frontend      ML Training     Odoo        │
│   Protobuf        Data Catalog      Codegen         Superset    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Storage Layer

| Component | Purpose |
|-----------|---------|
| PostgreSQL | Medallion architecture (bronze.*, silver.*, gold.*, workbench.*) |
| MinIO | Object storage (documents, uploads, exports) |
| Supabase | Knowledge base and vector storage |

## Pipelines & Workflows

### Data Pipelines (`pipelines/`)

| Pipeline | Description |
|----------|-------------|
| `ingest/parse.py` | Document ingestion and parsing |
| `build/code_generator.py` | Spec-to-code generation |
| `build/compliance_validator.py` | Compliance checks |
| `model/10_make_sft_jsonl.py` | Build SFT training datasets |
| `model/30_eval.py` | Model evaluation harness |

### GitHub Actions (`.github/workflows/`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `validate-specs.yml` | PR to specs/ | Lint OpenAPI, AsyncAPI, Protobuf |
| `detect-breaking-changes.yml` | PR to specs/ | Block breaking API changes |
| `generate-clients.yml` | Push to main (specs/) | Generate Python/TS/Go SDKs |
| `release-sdks.yml` | Release published | Publish to PyPI/NPM |
| `model-train.yml` | Manual dispatch | Train models (GPU runner) |
| `model-release.yml` | Manual dispatch | Export and release models |
| `comprehensive-tests.yml` | PR | Full test suite |

## Database & Migrations

### Apply Migrations

```bash
# Workbench schema (PostgreSQL)
make db-migrate

# Supabase migrations
cd supabase && supabase db push
```

### Key Tables

- `workbench.artifacts` - Artifact registry with envelope metadata
- `workbench.runs` - Pipeline execution tracking
- `workbench.artifact_run_links` - Artifact-to-run relationships
- `workbench.events` - Audit log

## Code Generation

### Generate SDK Clients

```bash
# All clients
make generate-all

# Individual languages
make generate-python
make generate-typescript
make generate-go
make generate-proto
```

### Development Services

```bash
# Start Swagger UI + ReDoc
make docs2code-up

# Start mock server
make mock-server

# Stop services
make docs2code-down
```

## ML Model Factory

### Training Pipeline

```bash
# Install ML dependencies
make ml-deps

# Build dataset
make ml-dataset VERSION=v1

# Train model (requires GPU)
make ml-train RUN_ID=run_001 CONFIG=sft_lora_1b.yaml

# Evaluate
make ml-eval RUN_ID=run_001

# Export for release
make ml-export RUN_ID=run_001 TAG=v0.1.0
```

### GPU Runner Setup

See `infra/runners/gpu-runner.md` for self-hosted GPU runner configuration.

## Conventions

### Artifact Envelope (Required for Ingestion)

All artifacts must include an envelope with:
- `artifact_id` (UUID)
- `artifact_type` (doc, pdf, csv, sql, openapi, code, dataset, etc.)
- `content_sha256` (idempotency key)
- `intent` (train, eval, etl, docs2code, debug, release)
- `target` (ml, odoo, superset, workbench)

See `specs/artifacts/artifact_envelope.schema.json` for full schema.

### Odoo Modules

All custom modules use prefix `ipai_*` and follow Smart Delta patterns:
- `ipai_expense_core` - Expense management
- `ipai_cash_advance` - Cash advance tracking
- `ipai_card_reconciliation` - Card statement reconciliation

### Generated Code

All generated files include header:
```python
# GENERATED FILE - DO NOT EDIT MANUALLY
# Source: {specification_path}
# Generated: {timestamp}
# Regenerate: {command}
```

## How to Add New Components

### New API Endpoint

1. Add to `specs/openapi/openapi.yaml`
2. Run `make spec-validate`
3. Run `make generate-all`
4. Implement in `apps/workbench-api/`

### New Agent Skill

1. Create `agents/YourAgent.SKILL.md`
2. Add config to `skills/your_agent.yaml`
3. Register in agent framework

### New Odoo Module

1. Create `odoo/addons/ipai_<name>/`
2. Include `__manifest__.py`, `models/`, `views/`, `security/`
3. Follow AGPL-3 license

### New ML Training Config

1. Add config to `ml/train/configs/`
2. Run via `make ml-train CONFIG=your_config.yaml`

## Troubleshooting

### Spec Validation Fails

```bash
# Check OpenAPI syntax
npx @redocly/cli lint specs/openapi/openapi.yaml

# Check Protobuf
buf lint specs/protobuf
```

### Code Generation Fails

```bash
# Install generator
npm install -g @openapitools/openapi-generator-cli

# Validate spec first
swagger-cli validate specs/openapi/openapi.yaml
```

### Docker Services Won't Start

```bash
# Check logs
make stack-logs

# Reset containers
make clean-all
make stack-up
```

## License

AGPL-3.0 - See LICENSE file

## Support

- **Issues**: [GitHub Issues](https://github.com/Insightpulseai-net/pulser-agent-framework/issues)
- **Slack**: #platform-engineering
