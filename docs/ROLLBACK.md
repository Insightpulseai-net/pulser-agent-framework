# Phase 1 Rollback Procedures

**Purpose**: Emergency rollback procedures for Phase 1 deployment failures

**Last Updated**: 2025-12-09
**Maintainer**: Jake Tolentino (JT)

---

## Rollback Decision Matrix

Use this matrix to determine rollback necessity and scope:

| Failure Type | Severity | Rollback Required | Rollback Scope | Time Budget |
|--------------|----------|-------------------|----------------|-------------|
| Database migration fails | 🔴 Critical | ✅ Yes | Full stack | <15 min |
| RLS policy violation | 🔴 Critical | ✅ Yes | Database only | <15 min |
| Visual parity SSIM drop >2% | 🟡 High | ✅ Yes | Frontend only | <1 hour |
| OCR backend P95 >40s | 🟡 High | ✅ Yes | Backend only | <1 hour |
| Edge Function deploy fails | 🟠 Medium | ⚠️ Partial | Failed functions only | <4 hours |
| n8n workflow import fails | 🟠 Medium | ❌ No | Fix and re-import | <4 hours |
| BIR calculation accuracy <98% | 🔴 Critical | ✅ Yes | Full stack | <15 min |
| Task queue stuck tasks >10 | 🟡 High | ✅ Yes | Backend + DB | <1 hour |
| Monitoring alerts fail | 🟢 Low | ❌ No | Fix webhook config | Next cycle |

---

## Pre-Rollback Checklist

Before initiating rollback:

- [ ] **Identify failure type** - Use validation script or manual inspection
- [ ] **Check rollback decision matrix** - Determine if rollback required
- [ ] **Notify stakeholders** - Mattermost #finance-alerts channel
- [ ] **Capture failure evidence** - Logs, screenshots, error messages
- [ ] **Verify rollback point exists** - Git tag and deployment IDs saved
- [ ] **Estimate rollback time** - Based on severity and scope

---

## Rollback Procedures by Component

### 1. Database Schema Rollback

**Trigger**: Migration failure, RLS violation, data integrity issue

**Rollback Steps**:

```bash
# 1. Identify last good schema state
psql "$POSTGRES_URL" -c "
  SELECT version, applied_at
  FROM schema_migrations
  ORDER BY applied_at DESC
  LIMIT 5;
"

# 2. Run down migrations in reverse order
cd packages/db/sql/down_migrations

# Rollback in reverse order: 13 → 12 → 11 → 10
psql "$POSTGRES_URL" -f 13_down_medallion_platinum.sql
psql "$POSTGRES_URL" -f 12_down_medallion_gold.sql
psql "$POSTGRES_URL" -f 11_down_medallion_silver.sql
psql "$POSTGRES_URL" -f 10_down_medallion_bronze.sql

# 3. Verify rollback
psql "$POSTGRES_URL" -c "
  SELECT schema_name
  FROM information_schema.schemata
  WHERE schema_name IN ('bronze', 'silver', 'gold', 'platinum');
"
# Expected: 0 rows if full rollback

# 4. Update migration log
psql "$POSTGRES_URL" -c "
  INSERT INTO rollback_log (component, reason, rolled_back_at)
  VALUES ('database_schema', 'Migration failure', NOW());
"
```

**Verification**:
- [ ] Schema migrations table shows correct version
- [ ] RLS policies removed for rolled-back tables
- [ ] Data integrity checks pass
- [ ] No orphaned data in rolled-back schemas

**Time Estimate**: 5-10 minutes

---

### 2. Supabase Edge Functions Rollback

**Trigger**: Edge Function deployment failure, runtime errors

**Rollback Steps**:

```bash
# 1. List deployed Edge Functions
supabase functions list --project-ref $SUPABASE_PROJECT_REF

# 2. Delete failed Edge Functions
supabase functions delete task-queue-processor --project-ref $SUPABASE_PROJECT_REF
supabase functions delete bir-form-validator --project-ref $SUPABASE_PROJECT_REF
supabase functions delete expense-ocr-processor --project-ref $SUPABASE_PROJECT_REF

# 3. Verify deletion
supabase functions list --project-ref $SUPABASE_PROJECT_REF
# Expected: 0 functions listed

# 4. Restore from previous deployment (if partial rollback)
cd worktree-integration/supabase/functions
git checkout rollback/phase1-pre-deploy

supabase functions deploy task-queue-processor --project-ref $SUPABASE_PROJECT_REF
# ... deploy other functions from last good commit
```

**Verification**:
- [ ] Edge Functions deleted or restored to working version
- [ ] Health check endpoints return 200 OK
- [ ] Function logs show no errors
- [ ] Integration tests pass

**Time Estimate**: 5-10 minutes

---

### 3. n8n Workflows Rollback

**Trigger**: Workflow import failure, execution errors >5%

**Rollback Steps**:

```bash
# 1. List all workflows
curl -s "$N8N_BASE_URL/api/v1/workflows" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" | jq -r '.data[] | "\(.id): \(.name)"'

# 2. Deactivate all workflows
curl -s "$N8N_BASE_URL/api/v1/workflows" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" | jq -r '.data[].id' | while read id; do
    curl -X PATCH "$N8N_BASE_URL/api/v1/workflows/${id}/deactivate" \
      -H "X-N8N-API-KEY: $N8N_API_KEY"
    echo "Deactivated workflow: $id"
  done

# 3. Delete failed workflows (optional - if re-import needed)
curl -s "$N8N_BASE_URL/api/v1/workflows" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" | jq -r '.data[].id' | while read id; do
    curl -X DELETE "$N8N_BASE_URL/api/v1/workflows/${id}" \
      -H "X-N8N-API-KEY: $N8N_API_KEY"
    echo "Deleted workflow: $id"
  done

# 4. Verify deactivation
curl -s "$N8N_BASE_URL/api/v1/workflows" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" | jq -r '.data[] | "\(.name): \(.active)"'
# Expected: All workflows active=false
```

**Verification**:
- [ ] All workflows deactivated or deleted
- [ ] No active workflow executions
- [ ] n8n UI shows correct state
- [ ] No pending tasks in workflow queue

**Time Estimate**: 5-10 minutes

---

### 4. DigitalOcean OCR Backend Rollback

**Trigger**: Deployment failure, health check failure, P95 >40s

**Rollback Steps**:

```bash
# 1. List recent deployments
APP_ID="b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9"

doctl apps list-deployments $APP_ID \
  --format ID,Phase,Created \
  --no-header | head -5

# 2. Identify last good deployment (Phase=ACTIVE, before current failed deployment)
PREV_DEPLOYMENT_ID=$(doctl apps list-deployments $APP_ID \
  --format ID,Phase \
  --no-header | grep ACTIVE | head -2 | tail -1 | awk '{print $1}')

echo "Rolling back to deployment: $PREV_DEPLOYMENT_ID"

# 3. Create rollback deployment
doctl apps create-deployment $APP_ID \
  --deployment-id $PREV_DEPLOYMENT_ID

# 4. Monitor rollback progress
while true; do
  STATUS=$(doctl apps get $APP_ID --format ActiveDeployment.Phase --no-header)
  echo "Rollback status: $STATUS"

  if [ "$STATUS" = "ACTIVE" ]; then
    echo "✅ Rollback complete"
    break
  elif [ "$STATUS" = "ERROR" ] || [ "$STATUS" = "SUPERSEDED" ]; then
    echo "❌ Rollback failed: $STATUS"
    exit 1
  fi

  sleep 15
done

# 5. Health check
BACKEND_URL=$(doctl apps get $APP_ID --format DefaultIngress --no-header)
curl -sf "https://${BACKEND_URL}/health" | jq -r '.status'
# Expected: "ok"
```

**Verification**:
- [ ] Deployment phase shows ACTIVE
- [ ] Health endpoint returns {"status": "ok"}
- [ ] P95 latency ≤30s
- [ ] OCR smoke test passes (confidence ≥0.60)

**Time Estimate**: 10-15 minutes

---

### 5. Vercel Frontend Rollback

**Trigger**: Visual parity failure, build error, deployment failure

**Rollback Steps**:

```bash
# 1. List recent deployments
cd worktree-ui
vercel ls --prod

# 2. Identify previous deployment URL
PREV_DEPLOYMENT=$(vercel ls --prod | grep "worktree-ui" | head -2 | tail -1 | awk '{print $2}')

echo "Rolling back to deployment: $PREV_DEPLOYMENT"

# 3. Rollback to previous deployment
vercel rollback $PREV_DEPLOYMENT

# 4. Wait for rollback completion (Vercel is instant)
sleep 5

# 5. Verify rollback
CURRENT_URL=$(vercel ls --prod | grep "worktree-ui" | head -1 | awk '{print $2}')
curl -sf "https://${CURRENT_URL}" | grep -q "Task Queue Monitor"
# Expected: HTML containing "Task Queue Monitor"

# 6. Visual parity validation
node scripts/snap.js \
  --base-url="https://${CURRENT_URL}" \
  --routes="/,/dashboard/task-queue,/dashboard/bir-status,/dashboard/ocr-confidence"

node scripts/ssim.js \
  --threshold-mobile=0.97 \
  --threshold-desktop=0.98
# Expected: All routes pass thresholds
```

**Verification**:
- [ ] Vercel dashboard shows previous deployment active
- [ ] Frontend loads successfully
- [ ] Visual parity SSIM ≥0.97 mobile, ≥0.98 desktop
- [ ] All 3 dashboards accessible

**Time Estimate**: 5-10 minutes

---

## Full Stack Rollback Procedure

**Trigger**: Critical failure affecting multiple components (database + backend + frontend)

**Time Budget**: <30 minutes

**Orchestration**:

```bash
#!/bin/bash
# Full stack rollback - execute components in reverse deployment order

set -euo pipefail

echo "🚨 Initiating full stack rollback..."

# Step 1: Rollback frontend (fastest, most visible to users)
echo "1/5 Rolling back Vercel frontend..."
cd worktree-ui
PREV_DEPLOYMENT=$(vercel ls --prod | grep "worktree-ui" | head -2 | tail -1 | awk '{print $2}')
vercel rollback $PREV_DEPLOYMENT
echo "✅ Frontend rolled back"

# Step 2: Rollback OCR backend
echo "2/5 Rolling back DigitalOcean OCR backend..."
APP_ID="b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9"
PREV_DEPLOYMENT_ID=$(doctl apps list-deployments $APP_ID \
  --format ID,Phase --no-header | grep ACTIVE | head -2 | tail -1 | awk '{print $1}')
doctl apps create-deployment $APP_ID --deployment-id $PREV_DEPLOYMENT_ID
echo "✅ OCR backend rollback initiated (monitoring...)"

# Step 3: Deactivate n8n workflows
echo "3/5 Deactivating n8n workflows..."
curl -s "$N8N_BASE_URL/api/v1/workflows" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" | jq -r '.data[].id' | while read id; do
    curl -X PATCH "$N8N_BASE_URL/api/v1/workflows/${id}/deactivate" \
      -H "X-N8N-API-KEY: $N8N_API_KEY"
  done
echo "✅ n8n workflows deactivated"

# Step 4: Delete Edge Functions
echo "4/5 Deleting Supabase Edge Functions..."
supabase functions delete task-queue-processor --project-ref $SUPABASE_PROJECT_REF
supabase functions delete bir-form-validator --project-ref $SUPABASE_PROJECT_REF
supabase functions delete expense-ocr-processor --project-ref $SUPABASE_PROJECT_REF
echo "✅ Edge Functions deleted"

# Step 5: Rollback database schema
echo "5/5 Rolling back database schema..."
cd packages/db/sql/down_migrations
psql "$POSTGRES_URL" -f 13_down_medallion_platinum.sql
psql "$POSTGRES_URL" -f 12_down_medallion_gold.sql
psql "$POSTGRES_URL" -f 11_down_medallion_silver.sql
psql "$POSTGRES_URL" -f 10_down_medallion_bronze.sql
echo "✅ Database schema rolled back"

# Verification
echo "Running post-rollback verification..."
./scripts/validate-phase1.sh

echo "✅ Full stack rollback complete"
```

---

## Post-Rollback Actions

After successful rollback:

### 1. Incident Documentation
```bash
# Create incident report
cat > docs/incidents/$(date +%Y-%m-%d)-rollback.md <<EOF
# Incident Report: $(date +%Y-%m-%d)

**Severity**: [Critical/High/Medium/Low]
**Components Affected**: [Database/Backend/Frontend/Workflows]
**Rollback Initiated**: $(date)
**Rollback Completed**: [timestamp]

## Root Cause
[Detailed analysis of what caused the failure]

## Rollback Procedure Used
[Which rollback procedure was executed]

## Verification Results
[Post-rollback validation results]

## Preventive Measures
[What will be done to prevent recurrence]

## Next Steps
[Actions required before re-deployment]
EOF
```

### 2. Mattermost Notification
```bash
curl -X POST "$MATTERMOST_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"🚨 **Rollback Executed**\n\n**Reason**: [failure description]\n**Components**: [affected components]\n**Status**: Rolled back to last known good state\n\n**Next Steps**: Root cause analysis in progress\n\n**Incident Report**: docs/incidents/$(date +%Y-%m-%d)-rollback.md\"
  }"
```

### 3. Root Cause Analysis
- [ ] Review logs from failed deployment
- [ ] Identify root cause (code, config, infrastructure)
- [ ] Document in incident report
- [ ] Create GitHub issue with "incident" label
- [ ] Assign to responsible team member

### 4. Fix Validation
- [ ] Fix identified issues in feature branch
- [ ] Run acceptance gates locally
- [ ] Add regression test for failure scenario
- [ ] Update CI/CD to catch this class of failure

### 5. Re-deployment Readiness
- [ ] All acceptance gates pass in staging
- [ ] Regression tests added and passing
- [ ] Incident report completed
- [ ] Team signoff on fix
- [ ] Rollback plan updated if needed

---

## Emergency Contacts

**On-Call Rotation** (Phase 1):
- **Primary**: Jake Tolentino (JT) - All components
- **Backup**: RIM - BIR workflows, database
- **Backup**: CKVC - Finance operations, validation

**Escalation Path**:
1. Check `docs/MONITORING.md` for alert playbooks
2. Execute rollback procedure matching failure type
3. Contact primary on-call via Mattermost #finance-alerts
4. If no response within 30 min, contact backup
5. Document all actions in incident report

---

## Rollback Testing

**Recommendation**: Test rollback procedures quarterly

```bash
# Rollback test schedule
# Q1 2026: Test database schema rollback
# Q2 2026: Test frontend rollback
# Q3 2026: Test full stack rollback
# Q4 2026: Test backend + Edge Functions rollback
```

**Test Procedure**:
1. Deploy to staging environment
2. Execute rollback procedure
3. Verify rollback successful
4. Document any issues or improvements
5. Update rollback procedures if needed

---

**Last Updated**: 2025-12-09
**Next Review**: After first production rollback or quarterly
**Maintainer**: Jake Tolentino (JT)
