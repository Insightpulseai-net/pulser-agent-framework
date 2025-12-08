# AI Workbench Specification Kit

**Project**: InsightPulseAI Multi-Agent AI Workbench
**Version**: 1.0.0
**Created**: 2025-12-08

---

## Overview

This is the complete **Spec Kit** for the InsightPulseAI Multi-Agent AI Workbench - a self-hosted alternative to Microsoft Foundry, Azure Data Factory, and Databricks Unity Catalog built on **Supabase + n8n + Odoo 18 CE + DigitalOcean**.

The workbench enables data teams to build, orchestrate, and monitor AI-powered data pipelines with no cloud vendor lock-in, transparent costs, and full customization.

---

## Document Structure

### 1. [constitution.md](./constitution.md) - **Project Charter**

**Purpose**: Defines the "why" and "what" of the project.

**Contents**:
- Mission statement and vision
- Target users (Data Engineer, BI Engineer, AI Orchestrator, Architect)
- Core principles (Spec-First, Smart Delta, Medallion, Guardian)
- Scope boundaries (in-scope vs out-of-scope features)
- Success criteria (v1.0 launch requirements)

**Read this first to understand**: What problem we're solving and who we're building for.

---

### 2. [prd.md](./prd.md) - **Product Requirements Document**

**Purpose**: Defines the "how" in product/UX terms.

**Contents**:
- **Section 0**: Explicit architectural assumptions (database, orchestration, AI, costs)
- **Section 1**: App snapshot (platforms, roles, core user flows)
- **Section 2**: Page inventory (navigation structure, page hierarchy)
- **Section 3**: Page specs (detailed layouts, zones, components per page)
- **Section 4**: Component library (reusable UI components)
- **Section 5**: Data model & API contracts (Supabase schema, RPC functions, API endpoints)
- **Section 6**: Permissions matrix (Viewer, Engineer, Admin, Service roles)
- **Section 7**: Edge cases & constraints (timeouts, rate limits, retries, circuit breakers)
- **Section 8**: Architecture mapping (Azure/Databricks → Self-Hosted equivalents with gaps)

**Read this to understand**: Exactly what features to build and how they work.

---

### 3. [plan.md](./plan.md) - **Implementation Plan**

**Purpose**: Defines the "when" and "who".

**Contents**:
- **Section 1**: Release strategy (v0.1 → v1.0 → v2.0 roadmap)
- **Section 2**: Epics (E1-E9: Foundation, Catalog, Pipelines, Quality, Lineage, AI, Odoo, UAT)
- **Section 3**: Milestones (M1-M8 with acceptance criteria)
- **Section 4**: Dependencies (external + internal + infrastructure)
- **Section 5**: Risks & mitigations (runaway agents, cost explosion, latency, security)
- **Section 6**: Resource allocation (team structure, infrastructure costs)
- **Section 7**: Timeline & Gantt chart (week-by-week breakdown)
- **Section 8**: Success metrics (launch + post-launch KPIs)

**Read this to understand**: What gets built when, by whom, and how to measure success.

---

### 4. [tasks.md](./tasks.md) - **Task Breakdown**

**Purpose**: Actionable implementation checklist.

**Contents**:
- **Section 1**: Legend (status codes, priority levels, area tags)
- **Section 2**: Task groups (T0-T9: 62 total tasks)
  - **T0**: Setup & Repo (7 tasks)
  - **T1**: Metadata Schema (5 tasks)
  - **T2**: Web App Shell & Auth (4 tasks)
  - **T3**: Catalog & SQL Editor (5 tasks)
  - **T4**: Pipelines (6 tasks)
  - **T5**: Data Quality (5 tasks)
  - **T6**: Lineage (6 tasks)
  - **T7**: AI Assist (9 tasks)
  - **T8**: Odoo Integration (6 tasks)
  - **T9**: UAT & Go-Live (8 tasks)
- **Section 3**: Dependency graph (critical path + parallel tracks)
- **Section 4**: Quick reference (task summary by area, weekly targets)

**Use this as**: Your day-to-day implementation checklist with clear acceptance criteria.

---

## Key Features

### What We're Building

- ✅ **Metadata Catalog** (search, browse, view lineage)
- ✅ **SQL Editor** (Monaco, autocomplete, query history)
- ✅ **Pipeline Canvas** (React Flow visual DAG editor)
- ✅ **AI Assist (Genie)** (NL2SQL, agent binding, observability)
- ✅ **Data Quality** (Guardian validation, scorecards, alerts)
- ✅ **Lineage Tracking** (Neo4j graph, table→table, column→column)
- ✅ **Agent Runtime** (LangGraph + n8n orchestration)
- ✅ **LLM Gateway** (LiteLLM multi-model proxy + cost tracking)
- ✅ **Odoo Integration** (Smart Delta modules for Finance domain)

### What We're Reversing

