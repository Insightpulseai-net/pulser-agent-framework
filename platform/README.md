# Platform Templates & Golden Paths

This directory contains standardized templates and golden paths maintained by the Platform/DevEx team.

## Purpose

"The team that makes teams faster" - provide paved roads so product pods can ship features without owning every infrastructure edge case.

## Directory Structure

```
platform/
├── templates/           # Starter templates for new projects
│   ├── nextjs-supabase/  # Next.js + Supabase + Actions
│   ├── fastapi-service/  # FastAPI + OpenAPI + deploy
│   └── edge-function/    # Supabase Edge Function
├── golden-paths/        # Reference implementations
│   ├── auth/             # Authentication patterns
│   ├── data-access/      # Database access patterns
│   └── observability/    # Logging, metrics, tracing
└── modules/             # Reusable infrastructure modules
    ├── terraform/        # Terraform modules
    └── kubernetes/       # K8s manifests
```

## Available Templates

### 1. Next.js + Supabase (`nextjs-supabase/`)

Full-stack web application template with:
- Next.js 16 + React 19 + TypeScript
- Supabase (Auth, Database, Storage)
- Tailwind CSS + shadcn/ui
- GitHub Actions (lint, test, preview, deploy)
- Pre-configured ESLint + Prettier

**Usage:**
```bash
npx degit platform/templates/nextjs-supabase my-app
cd my-app
npm install
```

### 2. FastAPI Service (`fastapi-service/`)

Backend API service template with:
- FastAPI + Pydantic v2
- OpenAPI auto-documentation
- Health checks + readiness probes
- Structured logging
- Docker + Kubernetes manifests

**Usage:**
```bash
cp -r platform/templates/fastapi-service my-service
cd my-service
uv venv && uv pip install -r requirements.txt
```

### 3. Supabase Edge Function (`edge-function/`)

Serverless function template with:
- Deno runtime
- TypeScript
- Secrets management
- Unit tests
- CI/CD integration

**Usage:**
```bash
supabase functions new my-function --template platform/templates/edge-function
```

## Golden Paths

Golden paths are reference implementations showing the recommended way to solve common problems.

### Authentication (`golden-paths/auth/`)

- JWT token handling
- Session management
- RBAC implementation
- RLS policy patterns

### Data Access (`golden-paths/data-access/`)

- Repository pattern
- Query optimization
- Connection pooling
- Migration strategies

### Observability (`golden-paths/observability/`)

- Structured logging format
- Metrics collection
- Distributed tracing
- Dashboard templates

## Contributing

1. Propose changes via PR to `platform/` directory
2. Get review from Platform team
3. Update documentation
4. Announce in `#platform-paved-road`

## Ownership

Maintained by: Platform/DevEx Team

Questions? Ask in `#platform-paved-road`
