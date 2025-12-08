# AI Workbench Infrastructure Deployment Checklist

Complete step-by-step checklist for deploying InsightPulseAI AI Workbench infrastructure.

## Pre-Deployment (Day 0)

### Prerequisites Verification

- [ ] **DigitalOcean Account**: Active account with payment method
- [ ] **Supabase Account**: Pro plan subscription ($25/month)
- [ ] **Domain Access**: Control over `insightpulseai.net` DNS
- [ ] **API Keys**: Anthropic, OpenAI, Google AI keys ready
- [ ] **Local Tools**: doctl, terraform, kubectl, helm, psql installed

### Environment Setup

```bash
# 1. Authenticate DigitalOcean
doctl auth init

# 2. Set environment variables
cat >> ~/.zshrc <<EOF
export DO_TOKEN=\$(doctl auth list --format Token --no-header)
export SUPABASE_PROJECT_REF="xkxyvboeubffxxbebsll"
export SUPABASE_URL="https://xkxyvboeubffxxbebsll.supabase.co"
export SUPABASE_ANON_KEY="<your-anon-key>"
export SUPABASE_SERVICE_ROLE_KEY="<your-service-role-key>"
export POSTGRES_URL="postgresql://postgres:[password]@aws-1-us-east-1.pooler.supabase.com:6543/postgres"
EOF

source ~/.zshrc
```

- [ ] Environment variables set and verified
- [ ] API tokens stored securely

## Phase 1: DigitalOcean Infrastructure (Day 1, ~2 hours)

### 1.1 Deploy VPC and DOKS Cluster

```bash
cd infra/digitalocean/terraform/

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
do_token                    = "$DO_TOKEN"
supabase_url                = "$SUPABASE_URL"
supabase_service_role_key   = "$SUPABASE_SERVICE_ROLE_KEY"
project_name                = "ai-workbench"
region                      = "sgp1"
environment                 = "production"
EOF

# Initialize and deploy
terraform init
terraform plan
terraform apply -auto-approve
```

**Acceptance Criteria**:
- [ ] Terraform apply completes without errors
- [ ] 3 DOKS nodes in "Ready" state: `kubectl get nodes`
- [ ] VPC created with CIDR 10.10.0.0/16
- [ ] Firewall rules configured
- [ ] Container registry accessible

**Estimated Time**: 20 minutes

### 1.2 Configure kubectl

```bash
# Get cluster credentials
doctl kubernetes cluster kubeconfig save $(terraform output -raw cluster_id)

# Verify connection
kubectl get nodes
kubectl cluster-info
```

**Acceptance Criteria**:
- [ ] kubectl configured with cluster credentials
- [ ] All 3 nodes show "Ready" status
- [ ] Cluster version is 1.29.4

**Estimated Time**: 5 minutes

### 1.3 Create Kubernetes Namespaces

```bash
cd ../kubernetes/

# Apply namespaces
kubectl apply -f namespace.yaml

# Verify
kubectl get namespaces | grep -E "ai-workbench|n8n|litellm|traefik"
```

**Acceptance Criteria**:
- [ ] 7 namespaces created: ai-workbench, n8n, litellm, qdrant, neo4j, langfuse, traefik
- [ ] All namespaces in "Active" status

**Estimated Time**: 2 minutes

### 1.4 Configure Kubernetes Secrets

```bash
# Copy template
cp secrets.yaml.example secrets.yaml

# Edit secrets.yaml (use your editor)
# IMPORTANT: Replace ALL placeholder values

# Apply secrets
kubectl apply -f secrets.yaml

# Verify
kubectl get secrets -A | grep -E "supabase|llm-api|n8n|neo4j|langfuse"
```

**Acceptance Criteria**:
- [ ] secrets.yaml created with real values (NOT committed to Git)
- [ ] 8 secrets created across namespaces
- [ ] No error messages from kubectl apply

**Estimated Time**: 10 minutes

### 1.5 Deploy Traefik Ingress Controller

```bash
cd ../

# Add Helm repo
helm repo add traefik https://traefik.github.io/charts
helm repo update

# Install Traefik
helm install traefik traefik/traefik \
  --namespace traefik \
  --values helm-values/traefik.yaml \
  --create-namespace

# Wait for LoadBalancer IP (this may take 2-5 minutes)
kubectl get svc -n traefik --watch
```

**Acceptance Criteria**:
- [ ] Traefik deployed successfully
- [ ] LoadBalancer IP assigned (EXTERNAL-IP column)
- [ ] Traefik pods running: `kubectl get pods -n traefik`

