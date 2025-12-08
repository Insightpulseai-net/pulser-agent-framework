# InsightPulseAI AI Workbench - Complete Stack

Production-ready self-hosted AI Workbench with infrastructure, data layer, agent orchestration, and Next.js UI.

## Overview

This repository contains:

### Infrastructure Layer
- **DigitalOcean DOKS cluster** (Kubernetes) for microservices
- **Supabase PostgreSQL** for metadata and data storage
- **LiteLLM Gateway** for multi-model AI routing
- **n8n** for workflow automation
- **Traefik** for ingress and SSL management

### Data Layer (Medallion Architecture)
```
External Sources (Google Drive, CSV, Webhooks)
    ↓
Bronze Layer (Raw JSONB ingestion)
    ↓ dbt run --models bronze
Silver Layer (Validated, schema-enforced)
    ↓ dbt run --models silver
Gold Layer (Business marts, aggregated)
    ↓ dbt run --models gold
Platinum Layer (AI features, embeddings)
    ↓
AI Workbench (Genie, Agents, Dashboards)
```

### Agent Layer (Multi-Agent Orchestration)
```
┌─────────────────────────────────────────────────────────────┐
│                    AI Workbench Frontend                     │
│              (Next.js + Material Web)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 Agent Runtime (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Research   │  │   Expense    │  │ Finance SSC  │      │
│  │    Agent     │  │  Classifier  │  │    Agent     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Qdrant     │ │  Langfuse    │ │   LiteLLM    │
│  (Vectors)   │ │ (Observ.)    │ │  (Gateway)   │
└──────────────┘ └──────────────┘ └──────────────┘
```

## Directory Structure

```
archi-agent-framework/
├── spec-kit/                   # Spec-Driven Development (SDD) bundle
│   └── spec/ai-workbench/
│       ├── constitution.md     # System values and constraints
│       ├── prd.md             # Product Requirements Document
│       ├── plan.md            # Implementation plan
│       └── tasks.md           # Task breakdown
│
├── infra/                     # Infrastructure Layer
│   ├── digitalocean/
│   │   ├── terraform/         # DOKS cluster, VPC, firewall
│   │   └── kubernetes/        # Namespaces, secrets, network policies
│   ├── supabase/
│   │   ├── migrations/        # Metadata + Medallion schemas
│   │   └── rls-policies/      # Row-Level Security policies
│   └── helm-values/           # Traefik, n8n configs
│
├── services/                  # Microservices
│   ├── litellm-proxy/         # Multi-model AI gateway
│   ├── n8n/                   # Workflow automation
│   └── agent-runtime/         # FastAPI agent runtime (agent-layer)
│
├── data-layer/                # Medallion Architecture
│   ├── dbt-workbench/         # Bronze → Silver → Gold → Platinum
│   ├── airflow/               # DAG orchestration
│   ├── n8n-etl/               # Real-time workflows
│   ├── schemas/               # Schema documentation
│   └── quality/               # Data quality framework
│
├── agent-layer/               # Multi-Agent Orchestration
│   ├── langgraph-agents/      # Research, Expense, Finance SSC agents
│   ├── qdrant/                # Vector search
│   ├── langfuse/              # Observability
│   ├── safety/                # Safety harnesses
│   └── bindings/              # Agent → Gold schema bindings
│
└── packages/                  # Experience Layer (Next.js UI)
    └── web/                   # AI Workbench frontend
```

## Quick Start

### Prerequisites

**Required Tools**:
```bash
# macOS
brew install doctl terraform kubectl helm postgresql python3 node

# Authenticate with DigitalOcean
doctl auth init

# Environment Variables
export DO_TOKEN=$(doctl auth list --format Token --no-header)
export SUPABASE_URL="https://xkxyvboeubffxxbebsll.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="<your-key>"
export POSTGRES_URL="postgresql://postgres:[password]@aws-1-us-east-1.pooler.supabase.com:6543/postgres"
```

**Python/Node Requirements**:
- Python 3.11+ (for dbt, Airflow, agent runtime)
- Node.js 20+ (for Next.js UI, n8n workflows)
- dbt-postgres, Apache Airflow 2.8+

### Deployment Sequence

**Total Time**: ~120 minutes (Infrastructure 75min + Data Layer 25min + Agent Layer 20min)

---

### 1. Infrastructure Layer (75 minutes)

#### 1.1 DigitalOcean DOKS Cluster (20 min)

```bash
cd infra/digitalocean/terraform/
terraform init && terraform plan && terraform apply

# Get credentials
doctl kubernetes cluster kubeconfig save $(terraform output -raw cluster_id)
kubectl get nodes  # Verify 3 nodes running
```

#### 1.2 Kubernetes Namespaces & Secrets (5 min)

