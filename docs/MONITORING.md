# Phase 1 Monitoring Setup Guide

**Purpose**: Comprehensive monitoring, alerting, and observability for Phase 1 production deployment

**Last Updated**: 2025-12-09
**Maintainer**: Jake Tolentino (JT)

---

## Monitoring Stack Overview

**Architecture**:
```
Production Services
   ↓ Metrics & Logs
Monitoring Layer (DigitalOcean, Supabase, Vercel)
   ↓ Alerts
Mattermost (#finance-alerts channel)
   ↓ On-Call
Finance SSC Team
```

**Components**:
- **DigitalOcean Monitoring**: App Platform metrics, container health
- **Supabase Logs**: Edge Function execution, database queries
- **Vercel Analytics**: Frontend performance, Web Vitals
- **n8n Execution History**: Workflow success/failure rates
- **Mattermost Webhooks**: Alert delivery and notifications

---

## 1. DigitalOcean App Platform Monitoring

### OCR Backend Monitoring (App ID: b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9)

**Metrics to Monitor**:
- CPU Utilization (Alert: >80%)
- Memory Utilization (Alert: >80%)
- Restart Count (Alert: >5 restarts in 15 min)
- HTTP Request Latency (Alert: P95 >30s)
- HTTP Error Rate (Alert: >5%)

**Setup Alerts**:
```bash
# Via App Platform spec (already configured in ade-ocr-backend.yaml)
# Alerts are defined in config/production/ade-ocr-backend.yaml:
#   - CPU_UTILIZATION: 80
#   - MEM_UTILIZATION: 80
#   - RESTART_COUNT: 5
#   - DEPLOYMENT_FAILED
#   - DOMAIN_FAILED
```

**View Metrics**:
```bash
# Via CLI
doctl apps get b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9 --format Spec.Services.Alerts

# Via Dashboard
# https://cloud.digitalocean.com/apps/b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9
```

**Custom Health Check**:
```bash
# OCR backend exposes /health endpoint
curl -sf https://ade-ocr-backend.insightpulseai.net/health

# Expected response:
# {
#   "status": "ok",
#   "uptime": 123456,
#   "metrics": {
#     "p95_latency_ms": 28000,
#     "total_requests": 1234,
#     "error_rate": 0.02
#   }
# }
```

**Alert Integration with Mattermost**:
```bash
# Configure webhook in DigitalOcean dashboard
# Webhook URL: https://mattermost.insightpulseai.net/hooks/xxxxxxxxxxxxxxxxxxxxxxxx
# Channel: #finance-alerts
```

---

## 2. Supabase Monitoring

### Edge Function Monitoring

**Metrics to Monitor**:
- Execution Count (per function)
- Error Rate (Alert: >5%)
- Execution Duration (Alert: P95 >5s)
- Cold Start Frequency
- Memory Usage

**View Logs**:
```bash
# Via Supabase CLI
supabase functions logs task-queue-processor --project-ref xkxyvboeubffxxbebsll
supabase functions logs bir-form-validator --project-ref xkxyvboeubffxxbebsll
supabase functions logs expense-ocr-processor --project-ref xkxyvboeubffxxbebsll

# Via Supabase Dashboard
# https://supabase.com/dashboard/project/xkxyvboeubffxxbebsll/functions
```

**Custom Metrics Query**:
```sql
-- Query Edge Function execution metrics
SELECT
  function_name,
  COUNT(*) as total_executions,
  AVG(duration_ms) as avg_duration_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration_ms,
  COUNT(*) FILTER (WHERE status = 'error') * 100.0 / COUNT(*) as error_rate_pct
FROM edge_function_logs
WHERE created_at >= NOW() - INTERVAL '1 hour'
GROUP BY function_name;
```

### Database Monitoring

**Metrics to Monitor**:
- Active Connections (Alert: >80% of max)
- Query Performance (Alert: >100 slow queries/hour)
- Disk Usage (Alert: >80%)
- Replication Lag (Alert: >5s)
- Row-Level Security Policy Violations (Alert: >0)

