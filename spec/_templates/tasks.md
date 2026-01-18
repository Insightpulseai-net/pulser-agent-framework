# {Project Name} - Task Breakdown

**Slug**: `{slug}`
**Plan**: [plan.md](./plan.md)
**Owner**: {owner}
**Last Updated**: {date}

---

## Task Legend

| Status | Symbol | Description |
|--------|--------|-------------|
| Not Started | `[ ]` | Task not yet begun |
| In Progress | `[~]` | Currently being worked on |
| Blocked | `[!]` | Waiting on dependency/blocker |
| Complete | `[x]` | Task finished and verified |
| Cancelled | `[-]` | Task no longer needed |

## Phase 1: Foundation

### P1.1: Database Schema Setup

**Assignee**: implementer
**Priority**: P0
**Dependencies**: None

#### Subtasks

- [ ] Design entity-relationship diagram
- [ ] Create migration files for base tables
- [ ] Add foreign key constraints
- [ ] Create indexes for common queries
- [ ] Write down migration

#### Acceptance Criteria

- [ ] ERD reviewed and approved
- [ ] Migrations run successfully on clean database
- [ ] Down migrations restore previous state
- [ ] No orphaned records after migrations

#### Work Order

```yaml
intent: "Create foundational database schema"
scope:
  - supabase/migrations/
  - docs/database-schema.md
constraints:
  - Must support zero-downtime migrations
  - Must include RLS policies
acceptance:
  - Migrations pass in CI
  - Schema matches ERD
  - RLS policies verified
rollback: |
  supabase migration repair --status reverted
  supabase db reset
```

---

### P1.2: Supabase Project Configuration

**Assignee**: implementer
**Priority**: P0
**Dependencies**: None

#### Subtasks

- [ ] Create Supabase project
- [ ] Configure environment variables
- [ ] Set up database connection pooling
- [ ] Enable Row Level Security
- [ ] Configure auth providers

#### Acceptance Criteria

- [ ] Project accessible via Supabase dashboard
- [ ] Connection pooling enabled (>50 connections)
- [ ] RLS enabled on all tables
- [ ] Service role key stored securely

---

### P1.3: RLS Policies

**Assignee**: implementer
**Priority**: P0
**Dependencies**: P1.1

#### Subtasks

- [ ] Define access patterns per table
- [ ] Write RLS policies
- [ ] Test policies with different roles
- [ ] Document policy decisions

#### Acceptance Criteria

- [ ] All tables have RLS enabled
- [ ] Policies tested with unit tests
- [ ] No data leakage in cross-tenant queries
- [ ] Performance impact < 5ms per query

#### Work Order

```yaml
intent: "Implement row-level security for multi-tenant isolation"
scope:
  - supabase/migrations/*_rls.sql
  - tests/security/test_rls.py
constraints:
  - Must support org-based isolation
  - Must allow service role bypass
acceptance:
  - All RLS tests pass
  - Security review approved
rollback: |
  -- Disable RLS (emergency only)
  ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;
```

---

### P1.4: API Scaffolding

**Assignee**: implementer
**Priority**: P0
**Dependencies**: P1.1

#### Subtasks

- [ ] Create FastAPI project structure
- [ ] Set up dependency injection
- [ ] Configure CORS and middleware
- [ ] Create health check endpoint
- [ ] Set up error handling
- [ ] Configure logging

#### Acceptance Criteria

- [ ] `GET /health` returns 200
- [ ] OpenAPI spec auto-generated
- [ ] Request logging working
- [ ] Error responses follow standard format

---

### P1.5: CI/CD Pipeline

**Assignee**: cicd
**Priority**: P0
**Dependencies**: None

#### Subtasks

- [ ] Create PR check workflow
- [ ] Create release gates workflow
- [ ] Set up preview environments
- [ ] Configure secrets in GitHub
- [ ] Set up SBOM generation

#### Acceptance Criteria

- [ ] PRs trigger lint/test/build
- [ ] Merge to main triggers staging deploy
- [ ] Release tags trigger production deploy
- [ ] SBOM generated for each release

---

## Phase 2: Core Features

### P2.1: {Feature 1 Name}

**Assignee**: implementer
**Priority**: P0
**Dependencies**: P1.4

#### Subtasks

- [ ] Create data models
- [ ] Implement API endpoints
- [ ] Write business logic
- [ ] Add input validation
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Update API documentation

#### Acceptance Criteria

- [ ] All endpoints return correct responses
- [ ] Validation errors return 422
- [ ] Test coverage >= 90%
- [ ] API docs updated

#### Work Order

```yaml
intent: "Implement {feature_1} functionality"
scope:
  - apps/workbench-api/src/{feature}/
  - tests/{feature}/
  - specs/openapi/{feature}.yaml
constraints:
  - Must follow existing patterns
  - Must include rate limiting
acceptance:
  - Unit tests pass
  - Integration tests pass
  - Manual QA approved
rollback: |
  git revert {commit_sha}
```

