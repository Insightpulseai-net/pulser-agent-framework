# Production Configuration Templates

This directory contains production-ready configuration templates for Phase 1 deployment.

---

## Files Overview

| File | Purpose | Used By |
|------|---------|---------|
| `ade-ocr-backend.yaml` | DigitalOcean App Platform spec | doctl apps update |
| `supabase.env.example` | Supabase environment variables | Database, Edge Functions |
| `vercel.env.example` | Vercel environment variables | Frontend deployment |
| `n8n.config.json` | n8n workflow engine config | n8n instance |

---

## Security Notice

**⚠️ NEVER commit actual credentials to git**

- All `.env.example` files are templates only
- Copy to `.env.production` and fill in actual values
- Add `.env.production` to `.gitignore` (already done)
- Store secrets in:
  - **Local**: `~/.zshrc` or macOS Keychain
  - **CI/CD**: GitHub Secrets, Vercel Environment Variables, DigitalOcean App Platform Secrets

---

## Usage Instructions

### 1. DigitalOcean OCR Backend

**File**: `ade-ocr-backend.yaml`

**Deployment**:
```bash
# Update app spec
doctl apps update b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9 \
  --spec config/production/ade-ocr-backend.yaml

# Trigger deployment
doctl apps create-deployment b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9 \
  --force-rebuild

# Monitor deployment
doctl apps logs b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9 --follow
```

**Configuration Notes**:
- **Instance Size**: professional-xs (1 vCPU, 1 GB RAM, $12/month)
- **Instance Count**: 2 (for high availability)
- **Health Check**: /health endpoint, 10s interval
- **Alerts**: CPU >80%, Memory >80%, Restart >5

**Environment Variables to Set**:
```bash
# Via DigitalOcean dashboard or CLI
doctl apps update b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9 \
  --env "OPENAI_API_KEY=${OPENAI_API_KEY}" \
  --env "SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}"
```

---

### 2. Supabase Configuration

**File**: `supabase.env.example`

**Setup**:
```bash
# Copy template
cp config/production/supabase.env.example .env.production

# Fill in actual values
nano .env.production

# Source for CLI operations
source .env.production
```

**Required Values**:
- `SUPABASE_PROJECT_REF`: xkxyvboeubffxxbebsll
- `SUPABASE_URL`: https://xkxyvboeubffxxbebsll.supabase.co
- `SUPABASE_ANON_KEY`: Get from https://supabase.com/dashboard/project/xkxyvboeubffxxbebsll/settings/api
- `SUPABASE_SERVICE_ROLE_KEY`: Get from same dashboard
- `SUPABASE_ACCESS_TOKEN`: Get from https://supabase.com/dashboard/account/tokens
- `SUPABASE_DB_PASSWORD`: Your database password

**Database Connections**:
- **Pooler (Port 6543)**: Use for serverless/API routes
- **Direct (Port 5432)**: Use for migrations

**Deployment**:
```bash
# Deploy Edge Functions
supabase functions deploy task-queue-processor --project-ref $SUPABASE_PROJECT_REF
supabase functions deploy bir-form-validator --project-ref $SUPABASE_PROJECT_REF
supabase functions deploy expense-ocr-processor --project-ref $SUPABASE_PROJECT_REF

# Run migrations
psql "$POSTGRES_URL" -f packages/db/sql/10_medallion_bronze.sql
psql "$POSTGRES_URL" -f packages/db/sql/11_medallion_silver.sql
psql "$POSTGRES_URL" -f packages/db/sql/12_medallion_gold.sql
psql "$POSTGRES_URL" -f packages/db/sql/13_medallion_platinum.sql
```

---

### 3. Vercel Frontend

**File**: `vercel.env.example`

**Setup**:
```bash
# Add environment variables via Vercel CLI
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel env add SUPABASE_SERVICE_ROLE_KEY production
vercel env add NEXT_PUBLIC_OCR_ENDPOINT production
vercel env add N8N_BASE_URL production
vercel env add N8N_API_KEY production

# Or via Vercel Dashboard:
# https://vercel.com/[team]/[project]/settings/environment-variables
```

**Deployment**:
```bash
cd worktree-ui
vercel --prod --yes
```

**Environment Variables by Scope**:
- **`NEXT_PUBLIC_*`**: Exposed to browser (public)
- **No prefix**: Server-side only (secrets)