| Azure/Databricks | Self-Hosted Equivalent |
|------------------|------------------------|
| Azure Data Factory | n8n + Airflow |
| Databricks Unity Catalog | Supabase + Neo4j + Qdrant |
| Azure OpenAI | LiteLLM + Claude/OpenAI/Gemini |
| Databricks Notebooks | JupyterHub + Observable (v1.2) |
| PowerBI | Apache Superset + Tableau |
| Microsoft Foundry | LangGraph + n8n + Langfuse |

---

## Tech Stack

### Core Infrastructure

- **Database**: Supabase PostgreSQL (Medallion: Bronze/Silver/Gold)
- **Orchestration**: n8n (visual workflows) + Airflow (batch jobs)
- **ERP**: Odoo 18 CE/OCA (Smart Delta approach - no forks)
- **Compute**: DigitalOcean App Platform + DOKS
- **Ingress**: Traefik (HTTPS, routing)

### AI/ML Stack

- **LLM Gateway**: LiteLLM (multi-model proxy)
- **Agent Runtime**: LangGraph (Python FastAPI)
- **Observability**: Langfuse (trace all LLM calls)
- **Vector Search**: Qdrant (catalog autocomplete)

### Data Stack

- **Transformations**: dbt (Silver/Gold models)
- **Lineage**: Neo4j (graph database)
- **Quality**: Guardian (8-step validation)
- **BI**: Apache Superset + Tableau

### Frontend

- **Framework**: Next.js 14 (TypeScript, App Router)
- **UI**: Material Web + Tailwind CSS
- **Charts**: ECharts
- **Editor**: Monaco (SQL syntax highlighting)

---

## Quick Start

### For Developers

1. **Read constitution.md** → Understand project vision and principles
2. **Skim prd.md** → Get familiar with features and architecture
3. **Review tasks.md** → Find your area (CATALOG, PIPELINE, AI, etc.)
4. **Start coding** → Follow acceptance criteria in each task

### For Product Managers

1. **Read constitution.md** → Confirm alignment with business goals
2. **Review prd.md Section 1-3** → Validate user flows and page specs
3. **Check plan.md Section 8** → Review success metrics
4. **Track progress** → Monitor tasks.md weekly targets

### For Architects

1. **Read prd.md Section 8** → Study architecture mapping table
2. **Review plan.md Section 5** → Assess risks and mitigations
3. **Validate assumptions** → Check prd.md Section 0 for architectural assumptions
4. **Design reviews** → Ensure alignment with Smart Delta + Medallion principles

---

## Success Criteria (v1.0)

### Functional Requirements

- ✅ At least 1 domain fully wired (Finance: BIR → Odoo → Workbench → Superset)
- ✅ Pipeline editor: Create, edit, schedule, monitor DAGs via UI
- ✅ Catalog search: Find tables/columns with <1s latency
- ✅ SQL editor: Execute queries with syntax highlighting, autocomplete
- ✅ AI Assist: Generate SQL from NL prompts with >80% accuracy
- ✅ Data quality: Automated validation on all Gold tables
- ✅ Lineage: Visualize table→table dependencies with Neo4j

### Non-Functional Requirements

- ✅ Pipeline success rate: >95%
- ✅ New domain setup time: <15 minutes
- ✅ Query performance: 90% of queries <3s
- ✅ Agent latency: 90th percentile <30s
- ✅ Uptime: >99.5%
- ✅ Cost: <$500/month baseline

### Quality Gates (Guardian Enforced)

- ✅ All Gold tables have: owner, SLO, dbt tests, lineage metadata
- ✅ All pipelines have: spec file, integration tests, monitoring, cost budget

---

## Timeline

| Week | Milestone | Deliverables |
|------|-----------|--------------|
| **1-2** | Infrastructure Ready | DOKS, Supabase, n8n, Traefik, Next.js |
| **3** | Catalog + SQL Live | Search, browse, query execution |
| **4-6** | Pipelines Operational | Canvas, validation, n8n integration |
| **7-8** | Data Quality Monitored | Scorecards, tests, alerts |
| **9-10** | Lineage Tracked | Neo4j graph, impact analysis |
| **11-13** | AI Assist Active | Genie, agent runtime, Langfuse |
| **14-16** | Odoo Integrated + UAT | Finance domain, BIR workflows, launch |

---

## Next Steps

1. **Kickoff Meeting**: Review constitution.md with all stakeholders
2. **Sprint Planning**: Assign tasks from tasks.md (start with T0 group)
3. **Infrastructure Setup**: Complete T0.1-T0.7 (Week 1)
4. **Development Sprints**: Follow weekly targets in plan.md Section 7
5. **UAT**: Execute T9.1-T9.8 (Weeks 15-16)
6. **Launch**: Deploy to production (T9.8)

---

## Contact

**Project Owner**: InsightPulseAI Engineering
**Last Updated**: 2025-12-08
**Version**: 1.0.0

---

**Status**: ✅ Spec Kit Complete - Ready for Implementation