```bash
cd ../kubernetes/
kubectl apply -f namespace.yaml

cp secrets.yaml.example secrets.yaml
# Edit with real values: SUPABASE_KEY, LITELLM_KEY, N8N_PASSWORD
kubectl apply -f secrets.yaml
```

#### 1.3 Traefik Ingress Controller (10 min)

```bash
helm repo add traefik https://traefik.github.io/charts
helm install traefik traefik/traefik \
  --namespace traefik \
  --values ../helm-values/traefik.yaml \
  --create-namespace

kubectl get svc -n traefik --watch  # Wait for LoadBalancer IP
# Configure DNS: *.insightpulseai.net → <LoadBalancer-IP>
```

#### 1.4 n8n Workflow Automation (10 min)

```bash
helm repo add 8gears https://8gears.container-registry.com/chartrepo/library
helm install n8n 8gears/n8n \
  --namespace n8n \
  --values ../helm-values/n8n.yaml \
  --create-namespace

# Access: https://n8n.insightpulseai.net
```

#### 1.5 Supabase Database Schemas (15 min)

```bash
cd ../../supabase/migrations/

# Run metadata schema (18 tables)
psql "$POSTGRES_URL" -f 001_metadata_schema.sql

# Run medallion schemas (Bronze/Silver/Gold/Platinum)
psql "$POSTGRES_URL" -f 002_medallion_schemas.sql

# Enable RLS policies
cd ../rls-policies/
psql "$POSTGRES_URL" -f workbench_policies.sql

# Verify
psql "$POSTGRES_URL" -c "\dt ip_workbench.*"
psql "$POSTGRES_URL" -c "\dn scout"
```

#### 1.6 LiteLLM Gateway (15 min)

```bash
cd ../../../services/litellm-proxy/

# Build and push
docker build -t registry.digitalocean.com/ai-workbench-registry/litellm-gateway:latest .
doctl registry login
docker push registry.digitalocean.com/ai-workbench-registry/litellm-gateway:latest

# Deploy to DOKS
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml

# Verify
kubectl get pods -n litellm
curl https://litellm.insightpulseai.net/health
```

---

### 2. Data Layer (25 minutes)

#### 2.1 Configure dbt (5 min)

```bash
cd ../../data-layer/dbt-workbench

# Install dbt
pip install dbt-postgres dbt-utils

# Configure profiles
cp profiles.yml.example ~/.dbt/profiles.yml
nano ~/.dbt/profiles.yml  # Add POSTGRES_URL, credentials

# Test connection
dbt debug
```

#### 2.2 Deploy dbt Models (10 min)

```bash
# Install dependencies
dbt deps

# Run Bronze → Silver → Gold → Platinum
dbt run --models bronze
dbt run --models silver
dbt run --models gold
dbt run --models platinum

# Run tests (must pass ≥80% Silver, 100% Gold)
dbt test
```

#### 2.3 Setup Airflow DAGs (10 min)

```bash
cd ../airflow

# Install Airflow
pip install apache-airflow==2.8.0 apache-airflow-providers-postgres

# Initialize Airflow DB
airflow db init

# Copy DAGs
cp dags/*.py ~/airflow/dags/

# Start Airflow (background)
airflow webserver -D
airflow scheduler -D

# Verify DAGs
airflow dags list
# Expected: scout_ingestion_dag, scout_transformation_dag, data_quality_dag
```

---

### 3. Agent Layer (20 minutes)

#### 3.1 Deploy Qdrant Vector Database (5 min)

```bash
cd ../../agent-layer/qdrant
docker-compose up -d

# Verify
curl http://localhost:6333/healthz
```

#### 3.2 Deploy Langfuse Observability (5 min)

```bash
cd ../langfuse
docker-compose up -d

# Access: http://localhost:3000
# Create account and get API keys
```

#### 3.3 Deploy Agent Runtime (10 min)

```bash
cd ../services/agent-runtime

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export QDRANT_URL="http://localhost:6333"
export LANGFUSE_URL="http://localhost:3000"
export LANGFUSE_PUBLIC_KEY="<from-langfuse-ui>"
export LANGFUSE_SECRET_KEY="<from-langfuse-ui>"
export LITELLM_URL="https://litellm.insightpulseai.net"
export SUPABASE_URL="https://xkxyvboeubffxxbebsll.supabase.co"

# Start FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Verify
curl http://localhost:8000/health
```

#### 3.4 Ingest Knowledge Base to Qdrant (optional)

```bash
cd ../../qdrant/ingest

# Chunk documents
python document_chunker.py --input ../../docs/ --output chunks.json

# Generate embeddings
python embedding_generator.py --input chunks.json --output embeddings.json

# Upload to Qdrant
# (embeddings automatically uploaded via Qdrant SDK)
```

---

### 4. Next.js UI (Experience Layer)

```bash
cd ../../packages/web

# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local with Supabase and Agent Runtime URLs

# Run dev server
npm run dev

# Access: http://localhost:3000
```

