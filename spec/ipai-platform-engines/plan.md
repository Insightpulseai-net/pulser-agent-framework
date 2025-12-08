# InsightPulseAI Platform Engines - Implementation Plan

## Document Control
- **Version**: 1.0.0
- **Status**: Draft
- **Last Updated**: 2025-12-08
- **Author**: InsightPulseAI Platform Team

---

## 1. Implementation Overview

This plan outlines the phased implementation of the InsightPulseAI Platform Engines architecture. The approach prioritizes foundational platform engines (H1-H8) first, then wires domain engines (TE-Cheq, Retail, Creative) on top.

### 1.1 Implementation Principles

1. **Foundation First**: Platform engines before domain engines
2. **Vertical Anchors**: Each phase delivers value to at least one vertical
3. **Incremental Value**: Working software at every milestone
4. **Shared Spine**: No siloed implementations

---

## 2. Phase Overview

```
Phase 1: Platform Foundation
    |
    v
Phase 2: Vertical Anchors (TE-Cheq + SariCoach)
    |
    v
Phase 3: Unified Agents & Experience
    |
    v
Phase 4: Advanced Features & RCT
```

---

## 3. Phase 1: Platform Foundation

### 3.1 Objectives

- Establish core platform engines (H1, H3, H5, H8)
- Implement identity and tenant model
- Set up data layer with Bronze/Silver/Gold pattern
- Deploy basic observability

### 3.2 Deliverables

#### H1 - Identity & Org Engine

**Schema**: `identity.*`

```sql
-- Core identity tables
identity.tenants
identity.users
identity.roles
identity.user_roles
identity.org_units
identity.permissions
```

**Deliverables**:
- [ ] Create identity schema migration
- [ ] Implement RLS policies for tenant isolation
- [ ] Wire Supabase Auth integration
- [ ] Create role hierarchy (viewer, user, manager, admin)
- [ ] Document RBAC matrix

---

#### H3 - Data & Knowledge Engine

**Schema**: `analytics.*`, domain schemas

**Deliverables**:
- [ ] Implement Bronze/Silver/Gold layer pattern
- [ ] Create base schema templates per vertical
- [ ] Set up pgvector for embeddings
- [ ] Create `ai.knowledge_chunks` table
- [ ] Implement materialized view refresh strategy

**Index Strategy**:
```sql
-- High-traffic table indices
CREATE INDEX idx_sales_daily_store_date ON analytics.sales_daily(store_id, date);
CREATE INDEX idx_agent_sessions_tenant ON ai.agent_sessions(tenant_id, created_at);
CREATE INDEX idx_knowledge_chunks_embedding ON ai.knowledge_chunks USING ivfflat(embedding);
```

---

#### H5 - Automation & Orchestration Engine

**Runtime**: `n8n.insightpulseai.net`

**Deliverables**:
- [ ] Set up n8n workspace for platform
- [ ] Create event schema (`orchestration.events`)
- [ ] Implement base workflow templates:
  - ETL trigger template
  - Approval workflow template
  - Alert routing template
- [ ] Wire Supabase webhook triggers
- [ ] Set up basic cron schedules

---

#### H8 - Governance & Observability Engine

**Schema**: `governance.*`

**Deliverables**:
- [ ] Create audit logging tables
- [ ] Implement cost tracking schema
- [ ] Set up basic metrics collection
- [ ] Create alert routing rules
- [ ] Deploy Grafana dashboard templates

---

### 3.3 Phase 1 Acceptance Criteria

- [ ] All tenants isolated via RLS
- [ ] At least 3 roles functional with RBAC
- [ ] Bronze/Silver/Gold pattern working for 1 vertical
- [ ] n8n running with 3+ workflow templates
- [ ] Audit logs capturing all data access

---

## 4. Phase 2: Vertical Anchors

### 4.1 Objectives

- Deploy TE-Cheq domain engines
- Deploy SariCoach production flow
- Wire PH Data Intelligence foundation
- Implement agent router (H7)

### 4.2 TE-Cheq Vertical

#### Travel & Expense Engine

**Schema**: `teq.*`

```sql
teq.cash_advances
teq.expense_reports
teq.expenses
teq.expense_receipts
```

**Deliverables**:
- [ ] Create teq schema migration
- [ ] Implement expense workflow state machine
- [ ] Wire OCR service integration
- [ ] Create Edge Functions:
  - `/teq/expense/create`
  - `/teq/expense/submit`
  - `/teq/expense/approve`
  - `/teq/expense/receipt/upload`
- [ ] Set up Odoo HR Expense sync via n8n

---

#### Rate & SRM Engine

**Schema**: `teq.*`

```sql
teq.roles
teq.vendors
teq.consultants
teq.rate_card_versions
teq.rate_card_items
teq.client_overrides
teq.employee_rates
teq.v_public_rates (view)
```

