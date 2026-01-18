# Alert Configuration

**Version**: 1.0.0
**Owner**: SRE Team
**Last Updated**: 2024-01-15

---

## Alert Philosophy

**Every alert must have:**
1. A clear, actionable runbook
2. An owner who can fix it
3. A defined severity
4. A business impact statement

**We do NOT alert on:**
- Metrics without actionable responses
- Expected conditions (scheduled maintenance)
- Informational events (use dashboards instead)

---

## Severity Levels

| Severity | Response Time | Notification | Example |
|----------|---------------|--------------|---------|
| **P1 - Critical** | < 15 min | PagerDuty + Slack | Service down, data loss |
| **P2 - High** | < 1 hour | PagerDuty (business hours) + Slack | Degraded performance |
| **P3 - Medium** | < 4 hours | Slack only | Non-critical errors |
| **P4 - Low** | Next business day | Email digest | Warnings, capacity planning |

---

## Alert Definitions

### Infrastructure Alerts

#### `infra-high-cpu`

```yaml
name: infra-high-cpu
severity: P2
description: "CPU usage exceeds 85% for 10 minutes"

condition:
  metric: system_cpu_usage_percent
  threshold: "> 85"
  duration: 10m

labels:
  team: platform
  service: "{{ $labels.service }}"

annotations:
  summary: "High CPU on {{ $labels.instance }}"
  description: "CPU usage is {{ $value }}% on {{ $labels.instance }}"
  runbook: "ops/runbooks/high-cpu.md"
  impact: "Service may become slow or unresponsive"

actions:
  - Check for runaway processes
  - Scale horizontally if needed
  - Review recent deployments
```

#### `infra-high-memory`

```yaml
name: infra-high-memory
severity: P2
description: "Memory usage exceeds 90% for 5 minutes"

condition:
  metric: system_memory_usage_percent
  threshold: "> 90"
  duration: 5m

runbook: "ops/runbooks/high-memory.md"
impact: "OOM kills may occur, affecting service availability"
```

#### `infra-disk-full`

```yaml
name: infra-disk-full
severity: P1
description: "Disk usage exceeds 95%"

condition:
  metric: system_disk_usage_percent
  threshold: "> 95"
  duration: 5m

runbook: "ops/runbooks/disk-full.md"
impact: "Service will fail to write data, potential data loss"
```

---

### Application Alerts

#### `app-high-error-rate`

```yaml
name: app-high-error-rate
severity: P1
description: "5xx error rate exceeds 1% for 5 minutes"

condition:
  metric: http_requests_total{status=~"5.."}
  threshold: "> 1%"
  duration: 5m
  comparison_metric: http_requests_total

runbook: "ops/runbooks/high-error-rate.md"
impact: "Users experiencing errors, potential revenue impact"

actions:
  - Check application logs
  - Verify database connectivity
  - Review recent deployments
  - Consider rollback
```

#### `app-high-latency`

```yaml
name: app-high-latency
severity: P2
description: "P99 latency exceeds SLO for 5 minutes"

condition:
  metric: http_request_duration_seconds{quantile="0.99"}
  threshold: "> 0.5"
  duration: 5m

runbook: "ops/runbooks/high-latency.md"
impact: "Poor user experience, potential timeout errors"
```

#### `app-health-check-failed`

```yaml
name: app-health-check-failed
severity: P1
description: "Health check endpoint returning non-200"

condition:
  metric: probe_success
  threshold: "== 0"
  duration: 2m

runbook: "ops/runbooks/health-check-failed.md"
impact: "Service may be down or misconfigured"
```

---

### Database Alerts

#### `db-connection-pool-exhausted`

```yaml
name: db-connection-pool-exhausted
severity: P1
description: "Database connection pool usage exceeds 90%"

condition:
  metric: pg_stat_activity_count / pg_settings_max_connections
  threshold: "> 0.9"
  duration: 5m

runbook: "ops/runbooks/db-connection-pool.md"
impact: "New requests will fail to acquire connections"

actions:
  - Kill idle connections
  - Identify connection leaks
  - Scale connection pool
```

#### `db-replication-lag`

```yaml
name: db-replication-lag
severity: P2
description: "Replication lag exceeds 5 seconds"

condition:
  metric: pg_replication_lag_seconds
  threshold: "> 5"
  duration: 5m

runbook: "ops/runbooks/db-replication-lag.md"
impact: "Read replicas serving stale data"
```

#### `db-slow-queries`

