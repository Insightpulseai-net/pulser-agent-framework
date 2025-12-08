# AI Workbench Implementation Plan

**Project**: InsightPulseAI Multi-Agent AI Workbench
**Version**: 1.0.0
**Last Updated**: 2025-12-08
**Owner**: InsightPulseAI Engineering

---

## Section 1: Release Strategy

### Version Roadmap

| Version | Focus | Key Features | Target Date | Success Criteria |
|---------|-------|--------------|-------------|------------------|
| **v0.1** | **Foundry Parity** | Catalog, SQL Editor, basic pipelines | Week 4 | 1 domain wired end-to-end |
| **v0.2** | **Multi-Agent** | Agent registry, tool binding, n8n integration | Week 8 | 5 agents deployed, >50 runs/day |
| **v0.3** | **Gateway + Observability** | LiteLLM proxy, Langfuse, cost tracking | Week 12 | <$0.10 per LLM query |
| **v1.0** | **Production Launch** | Data quality, lineage, UAT complete | Week 16 | All acceptance criteria met |
| **v1.1** | **Odoo Integration** | Smart Delta modules, BIR workflows | Week 20 | Finance domain automated |
| **v1.2** | **Notebooks** | JupyterHub, Observable cells | Week 24 | 10+ active notebooks |
| **v1.5** | **Mobile** | React Native app | Q2 2026 | iOS/Android parity |
| **v2.0** | **Marketplace** | Agent/tool marketplace, community contributions | Q3 2026 | 50+ community agents |

---

### v0.1: Foundry Parity (Weeks 1-4)

**Goal**: Minimal viable workbench with catalog, SQL editor, and basic pipeline execution.

**Deliverables**:
- ✅ Supabase metadata schema (`ip_workbench.*` tables)
- ✅ Next.js web app shell with Material Web UI
- ✅ Catalog page (search, browse, view table details)
- ✅ SQL editor (Monaco, autocomplete, execute queries)
- ✅ Pipeline canvas (React Flow, create/edit/save DAGs)
- ✅ n8n integration (trigger webhooks, monitor jobs)
- ✅ Basic auth (Supabase Auth, email/password)

**Acceptance Criteria**:
- User can search catalog and find `gold.finance_expenses` table
- User can write SQL query and export results to CSV
- User can create 3-node pipeline (Bronze → Silver → Gold)
- Pipeline executes successfully via n8n webhook
- Job logs visible in UI within 5 seconds of completion

---

### v0.2: Multi-Agent (Weeks 5-8)

**Goal**: Agent runtime with tool binding and observability.

**Deliverables**:
- ✅ Agent registry page (list, create, edit agents)
- ✅ LangGraph agent runtime (deployed to DO App Platform)
- ✅ Tool library (Supabase Query, Odoo XML-RPC, Calculator, Web Search)
- ✅ Agent run logs (timeline, trace links)
- ✅ n8n agent triggers (webhook → execute agent → log result)

**Acceptance Criteria**:
- 5 agents deployed (SQL Generator, Pipeline Validator, Cost Estimator, DQ Checker, Odoo Query)
- >50 agent runs/day (automated + manual)
- Average agent latency <30s (90th percentile)
- All runs logged in `ip_workbench.agent_runs`

---

### v0.3: Gateway + Observability (Weeks 9-12)

**Goal**: Production-grade LLM gateway with cost tracking and observability.

**Deliverables**:
- ✅ LiteLLM proxy (multi-model gateway)
- ✅ Langfuse integration (trace all LLM calls)
- ✅ Cost tracking dashboard (per agent, per pipeline, per user)
- ✅ Circuit breakers (auto-disable failing models)
- ✅ Budget alerts (Mattermost notifications)

**Acceptance Criteria**:
- <$0.10 per LLM query (average)
- >99% gateway uptime
- All LLM calls traced in Langfuse (100% coverage)
- Cost dashboard shows breakdown by service (LLM, storage, compute)

