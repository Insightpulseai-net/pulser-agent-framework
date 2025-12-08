# Observability Stack (Grafana + Prometheus) - Spec Kit

## Objective
Unified monitoring platform providing metrics collection, visualization, and alerting across all InsightPulseAI services including Odoo, Supabase, n8n, and AI agents.

## Status
- **Phase**: Planning
- **Priority**: P0
- **Dependencies**: None (foundational)

## Quick Links
- [Constitution](./constitution.md) - Guiding principles
- [PRD](./prd.md) - Requirements document
- [Plan](./plan.md) - Implementation plan
- [Tasks](./tasks.md) - Task breakdown

## Integration Points

| System | Type | Purpose |
|--------|------|---------|
| Prometheus | Collector | Metrics scraping |
| Grafana | Visualization | Dashboards, alerts |
| Alertmanager | Routing | Notification dispatch |
| Loki | Logs | Log aggregation |
| All services | Targets | Metrics endpoints |

## Key Features
- Infrastructure metrics (CPU, memory, disk, network)
- Application metrics (requests, latency, errors)
- Custom business metrics
- Pre-built dashboards
- Multi-channel alerting (Slack, email, PagerDuty)
- Log correlation

## Tech Stack
- Prometheus 2.x
- Grafana 10.x
- Alertmanager
- Loki (optional)
- Node Exporter
- PostgreSQL Exporter
- nginx Exporter
