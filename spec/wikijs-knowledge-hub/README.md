# Wiki.js Knowledge Hub - Spec Kit

## Objective
Self-hosted Wiki.js instance serving as the central knowledge management system for InsightPulseAI, with Git-backed content, full-text search, and integration with AI agents for knowledge retrieval.

## Status
- **Phase**: Planning
- **Priority**: P1
- **Dependencies**: supabase-core (auth)

## Quick Links
- [Constitution](./constitution.md) - Guiding principles
- [PRD](./prd.md) - Requirements document
- [Plan](./plan.md) - Implementation plan
- [Tasks](./tasks.md) - Task breakdown

## Integration Points

| System | Direction | Purpose |
|--------|-----------|---------|
| Supabase Auth | SSO | User authentication |
| GitHub | Sync | Content version control |
| OpenSearch | Index | Full-text search |
| MCP Agents | Consumer | Knowledge retrieval |
| Odoo | Embed | Documentation links |

## Key Features
- Markdown + WYSIWYG editing
- Git repository sync
- Full-text search
- Access control (spaces)
- Page history and versioning
- Diagram support (Mermaid, Draw.io)
- API for programmatic access

## Tech Stack
- Wiki.js 2.x
- PostgreSQL (storage)
- Git (content sync)
- OpenSearch (search)
- S3/MinIO (assets)
