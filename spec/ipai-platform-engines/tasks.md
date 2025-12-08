# InsightPulseAI Platform Engines - Task Breakdown

## Document Control
- **Version**: 1.0.0
- **Status**: Draft
- **Last Updated**: 2025-12-08
- **Source**: Implementation Plan (plan.md)

---

## Task Legend

- **Priority**: P0 (Critical), P1 (High), P2 (Medium), P3 (Low)
- **Status**: `[ ]` Not Started, `[~]` In Progress, `[x]` Complete
- **Owner**: Platform, Finance, Retail, Creative, Security

---

## Phase 1: Platform Foundation

### P0 - Critical Blockers

#### P0.1 Identity & Org Engine (H1)

**Owner**: Platform

- [ ] Create `identity` schema migration
  - [ ] `identity.tenants` - multi-tenant root table
  - [ ] `identity.users` - user accounts
  - [ ] `identity.roles` - role definitions
  - [ ] `identity.user_roles` - role assignments
  - [ ] `identity.org_units` - organizational hierarchy
  - [ ] `identity.permissions` - granular permissions

- [ ] Implement RLS policies
  - [ ] Tenant isolation policy template
  - [ ] Apply to all identity tables
  - [ ] Test cross-tenant isolation

- [ ] Wire Supabase Auth
  - [ ] Configure auth providers
  - [ ] Set up JWT claims for tenant/role
  - [ ] Create auth trigger for user sync

- [ ] Create role hierarchy
  - [ ] Define: viewer, user, manager, admin
  - [ ] Create permission matrix
  - [ ] Document in `RBAC_MATRIX.md`

---

#### P0.2 Data & Knowledge Engine (H3)

**Owner**: Platform

- [ ] Implement Bronze/Silver/Gold pattern
  - [ ] Create template migration for pattern
  - [ ] Document layer conventions
  - [ ] Create sample pipeline

- [ ] Set up pgvector
  - [ ] Enable pgvector extension
  - [ ] Create `ai.knowledge_chunks` table
  - [ ] Add HNSW index for embeddings

- [ ] Create base schema templates
  - [ ] `_template_bronze.sql`
  - [ ] `_template_silver.sql`
  - [ ] `_template_gold.sql`

- [ ] Implement refresh strategy
  - [ ] Materialized view refresh functions
  - [ ] Incremental update patterns
  - [ ] n8n trigger integration

---

#### P0.3 Automation & Orchestration Engine (H5)

**Owner**: Platform

- [ ] Set up n8n workspace
  - [ ] Create platform workspace
  - [ ] Configure Supabase credentials
  - [ ] Set up webhook endpoints

- [ ] Create event schema
  - [ ] `orchestration.events` table
  - [ ] Event types enumeration
  - [ ] Event producer/consumer docs

- [ ] Create workflow templates
  - [ ] ETL trigger template
  - [ ] Approval workflow template
  - [ ] Alert routing template
  - [ ] Odoo sync template

- [ ] Wire Supabase triggers
  - [ ] Database webhook setup
  - [ ] n8n webhook receivers
  - [ ] Error handling

---

#### P0.4 Governance & Observability Engine (H8)

**Owner**: Platform + Security

- [ ] Create audit schema
  - [ ] `governance.audit_logs` table
  - [ ] Audit triggers on identity tables
  - [ ] Retention policy

- [ ] Implement cost tracking
  - [ ] `governance.cost_tracking` table
  - [ ] Token usage schema
  - [ ] Aggregation views

- [ ] Set up metrics collection
  - [ ] Define key metrics
  - [ ] Create metrics tables
  - [ ] Grafana dashboard templates

- [ ] Create alert routing
  - [ ] Alert severity levels
  - [ ] Routing rules (Slack, email)
  - [ ] Escalation paths

---

### P1 - Architecture Alignment

#### P1.1 Index Strategy

**Owner**: Platform

- [ ] Document index strategy
  - [ ] Create `INDEX_STRATEGY.md`
  - [ ] High-traffic table analysis
  - [ ] Performance benchmarks

- [ ] Create core indices
  - [ ] `identity.*` tables
  - [ ] `governance.*` tables
  - [ ] Cross-reference queries

- [ ] Implement index monitoring
  - [ ] Unused index detection
  - [ ] Missing index suggestions
  - [ ] Periodic review process

---

#### P1.2 API Contract Standards

**Owner**: Platform

- [ ] Define API standards
  - [ ] Response format schema
  - [ ] Error code catalog
  - [ ] Versioning strategy

- [ ] Create Edge Function template
  - [ ] Standard request handling
  - [ ] Auth/RBAC middleware
  - [ ] Error handling patterns