**Save LoadBalancer IP**: ____________________

**Estimated Time**: 10 minutes

### 1.6 Configure DNS

**Action Required**: Update DNS records at your registrar (e.g., Cloudflare, Route 53)

```
Type: A
Name: *.insightpulseai.net
Value: <LoadBalancer-IP from above>
TTL: 300 (5 minutes)
```

**Acceptance Criteria**:
- [ ] DNS A record created
- [ ] DNS propagation complete (check with `dig n8n.insightpulseai.net`)
- [ ] All subdomains resolve to LoadBalancer IP

**Estimated Time**: 15 minutes (including DNS propagation)

### 1.7 Deploy n8n Workflow Automation

```bash
# Add Helm repo
helm repo add 8gears https://8gears.container-registry.com/chartrepo/library
helm repo update

# Install n8n
helm install n8n 8gears/n8n \
  --namespace n8n \
  --values helm-values/n8n.yaml \
  --create-namespace

# Wait for deployment
kubectl rollout status deployment/n8n -n n8n

# Verify
kubectl get pods -n n8n
```

**Acceptance Criteria**:
- [ ] n8n deployed successfully
- [ ] n8n pods running (2 replicas)
- [ ] n8n accessible at https://n8n.insightpulseai.net
- [ ] SSL certificate issued (may take 2-3 minutes)

**Estimated Time**: 15 minutes

**End of Phase 1 - Estimated Total Time: ~2 hours**

---

## Phase 2: Supabase Database Schema (Day 1, ~30 minutes)

### 2.1 Run Metadata Schema Migration

```bash
cd ../../infra/supabase/migrations/

# Run migration
psql "$POSTGRES_URL" -f 001_metadata_schema.sql

# Verify
psql "$POSTGRES_URL" -c "\dt ip_workbench.*"
```

**Acceptance Criteria**:
- [ ] Migration completes without errors
- [ ] 18 tables created in ip_workbench schema
- [ ] 4 domains seeded (Finance, Retail, Creative, HR)

**Estimated Time**: 10 minutes

### 2.2 Run Medallion Schemas Migration

```bash
# Run migration
psql "$POSTGRES_URL" -f 002_medallion_schemas.sql

# Verify
psql "$POSTGRES_URL" -c "\dt bronze.*"
psql "$POSTGRES_URL" -c "\dt silver.*"
psql "$POSTGRES_URL" -c "\dt gold.*"
psql "$POSTGRES_URL" -c "\dt platinum.*"
```

**Acceptance Criteria**:
- [ ] Migration completes without errors
- [ ] Bronze: 2 tables (scout_transactions_raw, expenses_raw)
- [ ] Silver: 2 tables (scout_transactions, expenses)
- [ ] Gold: 2 tables (finance_expenses, scout_sales)
- [ ] Platinum: 2 materialized views
- [ ] Tables registered in ip_workbench.tables catalog

**Estimated Time**: 10 minutes

### 2.3 Enable RLS Policies

```bash
cd ../rls-policies/

# Apply RLS policies
psql "$POSTGRES_URL" -f workbench_policies.sql

# Verify
psql "$POSTGRES_URL" -c "SELECT schemaname, tablename, policyname FROM pg_policies WHERE schemaname = 'ip_workbench' LIMIT 10;"
```

**Acceptance Criteria**:
- [ ] RLS enabled on all tables
- [ ] 30+ policies created
- [ ] Helper functions created (get_user_role, is_admin, is_engineer_or_admin, is_service)

**Estimated Time**: 5 minutes

### 2.4 Create Test Users

```bash
# Via Supabase dashboard: Authentication → Users → Invite user
# Create 3 test users:
# - viewer@test.com (role: viewer)
# - engineer@test.com (role: engineer)
# - admin@test.com (role: admin)
```

**Acceptance Criteria**:
- [ ] 3 test users created
- [ ] User metadata includes {"role": "<role>"}
- [ ] Email confirmation sent (if enabled)

**Estimated Time**: 5 minutes

**End of Phase 2 - Estimated Total Time: ~30 minutes**

---

## Phase 3: LiteLLM Gateway (Day 1, ~45 minutes)

### 3.1 Build Docker Image

```bash
cd ../../../services/litellm-proxy/

# Build image
docker build -t registry.digitalocean.com/ai-workbench-registry/litellm-gateway:latest .

# Test locally
docker run -p 8080:8080 \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  -e LITELLM_MASTER_KEY="sk-test-12345" \
  registry.digitalocean.com/ai-workbench-registry/litellm-gateway:latest &

# Wait 10 seconds for startup
sleep 10

# Test health endpoint
curl http://localhost:8080/health

# Stop container
docker stop $(docker ps -q --filter ancestor=registry.digitalocean.com/ai-workbench-registry/litellm-gateway:latest)
```

