# DigitalOcean Infrastructure

Complete DigitalOcean infrastructure for InsightPulseAI AI Workbench.

## Directory Structure

```
infra/digitalocean/
├── terraform/         # Infrastructure as Code
├── kubernetes/        # K8s manifests (namespaces, secrets)
└── helm-values/       # Helm chart configurations
```

## Prerequisites

1. **DigitalOcean CLI** (`doctl`)
   ```bash
   brew install doctl
   doctl auth init
   ```

2. **Terraform** (v1.0+)
   ```bash
   brew install terraform
   ```

3. **kubectl** (v1.28+)
   ```bash
   brew install kubectl
   ```

4. **Helm** (v3.0+)
   ```bash
   brew install helm
   ```

## Quick Start

### 1. Configure DigitalOcean Access

```bash
# Authenticate doctl
doctl auth init

# Export API token for Terraform
export DO_TOKEN=$(doctl auth list --format Token --no-header)
export DIGITALOCEAN_TOKEN=$DO_TOKEN
```

### 2. Deploy Infrastructure with Terraform

```bash
cd terraform/

# Initialize Terraform
terraform init

# Create terraform.tfvars with secrets
cat > terraform.tfvars <<EOF
do_token                    = "$DO_TOKEN"
supabase_url                = "https://xkxyvboeubffxxbebsll.supabase.co"
supabase_service_role_key   = "<your-service-role-key>"
EOF

# Plan deployment
terraform plan

# Apply (deploy)
terraform apply

# Save outputs
terraform output -json > outputs.json
```

### 3. Configure kubectl

```bash
# Get cluster credentials
doctl kubernetes cluster kubeconfig save $(terraform output -raw cluster_id)

# Verify connection
kubectl get nodes
```

### 4. Create Namespaces

```bash
cd ../kubernetes/

# Apply namespaces
kubectl apply -f namespace.yaml

# Verify
kubectl get namespaces
```

### 5. Configure Secrets

```bash
# Copy template
cp secrets.yaml.example secrets.yaml

# Edit secrets (DO NOT commit to Git)
vim secrets.yaml

# Apply secrets
kubectl apply -f secrets.yaml

# Verify
kubectl get secrets -A
```

### 6. Deploy Traefik (Ingress Controller)

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

# Wait for LoadBalancer IP
kubectl get svc -n traefik --watch

# Configure DNS (point *.insightpulseai.net to LoadBalancer IP)
# A record: *.insightpulseai.net → <LoadBalancer-IP>
```

### 7. Deploy n8n (Workflow Automation)

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

# Access n8n UI
echo "n8n URL: https://n8n.insightpulseai.net"
```

## Infrastructure Components

### VPC Configuration

- **CIDR**: 10.10.0.0/16
- **Private networking**: Enabled
- **Firewall rules**: Configured for HTTPS/PostgreSQL/Qdrant

### DOKS Cluster

- **Node pool**: 3 nodes (s-4vcpu-8gb)
- **Autoscaling**: 3-6 nodes
- **Kubernetes version**: 1.29.4
- **Auto-upgrade**: Enabled
- **Maintenance window**: Sunday 04:00 UTC

### App Platform Services

#### OCR Backend
- **URL**: Output from Terraform
- **Instance**: 2× professional-xs (1 vCPU, 2GB RAM)
- **Model**: PaddleOCR-VL-900M
- **Health check**: `/health`

#### Expense API
- **URL**: Output from Terraform
- **Instance**: 2× professional-xs
- **Database**: Supabase PostgreSQL
- **Health check**: `/health`

### Container Registry

- **Name**: ai-workbench-registry
- **Tier**: Basic (5 repos, 500MB)
- **Region**: Singapore (sgp1)

### Spaces Bucket

- **Name**: ai-workbench-assets-production
- **Region**: Singapore (sgp1)
- **Versioning**: Enabled
- **Lifecycle**: Delete old versions after 90 days

## Deployment Commands

### Deploy Application to DOKS