---

### v1.0: Production Launch (Weeks 13-16)

**Goal**: Full data quality, lineage, and UAT completion.

**Deliverables**:
- ✅ Guardian integration (8-step validation cycle)
- ✅ Data quality scorecards (all Gold tables)
- ✅ Neo4j lineage tracking (table → table)
- ✅ Qdrant vector search (catalog autocomplete)
- ✅ Comprehensive UAT (10+ test scenarios)
- ✅ Production deployment (DOKS + Traefik)

**Acceptance Criteria**:
- All Gold tables have DQ score >90%
- Lineage graph displays 100+ table dependencies
- Catalog search returns results in <1s
- UAT passes with 0 critical bugs
- Production uptime >99.5% for 30 days

---

## Section 2: Epics

### E1: Foundation (Weeks 1-2)

**Objective**: Setup core infrastructure and tooling.

**Stories**:
1. **E1-S1**: Provision DigitalOcean DOKS cluster (3 nodes, 8GB RAM each)
2. **E1-S2**: Setup Supabase project (PostgreSQL, Auth, Storage)
3. **E1-S3**: Deploy n8n to DOKS (persistent volumes, webhook ingress)
4. **E1-S4**: Setup Traefik ingress (SSL, routing rules)
5. **E1-S5**: Create `ip_workbench` schema in Supabase (run migrations)
6. **E1-S6**: Initialize Next.js app with Material Web + Tailwind
7. **E1-S7**: Configure Supabase Auth (email/password, RLS policies)

**Acceptance Criteria**:
- DOKS cluster healthy (all nodes ready)
- Supabase accessible at `https://xkxyvboeubffxxbebsll.supabase.co`
- n8n UI accessible at `https://n8n.insightpulseai.net`
- Traefik dashboard accessible (HTTPS enforced)
- Next.js app deployed to Vercel (`https://workbench.insightpulseai.net`)

---

### E2: Catalog (Weeks 2-3)

**Objective**: Build metadata catalog with search and browse capabilities.

**Stories**:
1. **E2-S1**: Design `ip_workbench.tables` and `ip_workbench.table_metadata` schemas
2. **E2-S2**: Implement catalog page (Material Data Table, schema tree nav)
3. **E2-S3**: Build search bar with Qdrant vector search (autocomplete)
4. **E2-S4**: Create table detail panel (schema, stats, lineage preview)
5. **E2-S5**: Add export DDL feature (download SQL CREATE statements)
6. **E2-S6**: Implement favorites feature (save tables to user favorites)

**Acceptance Criteria**:
- Catalog displays 100+ tables from Bronze/Silver/Gold schemas
- Search returns results in <1s (including fuzzy matching)
- Table detail shows column names, types, nullability
- Export DDL generates valid PostgreSQL CREATE statements

---

### E3: SQL Editor (Week 3)

**Objective**: Interactive SQL query interface with history and snippets.

**Stories**:
1. **E3-S1**: Integrate Monaco editor with SQL syntax highlighting
2. **E3-S2**: Implement schema-aware autocomplete (table/column names)
3. **E3-S3**: Build query execution engine (Supabase RPC wrapper)
4. **E3-S4**: Display results in Material Data Table (pagination, export)
5. **E3-S5**: Add query history (save last 50 queries per user)
6. **E3-S6**: Implement saved snippets (name, description, tags)

**Acceptance Criteria**:
- Monaco editor loads in <2s
- Autocomplete suggests table/column names with <100ms latency
- Queries execute and return results in <3s (90% of queries)
- Export to CSV/Excel works for result sets up to 10k rows

---

### E4: Pipelines (Weeks 4-6)

**Objective**: Visual pipeline editor with scheduling and monitoring.