**View Metrics**:
```bash
# Active connections
psql "$POSTGRES_URL" -c "
  SELECT COUNT(*) as active_connections,
         max_conn - COUNT(*) as available_connections
  FROM pg_stat_activity
  CROSS JOIN (SELECT setting::int as max_conn FROM pg_settings WHERE name = 'max_connections') s;
"

# Slow queries (>1s)
psql "$POSTGRES_URL" -c "
  SELECT query, calls, mean_exec_time, max_exec_time
  FROM pg_stat_statements
  WHERE mean_exec_time > 1000
  ORDER BY mean_exec_time DESC
  LIMIT 10;
"

# RLS policy violations
psql "$POSTGRES_URL" -c "
  SELECT tablename, COUNT(*) as violation_count
  FROM rls_violation_log
  WHERE created_at >= NOW() - INTERVAL '1 hour'
  GROUP BY tablename;
"
```

**Database Alerts via n8n Workflow**:
```javascript
// n8n workflow: Database Health Monitor (runs every 15 min)
{
  "name": "Database Health Monitor",
  "nodes": [
    {
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "rule": {
          "interval": [{ "field": "minutes", "minutesInterval": 15 }]
        }
      }
    },
    {
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT COUNT(*) as slow_queries FROM pg_stat_statements WHERE mean_exec_time > 1000;"
      }
    },
    {
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{$json.slow_queries}}",
              "operation": "larger",
              "value2": 100
            }
          ]
        }
      }
    },
    {
      "type": "n8n-nodes-base.mattermost",
      "parameters": {
        "message": "⚠️ **Database Alert**: {{$json.slow_queries}} slow queries detected in last hour (threshold: 100)"
      }
    }
  ]
}
```

---

## 3. Vercel Frontend Monitoring

### Web Vitals Monitoring

**Metrics to Monitor**:
- Largest Contentful Paint (LCP) - Alert: >2.5s
- First Input Delay (FID) - Alert: >100ms
- Cumulative Layout Shift (CLS) - Alert: >0.1
- First Contentful Paint (FCP) - Alert: >1.8s
- Time to First Byte (TTFB) - Alert: >600ms

**Setup Vercel Analytics**:
```bash
# Install Vercel Analytics package
cd worktree-ui
pnpm add @vercel/analytics

# Add to app/layout.tsx
import { Analytics } from '@vercel/analytics/react'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
```

**View Metrics**:
- Vercel Dashboard: https://vercel.com/[team]/[project]/analytics
- Web Vitals: https://vercel.com/[team]/[project]/analytics/web-vitals

**Custom Web Vitals Tracking**:
```typescript
// app/components/WebVitalsReporter.tsx
'use client'

import { useReportWebVitals } from 'next/web-vitals'

export function WebVitalsReporter() {
  useReportWebVitals((metric) => {
    const body = JSON.stringify(metric)
    const url = '/api/web-vitals'

    // Send to custom endpoint for aggregation
    if (navigator.sendBeacon) {
      navigator.sendBeacon(url, body)
    } else {
      fetch(url, { body, method: 'POST', keepalive: true })
    }
  })
  return null
}
```

### Deployment Monitoring

**Metrics to Monitor**:
- Deployment Status (Success/Failure)
- Build Duration (Alert: >10 min)
- Bundle Size (Alert: >500KB initial, >2MB total)
- Error Rate Post-Deployment (Alert: >1% increase)

**Deployment Notifications**:
```bash
# Configure via Vercel Integrations
# https://vercel.com/integrations/webhooks

# Webhook payload to Mattermost
{
  "deployment_url": "https://...",
  "status": "ready",
  "meta": {
    "githubCommitSha": "abc123",
    "githubCommitMessage": "Deploy Phase 1"
  }
}
```

---

## 4. Task Queue Monitoring

### Task Bus Metrics

