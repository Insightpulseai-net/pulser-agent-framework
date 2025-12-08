# AI Workbench Constitution

**Project**: InsightPulseAI Multi-Agent AI Workbench
**Version**: 1.0.0
**Last Updated**: 2025-12-08
**Owner**: InsightPulseAI Engineering

---

## Section 1: Purpose and Vision

### Mission Statement
Democratize enterprise AI workbench capabilities by reverse-engineering Microsoft Foundry/Azure/Databricks architectures into a **self-hosted, open-source stack** running on **Supabase + n8n + Odoo 18 CE + DigitalOcean**.

### Vision
Enable data teams to build, orchestrate, and monitor AI-powered data pipelines with:
- **No cloud vendor lock-in** (Azure, AWS, Snowflake)
- **Transparent costs** (predictable DigitalOcean + Supabase pricing)
- **Full customization** (Odoo Smart Delta extensions, custom agents)
- **Production-grade observability** (Langfuse, Guardian quality gates)

### What We Reverse-Engineer
- **Microsoft Foundry**: AI orchestration, prompt engineering, model gateway
- **Azure Data Factory**: Visual pipeline editor, scheduling, monitoring
- **Databricks Unity Catalog**: Metadata discovery, lineage tracking, permissions
- **Azure OpenAI**: Multi-model gateway with fallbacks, rate limiting, cost tracking
- **PowerBI**: Self-service BI dashboards (via Superset/Tableau)

### What We Build Differently
- **Smart Delta for Odoo**: Config-only extensions, no forks, OCA compliance
- **n8n for orchestration**: Visual workflows instead of YAML/Python DAGs
- **Supabase Medallion**: Bronze/Silver/Gold schemas, not cloud lakehouse
- **LangGraph + n8n**: Agent runtime on DigitalOcean App Platform, not serverless
- **Guardian quality gates**: Spec-first enforcement, not post-hoc testing

---

## Section 2: Target Users

### Primary Personas

| Persona | Role | Key Needs | Success Metric |
|---------|------|-----------|----------------|
| **Data Engineer** | Build ETL pipelines | Visual editor, scheduling, job logs | Pipeline success rate >95% |
| **BI Engineer** | Create dashboards | SQL editor, catalog search, lineage | Query latency <3s for 90% queries |
| **AI Orchestrator** | Deploy agents | Agent binding, tool library, observability | Agent execution time <30s (90th %ile) |
| **Architect** | Design domains | Metadata governance, data contracts, quality | All gold tables have owner/SLO/tests |

### Secondary Personas
- **Finance Manager** (Odoo user consuming AI-enhanced reports)
- **DevOps Engineer** (deploying workbench to DOKS)
- **Data Analyst** (self-service SQL queries via Genie NL2SQL)

---

## Section 3: Principles

### 1. Spec-First Development
- **Guardian enforces**: No pipeline without spec file + tests
- **Metadata store**: All specs stored in `ip_workbench.pipeline_specs` (Supabase)
- **Version control**: Specs in git, validated on PR merge

### 2. Smart Delta for Odoo
- **No forks**: Extend Odoo 18 CE via OCA-compliant modules only
- **Config-only**: Use `ir.config_parameter`, `res.groups`, `ir.rule` for customization
- **Domain boundaries**: Finance domain isolated from core Odoo (separate n8n webhooks)
- **Upgrade safety**: All customizations must survive `odoo -u all`

### 3. Medallion Everywhere
- **Bronze**: Raw ingestion (JSON blobs, minimal validation)
- **Silver**: Cleaned, normalized, deduped (dbt transformations)
- **Gold**: Business-ready marts (star schemas, aggregations)
- **Platinum** (optional): AI-enhanced views (embeddings, LLM summaries)

### 4. Self-Hosted First
- **No cloud-only features**: All components must run on DigitalOcean + Supabase
- **Transparent pricing**: Cost per pipeline run tracked in `ip_workbench.cost_tracker`
- **Data sovereignty**: All data stays in Supabase PostgreSQL (no external blob stores)

### 5. Guardian-Enforced Quality
- **8-step validation cycle** (syntax → type → lint → security → test → perf → docs → integration)
- **Pre-deployment gates**: All pipelines validated before promotion to production
- **Quality scorecards**: Per-table DQ metrics (completeness, uniqueness, consistency)

### 6. AI as Co-Engineer
- **Agent-assisted development**: LLM generates SQL, dbt models, n8n workflows from specs
- **Observability**: All LLM calls logged in Langfuse (prompt, response, tokens, latency)
- **Human-in-loop**: Critical decisions (schema changes, deletions) require approval

---

## Section 4: Scope Boundaries

### In Scope (v1.0)

