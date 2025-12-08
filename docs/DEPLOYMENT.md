# Phase 1 Deployment Runbook

**Target Environment**: Production
**Timeline**: 2-3 hours end-to-end
**Prerequisites**: All Phase 1 acceptance gates pass

---

## Pre-Deployment Checklist

### 1. Environment Validation
```bash
# Verify all required environment variables are set
source ~/.zshrc

# Required variables
echo "Supabase: ${SUPABASE_URL:0:30}... ✓"
echo "DigitalOcean: ${DO_ACCESS_TOKEN:0:15}... ✓"
echo "GitHub: ${GITHUB_TOKEN:0:15}... ✓"
echo "n8n: ${N8N_API_KEY:0:15}... ✓"

# Verify CLI tools installed
supabase --version  # ≥1.0.0
doctl version       # ≥1.90.0
vercel --version    # ≥32.0.0
gh --version        # ≥2.40.0
```

### 2. Run Acceptance Gates
```bash
# Run automated validation (see scripts/validate-phase1.sh)
./scripts/validate-phase1.sh

# Expected output:
# ✅ OCR backend health: P95 = 28s (threshold: ≤30s)
# ✅ Task queue operational: 0 stuck tasks (threshold: 0)
# ✅ DB migrations applied: schema hash match
# ✅ RLS policies enforced: 24/24 tables
# ✅ Visual parity: SSIM mobile=0.98, desktop=0.99
```

### 3. Create Rollback Point
```bash
# Tag current production state
git tag -a rollback/phase1-pre-deploy -m "Pre-Phase 1 deployment rollback point"
git push origin rollback/phase1-pre-deploy

# Save current DigitalOcean deployment IDs
doctl apps list --format ID,Spec.Name > .rollback/do-deployments-$(date +%Y%m%d).txt
```

---

## Deployment Steps

### Step 1: Deploy Database Schema (Supabase)

**Duration**: 15-20 minutes

```bash
# 1. Connect to Supabase project
export SUPABASE_PROJECT_REF=xkxyvboeubffxxbebsll
export POSTGRES_URL="postgresql://postgres.${SUPABASE_PROJECT_REF}:${SUPABASE_DB_PASSWORD}@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"

# 2. Apply medallion schema migrations (in order)
psql "$POSTGRES_URL" -f packages/db/sql/10_medallion_bronze.sql
psql "$POSTGRES_URL" -f packages/db/sql/11_medallion_silver.sql
psql "$POSTGRES_URL" -f packages/db/sql/12_medallion_gold.sql
psql "$POSTGRES_URL" -f packages/db/sql/13_medallion_platinum.sql

# 3. Verify schema deployment
psql "$POSTGRES_URL" -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('bronze', 'silver', 'gold', 'platinum');"
# Expected: 4 rows

# 4. Verify RLS enforcement
psql "$POSTGRES_URL" -c "SELECT schemaname, tablename, rowsecurity FROM pg_tables WHERE schemaname IN ('bronze', 'silver', 'gold', 'platinum') ORDER BY schemaname, tablename;"
# Expected: All tables have rowsecurity = true

# 5. Generate and save schema hash
psql "$POSTGRES_URL" -c "\dt bronze.*; \dt silver.*; \dt gold.*; \dt platinum.*;" | md5sum > .deployment/schema-hash-$(date +%Y%m%d).txt
```

**Rollback Command**:
```bash
# If migration fails, rollback to previous schema
psql "$POSTGRES_URL" -f packages/db/sql/down_migrations/13_down.sql
psql "$POSTGRES_URL" -f packages/db/sql/down_migrations/12_down.sql
psql "$POSTGRES_URL" -f packages/db/sql/down_migrations/11_down.sql
psql "$POSTGRES_URL" -f packages/db/sql/down_migrations/10_down.sql
```

---

### Step 2: Deploy Supabase Edge Functions

**Duration**: 10-15 minutes

```bash
# 1. Deploy task-queue-processor
cd worktree-integration
supabase functions deploy task-queue-processor --project-ref $SUPABASE_PROJECT_REF

# 2. Deploy bir-form-validator
supabase functions deploy bir-form-validator --project-ref $SUPABASE_PROJECT_REF

# 3. Deploy expense-ocr-processor
supabase functions deploy expense-ocr-processor --project-ref $SUPABASE_PROJECT_REF

# 4. Verify deployments
supabase functions list --project-ref $SUPABASE_PROJECT_REF
# Expected: 3 functions listed

# 5. Test Edge Functions
curl -sf "${SUPABASE_URL}/functions/v1/task-queue-processor" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
  -d '{"test": true}' | jq -r '.status'
# Expected: "ok" or task processing result
```