**Metrics to Monitor**:
- Pending Tasks (Alert: >100)
- Processing Tasks (Alert: >50)
- Stuck Tasks (Alert: >0 tasks stuck >5 min)
- Task Completion Rate (Alert: <90%)
- Task Error Rate (Alert: >5%)

**Real-Time Dashboard**:
- **URL**: https://[frontend-url]/dashboard/task-queue
- **Refresh**: Every 5 seconds via Supabase Realtime subscriptions

**Custom Metrics Query**:
```sql
-- Task queue health metrics
SELECT
  status,
  COUNT(*) as task_count,
  AVG(EXTRACT(EPOCH FROM (NOW() - created_at))) as avg_age_seconds
FROM task_queue
WHERE created_at >= NOW() - INTERVAL '1 hour'
GROUP BY status;

-- Stuck tasks detection
SELECT
  id,
  kind,
  status,
  EXTRACT(EPOCH FROM (NOW() - updated_at)) / 60 as stuck_minutes
FROM task_queue
WHERE status = 'processing'
  AND updated_at < NOW() - INTERVAL '5 minutes'
ORDER BY stuck_minutes DESC;
```

**Task Queue Alert Workflow** (n8n):
```javascript
// n8n workflow: Task Queue Monitor (runs every 5 min)
{
  "name": "Task Queue Monitor",
  "nodes": [
    {
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "rule": {
          "interval": [{ "field": "minutes", "minutesInterval": 5 }]
        }
      }
    },
    {
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT COUNT(*) as stuck_tasks FROM task_queue WHERE status = 'processing' AND updated_at < NOW() - INTERVAL '5 minutes';"
      }
    },
    {
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{$json.stuck_tasks}}",
              "operation": "larger",
              "value2": 0
            }
          ]
        }
      }
    },
    {
      "type": "n8n-nodes-base.mattermost",
      "parameters": {
        "message": "🚨 **Task Queue Alert**: {{$json.stuck_tasks}} stuck tasks detected (>5 min in processing)"
      }
    }
  ]
}
```

---

## 5. BIR Compliance Monitoring

### BIR Form Filing Metrics

**Metrics to Monitor**:
- Forms Due in Next 7 Days (Alert: >0 unsubmitted)
- Forms Overdue (Alert: >0)
- Form Accuracy (Alert: <98%)
- Approval Workflow SLA (Alert: >24h from prep to approval)

**BIR Status Dashboard**:
- **URL**: https://[frontend-url]/dashboard/bir-status
- **Refresh**: Real-time via Supabase subscriptions
- **Displays**: 8 agencies × 8 forms × 8 employees = 512 tracking records

**Custom Metrics Query**:
```sql
-- BIR deadline alerts (7-day look-ahead)
SELECT
  agency_name,
  form_type,
  filing_deadline,
  DATE_PART('day', filing_deadline - NOW()) as days_until_deadline,
  status
FROM bir_filings
WHERE filing_deadline BETWEEN NOW() AND NOW() + INTERVAL '7 days'
  AND status IN ('draft', 'pending')
ORDER BY filing_deadline ASC;

-- BIR accuracy tracking
SELECT
  form_type,
  AVG(accuracy_score) as avg_accuracy,
  COUNT(*) FILTER (WHERE accuracy_score < 0.98) as below_threshold_count
FROM bir_validation_log
WHERE validated_at >= NOW() - INTERVAL '30 days'
GROUP BY form_type;
```

**BIR Deadline Alert Workflow** (n8n):
```javascript
// n8n workflow: BIR Deadline Alert (runs daily at 8 AM)
{
  "name": "BIR Deadline Alert",
  "nodes": [
    {
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "rule": {
          "hour": 8,
          "minute": 0,
          "timezone": "Asia/Manila"
        }
      }
    },
    {
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT agency_name, form_type, filing_deadline FROM bir_filings WHERE filing_deadline BETWEEN NOW() AND NOW() + INTERVAL '7 days' AND status IN ('draft', 'pending');"
      }
    },
    {
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{$json.length}}",
              "operation": "larger",
              "value2": 0
            }
          ]
        }
      }
    },
    {
      "type": "n8n-nodes-base.mattermost",
      "parameters": {
        "message": "⚠️ **BIR Deadline Alert**: {{$json.length}} forms due in next 7 days\n\n{{$json.map(f => `- ${f.agency_name} ${f.form_type}: ${f.filing_deadline}`).join('\\n')}}"
      }
    }
  ]
}
```

