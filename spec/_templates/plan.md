# {Project Name} - Implementation Plan

**Slug**: `{slug}`
**Version**: 0.1.0
**PRD**: [prd.md](./prd.md)
**Owner**: {owner}
**Last Updated**: {date}

---

## Overview

This plan breaks down the PRD into implementable phases with clear deliverables, dependencies, and verification criteria.

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │  Web UI  │  │ Mobile   │  │   CLI    │                   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                   │
└───────┼─────────────┼─────────────┼─────────────────────────┘
        │             │             │
        v             v             v
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                           │
│              (Authentication, Rate Limiting)                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        v               v               v
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Service A   │ │  Service B   │ │  Service C   │
│  (FastAPI)   │ │  (Odoo)      │ │  (Edge Fn)   │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       v                v                v
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ Supabase │  │  Redis   │  │  S3/DO   │                   │
│  │ Postgres │  │  Cache   │  │  Spaces  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 16 + React 19 | Web UI |
| API | FastAPI | REST/GraphQL |
| ERP | Odoo 18 CE | Business logic |
| Database | Supabase (PostgreSQL) | Primary data store |
| Cache | Redis | Session, rate limiting |
| Edge | Supabase Edge Functions | Serverless compute |
| Infra | DigitalOcean / Kubernetes | Container orchestration |

## Phases

### Phase 1: Foundation

**Goal**: Set up infrastructure and core scaffolding

**Duration**: {estimated_duration}

#### Tasks

| ID | Task | Owner | Dependencies | Status |
|----|------|-------|--------------|--------|
| P1.1 | Create database schema | implementer | - | Not Started |
| P1.2 | Set up Supabase project | implementer | - | Not Started |
| P1.3 | Configure RLS policies | implementer | P1.1 | Not Started |
| P1.4 | Create API scaffolding | implementer | P1.1 | Not Started |
| P1.5 | Set up CI/CD pipelines | cicd | - | Not Started |

#### Deliverables

- [ ] Database schema deployed to staging
- [ ] RLS policies configured and tested
- [ ] API skeleton with health endpoint
- [ ] CI/CD pipeline operational

#### Verification

```bash
# Health check passes
curl -f https://api.staging.{domain}/health

# Database accessible
psql $DATABASE_URL -c "SELECT 1"

# CI passes
gh run list --workflow=ci-python.yml --status=success
```

### Phase 2: Core Features

**Goal**: Implement MVP feature set

**Duration**: {estimated_duration}

#### Tasks

| ID | Task | Owner | Dependencies | Status |
|----|------|-------|--------------|--------|
| P2.1 | Implement {feature_1} | implementer | P1.4 | Not Started |
| P2.2 | Implement {feature_2} | implementer | P1.4 | Not Started |
| P2.3 | Write unit tests | implementer | P2.1, P2.2 | Not Started |
| P2.4 | Write integration tests | reviewer | P2.3 | Not Started |

#### Deliverables

- [ ] {Feature 1} functional in staging
- [ ] {Feature 2} functional in staging
- [ ] Test coverage >= 90%
- [ ] API documentation complete

### Phase 3: Integration & Polish

**Goal**: Connect all components, add observability

**Duration**: {estimated_duration}

#### Tasks

| ID | Task | Owner | Dependencies | Status |
|----|------|-------|--------------|--------|
| P3.1 | Integrate frontend with API | implementer | P2.1-P2.4 | Not Started |
| P3.2 | Set up monitoring dashboards | observability | P2.1 | Not Started |
| P3.3 | Configure alerts | sre | P3.2 | Not Started |
| P3.4 | Write runbooks | dx-docs | P3.3 | Not Started |
| P3.5 | Performance testing | chaos | P3.1 | Not Started |

#### Deliverables

- [ ] End-to-end flows working
- [ ] Dashboards deployed
- [ ] Alerts configured
- [ ] Runbooks complete
- [ ] Performance benchmarks met

### Phase 4: Release

**Goal**: Production deployment and validation

**Duration**: {estimated_duration}

#### Tasks

