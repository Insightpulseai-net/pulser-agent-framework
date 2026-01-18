# FastAPI Service Golden Template

A production-ready FastAPI backend service with observability and deployment baked in.

## Stack

- **Framework**: FastAPI 0.115+
- **Language**: Python 3.11+
- **Validation**: Pydantic v2
- **Database**: PostgreSQL (via Supabase or direct)
- **ORM**: SQLAlchemy 2.x (optional)
- **Deployment**: Docker + Kubernetes / DigitalOcean
- **CI/CD**: GitHub Actions

## Quick Start

```bash
# Clone template
cp -r platform/templates/fastapi-service my-service
cd my-service

# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your config

# Run development server
uvicorn app.main:app --reload
```

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py    # API router
│   │   │   └── endpoints/   # Endpoint modules
│   │   └── deps.py          # Dependencies
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py      # Auth utilities
│   │   └── exceptions.py    # Custom exceptions
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic
│   └── db/                  # Database layer
│       ├── __init__.py
│       ├── session.py       # DB session
│       └── repositories/    # Data access
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── alembic/                 # Migrations (if using SQLAlchemy)
├── scripts/
│   ├── start.sh
│   └── healthcheck.sh
├── Dockerfile
├── docker-compose.yml
├── kubernetes/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
└── .github/workflows/
    ├── ci.yml
    └── deploy.yml
```

## API Structure

```
/                        # Root - redirect to docs
/health                  # Health check
/ready                   # Readiness probe
/metrics                 # Prometheus metrics
/api/v1/                 # API v1 root
/api/v1/{resource}       # Resource endpoints
/docs                    # OpenAPI (Swagger UI)
/redoc                   # ReDoc documentation
```

## Health Checks

```python
# GET /health - Liveness probe
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}

# GET /ready - Readiness probe
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "cache": "ok"
  }
}
```

## Configuration

Environment-based configuration with Pydantic Settings:

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    app_name: str = "My Service"
    debug: bool = False

    # Database
    database_url: str

    # Auth
    jwt_secret: str
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"
```

## Authentication

JWT-based authentication with configurable providers:

```python
from app.core.security import get_current_user

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return user
```

## Error Handling

Standardized error responses:

```python
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      {"field": "email", "message": "Invalid email format"}
    ]
  }
}
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/unit/test_service.py -v
```

## Docker

```bash
# Build
docker build -t my-service .

# Run
docker run -p 8000:8000 --env-file .env my-service

# Docker Compose (with dependencies)
docker-compose up -d
```

## Kubernetes Deployment

```bash
# Apply manifests
kubectl apply -f kubernetes/

# Check status
kubectl get pods -l app=my-service
```

## Observability

### Logging

Structured JSON logging:

```python
import structlog

logger = structlog.get_logger()
logger.info("request_processed", user_id=123, duration_ms=45)
```

Output:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "event": "request_processed",
  "user_id": 123,
  "duration_ms": 45,
  "service": "my-service"
}
```

### Metrics

Prometheus metrics at `/metrics`:
- `http_requests_total`
- `http_request_duration_seconds`
- `http_requests_in_progress`

### Tracing

OpenTelemetry integration ready:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("my_operation"):
    # Your code here
    pass
```

## Database Migrations

Using Alembic:

```bash
# Create migration
alembic revision --autogenerate -m "Add users table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Security Checklist

- [x] JWT token validation
- [x] Rate limiting middleware
- [x] CORS configuration
- [x] Input validation (Pydantic)
- [x] SQL injection protection (parameterized queries)
- [x] Secure headers middleware
- [x] Secrets via environment variables

## Performance

- Connection pooling enabled
- Async endpoints where beneficial
- Response caching headers
- Gzip compression middleware

## Support

Questions? Ask in `#platform-paved-road`