**Feature Flags** (Phase 1 enabled):
- `NEXT_PUBLIC_ENABLE_TASK_QUEUE_DASHBOARD=true`
- `NEXT_PUBLIC_ENABLE_BIR_STATUS_DASHBOARD=true`
- `NEXT_PUBLIC_ENABLE_OCR_CONFIDENCE_DASHBOARD=true`

**Feature Flags** (Phase 1.5 disabled):
- `NEXT_PUBLIC_ENABLE_SRM_SUPPLIERS=false`
- `NEXT_PUBLIC_ENABLE_SRM_RATE_CARDS=false`

---

### 4. n8n Workflow Engine

**File**: `n8n.config.json`

**Setup**:
```bash
# Copy config to n8n deployment directory
scp config/production/n8n.config.json user@n8n-server:/opt/n8n/config.json

# Update database password in config
ssh user@n8n-server
nano /opt/n8n/config.json
# Set N8N_DB_PASSWORD to actual Supabase password

# Restart n8n
sudo systemctl restart n8n
```

**Configuration Notes**:
- **Timezone**: Asia/Manila (PH time)
- **Database**: PostgreSQL on Supabase (schema: n8n)
- **Execution Timeout**: 300s (5 min)
- **Data Retention**: 336 hours (14 days)
- **Max Executions**: 10,000

**Workflow Import**:
```bash
# Import BIR workflows
cd worktree-ppm/workflows/bir

for workflow in *.json; do
  curl -X POST "${N8N_BASE_URL}/api/v1/workflows/import" \
    -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
    -H "Content-Type: application/json" \
    -d @"$workflow"
done

# Activate all workflows
curl -X GET "${N8N_BASE_URL}/api/v1/workflows" \
  -H "X-N8N-API-KEY: ${N8N_API_KEY}" | jq -r '.data[].id' | while read id; do
    curl -X PATCH "${N8N_BASE_URL}/api/v1/workflows/${id}/activate" \
      -H "X-N8N-API-KEY: ${N8N_API_KEY}"
  done
```

---

## Environment Variable Priority

**Resolution Order**:
1. `.env.production` (local development)
2. `~/.zshrc` (shell environment)
3. Platform-specific secrets:
   - DigitalOcean: App Platform Environment Variables
   - Vercel: Environment Variables dashboard
   - Supabase: Vault or CLI environment
   - n8n: config.json or process environment

**Best Practice**:
- **Development**: Use `.env.local` (excluded from git)
- **Staging**: Use `.env.staging` (excluded from git)
- **Production**: Use platform-specific secret management

---

## Validation Checklist

Before deploying:

- [ ] All `.env.example` files copied to `.env.production`
- [ ] All secret values filled in (no `your_..._here` placeholders)
- [ ] Feature flags set correctly (Phase 1 enabled, Phase 1.5+ disabled)
- [ ] Database connection strings tested
- [ ] API keys validated
- [ ] Health check endpoints configured
- [ ] Monitoring alerts enabled
- [ ] Rollback procedures documented

---

## Troubleshooting

### DigitalOcean Deployment Fails
```bash
# Check app logs
doctl apps logs b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9 --tail 100

# Validate app spec
doctl apps spec validate --spec config/production/ade-ocr-backend.yaml

# Check environment variables
doctl apps get b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9 --format Spec.Envs
```

### Supabase Connection Errors
```bash
# Test database connection (pooler)
psql "postgresql://postgres.xkxyvboeubffxxbebsll:PASSWORD@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require" -c "SELECT 1;"

# Test database connection (direct)
psql "postgresql://postgres.xkxyvboeubffxxbebsll:PASSWORD@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require" -c "SELECT 1;"

# Check Edge Function logs
supabase functions logs task-queue-processor --project-ref xkxyvboeubffxxbebsll
```

### Vercel Environment Variables Missing
```bash
# List all environment variables
vercel env ls

# Pull environment variables to local .env
vercel env pull .env.production
```

### n8n Workflow Errors
```bash
# Check n8n logs
ssh user@n8n-server
tail -f /opt/n8n/logs/n8n.log

# Test API access
curl -s "${N8N_BASE_URL}/api/v1/workflows" \
  -H "X-N8N-API-KEY: ${N8N_API_KEY}" | jq -r '.data[].name'
```

---

**Last Updated**: 2025-12-09
**Maintainer**: Jake Tolentino (JT)