**Rollback Command**:
```bash
# Delete Edge Functions
supabase functions delete task-queue-processor --project-ref $SUPABASE_PROJECT_REF
supabase functions delete bir-form-validator --project-ref $SUPABASE_PROJECT_REF
supabase functions delete expense-ocr-processor --project-ref $SUPABASE_PROJECT_REF
```

---

### Step 3: Deploy n8n Workflows

**Duration**: 10-15 minutes

```bash
# 1. Export workflows from worktree-ppm
cd worktree-ppm/workflows/bir

# 2. Import to n8n production (manual via UI or API)
for workflow in *.json; do
  curl -X POST "${N8N_BASE_URL}/api/v1/workflows/import" \
    -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
    -H "Content-Type: application/json" \
    -d @"$workflow"
done

# 3. Activate all workflows
curl -X GET "${N8N_BASE_URL}/api/v1/workflows" \
  -H "X-N8N-API-KEY: ${N8N_API_KEY}" | jq -r '.data[].id' | while read id; do
    curl -X PATCH "${N8N_BASE_URL}/api/v1/workflows/${id}/activate" \
      -H "X-N8N-API-KEY: ${N8N_API_KEY}"
  done

# 4. Verify workflows active
curl -s "${N8N_BASE_URL}/api/v1/workflows" \
  -H "X-N8N-API-KEY: ${N8N_API_KEY}" | jq -r '.data[] | "\(.name): \(.active)"'
# Expected: 8 workflows, all active=true
```

**Rollback Command**:
```bash
# Deactivate all workflows
curl -X GET "${N8N_BASE_URL}/api/v1/workflows" \
  -H "X-N8N-API-KEY: ${N8N_API_KEY}" | jq -r '.data[].id' | while read id; do
    curl -X PATCH "${N8N_BASE_URL}/api/v1/workflows/${id}/deactivate" \
      -H "X-N8N-API-KEY: ${N8N_API_KEY}"
  done
```

---

### Step 4: Deploy OCR Backend (DigitalOcean App Platform)

**Duration**: 15-20 minutes

```bash
# 1. Update app spec from config
doctl apps update b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9 \
  --spec config/production/ade-ocr-backend.yaml

# 2. Trigger deployment with force rebuild
doctl apps create-deployment b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9 \
  --force-rebuild

# 3. Monitor deployment progress
doctl apps logs b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9 --follow

# 4. Wait for deployment completion (~ 10-15 min)
while true; do
  STATUS=$(doctl apps get b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9 --format ActiveDeployment.Phase --no-header)
  echo "Deployment status: $STATUS"
  if [ "$STATUS" = "ACTIVE" ]; then
    echo "✅ Deployment complete"
    break
  elif [ "$STATUS" = "ERROR" ] || [ "$STATUS" = "SUPERSEDED" ]; then
    echo "❌ Deployment failed: $STATUS"
    exit 1
  fi
  sleep 30
done

# 5. Health check
curl -sf https://ade-ocr-backend-*.ondigitalocean.app/health | jq -r '.status'
# Expected: "ok"
```

**Rollback Command**:
```bash
# Get previous deployment ID
doctl apps list-deployments b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9 --format ID,Phase | head -2 | tail -1 | awk '{print $1}'

# Rollback to previous deployment
PREV_DEPLOYMENT_ID=<ID_FROM_ABOVE>
doctl apps create-deployment b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9 \
  --deployment-id $PREV_DEPLOYMENT_ID
```

---

### Step 5: Deploy Frontend (Vercel)

**Duration**: 5-10 minutes

```bash
# 1. Navigate to UI worktree
cd worktree-ui

# 2. Verify environment variables in Vercel dashboard
# - NEXT_PUBLIC_SUPABASE_URL
# - NEXT_PUBLIC_SUPABASE_ANON_KEY
# - SUPABASE_SERVICE_ROLE_KEY

# 3. Deploy to production
vercel --prod --yes

# 4. Wait for deployment completion
# Vercel will output deployment URL

# 5. Health check
VERCEL_URL=$(vercel ls --prod | grep "worktree-ui" | awk '{print $2}')
curl -sf "https://${VERCEL_URL}" | grep -q "Task Queue Monitor"
# Expected: HTML containing "Task Queue Monitor"

# 6. Visual parity validation
node scripts/snap.js --base-url="https://${VERCEL_URL}" --routes="/,/dashboard/task-queue,/dashboard/bir-status,/dashboard/ocr-confidence"
node scripts/ssim.js --threshold-mobile=0.97 --threshold-desktop=0.98
# Expected: All routes pass thresholds
```

**Rollback Command**:
```bash
# List recent deployments
vercel ls

# Rollback to previous deployment
vercel rollback <PREVIOUS_DEPLOYMENT_URL>
```

---

## Post-Deployment Validation

### 1. End-to-End Smoke Tests

