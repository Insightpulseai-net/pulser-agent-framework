# Service Level Objectives (SLOs)

**Version**: 1.0.0
**Owner**: SRE Team
**Last Updated**: 2024-01-15

---

## Overview

This document defines SLOs for all production services. Every service must have:
- At least one availability SLO
- At least one latency SLO
- A defined error budget
- An on-call owner

**Rule**: If it pages, it needs: runbook + owner + SLO + rollback command.

---

## SLO Framework

### Terminology

| Term | Definition |
|------|------------|
| **SLI** | Service Level Indicator - a quantitative measure of service |
| **SLO** | Service Level Objective - target value for an SLI |
| **SLA** | Service Level Agreement - contractual commitment |
| **Error Budget** | Allowed downtime/errors before action required |

### Standard SLOs

All services should target these baseline SLOs:

| Category | SLO | Measurement Window |
|----------|-----|-------------------|
| Availability | 99.9% | Rolling 30 days |
| Latency P50 | < 100ms | Rolling 24 hours |
| Latency P99 | < 500ms | Rolling 24 hours |
| Error Rate | < 0.1% | Rolling 24 hours |

---

## Service SLOs

### API Gateway

**Service**: `api-gateway`
**Owner**: Platform Team
**On-call**: @platform-oncall

| SLI | SLO | Error Budget (30d) | Alert Threshold |
|-----|-----|-------------------|-----------------|
| Availability | 99.95% | 21.6 minutes | < 99.9% for 5m |
| Latency P50 | < 50ms | - | > 75ms for 5m |
| Latency P99 | < 200ms | - | > 300ms for 5m |
| Error Rate (5xx) | < 0.05% | - | > 0.1% for 5m |

**Runbook**: [api-gateway-runbook.md](../runbooks/api-gateway-runbook.md)

**Rollback Command**:
```bash
./scripts/rollback.sh --service=api-gateway --env=production
```

---

### Workbench API

**Service**: `workbench-api`
**Owner**: Backend Team
**On-call**: @backend-oncall

| SLI | SLO | Error Budget (30d) | Alert Threshold |
|-----|-----|-------------------|-----------------|
| Availability | 99.9% | 43.2 minutes | < 99.8% for 5m |
| Latency P50 | < 100ms | - | > 150ms for 5m |
| Latency P99 | < 500ms | - | > 750ms for 5m |
| Error Rate (5xx) | < 0.1% | - | > 0.5% for 5m |

**Runbook**: [workbench-api-runbook.md](../runbooks/workbench-api-runbook.md)

**Rollback Command**:
```bash
./scripts/rollback.sh --service=workbench-api --env=production
```

---

### Platform UI

**Service**: `platform-ui`
**Owner**: Frontend Team
**On-call**: @frontend-oncall

| SLI | SLO | Error Budget (30d) | Alert Threshold |
|-----|-----|-------------------|-----------------|
| Availability | 99.9% | 43.2 minutes | < 99.8% for 5m |
| LCP (Largest Contentful Paint) | < 2.5s | - | > 4s for 10m |
| FID (First Input Delay) | < 100ms | - | > 300ms for 10m |
| CLS (Cumulative Layout Shift) | < 0.1 | - | > 0.25 for 10m |
| Error Rate (JS) | < 0.1% | - | > 0.5% for 5m |

**Runbook**: [platform-ui-runbook.md](../runbooks/platform-ui-runbook.md)

**Rollback Command**:
```bash
vercel rollback --scope=insightpulseai
```

---

### Supabase Database

**Service**: `supabase-db`
**Owner**: Platform Team
**On-call**: @platform-oncall

| SLI | SLO | Error Budget (30d) | Alert Threshold |
|-----|-----|-------------------|-----------------|
| Availability | 99.99% | 4.32 minutes | < 99.95% for 2m |
| Query Latency P50 | < 10ms | - | > 20ms for 5m |
| Query Latency P99 | < 100ms | - | > 200ms for 5m |
| Connection Pool Usage | < 80% | - | > 90% for 5m |
| Replication Lag | < 1s | - | > 5s for 1m |