```bash
# Build Docker image
docker build -t registry.digitalocean.com/ai-workbench-registry/app:v1.0 .

# Push to registry
doctl registry login
docker push registry.digitalocean.com/ai-workbench-registry/app:v1.0

# Deploy to DOKS
kubectl apply -f k8s/app-deployment.yaml
kubectl rollout status deployment/app -n ai-workbench
```

### Update App Platform Service

```bash
# Update OCR backend
doctl apps update $(terraform output -raw ocr_backend_id) \
  --spec infra/do/ocr-backend.yaml

# Create deployment
doctl apps create-deployment $(terraform output -raw ocr_backend_id) \
  --force-rebuild

# View logs
doctl apps logs $(terraform output -raw ocr_backend_id) --follow
```

## Monitoring & Logs

### View Cluster Logs

```bash
# Pod logs
kubectl logs -f <pod-name> -n <namespace>

# Deployment logs
kubectl logs -f deployment/<deployment-name> -n <namespace>

# n8n logs
kubectl logs -f deployment/n8n -n n8n
```

### Traefik Dashboard (Optional)

```bash
# Port-forward to Traefik dashboard
kubectl port-forward -n traefik $(kubectl get pods -n traefik -l app.kubernetes.io/name=traefik -o name) 9000:9000

# Access at http://localhost:9000/dashboard/
```

## Cost Management

### Estimated Monthly Costs

| Resource | Spec | Cost (USD) |
|----------|------|------------|
| DOKS (3 nodes) | s-4vcpu-8gb | $120 |
| App Platform (OCR) | 2× professional-xs | $24 |
| App Platform (Expense) | 2× professional-xs | $24 |
| Container Registry | Basic | $5 |
| Spaces (500MB) | 500MB | $5 |
| Load Balancer | 1× LB | $12 |
| **Total** | | **~$190/month** |

### Cost Optimization Tips

1. **Use autoscaling**: Scale down during off-peak hours
2. **Spot instances**: Not available for DOKS, use App Platform for batch jobs
3. **Image cleanup**: Delete old container images regularly
4. **Monitor bandwidth**: Optimize data transfer to reduce egress costs

## Troubleshooting

### Cluster Issues

```bash
# Check node status
kubectl get nodes

# Describe node
kubectl describe node <node-name>

# Check cluster events
kubectl get events --sort-by='.lastTimestamp'
```

### Pod Issues

```bash
# Check pod status
kubectl get pods -A

# Describe pod
kubectl describe pod <pod-name> -n <namespace>

# View logs
kubectl logs <pod-name> -n <namespace>

# Check resource usage
kubectl top pods -A
```

### Traefik Issues

```bash
# Check Traefik logs
kubectl logs -n traefik -l app.kubernetes.io/name=traefik

# Verify ingress resources
kubectl get ingress -A

# Check certificate status
kubectl get certificate -A
```

## Security Best Practices

1. **Secrets management**: Never commit secrets to Git
2. **RBAC**: Use Kubernetes RBAC for access control
3. **Network policies**: Implement network segmentation
4. **Image scanning**: Scan container images for vulnerabilities
5. **Firewall rules**: Minimize exposed ports
6. **SSL/TLS**: Enforce HTTPS for all services
7. **Regular updates**: Keep Kubernetes and Helm charts updated

## Backup & Disaster Recovery

### DOKS Cluster Backup

```bash
# Install Velero
helm repo add vmware-tanzu https://vmware-tanzu.github.io/helm-charts
helm install velero vmware-tanzu/velero \
  --namespace velero \
  --create-namespace \
  --set-file credentials.secretContents.cloud=./velero-credentials

# Create backup
velero backup create workbench-backup --include-namespaces ai-workbench,n8n,litellm

# Restore backup
velero restore create --from-backup workbench-backup
```

### Database Backup

Supabase handles PostgreSQL backups automatically (see `infra/supabase/README.md`).

## Next Steps

1. Deploy LiteLLM Gateway: `services/litellm-proxy/README.md`
2. Configure n8n workflows: `services/n8n/README.md`
3. Setup Supabase schema: `infra/supabase/README.md`

## Support

- **Documentation**: https://docs.digitalocean.com/products/kubernetes/
- **Status**: https://status.digitalocean.com/
- **Support**: https://cloud.digitalocean.com/support/tickets
