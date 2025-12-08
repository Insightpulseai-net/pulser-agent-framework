# Appsmith Internal Tools Studio - Spec Kit

## Objective
Self-hosted Appsmith platform for rapid development of internal tools, admin dashboards, and operational interfaces connected to Odoo, Supabase, and n8n workflows.

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

| System | Type | Purpose |
|--------|------|---------|
| Supabase | Datasource | App data |
| Odoo CE/OCA 18 | Datasource | ERP data |
| PostgreSQL | Datasource | Direct queries |
| n8n | API | Workflow triggers |
| REST APIs | Datasource | External services |

## Key Features
- Drag-and-drop UI builder
- 45+ pre-built widgets
- Multiple datasource support
- JavaScript transformations
- Git version control
- Role-based access control
- Custom themes

## Use Cases
- Odoo data entry forms
- Approval workflows
- Data quality dashboards
- Agent task management
- Report builders

## Tech Stack
- Appsmith CE
- MongoDB (metadata)
- Redis (sessions)
- PostgreSQL datasource
- REST API datasource