**Runbook**: [supabase-db-runbook.md](../runbooks/supabase-db-runbook.md)

**Rollback Command**:
```bash
# Migrations only
supabase migration repair --status reverted
```

---

### Edge Functions

**Service**: `edge-functions`
**Owner**: Backend Team
**On-call**: @backend-oncall

| SLI | SLO | Error Budget (30d) | Alert Threshold |
|-----|-----|-------------------|-----------------|
| Availability | 99.9% | 43.2 minutes | < 99.8% for 5m |
| Latency P50 | < 50ms | - | > 100ms for 5m |
| Latency P99 | < 200ms | - | > 500ms for 5m |
| Cold Start P99 | < 500ms | - | > 1s for 10m |
| Error Rate | < 0.1% | - | > 0.5% for 5m |

**Runbook**: [edge-functions-runbook.md](../runbooks/edge-functions-runbook.md)

**Rollback Command**:
```bash
supabase functions deploy --version=previous
```

---

### Odoo ERP

**Service**: `odoo-erp`
**Owner**: ERP Team
**On-call**: @erp-oncall

| SLI | SLO | Error Budget (30d) | Alert Threshold |
|-----|-----|-------------------|-----------------|
| Availability | 99.5% | 3.6 hours | < 99% for 10m |
| Page Load P50 | < 2s | - | > 3s for 10m |
| Page Load P99 | < 5s | - | > 8s for 10m |
| Background Jobs Success | > 99% | - | < 95% for 30m |
| Error Rate | < 0.5% | - | > 1% for 10m |

**Runbook**: [odoo-erp-runbook.md](../runbooks/odoo-erp-runbook.md)

**Rollback Command**:
```bash
./scripts/rollback.sh --service=odoo --env=production
```

---

## Error Budget Policy

### Budget Consumption Actions

| Budget Remaining | Action |
|------------------|--------|
| > 50% | Normal operations |
| 25-50% | Increase monitoring, review recent changes |
| 10-25% | Freeze non-critical deployments |
| < 10% | All hands on reliability |
| 0% | Full deployment freeze until budget restored |

### Budget Restoration

- Error budget resets at the start of each 30-day window
- If budget is exhausted, focus shifts entirely to reliability work
- Postmortems required for any incident consuming > 10% of budget

---

## SLO Review Process

### Monthly Review

1. Review SLO compliance for all services
2. Analyze error budget burn rate
3. Identify services at risk
4. Update SLOs if business needs change

### Quarterly Review

1. Validate SLOs against business requirements
2. Review and update thresholds
3. Add SLOs for new services
4. Retire SLOs for deprecated services

---

## Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| SLO Overview | `/dashboards/slo-overview` | All services at a glance |
| Error Budget | `/dashboards/error-budget` | Budget consumption tracking |
| Service Health | `/dashboards/service-health` | Real-time health status |
| Incident History | `/dashboards/incidents` | Past incidents and impact |

---

## Appendix: SLO Calculation

### Availability

```
Availability = (Total Time - Downtime) / Total Time * 100

Example (30 days):
99.9% = 43.2 minutes downtime allowed
99.95% = 21.6 minutes downtime allowed
99.99% = 4.32 minutes downtime allowed
```

### Error Budget

```
Error Budget = (1 - SLO) * Measurement Window

Example (99.9% over 30 days):
Error Budget = (1 - 0.999) * 43200 minutes = 43.2 minutes
```

### Latency Percentiles

```
P50 = 50th percentile (median)
P90 = 90th percentile
P99 = 99th percentile (only 1% slower)
P99.9 = 99.9th percentile (only 0.1% slower)
```

---

*SLOs are reviewed monthly. Last review: 2024-01-15*
