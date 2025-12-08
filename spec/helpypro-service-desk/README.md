# HelpyPro Service Desk - Spec Kit

## Objective
Self-hosted Helpy service desk providing ticket management, knowledge base, and customer support portal integrated with Odoo partners and AI-powered response suggestions.

## Status
- **Phase**: Planning
- **Priority**: P2
- **Dependencies**: supabase-core, n8n-automation-hub

## Quick Links
- [Constitution](./constitution.md) - Guiding principles
- [PRD](./prd.md) - Requirements document
- [Plan](./plan.md) - Implementation plan
- [Tasks](./tasks.md) - Task breakdown

## Integration Points

| System | Direction | Purpose |
|--------|-----------|---------|
| Odoo CE/OCA 18 | Bidirectional | Partner/contact sync |
| Supabase | Storage | Ticket data warehouse |
| n8n | Trigger | Workflow automation |
| MCP Agents | Consumer | AI response suggestions |
| Email | Bidirectional | Ticket creation/replies |

## Key Features
- Multi-channel support (email, web, chat)
- Ticket management with SLA tracking
- Customer-facing knowledge base
- Agent dashboard
- Reporting and analytics
- AI-powered response suggestions
- Odoo partner integration

## Tech Stack
- Helpy Pro (Rails)
- PostgreSQL
- Redis
- Elasticsearch (search)
- Sidekiq (jobs)