---

### Total Deployment Time

- **Infrastructure**: 75 minutes
- **Data Layer**: 25 minutes
- **Agent Layer**: 20 minutes
- **Experience Layer**: 5 minutes
- **Total**: ~125 minutes

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DigitalOcean Cloud                        │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              DOKS Cluster (Kubernetes)             │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────┐  │    │
│  │  │   Traefik   │  │   LiteLLM    │  │   n8n    │  │    │
│  │  │  (Ingress)  │→ │   Gateway    │  │(Workflows)│  │    │
│  │  └─────────────┘  └──────────────┘  └──────────┘  │    │
│  │         ↓                  ↓              ↓        │    │
│  │  ┌─────────────────────────────────────────────┐  │    │
│  │  │         AI Workbench Services               │  │    │
│  │  │  (Next.js, Agent Runtime, Guardian)         │  │    │
│  │  └─────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐                    │
│  │  App Platform  │  │  App Platform  │                    │
│  │  (OCR Backend) │  │ (Expense API)  │                    │
│  └────────────────┘  └────────────────┘                    │
│                                                              │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ↓
                    ┌──────────────────────┐
                    │    Supabase Cloud    │
                    │                      │
                    │  ┌────────────────┐  │
                    │  │  PostgreSQL 15 │  │
                    │  │  (Metadata +   │  │
                    │  │   Medallion)   │  │
                    │  └────────────────┘  │
                    │                      │
                    │  ┌────────────────┐  │
                    │  │   Supabase     │  │
                    │  │   Storage      │  │
                    │  └────────────────┘  │
                    └──────────────────────┘
```

## Service Endpoints

| Service | URL | Auth | Status |
|---------|-----|------|--------|
| **Traefik Dashboard** | https://traefik.insightpulseai.net/dashboard | Basic Auth | Port-forward only |
| **n8n** | https://n8n.insightpulseai.net | Basic Auth | Production |
| **LiteLLM** | https://litellm.insightpulseai.net | API Key | Production |
| **Supabase** | https://xkxyvboeubffxxbebsll.supabase.co | JWT | Production |
| **OCR Backend** | Output from Terraform | None | Production |
| **Expense API** | Output from Terraform | API Key | Production |

## Cost Estimate

### Monthly Costs (Production)

| Resource | Spec | Cost (USD) |
|----------|------|------------|
| **DOKS Cluster** | 3× s-4vcpu-8gb | $120 |
| **App Platform (OCR)** | 2× professional-xs | $24 |
| **App Platform (Expense)** | 2× professional-xs | $24 |
| **Container Registry** | Basic (5 repos, 500MB) | $5 |
| **Spaces** | 500MB storage + bandwidth | $5 |
| **Load Balancer** | 1× LB | $12 |
| **Supabase** | Pro plan | $25 |
| **LLM API Costs** | Variable (~100 requests/day) | ~$50 |
| **Total** | | **~$265/month** |

### Cost Optimization

- **Autoscaling**: DOKS nodes scale down during off-peak
- **Spot instances**: Use App Platform for batch jobs
- **LLM caching**: Redis reduces duplicate API calls (~30% savings)
- **Supabase pooler**: Connection pooling reduces database costs

## Monitoring

### Health Checks

```bash
# Check all services
kubectl get pods -A

# Traefik
curl https://traefik.insightpulseai.net/ping

# n8n
curl https://n8n.insightpulseai.net/healthz

# LiteLLM
curl https://litellm.insightpulseai.net/health

# Supabase
psql "$POSTGRES_URL" -c "SELECT version();"
```

### View Logs

```bash
# Traefik
kubectl logs -f deployment/traefik -n traefik

# n8n
kubectl logs -f deployment/n8n -n n8n

# LiteLLM
kubectl logs -f deployment/litellm-gateway -n litellm

# App Platform
doctl apps logs <app-id> --follow
```

### Metrics

```bash
# Prometheus metrics (LiteLLM)
curl https://litellm.insightpulseai.net:9090/metrics

# Kubernetes resource usage
kubectl top nodes
kubectl top pods -A
```

## Security

### Secrets Management

- **Never commit secrets to Git**: Use `secrets.yaml.example` template
- **Rotate API keys**: Every 90 days
- **Use RBAC**: Kubernetes role-based access control
- **Enable RLS**: Supabase Row-Level Security policies
- **SSL/TLS**: Enforce HTTPS for all services

### Firewall Rules

- **Ingress**: 443 (HTTPS), 80 (HTTP → 443 redirect)
- **Egress**: 443 (HTTPS), 5432 (PostgreSQL), 6543 (Supabase pooler), 6333 (Qdrant)

### Network Policies

```bash
# Apply network policies (optional)
kubectl apply -f infra/digitalocean/kubernetes/network-policies.yaml
```

## Backup & Disaster Recovery

### Database Backups

- **Supabase**: Automatic daily backups (7-day retention)
- **Manual backups**: `pg_dump "$POSTGRES_URL" > backup.sql`

### DOKS Backups

```bash
# Install Velero
helm install velero vmware-tanzu/velero \
  --namespace velero \
  --set-file credentials.secretContents.cloud=./velero-credentials