```yaml
name: db-slow-queries
severity: P3
description: "Multiple queries exceeding 1 second"

condition:
  metric: pg_slow_queries_count
  threshold: "> 10"
  duration: 15m

runbook: "ops/runbooks/db-slow-queries.md"
impact: "Database performance degradation"
```

---

### SLO Alerts

#### `slo-error-budget-burn-fast`

```yaml
name: slo-error-budget-burn-fast
severity: P1
description: "Error budget burning 14.4x faster than sustainable"

condition:
  # Burns through 10% of monthly budget in 1 hour
  metric: slo_error_budget_remaining
  threshold: "< 90% in 1h"

runbook: "ops/runbooks/slo-burn.md"
impact: "At this rate, SLO will be breached"

actions:
  - Immediately investigate root cause
  - Consider deployment freeze
  - Engage all hands if needed
```

#### `slo-error-budget-low`

```yaml
name: slo-error-budget-low
severity: P2
description: "Error budget below 25%"

condition:
  metric: slo_error_budget_remaining
  threshold: "< 25%"

runbook: "ops/runbooks/slo-low-budget.md"
impact: "Limited room for further incidents"

actions:
  - Freeze non-critical deployments
  - Prioritize reliability work
  - Review recent incident causes
```

---

### Security Alerts

#### `security-failed-auth-spike`

```yaml
name: security-failed-auth-spike
severity: P2
description: "Failed authentication attempts spike"

condition:
  metric: auth_failures_total
  threshold: "> 100 in 5m"

runbook: "ops/runbooks/auth-failure-spike.md"
impact: "Potential brute force attack"

actions:
  - Enable rate limiting
  - Check for credential stuffing
  - Review suspicious IPs
```

#### `security-rls-bypass-attempt`

```yaml
name: security-rls-bypass-attempt
severity: P1
description: "Potential RLS bypass detected"

condition:
  metric: rls_policy_violations
  threshold: "> 0"

runbook: "ops/runbooks/rls-violation.md"
impact: "Data security breach potential"
```

---

## Alert Routing

### PagerDuty Escalation Policy

```yaml
escalation_policy:
  name: "Production On-Call"

  levels:
    - level: 1
      timeout: 15m
      targets:
        - type: schedule
          id: "primary-oncall"

    - level: 2
      timeout: 30m
      targets:
        - type: schedule
          id: "secondary-oncall"

    - level: 3
      timeout: 30m
      targets:
        - type: user
          id: "engineering-manager"
```

### Slack Channels

| Channel | Purpose | Alert Types |
|---------|---------|-------------|
| `#alerts-critical` | P1 alerts | All critical alerts |
| `#alerts-production` | P2-P3 alerts | Production issues |
| `#alerts-staging` | Staging alerts | Non-blocking |
| `#incidents` | Active incidents | Incident updates |

---

## Alert Silencing

### Scheduled Maintenance

```yaml
silence:
  name: "Scheduled maintenance"
  matchers:
    - name: service
      value: "workbench-api"
  start_time: "2024-01-20T02:00:00Z"
  end_time: "2024-01-20T04:00:00Z"
  created_by: "@sre-oncall"
  comment: "Scheduled database migration"
```

### Silencing Rules

1. **Always document** the reason for silencing
2. **Set end time** - no indefinite silences
3. **Narrow scope** - silence specific alerts, not all
4. **Notify team** in `#alerts-production`

---

## Alert Testing

### Synthetic Tests

Run daily to verify alerting is working:

```bash
# Trigger test alert
./scripts/test-alert.sh --alert=app-health-check-failed --severity=P1

# Verify PagerDuty received alert
./scripts/verify-pagerduty.sh --incident-key=test-$(date +%Y%m%d)

# Auto-resolve test
./scripts/resolve-test-alert.sh
```

### Chaos Drills

Monthly drills to verify alert response:
- Inject failure
- Verify alert fires
- Measure response time
- Practice runbook

---

## Metrics to Collect

Required metrics for effective alerting:

```yaml
infrastructure:
  - system_cpu_usage_percent
  - system_memory_usage_percent
  - system_disk_usage_percent
  - system_network_receive_bytes
  - system_network_transmit_bytes

application:
  - http_requests_total
  - http_request_duration_seconds
  - http_requests_in_progress

database:
  - pg_stat_activity_count
  - pg_replication_lag_seconds
  - pg_slow_queries_count

business:
  - user_signups_total
  - orders_completed_total
  - revenue_total
```

---

*Alerts are reviewed quarterly. Last review: 2024-01-15*