| ID | Task | Owner | Dependencies | Status |
|----|------|-------|--------------|--------|
| P4.1 | Security audit | policy | P3.* | Not Started |
| P4.2 | Deploy to canary | release | P4.1 | Not Started |
| P4.3 | Validate canary metrics | sre | P4.2 | Not Started |
| P4.4 | Full production rollout | release | P4.3 | Not Started |
| P4.5 | Post-deployment verification | sre | P4.4 | Not Started |

#### Deliverables

- [ ] Security audit passed
- [ ] Canary deployment successful
- [ ] Production deployment successful
- [ ] SLOs met for 24 hours

## Database Migrations

### Migration Strategy

```yaml
approach: "incremental"
zero_downtime: true
rollback_tested: true
```

### Planned Migrations

| Version | Name | Description | Breaking |
|---------|------|-------------|----------|
| 001 | create_base_tables | Initial schema | No |
| 002 | add_{feature}_tables | Feature-specific tables | No |
| 003 | add_indexes | Performance indexes | No |

### Rollback Plan

```bash
# Rollback to previous version
supabase db reset --db-url $DATABASE_URL --version {previous_version}

# Or manual rollback
psql $DATABASE_URL -f migrations/{version}_down.sql
```

## Rollout Strategy

### Environments

| Environment | URL | Purpose | Auto-deploy |
|-------------|-----|---------|-------------|
| Preview | pr-{num}.preview.{domain} | PR validation | Yes |
| Staging | staging.{domain} | Integration testing | On merge |
| Canary | canary.{domain} | Production validation | Manual |
| Production | {domain} | Live traffic | Manual |

### Traffic Progression

```
Preview (100% test traffic)
    │
    v
Staging (100% internal traffic)
    │
    v
Canary (10% production traffic)
    │
    v
Production (100% traffic)
```

### Rollback Triggers

- P99 latency > 500ms for 5 minutes
- Error rate > 1% for 5 minutes
- Any 5xx errors in critical paths
- Health check failures

### Rollback Command

```bash
# Instant rollback to previous version
./scripts/rollback.sh --env=production --to=previous

# Or specific version
./scripts/rollback.sh --env=production --to=v1.2.3
```

## Testing Strategy

### Test Pyramid

```
        /\
       /  \    E2E Tests (10%)
      /----\   - Critical user journeys
     /      \  - Cross-service flows
    /--------\
   /          \ Integration Tests (30%)
  /            \ - API contracts
 /--------------\ - Database operations
/                \
/------------------\ Unit Tests (60%)
                    - Business logic
                    - Pure functions
```

### Test Requirements

| Type | Coverage Target | Framework |
|------|-----------------|-----------|
| Unit | >= 90% | pytest |
| Integration | >= 80% | pytest + testcontainers |
| E2E | Critical paths | Playwright |

## Observability Plan

### Metrics to Track

| Metric | Type | Alert Threshold |
|--------|------|-----------------|
| request_latency_p99 | histogram | > 500ms |
| request_error_rate | counter | > 1% |
| database_connections | gauge | > 80% pool |
| cache_hit_rate | gauge | < 80% |

### Dashboards

- [ ] Service overview
- [ ] Error analysis
- [ ] Performance breakdown
- [ ] Business metrics

### Log Format

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "{service_name}",
  "trace_id": "{trace_id}",
  "message": "{message}",
  "context": {}
}
```

## Risk Register

| Risk | Impact | Probability | Mitigation | Owner |
|------|--------|-------------|------------|-------|
| Database migration fails | High | Low | Test in staging, rollback script | implementer |
| Performance regression | Medium | Medium | Load testing, canary | sre |
| Security vulnerability | High | Low | Security audit, SAST/DAST | policy |

## Dependencies & Blockers

### External Dependencies

| Dependency | Status | Owner | ETA |
|------------|--------|-------|-----|
| {external_service} | Pending | {team} | {date} |

### Internal Blockers

| Blocker | Impact | Resolution | Owner |
|---------|--------|------------|-------|
| {blocker} | {impact} | {resolution} | {owner} |

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Tech Lead | | | Pending |
| SRE | | | Pending |
| Security | | | Pending |

---

*Plan last updated: {date}*