---

### P2.2: {Feature 2 Name}

**Assignee**: implementer
**Priority**: P1
**Dependencies**: P1.4

#### Subtasks

- [ ] {subtask_1}
- [ ] {subtask_2}
- [ ] {subtask_3}
- [ ] Write tests
- [ ] Update docs

#### Acceptance Criteria

- [ ] {criterion_1}
- [ ] {criterion_2}
- [ ] Test coverage >= 90%

---

## Phase 3: Integration & Polish

### P3.1: Frontend Integration

**Assignee**: implementer
**Priority**: P0
**Dependencies**: P2.1, P2.2

#### Subtasks

- [ ] Create API client
- [ ] Implement UI components
- [ ] Add loading states
- [ ] Add error handling
- [ ] Write E2E tests

#### Acceptance Criteria

- [ ] All user flows working
- [ ] E2E tests pass
- [ ] Lighthouse score > 90
- [ ] Accessible (WCAG 2.1 AA)

---

### P3.2: Monitoring Dashboards

**Assignee**: observability
**Priority**: P1
**Dependencies**: P2.1

#### Subtasks

- [ ] Create service overview dashboard
- [ ] Create error analysis dashboard
- [ ] Create performance dashboard
- [ ] Set up log aggregation
- [ ] Configure trace sampling

#### Acceptance Criteria

- [ ] All dashboards deployed
- [ ] Key metrics visible
- [ ] Logs searchable
- [ ] Traces connected to requests

---

### P3.3: Alerting

**Assignee**: sre
**Priority**: P1
**Dependencies**: P3.2

#### Subtasks

- [ ] Define alert thresholds
- [ ] Create PagerDuty integration
- [ ] Configure escalation policies
- [ ] Test alerts with synthetic failures
- [ ] Document runbooks for each alert

#### Acceptance Criteria

- [ ] All alerts have runbooks
- [ ] Escalation tested
- [ ] No alert fatigue (< 5 alerts/week)

---

### P3.4: Runbooks

**Assignee**: dx-docs
**Priority**: P1
**Dependencies**: P3.3

#### Subtasks

- [ ] Create runbook template
- [ ] Write runbook for each service
- [ ] Document common issues
- [ ] Add rollback procedures
- [ ] Review with SRE

#### Acceptance Criteria

- [ ] All services have runbooks
- [ ] Runbooks tested during chaos drill
- [ ] On-call team trained

---

### P3.5: Performance Testing

**Assignee**: chaos
**Priority**: P1
**Dependencies**: P3.1

#### Subtasks

- [ ] Create load test scenarios
- [ ] Run baseline tests
- [ ] Identify bottlenecks
- [ ] Optimize critical paths
- [ ] Document findings

#### Acceptance Criteria

- [ ] P99 latency < target
- [ ] System handles 2x expected load
- [ ] No memory leaks
- [ ] Database connections stable

---

## Phase 4: Release

### P4.1: Security Audit

**Assignee**: policy
**Priority**: P0
**Dependencies**: P3.*

#### Subtasks

- [ ] Run SAST scan
- [ ] Run DAST scan
- [ ] Review RLS policies
- [ ] Check secrets management
- [ ] Verify auth flows

#### Acceptance Criteria

- [ ] No critical vulnerabilities
- [ ] No high vulnerabilities
- [ ] Medium issues documented
- [ ] Security review signed off

---

### P4.2: Canary Deployment

**Assignee**: release
**Priority**: P0
**Dependencies**: P4.1

#### Subtasks

- [ ] Create release tag
- [ ] Deploy to canary
- [ ] Configure traffic split (10%)
- [ ] Monitor for 4 hours
- [ ] Validate key metrics

#### Acceptance Criteria

- [ ] Canary deployment successful
- [ ] Error rate < 0.1%
- [ ] Latency within baseline
- [ ] No rollback triggered

---

### P4.3: Production Rollout

**Assignee**: release
**Priority**: P0
**Dependencies**: P4.2

#### Subtasks

- [ ] Get SRE approval
- [ ] Execute production deploy
- [ ] Monitor for 24 hours
- [ ] Validate all SLOs
- [ ] Close release

#### Acceptance Criteria

- [ ] Production deployment successful
- [ ] All SLOs met for 24 hours
- [ ] No incidents
- [ ] Release notes published

---

## Backlog

> Tasks identified but not yet scheduled

| ID | Task | Priority | Notes |
|----|------|----------|-------|
| B1 | {future_task_1} | P2 | {notes} |
| B2 | {future_task_2} | P2 | {notes} |

---

## Completed Tasks

> Move tasks here when complete for historical reference

| ID | Task | Completed | PR/Commit |
|----|------|-----------|-----------|
| | | | |

---

*Tasks last updated: {date}*
