# LiteLLM Gateway

Multi-model AI gateway with fallbacks, rate limiting, and observability for AI Workbench.

## Features

- **Multi-model support**: Claude Sonnet 4.5, GPT-4o-mini, Gemini 1.5 Flash
- **Automatic fallbacks**: Claude → GPT-4o-mini → Gemini
- **Rate limiting**: 500 req/min, 10K TPM per user
- **Cost tracking**: Integrated with Langfuse
- **Caching**: Redis-backed response caching
- **Monitoring**: Prometheus metrics

## Quick Start

### 1. Build Docker Image

```bash
cd services/litellm-proxy/

# Build image
docker build -t registry.digitalocean.com/ai-workbench-registry/litellm-gateway:latest .

# Test locally
docker run -p 8080:8080 \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  -e LITELLM_MASTER_KEY="sk-test-12345" \
  registry.digitalocean.com/ai-workbench-registry/litellm-gateway:latest

# Test health endpoint
curl http://localhost:8080/health
```

### 2. Push to Registry

```bash
# Login to DigitalOcean registry
doctl registry login

# Push image
docker push registry.digitalocean.com/ai-workbench-registry/litellm-gateway:latest
```

### 3. Deploy to DOKS

```bash
# Create secrets first (if not already created)
kubectl create secret generic llm-api-keys \
  --namespace=litellm \
  --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  --from-literal=GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  --from-literal=LITELLM_MASTER_KEY="sk-$(openssl rand -hex 16)"

# Deploy
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml

# Wait for rollout
kubectl rollout status deployment/litellm-gateway -n litellm

# Verify
kubectl get pods -n litellm
kubectl logs -f deployment/litellm-gateway -n litellm
```

## Configuration

### Model Routing

Edit `config.yaml` to add/remove models:

```yaml
model_list:
  - model_name: claude-sonnet-4.5
    litellm_params:
      model: claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY
      rpm: 500
      tpm: 100000
```

### Fallback Strategy

```yaml
router_settings:
  fallbacks:
    - claude-sonnet-4.5: [gpt-4o-mini, gemini-1.5-flash]
    - gpt-4o-mini: [gemini-1.5-flash, gpt-3.5-turbo]
  allowed_fails: 3
  cooldown_time: 30
```

### Rate Limiting

```yaml
litellm_settings:
  rpm: 100 # Per user
  tpm: 10000 # Per user
  max_budget: 100 # $100 per day per user
```

## Usage

### OpenAI-Compatible API

```bash
# Using curl
curl https://litellm.insightpulseai.net/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4.5",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "temperature": 0.7
  }'

# Using Python
from openai import OpenAI

client = OpenAI(
    base_url="https://litellm.insightpulseai.net/v1",
    api_key=os.environ["LITELLM_MASTER_KEY"]
)

response = client.chat.completions.create(
    model="claude-sonnet-4.5",
    messages=[{"role": "user", "content": "Generate SQL for top 5 vendors"}]
)
print(response.choices[0].message.content)
```

### Model Aliases

```python
# Use shorter aliases
response = client.chat.completions.create(
    model="claude-sonnet-4.5",  # Full name
    # or
    model="gpt-4o-mini",        # Fallback
    messages=[...]
)
```

## Monitoring

### Health Check

```bash
curl https://litellm.insightpulseai.net/health
```

### Prometheus Metrics

```bash
# Access metrics endpoint
curl https://litellm.insightpulseai.net:9090/metrics

# Example metrics:
# - litellm_requests_total{model="claude-sonnet-4.5", status="success"}
# - litellm_request_duration_seconds{model="claude-sonnet-4.5"}
# - litellm_tokens_total{model="claude-sonnet-4.5", type="input"}
# - litellm_cost_usd{model="claude-sonnet-4.5"}
```

### Langfuse Integration

View traces at: https://langfuse.insightpulseai.net

- **Request logs**: All LLM calls with prompts and responses
- **Cost tracking**: Token usage and costs per agent
- **Latency analysis**: P50/P95/P99 latency by model
- **Error tracking**: Failed requests and fallback triggers

## Cost Optimization

### 1. Enable Caching

Redis caching reduces costs for repeated queries:

```yaml
cache_settings:
  type: redis
  host: redis-service.litellm.svc.cluster.local
  ttl: 3600 # 1 hour
```

### 2. Use Budget Limits

Set per-user daily budgets:

```yaml
litellm_settings:
  max_budget: 100 # $100 per day
  budget_duration: 24h
```

### 3. Route to Cheaper Models

For simple tasks, route to GPT-3.5 or Gemini Flash:

```python
# For simple queries
response = client.chat.completions.create(
    model="gpt-3.5-turbo",  # $0.50/1M input tokens
    messages=[...]
)

# For complex analysis
response = client.chat.completions.create(
    model="claude-sonnet-4.5",  # $3/1M input tokens
    messages=[...]
)
```

## Troubleshooting

### Connection Issues

```bash
# Check pod status
kubectl get pods -n litellm

# View logs
kubectl logs -f deployment/litellm-gateway -n litellm

# Check service endpoint
kubectl get svc -n litellm
```

### Rate Limit Errors

```bash
# 429 Too Many Requests
# Check user rate limits in config.yaml

# Increase limits
kubectl edit configmap litellm-config -n litellm
# Update rpm/tpm values
kubectl rollout restart deployment/litellm-gateway -n litellm
```

### Fallback Not Working

```bash
# Check logs for fallback triggers
kubectl logs deployment/litellm-gateway -n litellm | grep fallback

# Verify fallback configuration
kubectl get configmap litellm-config -n litellm -o yaml
```

## Security

### API Key Rotation

```bash
# Generate new master key
NEW_KEY="sk-$(openssl rand -hex 16)"

# Update secret
kubectl create secret generic llm-api-keys \
  --namespace=litellm \
  --from-literal=LITELLM_MASTER_KEY="$NEW_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart deployment
kubectl rollout restart deployment/litellm-gateway -n litellm
```

### Rate Limit Abuse

```bash
# View request logs
kubectl logs deployment/litellm-gateway -n litellm | grep "rate_limit_exceeded"

# Block specific user (add to config.yaml)
blocked_users:
  - user_id_or_api_key
```

## Cost Tracking

### Daily Cost Report

```bash
# Query Langfuse for daily costs
curl https://langfuse.insightpulseai.net/api/public/metrics/cost \
  -H "Authorization: Bearer $LANGFUSE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-12-01", "end_date": "2025-12-08"}'
```

### Per-Model Cost Breakdown

| Model | Input Cost | Output Cost | Avg Latency |
|-------|------------|-------------|-------------|
| Claude Sonnet 4.5 | $3/1M | $15/1M | 1.2s |
| GPT-4o-mini | $0.15/1M | $0.60/1M | 0.8s |
| Gemini 1.5 Flash | $0.075/1M | $0.30/1M | 0.5s |
| GPT-3.5 Turbo | $0.50/1M | $1.50/1M | 0.6s |

## Next Steps

1. Configure Langfuse observability
2. Setup cost alerts via Mattermost
3. Integrate with AI Workbench frontend

## Resources

- **LiteLLM Docs**: https://docs.litellm.ai/
- **Langfuse Docs**: https://langfuse.com/docs
- **OpenAI API**: https://platform.openai.com/docs/api-reference