- [ ] Document in `API_STANDARDS.md`

---

## Phase 2: Vertical Anchors

### P0 - TE-Cheq Engines

#### P0.5 Travel & Expense Engine

**Owner**: Finance

- [ ] Create teq schema migration
  - [ ] `teq.cash_advances`
  - [ ] `teq.expense_reports`
  - [ ] `teq.expenses`
  - [ ] `teq.expense_receipts`

- [ ] Implement workflow state machine
  - [ ] Define states: draft, submitted, approved, released, closed
  - [ ] State transition rules
  - [ ] Validation at each transition

- [ ] Wire OCR integration
  - [ ] Receipt upload endpoint
  - [ ] OCR service call
  - [ ] Result mapping to expense

- [ ] Create Edge Functions
  - [ ] `POST /teq/expense/create`
  - [ ] `POST /teq/expense/submit`
  - [ ] `POST /teq/expense/approve`
  - [ ] `POST /teq/expense/receipt/upload`

- [ ] Set up Odoo sync
  - [ ] HR Expense model mapping
  - [ ] n8n sync workflow
  - [ ] Conflict resolution

---

#### P0.6 Rate & SRM Engine

**Owner**: Finance

- [ ] Create rate schema
  - [ ] `teq.roles`
  - [ ] `teq.vendors`
  - [ ] `teq.consultants`
  - [ ] `teq.rate_card_versions`
  - [ ] `teq.rate_card_items`
  - [ ] `teq.client_overrides`
  - [ ] `teq.employee_rates`

- [ ] Create `v_public_rates` view
  - [ ] Non-FD accessible view
  - [ ] Effective date logic
  - [ ] Override resolution

- [ ] Implement effective rate lookup
  - [ ] Client override priority
  - [ ] Version resolution
  - [ ] Currency handling

- [ ] Create Edge Functions
  - [ ] `GET /teq/rates/effective-rate`
  - [ ] `POST /teq/rates/card/upsert`
  - [ ] `POST /teq/rates/override/upsert`

- [ ] Wire RLS for FD-only tables
  - [ ] Define FD role check
  - [ ] Apply to sensitive tables

---

#### P0.7 PPM & Budget Engine

**Owner**: Finance

- [ ] Create PPM schema
  - [ ] `teq.portfolios`
  - [ ] `teq.projects`
  - [ ] `teq.project_workstreams`
  - [ ] `teq.rate_inquiries`
  - [ ] `teq.rate_suggestions`
  - [ ] `teq.project_budget_templates`
  - [ ] `teq.project_budget_lines`

- [ ] Implement project hierarchy
  - [ ] Portfolio -> Project -> Workstream
  - [ ] Budget rollup logic
  - [ ] Status propagation

- [ ] Wire rate engine
  - [ ] Rate inquiry to suggestion
  - [ ] Budget line pricing
  - [ ] Margin calculations

- [ ] Create AI budget generation
  - [ ] Template selection
  - [ ] Rate lookup integration
  - [ ] Suggestion refinement

- [ ] Set up Odoo quote sync
  - [ ] Quote model mapping
  - [ ] Bidirectional sync
  - [ ] Approval state sync

---

#### P0.8 Library / Inventory Engine

**Owner**: Finance

- [ ] Create inventory schema
  - [ ] `teq.asset_locations`
  - [ ] `teq.asset_categories`
  - [ ] `teq.assets`
  - [ ] `teq.asset_reservations`
  - [ ] `teq.asset_movements`

- [ ] Implement reservation logic
  - [ ] Availability checking
  - [ ] Conflict detection
  - [ ] Auto-release rules

- [ ] Create Edge Functions
  - [ ] `POST /teq/inventory/reserve`
  - [ ] `POST /teq/inventory/checkout`
  - [ ] `POST /teq/inventory/checkin`
  - [ ] `GET /teq/inventory/availability`

---

#### P0.9 Maintenance Engine

**Owner**: Finance

- [ ] Create maintenance schema
  - [ ] `teq.maintenance_plans`
  - [ ] `teq.maintenance_jobs`

- [ ] Implement scheduling
  - [ ] Recurring job generation
  - [ ] Conflict with reservations
  - [ ] Completion tracking

---

### P0 - SariCoach Engine

#### P0.10 Store Coach Engine

**Owner**: Retail

- [ ] Create saricoach schema
  - [ ] `saricoach.stores`
  - [ ] `saricoach.transactions`
  - [ ] `saricoach.transaction_items`
  - [ ] `saricoach.shelf_events`
  - [ ] `saricoach.stt_events`
  - [ ] `saricoach.coach_sessions`

