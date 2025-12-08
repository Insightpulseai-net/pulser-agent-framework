# InsightPulseAI AI Workbench Infrastructure

Complete deployment-ready infrastructure for the AI Workbench on DigitalOcean + Supabase.

## Overview

This infrastructure provides:
- **DigitalOcean DOKS cluster** (Kubernetes) for microservices
- **Supabase PostgreSQL** for metadata and data storage
- **LiteLLM Gateway** for multi-model AI routing
- **n8n** for workflow automation
- **Traefik** for ingress and SSL management

## Quick Start

### Prerequisites

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