**Stories**:
1. **E4-S1**: Design `ip_workbench.pipelines` and `ip_workbench.job_runs` schemas
2. **E4-S2**: Build pipeline canvas with React Flow (drag-drop nodes)
3. **E4-S3**: Implement node types (Bronze, Silver, Gold, Custom)
4. **E4-S4**: Create node config forms (SQL, schedule, owner)
5. **E4-S5**: Build Guardian validation integration (8-step cycle)
6. **E4-S6**: Implement n8n webhook creation (schedule pipelines)
7. **E4-S7**: Build job log viewer (timeline, status, error messages)
8. **E4-S8**: Add retry/cancel buttons for failed jobs

**Acceptance Criteria**:
- User can create pipeline with 5+ nodes in <10 min
- Guardian validation runs in <30s
- n8n webhook triggers pipeline execution
- Job logs displayed within 5s of completion

---

### E5: Data Quality (Weeks 7-8)

**Objective**: Automated data quality validation and scorecards.

**Stories**:
1. **E5-S1**: Design `ip_workbench.dq_test_results` schema
2. **E5-S2**: Integrate Guardian validation framework
3. **E5-S3**: Build DQ scorecard page (grid of table cards)
4. **E5-S4**: Implement test results table (filter by test type)
5. **E5-S5**: Create alert configuration (Mattermost/Slack/Email)
6. **E5-S6**: Add trend chart (historical DQ scores)
7. **E5-S7**: Build remediation workflow (assign owner, create task)

**Acceptance Criteria**:
- All Gold tables have DQ score calculated daily
- Scorecards display completeness, uniqueness, consistency metrics
- Alerts trigger when score drops below threshold
- Trend chart shows 30 days of historical data

---

### E6: Lineage (Weeks 9-10)

**Objective**: Visual lineage tracking with Neo4j.

**Stories**:
1. **E6-S1**: Design `ip_workbench.lineage` schema
2. **E6-S2**: Setup Neo4j database (DOKS deployment or hosted)
3. **E6-S3**: Implement SQL parser (extract table dependencies with sqlglot)
4. **E6-S4**: Build lineage ingestion (pipeline runs → Neo4j)
5. **E6-S5**: Create graph viewer (Neo4j Bloom embed or custom D3)
6. **E6-S6**: Implement filter panel (schema, table, depth)
7. **E6-S7**: Add impact analysis (show downstream tables)
8. **E6-S8**: Build column lineage (parse SELECT statements)

**Acceptance Criteria**:
- Lineage graph displays 100+ table relationships
- Graph renders in <5s
- Filter panel allows drilling down by schema/table
- Column lineage shows source → target mappings

---

### E7: AI Assist (Weeks 11-13)

**Objective**: LLM-powered assistance with agent runtime.

**Stories**:
1. **E7-S1**: Design `ip_workbench.agents` and `ip_workbench.agent_runs` schemas
2. **E7-S2**: Setup LiteLLM proxy (multi-model gateway)
3. **E7-S3**: Integrate Langfuse (trace all LLM calls)
4. **E7-S4**: Build Genie chat interface (NL2SQL)
5. **E7-S5**: Create agent registry page (list, create, edit)
6. **E7-S6**: Implement tool library (Supabase Query, Odoo XML-RPC, etc.)
7. **E7-S7**: Build LangGraph agent runtime (deploy to DO App Platform)
8. **E7-S8**: Create agent run timeline (logs, traces, costs)
9. **E7-S9**: Add cost tracking dashboard (per agent, per user)
10. **E7-S10**: Implement budget alerts (Mattermost notifications)

**Acceptance Criteria**:
- Genie generates correct SQL for 80% of NL queries
- Agent runtime handles 100+ concurrent requests
- All LLM calls logged in Langfuse (100% coverage)
- Cost dashboard shows per-agent breakdown

---

### E8: Odoo Integration (Weeks 14-16)

**Objective**: Smart Delta modules for Finance domain.