# Create backup
velero backup create workbench-backup --include-namespaces ai-workbench,n8n,litellm

# Restore
velero restore create --from-backup workbench-backup
```

### Recovery Time Objectives

- **RTO** (Recovery Time): <1 hour for critical services
- **RPO** (Recovery Point): <1 day for database, <1 hour for DOKS

## Troubleshooting

### Common Issues

#### Pods Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# Check image pull
kubectl get events -n <namespace> | grep -i error

# Verify secrets
kubectl get secrets -n <namespace>
```

#### SSL Certificate Issues

```bash
# Check cert-manager
kubectl get certificate -A

# Verify Let's Encrypt challenge
kubectl logs -n traefik -l app.kubernetes.io/name=traefik | grep acme
```

#### Database Connection Issues

```bash
# Test direct connection
psql "$POSTGRES_URL" -c "SELECT 1;"

# Check pooler mode
psql "$POSTGRES_URL" -c "SHOW pool_mode;"

# Use direct connection (port 5432) if pooler fails
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/deploy-infrastructure.yml
name: Deploy to DOKS

on:
  push:
    branches: [main]
    paths: ['infrastructure/**', 'k8s/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install doctl
        uses: digitalocean/action-doctl@v2
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}

      - name: Configure kubectl
        run: doctl kubernetes cluster kubeconfig save ${{ secrets.CLUSTER_ID }}

      - name: Deploy services
        run: kubectl apply -f k8s/
```

---

# Data Layer

Production-grade data orchestration with dbt, Airflow, and n8n integration.

## Prerequisites

- PostgreSQL 15+ (Supabase)
- Python 3.11+
- dbt-postgres
- Apache Airflow 2.8+
- n8n (self-hosted or cloud)

## Setup

```bash
# 1. Clone repository
cd /Users/tbwa/archi-agent-framework/worktree/data-layer

# 2. Install dbt
pip install dbt-postgres dbt-utils

# 3. Configure profiles
cp dbt-workbench/profiles.yml.example ~/.dbt/profiles.yml
nano ~/.dbt/profiles.yml

# 4. Set environment variables
export SUPABASE_HOST=aws-1-us-east-1.pooler.supabase.com
export SUPABASE_PORT=6543
export POSTGRES_USER=postgres.xkxyvboeubffxxbebsll
export POSTGRES_PASSWORD=your_password
export POSTGRES_DB=postgres

# 5. Test connection
cd dbt-workbench
dbt debug

# 6. Install dependencies
dbt deps

# 7. Run first transformation
dbt run --models bronze
```

### First Run

