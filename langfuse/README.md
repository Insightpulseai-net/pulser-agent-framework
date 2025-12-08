# Langfuse Observability

Self-hosted Langfuse deployment for LLM observability and cost tracking.

## Quick Start

### 1. Start Langfuse
```bash
docker-compose up -d
```

### 2. Access UI
Open browser: http://localhost:3000

**Default Credentials**:
- Email: admin@example.com
- Password: admin

### 3. Create Project
1. Login to Langfuse UI
2. Click "Create Project"
3. Name: "AI Workbench"
4. Copy API keys (public + secret)

### 4. Configure Environment
```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_HOST="http://localhost:3000"
```

## Usage

### Trace LLM Requests
```python
from langfuse.integrations.litellm import LiteLLMLangfuseTracer

tracer = LiteLLMLangfuseTracer(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)

# Create trace
trace_metadata = await tracer.trace_request(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7,
    max_tokens=100,
    user_id="user-123",
    session_id="session-456",
    metadata={"agent": "research"}
)

# Record response
tracer.record_response(
    trace_id=trace_metadata['trace_id'],
    generation_id=trace_metadata['generation_id'],
    response="Hi there!",
    prompt_tokens=10,
    completion_tokens=5,
    cost_usd=0.0015,
    latency_ms=350
)

# Add user feedback
tracer.add_user_feedback(
    trace_id=trace_metadata['trace_id'],
    score=0.9,
    comment="Great response!"
)
```

### View Traces
```
http://localhost:3000/trace/{trace_id}
```

## Features

### Traces
- **Input/Output**: Full prompt and response
- **Model**: LLM model used
- **Tokens**: Prompt + completion counts
- **Cost**: USD cost calculation
- **Latency**: Response time in ms
- **Metadata**: Custom tags and attributes

### Scores
- **User Feedback**: Thumbs up/down
- **Cost**: Per-request cost tracking
- **Latency**: Response time tracking
- **Custom**: Any custom metric

### Dashboards
- **Cost Overview**: Daily/monthly cost trends
- **Latency Analysis**: P50/P95/P99 latency
- **Model Usage**: Requests per model
- **User Activity**: Requests per user

## Configuration

### docker-compose.yml
```yaml
services:
  langfuse-db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: langfuse
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse_password

  langfuse:
    image: langfuse/langfuse:latest
    depends_on:
      - langfuse-db
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse_password@langfuse-db:5432/langfuse
      NEXTAUTH_URL: http://localhost:3000
      NEXTAUTH_SECRET: your-secret
```

### Environment Variables
```bash
# Langfuse
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_HOST="http://localhost:3000"

# Database (production)
export DATABASE_URL="postgresql://user:pass@host:5432/langfuse"
```

## Integration

### LiteLLM
Automatic tracing via `integrations/litellm.py`:
```python
from langfuse.integrations.litellm import LiteLLMLangfuseTracer

# Initialize once
tracer = LiteLLMLangfuseTracer(...)

# All LLM calls automatically traced
```

### LangGraph
Manual tracing via decorators:
```python
from langfuse.decorators import observe, langfuse_context

@observe(name="research_agent_step")
async def research_step(state):
    # Step logic
    return state
```

## Monitoring

### Health Check
```bash
curl http://localhost:3000/api/health
```

### Database Connection
```bash
docker exec -it langfuse-db psql -U langfuse -d langfuse -c "SELECT COUNT(*) FROM traces;"
```

## Cost Tracking

### Per-Model Pricing
Configure in Langfuse UI:
1. Settings → Models
2. Add model pricing:
   - gpt-4: $0.03/1K input, $0.06/1K output
   - claude-sonnet-4.5: $0.003/1K input, $0.015/1K output
   - gpt-3.5-turbo: $0.0005/1K input, $0.0015/1K output

### Budget Alerts
Set in agent runtime:
```python
# Check daily cost
daily_cost = sum_traces_today()

if daily_cost > 100.0:
    # Alert admin
    send_mattermost_notification({
        "type": "budget_exceeded",
        "cost": daily_cost,
        "limit": 100.0
    })
```

## Troubleshooting

### Langfuse Not Starting
**Symptom**: Container exits or 502 error

**Solutions**:
1. Check database connection: `docker logs langfuse-db`
2. Verify environment variables
3. Check port availability: `lsof -i :3000`

### Traces Not Appearing
**Symptom**: LLM calls not visible in UI

**Solutions**:
1. Verify API keys are correct
2. Check network connectivity: `curl $LANGFUSE_HOST/api/health`
3. Enable debug logging in tracer
4. Check trace creation: `tracer.langfuse.flush()`

### High Database Usage
**Symptom**: Database growing rapidly

**Solutions**:
1. Set trace retention policy (e.g., 90 days)
2. Archive old traces to cold storage
3. Implement sampling (trace 10% of requests)