**Stories**:
1. **E8-S1**: Design Odoo Smart Delta architecture (no forks)
2. **E8-S2**: Create `ipai_finance_ppm` module (Finance PPM)
3. **E8-S3**: Build BIR workflow integration (1601-C, 2550Q)
4. **E8-S4**: Implement expense automation (OCR → Odoo)
5. **E8-S5**: Create n8n workflows (Odoo → Workbench sync)
6. **E8-S6**: Build analytics bridge (Odoo → Supabase → Superset)
7. **E8-S7**: Add visual parity tests (SSIM thresholds)

**Acceptance Criteria**:
- Finance domain fully automated (BIR forms auto-generated)
- Expense data syncs to Workbench within 15 min
- Superset dashboards display Odoo data
- Visual parity SSIM ≥0.97 (mobile), ≥0.98 (desktop)

---

### E9: UAT (Weeks 15-16)

**Objective**: User acceptance testing with production scenarios.

**Stories**:
1. **E9-S1**: Write UAT test plan (10+ scenarios)
2. **E9-S2**: Execute UAT with stakeholders
3. **E9-S3**: Fix critical bugs (P0 severity)
4. **E9-S4**: Conduct security audit (penetration testing)
5. **E9-S5**: Perform load testing (simulate 100 concurrent users)
6. **E9-S6**: Create user documentation (guides, videos)
7. **E9-S7**: Setup production monitoring (Grafana dashboards)
8. **E9-S8**: Configure backup/restore procedures

**Acceptance Criteria**:
- UAT passes with 0 critical bugs (P0)
- Security audit identifies 0 high-severity vulnerabilities
- Load testing: >95% requests complete in <3s
- User documentation covers all features

---

## Section 3: Milestones

### M1: Infrastructure Ready (Week 2)

**Deliverables**:
- DOKS cluster provisioned and healthy
- Supabase project configured (auth, RLS policies)
- n8n deployed with webhook ingress
- Traefik routing configured (HTTPS enforced)
- Next.js app deployed to Vercel

**Acceptance Criteria**:
- All services accessible via HTTPS
- Supabase schema `ip_workbench` created
- n8n can execute test workflow
- Next.js app displays "Hello World"

---

### M2: Catalog + SQL Editor Live (Week 3)

**Deliverables**:
- Catalog page with search and browse
- SQL editor with Monaco and autocomplete
- Query execution via Supabase RPC
- Export results to CSV/Excel

**Acceptance Criteria**:
- User can find table in <1s using search
- User can write and execute SQL query
- Results displayed in <3s
- Export works for 10k+ rows

---

### M3: Pipelines Operational (Week 6)

**Deliverables**:
- Pipeline canvas with React Flow
- Node config forms (SQL, schedule, owner)
- Guardian validation integration
- n8n webhook creation
- Job log viewer

**Acceptance Criteria**:
- User can create 3-node pipeline in <10 min
- Pipeline validates successfully with Guardian
- n8n webhook triggers execution
- Job logs visible in UI

---

### M4: Data Quality Monitored (Week 8)

**Deliverables**:
- DQ scorecard page
- Test results table
- Alert configuration
- Trend chart (30 days)

**Acceptance Criteria**:
- All Gold tables have DQ score >90%
- Alerts trigger when score drops below threshold
- Trend chart shows historical data

---

### M5: Lineage Tracked (Week 10)

**Deliverables**:
- Neo4j lineage database
- Graph viewer (table → table)
- Filter panel (schema, table, depth)
- Impact analysis (downstream tables)

**Acceptance Criteria**:
- Lineage graph displays 100+ relationships
- Graph renders in <5s
- Filter panel works correctly

---

### M6: AI Assist Active (Week 13)

**Deliverables**:
- Genie chat interface (NL2SQL)
- Agent registry page
- LangGraph agent runtime
- Langfuse observability
- Cost tracking dashboard

**Acceptance Criteria**:
- Genie generates correct SQL for 80% of queries
- 5 agents deployed and running
- All LLM calls logged in Langfuse
- Cost dashboard shows per-agent breakdown