**Acceptance Criteria**:
- [ ] Docker image builds successfully
- [ ] Local test returns {"status": "ok"}
- [ ] No errors in docker logs

**Estimated Time**: 15 minutes

### 3.2 Push to Container Registry

```bash
# Login to DigitalOcean registry
doctl registry login

# Push image
docker push registry.digitalocean.com/ai-workbench-registry/litellm-gateway:latest
```

**Acceptance Criteria**:
- [ ] Image pushed successfully
- [ ] Image visible in DigitalOcean registry dashboard

**Estimated Time**: 10 minutes

### 3.3 Deploy to DOKS

```bash
# Create secrets (if not already created)
kubectl create secret generic llm-api-keys \
  --namespace=litellm \
  --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  --from-literal=GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  --from-literal=LITELLM_MASTER_KEY="sk-$(openssl rand -hex 16)" \
  --dry-run=client -o yaml | kubectl apply -f -

# Deploy
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml

# Wait for rollout
kubectl rollout status deployment/litellm-gateway -n litellm

# Verify
kubectl get pods -n litellm
kubectl get ingress -n litellm
```

**Acceptance Criteria**:
- [ ] 3 LiteLLM pods running
- [ ] Redis pod running
- [ ] Ingress configured
- [ ] SSL certificate issued

**Estimated Time**: 15 minutes

### 3.4 Verify Gateway

```bash
# Wait for SSL (may take 2-3 minutes)
sleep 180

# Test health endpoint
curl https://litellm.insightpulseai.net/health

# Test model routing
curl https://litellm.insightpulseai.net/v1/chat/completions \
  -H "Authorization: Bearer $(kubectl get secret llm-api-keys -n litellm -o jsonpath='{.data.LITELLM_MASTER_KEY}' | base64 -d)" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Test"}]}'
```

**Acceptance Criteria**:
- [ ] Health check returns {"status": "ok"}
- [ ] Test completion returns valid response
- [ ] No errors in logs: `kubectl logs -f deployment/litellm-gateway -n litellm`

**Estimated Time**: 5 minutes

**End of Phase 3 - Estimated Total Time: ~45 minutes**

---

## Phase 4: n8n Workflows (Day 2, ~30 minutes)

### 4.1 Access n8n UI

```bash
# Open n8n
open https://n8n.insightpulseai.net

# Login with credentials from secrets.yaml
# Username: admin
# Password: <N8N_BASIC_AUTH_PASSWORD>
```

**Acceptance Criteria**:
- [ ] n8n UI loads successfully
- [ ] Authentication successful

**Estimated Time**: 2 minutes

### 4.2 Configure Credentials

#### Supabase PostgreSQL

1. Credentials → Add Credential → Postgres
2. Name: `Supabase PostgreSQL`
3. Configuration:
   - Host: `aws-1-us-east-1.pooler.supabase.com`
   - Database: `postgres`
   - User: `postgres`
   - Password: `<from SUPABASE_SERVICE_ROLE_KEY>`
   - Port: `6543`
   - SSL Mode: `require`
4. Save → Test Connection

**Acceptance Criteria**:
- [ ] Credential saved
- [ ] Connection test successful

#### Mattermost Webhook

1. Credentials → Add Credential → HTTP Request
2. Name: `Mattermost Webhook`
3. URL: `https://mattermost.insightpulseai.net/hooks/...`
4. Method: `POST`
5. Headers: `Content-Type: application/json`

**Acceptance Criteria**:
- [ ] Credential saved

**Estimated Time**: 10 minutes

### 4.3 Import Workflows

```bash
# Via n8n UI
# 1. Workflows → Import from File
# 2. Select workflows/expense-approval.json
# 3. Repeat for workflows/pipeline-trigger.json
```

**Acceptance Criteria**:
- [ ] 2 workflows imported
- [ ] All nodes have credentials assigned
- [ ] No error markers on nodes

**Estimated Time**: 10 minutes

### 4.4 Activate Workflows

1. Select "Expense Approval Workflow"
2. Toggle "Active" switch
3. Note webhook URL
4. Repeat for "Pipeline Trigger Workflow"

**Acceptance Criteria**:
- [ ] Both workflows active
- [ ] Webhook URLs accessible