---

## 6. OCR Confidence Monitoring

### OCR Performance Metrics

**Metrics to Monitor**:
- Average Confidence Score (Alert: <0.70)
- Low Confidence Extractions (Alert: >10% with confidence <0.60)
- Field Extraction Success Rate (Alert: <90%)
- Processing Time (Alert: P95 >30s)

**OCR Confidence Dashboard**:
- **URL**: https://[frontend-url]/dashboard/ocr-confidence
- **Displays**: Real-time OCR metrics by vendor, category, time range

**Custom Metrics Query**:
```sql
-- OCR confidence distribution
SELECT
  CASE
    WHEN confidence >= 0.90 THEN 'High (≥0.90)'
    WHEN confidence >= 0.60 THEN 'Medium (0.60-0.89)'
    ELSE 'Low (<0.60)'
  END as confidence_range,
  COUNT(*) as extraction_count,
  AVG(processing_time_ms) as avg_processing_time_ms
FROM ocr_results
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY confidence_range;

-- Field extraction success rate
SELECT
  COUNT(*) as total_extractions,
  COUNT(*) FILTER (WHERE vendor_name IS NOT NULL) * 100.0 / COUNT(*) as vendor_extraction_rate,
  COUNT(*) FILTER (WHERE amount IS NOT NULL) * 100.0 / COUNT(*) as amount_extraction_rate,
  COUNT(*) FILTER (WHERE date IS NOT NULL) * 100.0 / COUNT(*) as date_extraction_rate
FROM ocr_results
WHERE created_at >= NOW() - INTERVAL '24 hours';
```

**OCR Quality Alert Workflow** (n8n):
```javascript
// n8n workflow: OCR Quality Monitor (runs every 30 min)
{
  "name": "OCR Quality Monitor",
  "nodes": [
    {
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "rule": {
          "interval": [{ "field": "minutes", "minutesInterval": 30 }]
        }
      }
    },
    {
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT AVG(confidence) as avg_confidence, COUNT(*) FILTER (WHERE confidence < 0.60) * 100.0 / COUNT(*) as low_confidence_pct FROM ocr_results WHERE created_at >= NOW() - INTERVAL '1 hour';"
      }
    },
    {
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{$json.low_confidence_pct}}",
              "operation": "larger",
              "value2": 10
            }
          ]
        }
      }
    },
    {
      "type": "n8n-nodes-base.mattermost",
      "parameters": {
        "message": "⚠️ **OCR Quality Alert**: {{$json.low_confidence_pct.toFixed(1)}}% of extractions have confidence <0.60 (threshold: 10%)"
      }
    }
  ]
}
```

---

## 7. Mattermost Alert Configuration

### Webhook Setup

**Create Incoming Webhook**:
1. Go to Mattermost: https://mattermost.insightpulseai.net
2. Navigate to Integrations → Incoming Webhooks
3. Create webhook for #finance-alerts channel
4. Copy webhook URL

**Store Webhook URL**:
```bash
# Add to ~/.zshrc
export MATTERMOST_WEBHOOK_URL="https://mattermost.insightpulseai.net/hooks/xxxxxxxxxxxxxxxxxxxxxxxx"

# Test webhook
curl -X POST "$MATTERMOST_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "✅ Test alert - monitoring system operational"}'
```

### Alert Templates