---

### M7: Odoo Integrated (Week 16)

**Deliverables**:
- Finance domain Smart Delta modules
- BIR workflow automation
- Expense OCR integration
- Analytics bridge (Odoo → Superset)

**Acceptance Criteria**:
- BIR forms auto-generated
- Expense data syncs to Workbench
- Superset dashboards display Odoo data

---

### M8: Production Launch (Week 16)

**Deliverables**:
- UAT complete (0 critical bugs)
- Security audit passed
- Load testing passed
- User documentation published
- Production monitoring active

**Acceptance Criteria**:
- All v1.0 acceptance criteria met
- Uptime >99.5% for 30 days
- User feedback score >4/5

---

## Section 4: Dependencies

### External Dependencies

| Dependency | Type | Version | SLA | Contingency |
|-----------|------|---------|-----|-------------|
| **Supabase** | Database + Auth | PostgreSQL 15 | 99.9% uptime | Backup to self-hosted Postgres |
| **DigitalOcean** | Compute + DOKS | K8s 1.28+ | 99.95% uptime | Migrate to AWS/GCP (Terraform) |
| **n8n** | Orchestration | v1.x | Self-hosted | Airflow fallback for batch jobs |
| **LiteLLM** | LLM Gateway | v1.x | Self-hosted | Direct API calls to Claude/OpenAI |
| **Langfuse** | Observability | v2.x | Self-hosted | Custom logging to Supabase |
| **Neo4j** | Lineage | v5.x | Self-hosted or Aura | Fallback to Supabase JSONB graphs |
| **Qdrant** | Vector Search | v1.x | Self-hosted | Fallback to PostgreSQL pg_trgm |
| **Odoo** | ERP | v18 CE | Self-hosted | Manual data entry if Odoo down |

### Internal Dependencies

| Dependency | Owner | ETA | Blocker For |
|-----------|-------|-----|-------------|
| **Guardian Framework** | Platform Team | Week 2 | E4 (Pipelines), E5 (Data Quality) |
| **Knowledge Graph Workbench** | AI Team | Week 6 | E6 (Lineage) |
| **Finance PPM Module** | Odoo Team | Week 10 | E8 (Odoo Integration) |
| **Material Web Components** | UI Team | Week 1 | E2 (Catalog), E3 (SQL Editor) |

### Infrastructure Dependencies

| Component | Provider | Status | Risk |
|-----------|----------|--------|------|
| **DOKS Cluster** | DigitalOcean | Provisioned | Low (stable) |
| **Supabase Project** | Supabase | Active | Low (99.9% SLA) |
| **n8n Deployment** | Self-hosted | Pending | Medium (config required) |
| **Traefik Ingress** | Self-hosted | Pending | Medium (SSL cert setup) |
| **Neo4j Database** | Self-hosted or Aura | Not started | High (evaluation needed) |
| **Qdrant Cluster** | Self-hosted | Not started | Medium (deploy to DOKS) |

---

## Section 5: Risks & Mitigations

### High-Priority Risks

| Risk | Probability | Impact | Mitigation | Contingency |
|------|-------------|--------|------------|-------------|
| **Runaway Agents** | Medium | High | Kill switches, budget caps, circuit breakers | Manual shutdown via n8n webhook |
| **Cost Explosion** | High | High | Budget alerts, per-agent caps, LiteLLM rate limiting | Pause all agent runs, audit costs |
| **LLM Latency** | Medium | Medium | Caching, model fallbacks (GPT-4 → GPT-3.5) | Disable AI Assist, use cached responses |
| **Vendor API Changes** | Low | High | Abstraction layer (LiteLLM), version pinning | Lock to last known working version |
| **Data Quality Degradation** | Medium | High | Guardian gates, daily DQ scorecards, alerts | Pause pipelines, rollback to last good state |
| **Supabase Downtime** | Low | Critical | Backup to self-hosted Postgres, RTO <1hr | Fail over to secondary DB, restore from backup |
| **Security Breach** | Low | Critical | RLS policies, audit logs, penetration testing | Immediate lockdown, forensic analysis, notify users |
| **DOKS Cluster Failure** | Low | High | Multi-node cluster, auto-healing, backups | Redeploy to new cluster, restore from backups |