```bash
# Run full pipeline
dbt run

# Run tests
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

## Data Models

### Bronze Layer (Raw)

**Tables**: 2
**Purpose**: Raw ingestion from all sources
**Retention**: 30-90 days

- `bronze_transactions` - Raw transaction JSONB
- `bronze_products` - Raw product catalog JSONB

**Ingestion**:
- Daily batch: Airflow DAG at 2 AM UTC
- Real-time: n8n webhook `/scout-transactions`

### Silver Layer (Validated)

**Tables**: 2
**Purpose**: Schema-enforced, validated data
**Retention**: 2 years

- `silver_validated_transactions` - Cleaned transactions with validation
- `silver_products` - Deduplicated product catalog

**Validation Rules**:
- Amount > 0
- Date <= CURRENT_DATE
- Category in allowed list
- No duplicate transaction IDs

**Refresh**: Hourly via Airflow DAG

### Gold Layer (Business Marts)

**Tables**: 2
**Purpose**: Pre-aggregated analytics
**Retention**: 5 years

- `gold_monthly_summary` - Monthly totals by category
- `gold_category_trends` - Weekly trends with anomaly detection

**Metrics**:
- MoM/YoY growth rates
- Moving averages
- Anomaly detection (>2σ)

**Refresh**: Every 6 hours

### Platinum Layer (AI-Ready)

**Views**: 2
**Purpose**: ML features and embeddings
**Retention**: 90 days (regenerated)

- `platinum_transaction_embeddings` - Text for embedding generation
- `platinum_product_recommendations` - Collaborative filtering features

**Use Cases**:
- Semantic search (Genie)
- RAG context for LLMs
- Product recommendations
- Spend pattern analysis

## Orchestration

### Airflow DAGs

**`scout_ingestion_dag`** (Daily at 2 AM UTC):
```
fetch_google_drive → fetch_csv → validate → trigger_dbt_bronze → notify
```

**`scout_transformation_dag`** (Hourly):
```
check_bronze_freshness → run_dbt_silver → test_silver → validate_silver
→ run_dbt_gold → test_gold → update_metadata → notify
```

**`data_quality_dag`** (Daily at 8 AM UTC):
```
run_dbt_tests → calculate_dq_scores → check_thresholds → [send_alert | skip]
→ update_dashboard
```

### n8n Workflows

**Real-Time Transaction Ingestion**:
- Webhook: `POST /webhook/scout-transactions`
- Insert to Bronze → Validate → Trigger dbt Silver
- Response: 200 OK with batch_id

**Odoo Sync** (Future):
- Schedule: Every 15 minutes
- Fetch invoices → Insert Bronze → Trigger dbt

**Quality Alerts**:
- Trigger: DQ score <80%
- Action: Mattermost notification
- Escalation: Email to data-engineering@

## Data Quality

### 8-Step Validation Cycle

1. **Syntax**: JSON valid, types correct
2. **Type**: amount > 0, dates valid
3. **Lint**: SQL style, naming
4. **Security**: RLS policies enforced
5. **Test**: dbt tests pass (≥80% Silver, 100% Gold)
6. **Performance**: Query latency <3s
7. **Documentation**: 100% model coverage
8. **Integration**: >95% pipeline success (7d)

### Quality Scores

| Layer | Completeness | Uniqueness | Timeliness | Overall |
|-------|--------------|------------|------------|---------|
| Bronze | ≥99% | N/A | <5 min | N/A |
| Silver | ≥95% | 100% | <1 hour | ≥95% |
| Gold | 100% | 100% | <6 hours | 100% |
| Platinum | 100% | 100% | On-demand | 100% |

### Running Tests

```bash
# dbt tests
cd dbt-workbench
dbt test --target prod

# SQL tests
psql "$POSTGRES_URL" -f quality/tests/row_count_checks.sql
psql "$POSTGRES_URL" -f quality/tests/null_checks.sql

# Airflow DQ DAG
airflow dags trigger data_quality_validation
```

## Monitoring

### Key Metrics

```sql
-- Data freshness
SELECT
    schema_name,
    table_name,
    MAX(last_updated) AS last_refresh,
    EXTRACT(EPOCH FROM (NOW() - MAX(last_updated))) / 3600 AS hours_old
FROM ip_workbench.tables
GROUP BY schema_name, table_name
ORDER BY hours_old DESC;

-- Row counts by layer
SELECT
    'bronze' AS layer,
    COUNT(*) AS row_count
FROM scout.bronze_transactions
UNION ALL
SELECT 'silver', COUNT(*)
FROM scout.silver_validated_transactions
UNION ALL
SELECT 'gold', COUNT(*)
FROM scout.gold_monthly_summary;

-- DQ scores
SELECT
    schema_name || '.' || table_name AS table_name,
    dq_score,
    last_updated
FROM ip_workbench.tables
WHERE dq_score IS NOT NULL
ORDER BY dq_score ASC;
```

### Alerts

- **Mattermost**: https://mattermost.insightpulseai.net/hooks/...
- **Email**: alerts@insightpulseai.net
- **Threshold**: DQ score <80%

## Deployment

### Production Workflow

```bash
# 1. Validate changes
cd dbt-workbench
dbt compile
dbt test

# 2. Deploy to production
dbt run --target prod

# 3. Verify deployment
dbt test --target prod

# 4. Generate documentation
dbt docs generate

# 5. Upload to DO Spaces
aws s3 sync target/ s3://dbt-docs-bucket/ --endpoint-url=https://sgp1.digitaloceanspaces.com
```

### CI/CD Integration

```yaml
# .github/workflows/deploy-data-layer.yml
name: Deploy Data Layer

on:
  push:
    branches: [main]
    paths: ['data-layer/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      # Infrastructure deployment (if needed)
      - name: Install doctl
        uses: digitalocean/action-doctl@v2
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}

      - name: Configure kubectl
        run: doctl kubernetes cluster kubeconfig save ${{ secrets.CLUSTER_ID }}

      - name: Deploy infrastructure
        run: kubectl apply -f k8s/

      # Data layer deployment
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dbt
        run: pip install dbt-postgres

      - name: Run dbt
        run: |
          cd dbt-workbench
          dbt run --target prod
          dbt test --target prod
```

---

## Next Steps

1. **Deploy Frontend**: `packages/web/README.md`
2. **Configure n8n Workflows**: Import workflows from `services/n8n/workflows/`
3. **Setup Monitoring**: Grafana + Prometheus (optional)
4. **UAT Testing**: Follow `docs/UAT_PLAN.md`

## Support

- **DigitalOcean**: https://cloud.digitalocean.com/support
- **Supabase**: https://supabase.com/support
- **Internal Docs**: `docs/`

## License

Proprietary - InsightPulseAI © 2025

---

## Integration Points

### AI Workbench (Frontend)

```typescript
// Query Gold layer via PostgREST
const { data } = await supabase
  .from('gold_monthly_summary')
  .select('*')
  .eq('month', '2025-12-01');