**Deliverables**:
- [ ] Create rate engine schema
- [ ] Implement effective rate lookup logic
- [ ] Create rate inquiry workflow
- [ ] Wire RLS for FD-only tables
- [ ] Create Edge Functions:
  - `/teq/rates/effective-rate`
  - `/teq/rates/card/upsert`
  - `/teq/rates/override/upsert`

---

#### PPM & Budget Engine

**Schema**: `teq.*`

```sql
teq.portfolios
teq.projects
teq.project_workstreams
teq.rate_inquiries
teq.rate_suggestions
teq.project_budget_templates
teq.project_budget_lines
```

**Deliverables**:
- [ ] Create PPM schema
- [ ] Implement project hierarchy
- [ ] Wire rate engine for budget pricing
- [ ] Create AI budget generation endpoint
- [ ] Set up Odoo quote sync

---

### 4.3 SariCoach Vertical

#### Store Coach Engine

**Schema**: `saricoach.*`

```sql
saricoach.stores
saricoach.transactions
saricoach.transaction_items
saricoach.shelf_events
saricoach.stt_events
saricoach.coach_sessions
```

**Deliverables**:
- [ ] Create saricoach schema migration
- [ ] Implement store_day_metrics Gold view
- [ ] Wire Gemini API integration
- [ ] Implement 3-agent pipeline:
  - PlannerAgent
  - DataAnalystAgent
  - CoachAgent
- [ ] Create Edge Functions:
  - `/coach/analyze_store`
  - `/coach/generate_plan`
- [ ] Deploy frontend to Vercel

---

### 4.4 H7 - Experience & Agent Engine

**Schema**: `ai.*`

```sql
ai.agents
ai.skills
ai.agent_skills
ai.prompt_templates
ai.agent_sessions
ai.agent_messages
ai.agent_judgments
ai.agent_human_feedback
```

**Deliverables**:
- [ ] Create agent registry schema
- [ ] Implement agent router Edge Function
- [ ] Register initial agents:
  - TE-Cheq Financist
  - SariCoach Coach
  - Tax Agent
- [ ] Create skill definitions
- [ ] Wire model gateway (Claude/Gemini abstraction)
- [ ] Implement session logging

---

### 4.5 PH Data Intelligence Engine

**Schema**: `ph_intel.*`

```sql
ph_intel.sources
ph_intel.datasets
ph_intel.macro_indicators
ph_intel.retail_trends
ph_intel.media_trends
ph_intel.consumer_segments
```

**Deliverables**:
- [ ] Create ph_intel schema
- [ ] Implement 1-2 PH data source ingestion
- [ ] Create retail trends view
- [ ] Wire to SariCoach for context enrichment

---

### 4.6 Phase 2 Acceptance Criteria

- [ ] TE-Cheq: All 6 domain engines deployed
- [ ] TE-Cheq: Expense workflow end-to-end working
- [ ] SariCoach: Production coach flow operational
- [ ] Agent router: >= 3 agents registered
- [ ] PH Intel: At least 1 data source flowing

---

## 5. Phase 3: Unified Agents & Experience

### 5.1 Objectives

- Unify agent experience across tenants
- Deploy evaluation framework
- Implement cost controls
- Launch tenant dashboards

### 5.2 Deliverables

#### Agent Evaluation Framework

**Deliverables**:
- [ ] Implement AI judge prompts
- [ ] Create evaluation pipeline
- [ ] Wire human feedback collection
- [ ] Build evaluation dashboard
- [ ] Set up certification process

---

#### Tenant-Specific Agents

**Deliverables**:
- [ ] TBWA tenant setup:
  - Finance portal + TE-Cheq assistant
  - CES assistant (basic)
- [ ] Prisma tenant setup:
  - Prisma consulting assistant
  - PH intel access

---

#### Cost Control System

**Deliverables**:
- [ ] Implement per-tenant token budgets
- [ ] Create cost tracking dashboard
- [ ] Set up budget alerts
- [ ] Implement circuit breaker at 80%

---

#### H6 - Creative / GenAI Engine

**Schema**: `creative.*`

```sql
creative.templates
creative.artifacts
creative.generations
```

**Deliverables**:
- [ ] Create creative schema
- [ ] Implement template management
- [ ] Wire fal.ai integration (optional)
- [ ] Create generation logging

---

### 5.3 Phase 3 Acceptance Criteria

- [ ] Evaluation: AI judges scoring all agents
- [ ] Evaluation: Human feedback flow operational
- [ ] Tenants: TBWA tenant live with 2+ agents
- [ ] Tenants: Prisma tenant live with consulting assistant
- [ ] Costs: Budget tracking and alerts working

---

## 6. Phase 4: Advanced Features & RCT

### 6.1 Objectives

- Enable RCT/experiment support
- Extend retail engines
- Optimize performance
- Scale infrastructure