### Medium-Priority Risks

| Risk | Probability | Impact | Mitigation | Contingency |
|------|-------------|--------|------------|-------------|
| **Slow Lineage Queries** | Medium | Medium | Neo4j indexing, query optimization, pagination | Fallback to simplified graph view |
| **n8n Workflow Failures** | Medium | Medium | Retry logic, error handling, monitoring | Manual workflow execution via UI |
| **Odoo Integration Breaks** | Medium | Medium | Smart Delta approach (no forks), version pinning | Decouple Workbench from Odoo, manual sync |
| **UAT Delays** | High | Low | Early stakeholder engagement, buffer time | Extend timeline, reduce scope |
| **Performance Bottlenecks** | Medium | Medium | Load testing, caching, query optimization | Add read replicas, CDN for static assets |

### Low-Priority Risks

| Risk | Probability | Impact | Mitigation | Contingency |
|------|-------------|--------|------------|-------------|
| **UI/UX Issues** | High | Low | User testing, iterative design | Incremental improvements post-launch |
| **Documentation Gaps** | High | Low | Continuous docs updates, user guides | Community wiki, video tutorials |
| **Slow Catalog Search** | Low | Medium | Qdrant optimization, index tuning | Fallback to PostgreSQL pg_trgm search |
| **Mobile Experience** | Medium | Low | Responsive design, progressive web app | Defer mobile to v1.5 |

---

### Risk Monitoring & Response

**Weekly Risk Review**:
- Review top 5 risks every Monday
- Update probability/impact based on current state
- Assign mitigation tasks to owners

**Risk Escalation**:
- **High impact + high probability** → Immediate action, daily standup
- **High impact + medium probability** → Weekly review, mitigation plan
- **Medium impact + high probability** → Monitor closely, assign owner
- **Low impact** → Log for awareness, revisit quarterly

**Risk Dashboard** (Grafana):
- Real-time cost tracking (budget vs. actual)
- LLM latency (p50, p90, p99)
- Pipeline success rate (daily trend)
- Security alerts (failed logins, permission violations)

---

## Section 6: Resource Allocation

### Team Structure

| Role | Team Members | Allocation | Responsibilities |
|------|--------------|------------|------------------|
| **Project Lead** | 1 | 100% | Overall planning, stakeholder management |
| **Backend Engineers** | 2 | 100% | Supabase schema, RPC functions, API integrations |
| **Frontend Engineers** | 2 | 100% | Next.js UI, Material Web components, UX |
| **AI/ML Engineers** | 1 | 100% | LangGraph agents, LiteLLM, Langfuse |
| **DevOps Engineers** | 1 | 50% | DOKS, Traefik, deployments, monitoring |
| **Odoo Developers** | 1 | 50% | Smart Delta modules, n8n workflows |
| **QA Engineers** | 1 | 100% | UAT, load testing, security audit |
| **Technical Writer** | 1 | 50% | User docs, API docs, guides |

### Infrastructure Costs (Monthly)

| Service | Plan | Cost | Notes |
|---------|------|------|-------|
| **Supabase** | Pro | $25 | 8GB database, 100GB bandwidth |
| **DigitalOcean DOKS** | 3 nodes × $48 | $144 | 8GB RAM per node |
| **DigitalOcean Spaces** | Standard | $5 | 250GB storage, 1TB bandwidth |
| **Vercel** | Pro | $20 | Next.js hosting |
| **Neo4j Aura** | Professional | $65 | 8GB RAM, 32GB storage |
| **LiteLLM** | Self-hosted | $0 | Deployed to DOKS |
| **Langfuse** | Self-hosted | $0 | Deployed to DOKS |
| **Qdrant** | Self-hosted | $0 | Deployed to DOKS |
| **n8n** | Self-hosted | $0 | Deployed to DOKS |
| **LLM API Costs** | Variable | ~$200 | Claude/OpenAI usage |
| **Monitoring** | Grafana Cloud | $50 | Prometheus, Loki, Tempo |
| **Total** | - | **~$509/month** | Target: <$500 |