```

### Genie (NL2SQL)

```python
# Genie uses Platinum views for context
context = supabase.table('platinum_transaction_embeddings')
  .select('text, metadata')
  .limit(10)
  .execute()
```

### Apache Superset

```sql
-- Dashboard query (Gold layer)
SELECT
    month,
    category,
    total_amount,
    mom_growth_pct
FROM scout.gold_monthly_summary
WHERE month >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months')
ORDER BY month DESC, total_amount DESC;
```

## Troubleshooting

### Connection Issues

**Symptom**: `dbt debug` fails

**Solution**:
```bash
# Use pooler port 6543, not direct 5432
export SUPABASE_PORT=6543

# Use service role key for dbt
export POSTGRES_PASSWORD=$SUPABASE_SERVICE_ROLE_KEY
```

### RLS Blocking Queries

**Symptom**: `SELECT` returns 0 rows for admin

**Solution**:
```sql
-- Disable RLS for dbt/Airflow
ALTER TABLE scout.bronze_transactions DISABLE ROW LEVEL SECURITY;
```

### Slow Transformations

**Symptom**: `dbt run` takes >10 minutes

**Solution**:
```bash
# Reduce thread count
dbt run --threads 2

# Use incremental models
dbt run --models silver+ --full-refresh
```

### Failed Tests

**Symptom**: `dbt test` fails with >100 errors

**Solution**:
```bash
# Store failures for analysis
dbt test --store-failures

# View failures
psql "$POSTGRES_URL" -c "SELECT * FROM test_failures.silver_validated_transactions LIMIT 10;"

# Fix data quality issues in Bronze layer
```

## Performance Optimization

### Indexes

All critical indexes are created via dbt post-hooks:
- Date columns (time-series queries)
- Foreign keys (joins)
- Category columns (grouping)
- Unique constraints (deduplication)

### Query Optimization

```sql
-- Use EXPLAIN ANALYZE
EXPLAIN ANALYZE
SELECT * FROM scout.gold_monthly_summary
WHERE month >= '2025-01-01';

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'scout'
ORDER BY idx_scan DESC;
```

## References

- [AI Workbench PRD](../spec-kit/spec/ai-workbench/prd.md)
- [Tasks Document](../spec-kit/spec/ai-workbench/tasks.md)
- [dbt Documentation](https://docs.getdbt.com/)
- [Airflow Documentation](https://airflow.apache.org/docs/)
- [n8n Documentation](https://docs.n8n.io/)
- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)

## Support

- **Issues**: GitHub Issues
- **Slack**: #data-engineering
- **Email**: data-engineering@insightpulseai.net

---

# Agent Layer - Multi-Agent Orchestration System

**Purpose**: LangGraph-based multi-agent orchestration with Qdrant vector search, Langfuse observability, and comprehensive safety harnesses.

**Version**: 1.0.0
**Last Updated**: 2025-12-08
**Stack**: LangGraph, Qdrant, Langfuse, FastAPI, LiteLLM

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Workbench Frontend                     │
│              (Next.js + Material Web)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 Agent Runtime (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Research   │  │   Expense    │  │ Finance SSC  │      │
│  │    Agent     │  │  Classifier  │  │    Agent     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            ▼                                 │
│              ┌─────────────────────────┐                     │
│              │   LangGraph State      │                     │
│              │   Management Layer     │                     │
│              └─────────────────────────┘                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Qdrant     │ │  Langfuse    │ │   LiteLLM    │
│  (Vectors)   │ │ (Observ.)    │ │  (Gateway)   │
└──────────────┘ └──────────────┘ └──────────────┘
        │                               │
        ▼                               ▼
┌──────────────┐                 ┌──────────────┐
│  Supabase    │                 │ Claude/GPT-4 │
│   (Data)     │                 │   (LLMs)     │
└──────────────┘                 └──────────────┘
```

---

## Directory Structure

