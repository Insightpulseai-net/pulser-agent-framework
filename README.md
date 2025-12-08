# InsightPulseAI AI Workbench - Complete Stack

Production-ready infrastructure + data layer for self-hosted AI Workbench.

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

## Directory Structure

```
data-layer/
├── dbt-workbench/              # dbt transformation project
│   ├── models/
│   │   ├── bronze/             # Raw ingestion models
│   │   ├── silver/             # Validated models
│   │   ├── gold/               # Business marts
│   │   └── platinum/           # AI-ready views
│   ├── tests/                  # dbt test cases
│   ├── macros/                 # SQL macros
│   └── README.md
│
├── airflow/                    # Orchestration DAGs
│   ├── dags/
│   │   ├── scout_ingestion_dag.py          # Daily batch ingestion
│   │   ├── scout_transformation_dag.py     # Hourly transformations
│   │   ├── data_quality_dag.py             # Daily DQ validation
│   │   └── backfill_dag.py                 # Historical backfill
│   └── README.md
│
├── n8n-etl/                    # Real-time workflows
│   ├── workflows/
│   │   ├── real-time-transactions.json     # Webhook ingestion
│   │   ├── odoo-sync.json                  # Odoo integration
│   │   └── quality-alerts.json             # DQ alerting
│   └── README.md
│
├── schemas/                    # Schema documentation
│   ├── bronze_schema.md
│   ├── silver_schema.md
│   ├── gold_schema.md
│   ├── platinum_schema.md
│   ├── entity_relationships.md
│   └── README.md
│
└── quality/                    # Data quality framework
    ├── tests/
    │   ├── row_count_checks.sql
    │   ├── null_checks.sql
    │   ├── unique_checks.sql
    │   └── referential_integrity.sql
    ├── great_expectations/     # GE suite (future)
    └── README.md
```
>>>>>>> data-layer

## Quick Start

### Prerequisites

<<<<<<< HEAD
```bash
# Install required tools
brew install doctl terraform kubectl helm postgresql

# Authenticate with DigitalOcean
doctl auth init

# Set environment variables
export DO_TOKEN=$(doctl auth list --format Token --no-header)
export SUPABASE_URL="https://xkxyvboeubffxxbebsll.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="<your-key>"
export POSTGRES_URL="postgresql://postgres:[password]@aws-1-us-east-1.pooler.supabase.com:6543/postgres"
```

### Deploy in Order

#### 1. DigitalOcean Infrastructure (20 min)

```bash
cd infra/digitalocean/terraform/

# Initialize and deploy
terraform init
terraform plan
terraform apply

# Get cluster credentials
doctl kubernetes cluster kubeconfig save $(terraform output -raw cluster_id)

# Verify
kubectl get nodes
```

See: [`infra/digitalocean/README.md`](infra/digitalocean/README.md)

#### 2. Kubernetes Resources (5 min)

```bash
cd ../kubernetes/

# Create namespaces
kubectl apply -f namespace.yaml

# Configure secrets
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml with real values (DO NOT commit)
kubectl apply -f secrets.yaml
```

#### 3. Traefik Ingress (10 min)

```bash
cd ../

# Deploy Traefik
helm repo add traefik https://traefik.github.io/charts
helm install traefik traefik/traefik \
  --namespace traefik \
  --values helm-values/traefik.yaml \
  --create-namespace

# Wait for LoadBalancer IP
kubectl get svc -n traefik --watch

# Configure DNS: *.insightpulseai.net → <LoadBalancer-IP>
```

#### 4. n8n Workflow Automation (10 min)

```bash
# Deploy n8n
helm repo add 8gears https://8gears.container-registry.com/chartrepo/library
helm install n8n 8gears/n8n \
  --namespace n8n \
  --values helm-values/n8n.yaml \
  --create-namespace

# Access: https://n8n.insightpulseai.net
```

See: [`services/n8n/README.md`](services/n8n/README.md)

#### 5. Supabase Database Schema (15 min)

```bash
cd ../../infra/supabase/migrations/

# Run migrations
psql "$POSTGRES_URL" -f 001_metadata_schema.sql
psql "$POSTGRES_URL" -f 002_medallion_schemas.sql

# Enable RLS policies
cd ../rls-policies/
psql "$POSTGRES_URL" -f workbench_policies.sql

# Verify
psql "$POSTGRES_URL" -c "\dt ip_workbench.*"
```

See: [`infra/supabase/README.md`](infra/supabase/README.md)

#### 6. LiteLLM Gateway (15 min)

```bash
cd ../../../services/litellm-proxy/

# Build and push image
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

See: [`services/litellm-proxy/README.md`](services/litellm-proxy/README.md)

### Total Deployment Time: ~75 minutes

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
# .github/workflows/deploy.yml
name: Deploy to DOKS

on:
  push:
    branches: [main]
=======
- PostgreSQL 15+ (Supabase)
- Python 3.11+
- dbt-postgres
- Apache Airflow 2.8+
- n8n (self-hosted or cloud)

### Setup

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
# GitHub Actions example
name: Deploy Data Layer
on:
  push:
    branches: [main]
    paths: ['data-layer/**']
>>>>>>> data-layer

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
<<<<<<< HEAD

      - name: Install doctl
        uses: digitalocean/action-doctl@v2
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}

      - name: Configure kubectl
        run: doctl kubernetes cluster kubeconfig save ${{ secrets.CLUSTER_ID }}

      - name: Deploy
        run: kubectl apply -f k8s/
```

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
=======
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
>>>>>>> data-layer