---

## Section 7: Timeline & Gantt Chart

### Week-by-Week Breakdown

| Week | Epic | Milestones | Deliverables | Team Focus |
|------|------|-----------|--------------|------------|
| **1** | E1 | - | DOKS + Supabase + n8n setup | DevOps, Backend |
| **2** | E1, E2 | M1 | Infrastructure ready, Catalog schema | DevOps, Backend, Frontend |
| **3** | E2, E3 | M2 | Catalog + SQL Editor live | Frontend, Backend |
| **4** | E4 | - | Pipeline canvas (React Flow) | Frontend |
| **5** | E4 | - | Pipeline validation + n8n integration | Backend, DevOps |
| **6** | E4 | M3 | Pipelines operational | Backend, Frontend |
| **7** | E5 | - | DQ schema + Guardian integration | Backend, QA |
| **8** | E5 | M4 | Data Quality monitored | Backend, Frontend |
| **9** | E6 | - | Neo4j setup + lineage ingestion | Backend, DevOps |
| **10** | E6 | M5 | Lineage tracked | Frontend, Backend |
| **11** | E7 | - | LiteLLM + Langfuse setup | AI/ML, DevOps |
| **12** | E7 | - | Agent registry + runtime | AI/ML, Backend |
| **13** | E7 | M6 | AI Assist active | AI/ML, Frontend |
| **14** | E8 | - | Odoo Smart Delta modules | Odoo, Backend |
| **15** | E8, E9 | - | Odoo integration + UAT start | Odoo, QA |
| **16** | E9 | M7, M8 | UAT complete, Production launch | All teams |

---

## Section 8: Success Metrics

### Launch Metrics (Week 16)

| Metric | Target | Measurement | Owner |
|--------|--------|-------------|-------|
| **Pipeline Success Rate** | >95% | `ip_workbench.job_runs` (status='completed') | Platform Team |
| **DQ Score (Gold Tables)** | >90% | `ip_workbench.dq_scorecards` (avg score) | QA Team |
| **Catalog Search Latency** | <1s | Qdrant response time (p90) | Backend Team |
| **SQL Query Latency** | <3s | Supabase query logs (p90) | Backend Team |
| **Agent Latency** | <30s | Langfuse traces (p90) | AI/ML Team |
| **LLM Cost per Query** | <$0.10 | `ip_workbench.llm_requests` (avg cost) | AI/ML Team |
| **Uptime** | >99.5% | Grafana uptime monitor | DevOps Team |
| **UAT Pass Rate** | 100% | UAT test results (0 critical bugs) | QA Team |

### Post-Launch Metrics (3 Months)

| Metric | Target | Measurement | Owner |
|--------|--------|-------------|-------|
| **Daily Active Users** | >10 | Supabase auth logs | Product Team |
| **Pipelines Deployed** | >20 | `ip_workbench.pipelines` (count) | Product Team |
| **Tables Cataloged** | >100 | `ip_workbench.tables` (count) | Product Team |
| **AI Queries/Day** | >50 | Langfuse analytics | AI/ML Team |
| **Cost per User/Month** | <$50 | (LLM + infra) / active users | Finance Team |
| **User Satisfaction** | >4/5 | NPS survey | Product Team |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-12-08 | Initial implementation plan | InsightPulseAI Engineering |

---

**Next Document**: [Tasks (Task Breakdown)](./tasks.md)