```
agent-layer/
├── langgraph-agents/           # LangGraph agent implementations
│   ├── agents/
│   │   ├── research_agent.py   # Multi-step research agent
│   │   ├── expense_classifier.py  # OCR → category classification
│   │   └── finance_ssc_agent.py   # BIR form generation
│   ├── graphs/
│   │   ├── research_graph.py   # Research workflow graph
│   │   └── expense_graph.py    # Expense processing graph
│   ├── tools/
│   │   ├── supabase_tool.py    # Supabase query tool
│   │   ├── qdrant_tool.py      # Vector search tool
│   │   └── odoo_tool.py        # Odoo XML-RPC tool
│   ├── state/
│   │   ├── agent_state.py      # State schemas
│   │   └── message_state.py    # Message handling
│   └── README.md
├── qdrant/                     # Vector search setup
│   ├── collections/
│   │   └── knowledge_base.json # Collection schema
│   ├── ingest/
│   │   ├── document_chunker.py # Document chunking
│   │   └── embedding_generator.py  # OpenAI embeddings
│   ├── query/
│   │   └── semantic_search.py  # Search API
│   ├── docker-compose.yml      # Qdrant deployment
│   └── README.md
├── langfuse/                   # Observability setup
│   ├── docker-compose.yml      # Langfuse deployment
│   ├── integrations/
│   │   ├── litellm.py          # LiteLLM tracing
│   │   └── langgraph.py        # LangGraph tracing
│   ├── dashboards/
│   │   └── cost_dashboard.json # Cost/latency dashboard
│   ├── alerts/
│   │   └── budget_alerts.py    # Budget threshold alerts
│   └── README.md
├── safety/                     # Safety harnesses
│   ├── prompt_injection_detector.py  # Injection detection
│   ├── content_moderator.py    # Content moderation
│   ├── rate_limiter.py         # Rate limiting
│   ├── kill_switch.py          # Emergency stop
│   ├── audit_logger.py         # Security logging
│   └── README.md
├── bindings/                   # Agent bindings to Gold schemas
│   ├── saricoach_binding.py    # SariCoach agent binding
│   ├── genieview_binding.py    # GenieView NL2SQL binding
│   ├── schema_mapper.py        # Gold table → context
│   ├── role_generator.py       # Read-only SQL roles
│   └── README.md
├── services/                   # FastAPI runtime
│   ├── agent-runtime/
│   │   ├── main.py             # FastAPI app
│   │   ├── routers/
│   │   │   ├── agents.py       # Agent execution routes
│   │   │   └── health.py       # Health check routes
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── docker-compose.yml
├── tests/                      # Integration tests
│   ├── test_research_agent.py
│   ├── test_expense_classifier.py
│   ├── test_safety_harnesses.py
│   └── test_qdrant_search.py
├── infra/                      # Infrastructure configs
│   └── do/
│       └── agent-runtime.yaml  # DO App Platform spec
└── README.md
```

---

## Quick Start

### 1. Deploy Qdrant
```bash
cd qdrant
docker-compose up -d
```

### 2. Deploy Langfuse
```bash
cd langfuse
docker-compose up -d
```

### 3. Setup Agent Runtime
```bash
cd services/agent-runtime
pip install -r requirements.txt
uvicorn main:app --reload
```

### 4. Ingest Knowledge Base
```bash
cd qdrant/ingest
python document_chunker.py --input docs/ --output chunks.json
python embedding_generator.py --input chunks.json --output embeddings.json
```

### 5. Test Agent
```bash
curl -X POST http://localhost:8000/api/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "research-agent",
    "query": "What are the top expense categories last month?",
    "user_id": "user-123"
  }'
```

---

## Agent Types

### 1. Research Agent
**Purpose**: Multi-step research with knowledge base retrieval

**Workflow**:
```
Entry → Search Qdrant → Fetch Context → Generate Answer → Validate → Retry (if needed)
```

**Use Cases**:
- Analyze Scout transaction trends
- Research BIR filing requirements
- Compare vendors by expense amounts

### 2. Expense Classifier
**Purpose**: OCR → category classification with policy validation

**Workflow**:
```
Entry → OCR Extract → Validate → Classify Category → Route to Approval → Notify
```

**Use Cases**:
- Classify receipts from PaddleOCR-VL
- Route expenses to correct approval workflow
- Flag policy violations

### 3. Finance SSC Agent
**Purpose**: BIR form generation and multi-employee finance operations

**Workflow**:
```
Entry → Query Odoo → Aggregate Tax Data → Generate BIR Form → Store → Notify
```

**Use Cases**:
- Generate 1601-C monthly
- Generate 2550Q quarterly
- Multi-employee tax calculations

---

## Safety Harnesses

### 1. Prompt Injection Detection
- **Regex Patterns**: 10+ injection patterns
- **LlamaGuard**: AI-based detection
- **Action**: Block + audit log

### 2. Content Moderation
- **OpenAI Moderation API**: Automatic flagging
- **Categories**: hate, harassment, violence, sexual
- **Action**: Block + notify admin

### 3. Rate Limiting
- **Per User**: 100 requests/hour
- **Global**: 1000 requests/hour
- **Action**: Return 429 + suggest retry

### 4. Budget Limits
- **Per Agent**: $1 per run (configurable)
- **Per Project**: $100/day
- **Action**: Pause agent + alert

