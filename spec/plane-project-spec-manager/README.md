# Plane Project & Spec Manager - Spec Kit

## Objective
Self-hosted Plane instance for project management, issue tracking, and spec-driven development workflows, with Odoo project sync and n8n automation integration.

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
| Odoo Project | Bidirectional | Project/task sync |
| Supabase | Storage | Analytics data |
| n8n | Trigger | Workflow automation |
| GitHub | Bidirectional | Issue sync |
| Slack | Notification | Updates |

## Key Features
- Issue tracking with customizable workflows
- Cycles (sprints) and modules
- Kanban, list, and calendar views
- Time tracking
- Custom properties
- Roadmaps
- API for automation

## Spec-Driven Features
- Spec document attachments
- PRD → Epic → Task hierarchy
- UAT checklist tracking
- Go-live checklists
- Architecture decision records

## Tech Stack
- Plane CE
- PostgreSQL
- Redis
- MinIO (files)
- Next.js frontend
