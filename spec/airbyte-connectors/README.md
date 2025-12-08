# Airbyte Connectors - Spec Kit

## Objective
Self-hosted Airbyte instance providing 300+ pre-built connectors for ELT pipelines, landing external data sources into Bronze layer and syncing with Odoo/Supabase ecosystem.

## Status
- **Phase**: Planning
- **Priority**: P1
- **Dependencies**: supabase-core, n8n-automation-hub

## Quick Links
- [Constitution](./constitution.md) - Guiding principles
- [PRD](./prd.md) - Requirements document
- [Plan](./plan.md) - Implementation plan
- [Tasks](./tasks.md) - Task breakdown

## Integration Points

| System | Direction | Purpose |
|--------|-----------|---------|
| Supabase PostgreSQL | Target | Bronze layer destination |
| Odoo CE/OCA 18 | Source | ERP data extraction |
| n8n | Trigger | Sync orchestration |
| External APIs | Source | Third-party data |

## Key Features
- 300+ pre-built connectors
- Incremental sync support
- Schema normalization
- Sync scheduling
- Failure alerting

## Tech Stack
- Airbyte OSS (Docker)
- PostgreSQL (metadata)
- Temporal (orchestration)
- MinIO (state storage)