### 5. Kill Switch
- **Manual**: Admin dashboard button
- **Auto**: Budget exceeded or rate limit breached
- **Action**: Stop all agents + notify

---

## Observability

### Langfuse Traces
**Captured Data**:
- Input prompt
- Output response
- Model used (claude-sonnet-4.5, gpt-4, etc.)
- Tokens (prompt + completion)
- Cost (USD)
- Latency (ms)

**Tags**:
- `agent_type`: research, expense, finance
- `user_id`: User identifier
- `session_id`: Session tracking
- `environment`: dev, staging, production

**Annotations**:
- Human feedback (thumbs up/down)
- Error flags (timeout, rate limit)
- Quality scores (confidence, relevance)

### Cost Dashboard
**Metrics**:
- Total cost today
- Cost per agent
- Cost per model
- Cost per user

**Alerts**:
- Budget threshold exceeded (email + Mattermost)
- Unusual spike in cost (auto-investigation)
- Model failure (fallback triggered)

---

## Agent Bindings

### SariCoach Binding
**Purpose**: Bind SariCoach agent to Scout gold tables

**Gold Tables**:
- `gold.finance_expenses`
- `gold.finance_vendors`
- `gold.scout_transactions`

**Context**:
```python
{
  "tables": ["gold.finance_expenses"],
  "columns": ["vendor", "amount", "category", "date"],
  "filters": ["status = 'approved'", "date > '2025-01-01'"],
  "aggregations": ["SUM(amount)", "COUNT(*)"]
}
```

### GenieView Binding
**Purpose**: Natural language to SQL (NL2SQL) for Tableau

**Workflow**:
1. User query: "Show me top 5 vendors by expense amount"
2. Agent → Qdrant: Find similar queries
3. Agent → LLM: Generate SQL
4. Agent → Supabase: Execute SQL
5. Agent → User: Results + SQL

**SQL Role**:
```sql
CREATE ROLE genieview_readonly;
GRANT SELECT ON gold.* TO genieview_readonly;
REVOKE INSERT, UPDATE, DELETE ON gold.* FROM genieview_readonly;
```

---

## Testing

### Unit Tests
```bash
pytest tests/test_research_agent.py -v
pytest tests/test_expense_classifier.py -v
```

### Integration Tests
```bash
pytest tests/ -v --cov=langgraph-agents
```

### Safety Tests
```bash
pytest tests/test_safety_harnesses.py -v
```

---

## Deployment

### DigitalOcean App Platform
```bash
doctl apps create --spec infra/do/agent-runtime.yaml
```

### Kubernetes (DOKS)
```bash
kubectl apply -f k8s/agent-runtime-deployment.yaml
```

---

## Configuration

### Environment Variables
```bash
# Supabase
export SUPABASE_URL="https://xkxyvboeubffxxbebsll.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="..."

# Qdrant
export QDRANT_URL="http://qdrant:6333"

# Langfuse
export LANGFUSE_URL="http://langfuse:3000"
export LANGFUSE_PUBLIC_KEY="..."
export LANGFUSE_SECRET_KEY="..."

# LiteLLM
export LITELLM_URL="https://litellm.insightpulseai.net"
export LITELLM_API_KEY="..."

# Odoo
export ODOO_URL="https://odoo.insightpulseai.net"
export ODOO_DB="production"
export ODOO_USERNAME="admin"
export ODOO_PASSWORD="..."

# OpenAI (for embeddings + moderation)
export OPENAI_API_KEY="..."
```

---

## Performance

### Latency Targets
- **Agent Execution**: <5s (p95)
- **Vector Search**: <100ms (p95)
- **LLM Call**: <3s (p95)

### Throughput
- **Concurrent Agents**: 50+
- **Requests/min**: 500+
- **Vector Searches/s**: 100+

---

## Security

### Authentication
- API keys (Supabase JWT)
- Rate limiting per user
- RLS policies enforced

### Secrets Management
- Supabase Vault
- Environment variables only
- No hardcoded secrets

### Audit Logging
- All agent runs logged
- Security events flagged
- Suspicious activity alerts

---

## Next Steps

1. **T7.1**: Setup LiteLLM Gateway (see `prd.md`)
2. **T7.2**: Integrate Langfuse
3. **T7.3**: Build Genie Chat Interface
4. **T7.4**: Create Agent Registry Page
5. **T7.5**: Implement Tool Library
6. **T7.6**: Build LangGraph Agent Runtime
7. **T7.7**: Create Agent Run Timeline
8. **T7.8**: Build Cost Tracking Dashboard
9. **T7.9**: Implement Budget Alerts

---

## References

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [Langfuse Docs](https://langfuse.com/docs)
- [LiteLLM Docs](https://docs.litellm.ai/)
- [PRD](../spec-kit/spec/ai-workbench/prd.md)
- [Tasks](../spec-kit/spec/ai-workbench/tasks.md)