**Critical Alert**:
```bash
curl -X POST "$MATTERMOST_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "🚨 **CRITICAL**: [Component] [Issue Description]",
    "attachments": [{
      "color": "#FF0000",
      "fields": [
        {"title": "Severity", "value": "Critical", "short": true},
        {"title": "Component", "value": "[Component Name]", "short": true},
        {"title": "Metric", "value": "[Metric Value]", "short": true},
        {"title": "Threshold", "value": "[Threshold Value]", "short": true}
      ]
    }]
  }'
```

**Warning Alert**:
```bash
curl -X POST "$MATTERMOST_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "⚠️ **WARNING**: [Component] [Issue Description]",
    "attachments": [{
      "color": "#FFA500"
    }]
  }'
```

**Info Alert**:
```bash
curl -X POST "$MATTERMOST_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "ℹ️ **INFO**: [Component] [Status Update]",
    "attachments": [{
      "color": "#0000FF"
    }]
  }'
```

---

## 8. Incident Response Playbooks

### Critical Incident Runbook

**Trigger**: Any critical alert (database down, OCR backend unavailable, deployment failure)

**Response Steps**:
1. **Acknowledge** (within 5 min):
   ```bash
   # Reply in Mattermost #finance-alerts
   "Acknowledged - investigating [component]"
   ```

2. **Assess** (within 10 min):
   ```bash
   # Check component health
   ./scripts/validate-phase1.sh --verbose
   ```

3. **Mitigate** (within 30 min):
   ```bash
   # Execute rollback if needed (see docs/ROLLBACK.md)
   # Or apply hotfix
   ```

4. **Document** (within 24 hours):
   ```bash
   # Create incident report
   cat > docs/incidents/$(date +%Y-%m-%d)-[incident-name].md
   ```

5. **Postmortem** (within 72 hours):
   - Root cause analysis
   - Preventive measures
   - Update monitoring/alerting

### Non-Critical Issue Runbook

**Trigger**: Warning alerts (high resource usage, slow queries, approaching thresholds)

**Response Steps**:
1. **Log** (immediate):
   ```bash
   # Add to monitoring log
   echo "$(date) - WARNING: [component] [metric] [value]" >> logs/monitoring.log
   ```

2. **Analyze** (within 4 hours):
   - Trend analysis (is this worsening?)
   - Compare to baselines
   - Identify contributing factors

3. **Schedule** (within 24 hours):
   - Add to backlog if fix needed
   - Set priority based on risk
   - Assign to responsible team member

4. **Follow-Up** (next sprint):
   - Implement fix or optimization
   - Validate resolution
   - Update monitoring thresholds if needed

---

## 9. Monitoring Checklist

### Daily Checks (Automated)
- [ ] OCR backend health (via n8n cron)
- [ ] Task queue status (via n8n cron)
- [ ] BIR deadlines (via n8n cron at 8 AM)
- [ ] Database slow queries (via n8n cron every 15 min)

### Weekly Checks (Manual)
- [ ] Review error logs across all components
- [ ] Check storage usage (Supabase, DigitalOcean)
- [ ] Validate backup retention (database dumps)
- [ ] Review monitoring alert history

### Monthly Checks (Manual)
- [ ] BIR compliance rate (target: 100%)
- [ ] Visual parity trends (SSIM over time)
- [ ] Cost analysis (DigitalOcean, Supabase, Vercel)
- [ ] Security patch status (dependencies, OS)

---

## 10. Monitoring Tools Reference

| Tool | Purpose | Access URL |
|------|---------|------------|
| DigitalOcean Dashboard | App Platform metrics | https://cloud.digitalocean.com/apps |
| Supabase Dashboard | Database, Edge Functions | https://supabase.com/dashboard/project/xkxyvboeubffxxbebsll |
| Vercel Dashboard | Frontend analytics | https://vercel.com/[team]/[project] |
| n8n Dashboard | Workflow execution history | https://ipa.insightpulseai.net |
| Mattermost Alerts | Alert notifications | https://mattermost.insightpulseai.net (#finance-alerts) |

---

**Last Updated**: 2025-12-09
**Next Review**: Weekly during Phase 1, then monthly
**Maintainer**: Jake Tolentino (JT)