```bash
# Test task queue creation
curl -X POST "https://${VERCEL_URL}/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{"kind":"BIR_FORM_FILING","payload":{"test":true},"priority":5}' | jq -r '.task.id'
# Expected: UUID returned

# Test BIR form creation
curl -X POST "https://${VERCEL_URL}/api/bir" \
  -H "Content-Type: application/json" \
  -d '{
    "form_type":"1601-C",
    "filing_period":"2025-12",
    "filing_deadline":"2026-01-10",
    "agency_name":"TBWA\\SMP",
    "employee_name":"RIM"
  }' | jq -r '.form.id'
# Expected: UUID returned

# Test OCR processing
curl -X POST "https://${VERCEL_URL}/api/ocr" \
  -H "Content-Type: application/json" \
  -d '{
    "expense_id":"'$(uuidgen)'",
    "receipt_url":"https://example.com/receipt.jpg",
    "tenant_id":"test-tenant",
    "workspace_id":"test-workspace"
  }' | jq -r '.result.confidence'
# Expected: Confidence score ≥0.60
```

### 2. Dashboard Accessibility

```bash
# Verify all dashboards load
curl -sf "https://${VERCEL_URL}/" | grep -q "Finance SSC Dashboard"
curl -sf "https://${VERCEL_URL}/dashboard/task-queue" | grep -q "Task Queue Monitor"
curl -sf "https://${VERCEL_URL}/dashboard/bir-status" | grep -q "BIR Status Dashboard"
curl -sf "https://${VERCEL_URL}/dashboard/ocr-confidence" | grep -q "OCR Confidence Metrics"
# Expected: All checks pass
```

### 3. Real-Time Subscriptions

```bash
# Test Supabase Realtime connection
# (Manual test: Open dashboard, create task, verify real-time update)
```

### 4. Monitoring Alerts

```bash
# Send test alert to Mattermost
curl -X POST "$MATTERMOST_WEBHOOK_URL" \
  -d '{"text":"🚀 Phase 1 deployment complete - all systems operational"}' \
  -H "Content-Type: application/json"
# Expected: Message appears in #finance-alerts channel
```

---

## Deployment Verification Checklist

- [ ] **Database**: All 4 schemas deployed (bronze, silver, gold, platinum)
- [ ] **RLS**: All tables enforce row-level security
- [ ] **Edge Functions**: 3 functions deployed and responsive
- [ ] **n8n Workflows**: 8 workflows active
- [ ] **OCR Backend**: Health check passes, P95 ≤30s
- [ ] **Frontend**: All 3 dashboards load, visual parity ≥97%
- [ ] **API Routes**: All 3 routes (tasks, bir, ocr) functional
- [ ] **Real-Time**: Supabase subscriptions working
- [ ] **Monitoring**: Mattermost alerts configured

---

## Rollback Decision Matrix

| Failure Type | Rollback Required | Rollback Steps |
|--------------|-------------------|----------------|
| Database migration fails | ✅ Yes | Run down migrations, restore schema |
| Edge Function deploy fails | ⚠️ Partial | Delete failed functions, keep working ones |
| n8n workflow import fails | ❌ No | Fix workflow JSON, re-import |
| OCR backend deploy fails | ✅ Yes | Rollback to previous DigitalOcean deployment |
| Frontend deploy fails | ✅ Yes | Vercel rollback to previous deployment |
| Visual parity fails | ⚠️ Partial | Fix UI issues, redeploy frontend only |
| Monitoring alerts fail | ❌ No | Fix webhook config, no rollback needed |

---

## Emergency Contacts

**On-Call Rotation** (Phase 1):
- **Primary**: Jake Tolentino (JT) - All components
- **Backup**: RIM - BIR workflows, database
- **Backup**: CKVC - Finance operations, validation

**Escalation Path**:
1. Check `docs/MONITORING.md` for alert playbooks
2. Review `docs/ROLLBACK.md` for rollback procedures
3. Contact primary on-call via Mattermost #finance-alerts
4. If no response within 30 min, contact backup

---

## Post-Deployment Cleanup

```bash
# 1. Remove temporary deployment files
rm -rf .deployment/

# 2. Archive rollback files
mkdir -p .rollback/archive
mv .rollback/do-deployments-*.txt .rollback/archive/

# 3. Update deployment log
echo "$(date +%Y-%m-%d\ %H:%M:%S) - Phase 1 deployed successfully" >> docs/DEPLOYMENT_LOG.md

# 4. Create deployment tag
git tag -a v1.0.0-phase1 -m "Phase 1: PPM + Expense + BIR (Production)"
git push origin v1.0.0-phase1
```

---

**Last Updated**: 2025-12-09
**Next Review**: After Phase 1 deployment
**Maintainer**: Jake Tolentino (JT)
