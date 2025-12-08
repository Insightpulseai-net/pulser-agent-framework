# OpenSearch Enterprise Search - Spec Kit

## Objective
Self-hosted OpenSearch cluster providing full-text search, vector embeddings, and semantic search across Odoo documents, knowledge base, and Medallion data layers.

## Status
- **Phase**: Planning
- **Priority**: P2
- **Dependencies**: supabase-core, wikijs-knowledge-hub

## Quick Links
- [Constitution](./constitution.md) - Guiding principles
- [PRD](./prd.md) - Requirements document
- [Plan](./plan.md) - Implementation plan
- [Tasks](./tasks.md) - Task breakdown

## Integration Points

| System | Direction | Purpose |
|--------|-----------|---------|
| Odoo CE/OCA 18 | Source | Document indexing |
| Wiki.js | Source | Knowledge base search |
| Supabase | Source | Gold layer search |
| MCP Agents | Consumer | RAG retrieval |
| Workbench | Consumer | Query interface |

## Key Features
- Full-text search with relevance tuning
- Vector search (k-NN) for semantic queries
- Multi-tenant index isolation
- Real-time indexing
- Search analytics
- OpenSearch Dashboards

## Tech Stack
- OpenSearch 2.x
- OpenSearch Dashboards
- Logstash (ingestion)
- PostgreSQL sync connector
- Custom embedding service