**Save Webhook URLs**:
- Expense Approval: ____________________
- Pipeline Trigger: ____________________

**Estimated Time**: 5 minutes

### 4.5 Test Workflows

```bash
# Test expense approval workflow
curl -X POST https://n8n.insightpulseai.net/webhook/expense-approval \
  -H "Content-Type: application/json" \
  -d '{"expense_id": "00000000-0000-0000-0000-000000000000"}'

# Check execution in n8n UI: Executions → View details
```

**Acceptance Criteria**:
- [ ] Workflow executes successfully
- [ ] All nodes show green checkmarks
- [ ] Response received

**Estimated Time**: 3 minutes

**End of Phase 4 - Estimated Total Time: ~30 minutes**

---

## Phase 5: Verification & Testing (Day 2, ~1 hour)

### 5.1 Infrastructure Health Check

```bash
# Check all pods
kubectl get pods -A

# Check services
kubectl get svc -A

# Check ingresses
kubectl get ingress -A

# Check certificates
kubectl get certificate -A
```

**Acceptance Criteria**:
- [ ] All pods in "Running" state
- [ ] All services have ClusterIP or LoadBalancer IP
- [ ] All ingresses have HTTPS enabled
- [ ] All certificates in "Ready" state

**Estimated Time**: 10 minutes

### 5.2 Database Verification

```bash
# Check table counts
psql "$POSTGRES_URL" <<EOF
SELECT
    schemaname,
    COUNT(*) as table_count
FROM pg_tables
WHERE schemaname IN ('ip_workbench', 'bronze', 'silver', 'gold', 'platinum')
GROUP BY schemaname;
EOF

# Check RLS policies
psql "$POSTGRES_URL" -c "SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'ip_workbench';"

# Test query execution
psql "$POSTGRES_URL" -c "SELECT * FROM ip_workbench.domains;"
```

**Acceptance Criteria**:
- [ ] ip_workbench: 18 tables
- [ ] bronze: 2 tables
- [ ] silver: 2 tables
- [ ] gold: 2 tables
- [ ] platinum: 2 materialized views
- [ ] 30+ RLS policies
- [ ] 4 domains returned

**Estimated Time**: 10 minutes

### 5.3 LiteLLM Gateway Test

```bash
# Get master key
LITELLM_KEY=$(kubectl get secret llm-api-keys -n litellm -o jsonpath='{.data.LITELLM_MASTER_KEY}' | base64 -d)

# Test Claude Sonnet
curl https://litellm.insightpulseai.net/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4.5",
    "messages": [{"role": "user", "content": "Generate SQL for top 5 vendors by expense amount"}],
    "temperature": 0.7
  }'

# Test fallback
curl https://litellm.insightpulseai.net/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "What is 2+2?"}]
  }'
```

**Acceptance Criteria**:
- [ ] Claude Sonnet returns valid SQL
- [ ] GPT-4o-mini returns correct answer
- [ ] Langfuse traces visible (if configured)

**Estimated Time**: 10 minutes

### 5.4 n8n Workflow Test

```bash
# Test expense approval (auto-approve)
curl -X POST https://n8n.insightpulseai.net/webhook/expense-approval \
  -H "Content-Type: application/json" \
  -d '{"expense_id": "123e4567-e89b-12d3-a456-426614174000", "amount": 1000}'

# Test expense approval (requires approval)
curl -X POST https://n8n.insightpulseai.net/webhook/expense-approval \
  -H "Content-Type: application/json" \
  -d '{"expense_id": "123e4567-e89b-12d3-a456-426614174001", "amount": 10000}'
```

**Acceptance Criteria**:
- [ ] Auto-approve workflow returns {"status": "success"}
- [ ] Manual approval workflow returns {"status": "pending"}
- [ ] Mattermost notification received (if webhook configured)

**Estimated Time**: 10 minutes

### 5.5 End-to-End Test

Create a simple pipeline via UI (placeholder - UI not built yet):

```bash
# Insert test pipeline
psql "$POSTGRES_URL" <<EOF
INSERT INTO ip_workbench.pipelines (name, description, definition, owner, domain_id, enabled)
VALUES (
    'Test Pipeline',
    'End-to-end test pipeline',
    '{"nodes": [{"id": "1", "type": "bronze", "data": {"label": "Test", "sql": "SELECT 1 as test"}}], "edges": []}'::jsonb,
    (SELECT id FROM auth.users WHERE email = 'admin@test.com'),
    (SELECT id FROM ip_workbench.domains WHERE name = 'Finance'),
    true
) RETURNING id;
EOF

# Trigger pipeline (copy ID from above)
curl -X POST https://n8n.insightpulseai.net/webhook/pipeline-trigger \
  -H "Content-Type: application/json" \
  -d '{"pipeline_id": "<pipeline-id-from-above>"}'
```