### 6.2 Deliverables

#### RCT Support

**Deliverables**:
- [ ] Create research schema for consent tracking
- [ ] Implement A/B experiment framework
- [ ] Build anonymization pipelines
- [ ] Partner with PH university
- [ ] Document IRB process

---

#### Retail OS Extensions

**Deliverables**:
- [ ] Scout dashboard improvements
- [ ] AR/creative recommendation APIs
- [ ] Brand sponsor portal
- [ ] Retail Recommendation Engine (basic)

---

#### Performance Optimization

**Deliverables**:
- [ ] Query optimization audit
- [ ] Connection pooling tuning
- [ ] Caching layer (Redis optional)
- [ ] Load testing and benchmarking

---

### 6.3 Phase 4 Acceptance Criteria

- [ ] RCT: Consent framework operational
- [ ] RCT: 1 pilot study designed
- [ ] Performance: p95 latency < 2s for agent calls
- [ ] Scale: Support 50+ concurrent users

---

## 7. Technical Architecture

### 7.1 Supabase Schema Layout

```
supabase/migrations/
  001_identity_foundation.sql      # Phase 1: H1 tables
  002_governance_audit.sql         # Phase 1: H8 tables
  003_teq_travel_expense.sql       # Phase 2: T&E engine
  004_teq_rates_srm.sql            # Phase 2: Rate engine
  005_teq_inventory.sql            # Phase 2: Library engine
  006_teq_ppm.sql                  # Phase 2: PPM engine
  007_teq_maintenance.sql          # Phase 2: Maintenance
  008_saricoach_core.sql           # Phase 2: SariCoach
  009_ai_agents.sql                # Phase 2: H7 tables
  010_ph_intel.sql                 # Phase 2: PH data
  011_creative.sql                 # Phase 3: H6 tables
  012_research_rct.sql             # Phase 4: RCT support
```

### 7.2 Edge Functions Layout

```
supabase/functions/
  agent-router/                    # H7: Unified agent entry point
  teq-expense/                     # TE-Cheq expense APIs
  teq-rates/                       # TE-Cheq rate APIs
  teq-ppm/                         # TE-Cheq PPM APIs
  coach-analyze/                   # SariCoach analysis
  coach-plan/                      # SariCoach planning
  dmx-search/                      # Intelligence search
```

### 7.3 n8n Workflows

```
n8n/workflows/
  etl/
    daily_silver_refresh.json
    weekly_gold_refresh.json
  approvals/
    expense_approval.json
    budget_approval.json
  alerts/
    anomaly_alert.json
    cost_budget_alert.json
  sync/
    odoo_expense_sync.json
    odoo_quote_sync.json
```

---

## 8. Dependencies & Prerequisites

### 8.1 Infrastructure

- [ ] Supabase project provisioned
- [ ] DigitalOcean droplets allocated
- [ ] n8n instance deployed
- [ ] Superset instance configured
- [ ] Domain DNS configured

### 8.2 External Services

- [ ] Supabase Auth configured
- [ ] Claude API access
- [ ] Gemini API access
- [ ] OCR service deployed
- [ ] Odoo instance accessible

### 8.3 Team

- Platform Team: H1-H8 engines
- Finance Team: TE-Cheq domain engines
- Retail Team: SariCoach/Scout engines
- Security: RLS policies, audit

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Scope creep | Strict PRD adherence, phase gates |
| Integration failures | Contract-first APIs, mocked dependencies |
| Performance issues | Early load testing, index strategy |
| Security gaps | Continuous RLS audits, pen testing |
| Team bandwidth | Clear ownership, modular work |

---

## 10. Success Metrics

### Phase 1 Exit Criteria

| Metric | Target |
|--------|--------|
| Platform engines deployed | 4/4 (H1, H3, H5, H8) |
| Tenants isolated | 100% via RLS |
| n8n workflows active | >= 3 |
| Audit coverage | 100% for identity ops |

### Phase 2 Exit Criteria

| Metric | Target |
|--------|--------|
| TE-Cheq engines deployed | 6/6 |
| SariCoach coach flow | End-to-end working |
| Agents registered | >= 3 |
| Agent latency p95 | < 3s |

### Phase 3 Exit Criteria

| Metric | Target |
|--------|--------|
| Active tenants | >= 2 |
| AI evaluation coverage | 100% of agents |
| Human feedback rate | >= 10% of sessions |
| Cost tracking accuracy | 100% |

### Phase 4 Exit Criteria

| Metric | Target |
|--------|--------|
| RCT framework ready | Consent + anonymization |
| Performance p95 | < 2s for agent calls |
| Concurrent users supported | 50+ |
| Verticals on platform | >= 3 |

---

## Appendix A: Related Documents

- [Product Requirements Document](./prd.md)
- [Constitution](./constitution.md)
- [Task Breakdown](./tasks.md)