- [ ] Implement Gold views
  - [ ] `analytics.store_day_metrics`
  - [ ] `analytics.brand_store_day_metrics`
  - [ ] `analytics.store_trends`

- [ ] Wire Gemini integration
  - [ ] API client setup
  - [ ] Rate limiting
  - [ ] Error handling

- [ ] Implement 3-agent pipeline
  - [ ] PlannerAgent - goal classification
  - [ ] DataAnalystAgent - feature computation
  - [ ] CoachAgent - recommendation generation

- [ ] Create Edge Functions
  - [ ] `POST /coach/analyze_store`
  - [ ] `POST /coach/generate_plan`

- [ ] Deploy frontend
  - [ ] Vercel deployment
  - [ ] API proxy configuration
  - [ ] Error/loading states

---

### P0 - Agent Engine

#### P0.11 Experience & Agent Engine (H7)

**Owner**: Platform

- [ ] Create agent registry schema
  - [ ] `ai.agents`
  - [ ] `ai.skills`
  - [ ] `ai.agent_skills`
  - [ ] `ai.prompt_templates`
  - [ ] `ai.agent_sessions`
  - [ ] `ai.agent_messages`

- [ ] Implement agent router
  - [ ] Edge Function: `/functions/v1/agent-router`
  - [ ] Agent lookup by slug
  - [ ] Skill/tool resolution
  - [ ] Context assembly

- [ ] Register initial agents
  - [ ] TE-Cheq Financist
  - [ ] SariCoach Coach
  - [ ] Tax Agent

- [ ] Create skill definitions
  - [ ] Input/output schemas
  - [ ] Required roles
  - [ ] Rate limits

- [ ] Wire model gateway
  - [ ] Claude/Gemini abstraction
  - [ ] Tenant routing
  - [ ] Usage logging

- [ ] Implement session logging
  - [ ] Session creation
  - [ ] Message logging
  - [ ] Metadata capture

---

### P1 - PH Data Intelligence

#### P1.3 PH Intel Engine

**Owner**: Platform

- [ ] Create ph_intel schema
  - [ ] `ph_intel.sources`
  - [ ] `ph_intel.datasets`
  - [ ] `ph_intel.macro_indicators`
  - [ ] `ph_intel.retail_trends`
  - [ ] `ph_intel.consumer_segments`

- [ ] Implement source ingestion
  - [ ] PSA data connector
  - [ ] BSP data connector
  - [ ] Schedule refresh

- [ ] Create retail trends view
  - [ ] Category performance
  - [ ] Regional patterns
  - [ ] Seasonal adjustments

- [ ] Wire to SariCoach
  - [ ] Context enrichment
  - [ ] Trend overlay
  - [ ] Insight generation

---

## Phase 3: Unified Agents & Experience

### P1 - Agent Evaluation

#### P1.4 Evaluation Framework

**Owner**: Platform

- [ ] Create evaluation schema
  - [ ] `ai.agent_judgments`
  - [ ] `ai.agent_human_feedback`
  - [ ] `ai.agent_experiments`

- [ ] Implement AI judges
  - [ ] Factuality judge prompt
  - [ ] Actionability judge prompt
  - [ ] Safety judge prompt

- [ ] Create evaluation pipeline
  - [ ] Async evaluation trigger
  - [ ] Score aggregation
  - [ ] Threshold alerts

- [ ] Wire human feedback
  - [ ] UI components (thumbs up/down)
  - [ ] Feedback API
  - [ ] Analytics dashboard

- [ ] Set up certification process
  - [ ] Benchmark definitions
  - [ ] Certification criteria
  - [ ] Version tagging

---

### P1 - Cost Controls

#### P1.5 Budget & Cost System

**Owner**: Platform

- [ ] Implement token budgets
  - [ ] Per-tenant budget table
  - [ ] Usage tracking
  - [ ] Budget period (monthly)

- [ ] Create cost dashboard
  - [ ] Grafana/Superset views
  - [ ] Per-agent breakdown
  - [ ] Trend analysis

- [ ] Set up alerts
  - [ ] 50% threshold alert
  - [ ] 75% threshold alert
  - [ ] 80% circuit breaker

---

### P1 - Tenant Setup

#### P1.6 TBWA Tenant

**Owner**: Platform + Finance

- [ ] Create TBWA tenant
  - [ ] Tenant record
  - [ ] Admin users
  - [ ] Role assignments

- [ ] Configure TE-Cheq agents
  - [ ] TE-Cheq Financist
  - [ ] Tenant-specific prompts