**Acceptance Criteria**:
- [ ] Pipeline created successfully
- [ ] Webhook returns job_run_id
- [ ] Job run visible in ip_workbench.job_runs table

**Estimated Time**: 10 minutes

### 5.6 Security Verification

```bash
# Test RLS policies
psql "$POSTGRES_URL" <<EOF
-- Test viewer can read tables
SET LOCAL role TO 'authenticated';
SET LOCAL request.jwt.claims TO '{"sub": "<viewer-user-uuid>"}';
SELECT * FROM ip_workbench.tables LIMIT 1;

-- Test viewer cannot delete tables (should fail)
DELETE FROM ip_workbench.tables WHERE id = '<some-uuid>';
EOF

# Verify secrets not exposed
kubectl get secrets -A -o json | grep -i "password\|key\|token" | wc -l
# Should return 0 (no secrets exposed in plaintext)
```

**Acceptance Criteria**:
- [ ] Viewer can read tables
- [ ] Viewer cannot delete tables (error returned)
- [ ] No secrets exposed in kubectl output

**Estimated Time**: 10 minutes

**End of Phase 5 - Estimated Total Time: ~1 hour**

---

## Post-Deployment (Day 2)

### Documentation

- [ ] Update DNS records in project wiki
- [ ] Document LoadBalancer IP
- [ ] Save n8n webhook URLs
- [ ] Save LiteLLM master key (secure storage)
- [ ] Document test user credentials

### Monitoring Setup

- [ ] Configure Prometheus (optional)
- [ ] Setup Grafana dashboards (optional)
- [ ] Enable DigitalOcean monitoring
- [ ] Configure Supabase alerts

### Backup Verification

- [ ] Verify Supabase automatic backups enabled
- [ ] Test Velero backup/restore (optional)
- [ ] Document backup procedures

### Team Handoff

- [ ] Share deployment documentation
- [ ] Provide access credentials (secure channel)
- [ ] Schedule knowledge transfer session
- [ ] Create runbook for common operations

---

## Success Criteria Summary

**Infrastructure**:
- [x] DOKS cluster with 3 nodes running
- [x] Traefik ingress with SSL
- [x] n8n deployed and accessible
- [x] LiteLLM gateway operational

**Database**:
- [x] 18 metadata tables in ip_workbench schema
- [x] Medallion schemas (Bronze/Silver/Gold/Platinum)
- [x] 30+ RLS policies active
- [x] Test users created

**Services**:
- [x] LiteLLM health check passing
- [x] n8n workflows active
- [x] All services accessible via HTTPS
- [x] SSL certificates issued

**Testing**:
- [x] Database queries execute successfully
- [x] LiteLLM model routing works
- [x] n8n workflows trigger and execute
- [x] RLS policies enforce correctly

---

## Troubleshooting

### Common Issues

**DNS not resolving**:
```bash
# Check DNS propagation
dig n8n.insightpulseai.net

# If not resolving, verify:
# 1. A record created at registrar
# 2. TTL expired (wait 5-10 minutes)
# 3. LoadBalancer IP correct
```

**SSL certificate not issued**:
```bash
# Check cert-manager logs
kubectl logs -n traefik -l app.kubernetes.io/name=traefik | grep acme

# Force certificate renewal
kubectl delete certificate <cert-name> -n <namespace>
```

**Pod not starting**:
```bash
# Describe pod
kubectl describe pod <pod-name> -n <namespace>

# Check events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Check secrets
kubectl get secrets -n <namespace>
```

---

## Estimated Total Time

| Phase | Duration |
|-------|----------|
| Pre-Deployment | 30 min |
| Phase 1: DigitalOcean | 2 hours |
| Phase 2: Supabase | 30 min |
| Phase 3: LiteLLM | 45 min |
| Phase 4: n8n | 30 min |
| Phase 5: Verification | 1 hour |
| Post-Deployment | 30 min |
| **Total** | **~6 hours** |

**Recommended Schedule**: Deploy over 2 days

- **Day 1**: Phases 1-3 (Infrastructure, Database, LiteLLM)
- **Day 2**: Phases 4-5 (n8n, Verification, Handoff)

---

**Status**: Ready for deployment
**Last Updated**: 2025-12-08
**Owner**: InsightPulseAI Infrastructure Agent