| Feature | Component | Implementation |
|---------|-----------|----------------|
| **Metadata Catalog** | UI + Supabase | Search tables, view lineage, browse schemas |
| **SQL Editor** | Monaco + PostgREST | Write queries, save snippets, export results |
| **Pipeline Canvas** | React Flow + n8n | Visual DAG editor, trigger/schedule, monitor jobs |
| **AI Assist (Genie)** | LangGraph + Claude | NL2SQL, pipeline generation, data quality insights |
| **Data Quality** | Guardian + dbt tests | Automated validation, scorecards, alerting |
| **Lineage Tracking** | Neo4j + Supabase | Table→table, column→column, query→result |
| **Agent Binding** | n8n webhooks + LiteLLM | Bind tools to agents, execute workflows, log traces |
| **Odoo Integration** | Smart Delta modules | Finance domain (BIR, expenses) → Workbench metadata |
| **Cost Tracking** | LiteLLM + Supabase | Token usage, API costs, pipeline run costs |

### Out of Scope (v1.0)

| Feature | Reason | Alternative |
|---------|--------|-------------|
| **Real-time streaming** | Not core to Foundry parity | Use Airflow batch jobs, 15-min intervals |
| **Multi-tenancy** | Single org deployment | Use Supabase RLS for team isolation |
| **Non-web clients** | Focus on web UI first | CLI/API in v2.0 |
| **GPU workloads** | No ML training in Foundry | Use external Paperspace/RunPod for training |
| **Federated queries** | Complexity overhead | ETL external data to Bronze first |
| **Advanced ML features** | Not in Foundry scope | Use external MLflow/Weights&Biases |

### Deferred to Future Versions

| Feature | Target Version | Dependency |
|---------|----------------|------------|
| **Mobile app** | v1.5 | React Native |
| **Slack/Teams integration** | v1.3 | n8n nodes |
| **Advanced lineage (column-level)** | v1.2 | Neo4j optimization |
| **Custom agent marketplace** | v2.0 | Agent registry + approval workflow |
| **Multi-cloud deployment** | v2.5 | Terraform modules |

---

## Section 5: Success Criteria

### v1.0 Launch Criteria (Production-Ready)

#### Functional Requirements
- ✅ **At least 1 domain fully wired** (Finance: BIR → Odoo → Workbench → Superset)
- ✅ **Pipeline editor**: Create, edit, schedule, monitor DAGs via UI
- ✅ **Catalog search**: Find tables/columns with <1s latency
- ✅ **SQL editor**: Execute queries with syntax highlighting, autocomplete
- ✅ **AI Assist**: Generate SQL from NL prompts with >80% accuracy
- ✅ **Data quality**: Automated validation on all Gold tables
- ✅ **Lineage**: Visualize table→table dependencies with Neo4j

#### Non-Functional Requirements
- ✅ **Pipeline success rate**: >95% for all scheduled jobs
- ✅ **New domain setup time**: <15 minutes (Bronze table → Gold mart)
- ✅ **Query performance**: 90% of queries <3s
- ✅ **Agent latency**: 90th percentile <30s
- ✅ **Uptime**: >99.5% (Supabase + DO App Platform SLA)
- ✅ **Cost**: <$500/month for baseline deployment

#### Quality Gates (Guardian Enforced)
- ✅ **All Gold tables** have:
  - Declared owner (team/person)
  - SLO definition (freshness, completeness)
  - dbt tests (uniqueness, not_null, relationships)
  - Lineage metadata (upstream sources documented)
- ✅ **All pipelines** have:
  - Spec file in git (`specs/pipelines/<name>.yaml`)
  - Integration tests (validate end-to-end flow)
  - Monitoring alerts (failure → Mattermost)
  - Cost budget (<$5 per run)

#### User Acceptance Criteria
- ✅ **Data Engineer**: Can build new pipeline in <30 min using visual editor
- ✅ **BI Engineer**: Can write SQL query and save as reusable snippet
- ✅ **AI Orchestrator**: Can bind new tool to agent and test in <15 min
- ✅ **Architect**: Can audit all data assets and enforce governance policies

### Post-Launch Metrics (3 Months)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Daily active users** | >10 | Supabase auth logs |
| **Pipelines deployed** | >20 | `ip_workbench.pipelines` count |
| **Tables cataloged** | >100 | `ip_workbench.tables` count |
| **AI queries/day** | >50 | Langfuse analytics |
| **Data quality score** | >90% | Guardian aggregated score |
| **Cost per user/month** | <$50 | LiteLLM + DO billing / active users |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-12-08 | Initial constitution | InsightPulseAI Engineering |

---

**Next Document**: [PRD (Product Requirements Document)](./prd.md)