- [ ] Configure CES agent (basic)
  - [ ] CES Genie registration
  - [ ] Creative feedback skills

---

#### P1.7 Prisma Tenant

**Owner**: Platform

- [ ] Create Prisma tenant
  - [ ] Tenant record
  - [ ] Research users
  - [ ] Role assignments

- [ ] Configure Prisma Assistant
  - [ ] Meta-analysis skills
  - [ ] PH intel access

---

### P2 - Creative Engine

#### P2.1 Creative / GenAI Engine (H6)

**Owner**: Creative

- [ ] Create creative schema
  - [ ] `creative.templates`
  - [ ] `creative.artifacts`
  - [ ] `creative.generations`

- [ ] Implement template management
  - [ ] Template CRUD APIs
  - [ ] Version control
  - [ ] Category tagging

- [ ] Wire fal.ai (optional)
  - [ ] Image generation API
  - [ ] Rate limiting
  - [ ] Result storage

---

## Phase 4: Advanced Features & RCT

### P2 - RCT Support

#### P2.2 Research Framework

**Owner**: Platform

- [ ] Create research schema
  - [ ] `research.studies`
  - [ ] `research.consent_records`
  - [ ] `research.participants`

- [ ] Implement consent capture
  - [ ] Consent UI components
  - [ ] Consent API
  - [ ] Audit trail

- [ ] Create anonymization pipeline
  - [ ] PII detection
  - [ ] Data masking
  - [ ] Export utilities

- [ ] Design pilot study
  - [ ] University partnership
  - [ ] IRB documentation
  - [ ] Study protocol

---

### P2 - Retail Extensions

#### P2.3 Scout Improvements

**Owner**: Retail

- [ ] Dashboard enhancements
  - [ ] New visualizations
  - [ ] Filter improvements
  - [ ] Export features

- [ ] Brand sponsor portal
  - [ ] Role-based access
  - [ ] Masked data views
  - [ ] Campaign tracking

---

### P3 - Performance

#### P3.1 Optimization

**Owner**: Platform

- [ ] Query optimization
  - [ ] Slow query analysis
  - [ ] Index additions
  - [ ] Query rewrites

- [ ] Connection pooling
  - [ ] Pool size tuning
  - [ ] Connection limits
  - [ ] Timeout optimization

- [ ] Load testing
  - [ ] Benchmark suite
  - [ ] Concurrent user tests
  - [ ] Bottleneck identification

---

## Milestones

### Milestone 1: Platform Foundation Complete

**Target Exit Criteria**:
- [ ] H1 Identity Engine deployed with RLS
- [ ] H3 Data Engine with Bronze/Silver/Gold
- [ ] H5 Automation with 3+ workflows
- [ ] H8 Governance with audit logging

### Milestone 2: Vertical Anchors Live

**Target Exit Criteria**:
- [ ] TE-Cheq 6 engines deployed
- [ ] SariCoach production flow working
- [ ] H7 Agent router with 3+ agents
- [ ] PH Intel basic ingestion

### Milestone 3: Unified Experience

**Target Exit Criteria**:
- [ ] TBWA tenant live
- [ ] Prisma tenant live
- [ ] Evaluation framework operational
- [ ] Cost controls active

### Milestone 4: Production Ready

**Target Exit Criteria**:
- [ ] p95 latency < 2s
- [ ] 50+ concurrent users
- [ ] RCT framework ready
- [ ] 3+ verticals on platform

---

## Appendix: Task Dependencies

```
Phase 1 Foundation
  H1 Identity --> H3 Data (RLS depends on identity)
  H1 Identity --> H5 Automation (workflows need auth)
  H3 Data --> H8 Governance (audit needs schemas)

Phase 2 Verticals
  H1 Identity --> TE-Cheq (tenant/role context)
  H3 Data --> TE-Cheq (schema patterns)
  H5 Automation --> TE-Cheq (approval workflows)

  H1 Identity --> SariCoach (store owner auth)
  H3 Data --> SariCoach (analytics views)

  H3 Data --> H7 Agent (knowledge chunks)
  H1 Identity --> H7 Agent (RBAC context)

Phase 3 Unified
  H7 Agent --> Evaluation (session data)
  H8 Governance --> Cost Controls (usage tracking)
  H1 Identity --> Tenant Setup (tenant records)

Phase 4 Advanced
  All Engines --> Performance (optimization)
  H1 Identity --> RCT (consent/research roles)
```

---

## Related Documents

- [Product Requirements Document](./prd.md)
- [Constitution](./constitution.md)
- [Implementation Plan](./plan.md)
