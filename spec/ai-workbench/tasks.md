# AI Workbench Tasks

**Project**: InsightPulseAI Multi-Agent AI Workbench
**Version**: 1.0.0
**Last Updated**: 2025-12-08
**Owner**: InsightPulseAI Engineering

---

## Section 1: Legend

### Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| **TODO** | Not started | Task ready to begin |
| **IN_PROGRESS** | Active work | Task currently being worked on |
| **BLOCKED** | Waiting | Task blocked by dependency |
| **DONE** | Completed | Task finished and validated |

### Priority Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **P0** | Critical | Must complete before launch |
| **P1** | High | Required for milestone |
| **P2** | Medium | Nice to have |
| **P3** | Low | Deferred to future version |

### Area Tags

| Tag | Component | Team |
|-----|-----------|------|
| **INFRA** | Infrastructure & DevOps | DevOps Engineers |
| **CATALOG** | Metadata catalog | Backend + Frontend |
| **SQL** | SQL editor | Frontend + Backend |
| **PIPELINE** | Pipeline orchestration | Backend + Frontend |
| **QUALITY** | Data quality | Backend + QA |
| **LINEAGE** | Lineage tracking | Backend + Frontend |
| **AI** | AI Assist & agents | AI/ML Engineers |
| **ODOO** | Odoo integration | Odoo Developers |
| **UAT** | Testing & validation | QA Engineers |

---

## Section 2: Task Groups

### T0: Setup & Repo (Week 1)

**Objective**: Initialize project repository and development environment.

---

**[T0.1] Initialize Git Repository** - **DONE** - **P0** - **INFRA**

**Dependencies**: None

**Acceptance Criteria**:
- Git repo created at `github.com/insightpulseai/ai-workbench`
- Main branch protected (require PR reviews)
- `.gitignore` configured (node_modules, .env, etc.)
- README.md with project overview

---

**[T0.2] Setup DigitalOcean DOKS Cluster** - **TODO** - **P0** - **INFRA**

**Dependencies**: T0.1

**Acceptance Criteria**:
- DOKS cluster provisioned (3 nodes, 8GB RAM each)
- kubectl configured and able to list nodes
- Cluster nodes healthy (all in "Ready" state)
- VPC configured with private networking

**Commands**:
```bash
doctl kubernetes cluster create ai-workbench-prod \
  --region sgp1 \
  --version 1.28 \
  --node-pool "name=worker-pool;size=s-4vcpu-8gb;count=3"
```

---

**[T0.3] Setup Supabase Project** - **TODO** - **P0** - **INFRA**

**Dependencies**: None

**Acceptance Criteria**:
- Supabase project created (project_ref: xkxyvboeubffxxbebsll)
- PostgreSQL 15 database provisioned
- Auth enabled (email/password provider)
- Connection string saved to `.env.local`

**Commands**:
```bash
# Via Supabase dashboard
# Store credentials in ~/.zshrc
export SUPABASE_URL="https://xkxyvboeubffxxbebsll.supabase.co"
export SUPABASE_ANON_KEY="..."
export SUPABASE_SERVICE_ROLE_KEY="..."
```

---

**[T0.4] Deploy n8n to DOKS** - **TODO** - **P0** - **INFRA**

**Dependencies**: T0.2

**Acceptance Criteria**:
- n8n deployed via Helm chart
- Persistent volume configured (10GB)
- Webhook ingress enabled (HTTPS)
- n8n UI accessible at `https://n8n.insightpulseai.net`

**Commands**:
```bash
helm repo add n8n https://n8nio.github.io/n8n-helm-chart
helm install n8n n8n/n8n \
  --set persistence.enabled=true \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=n8n.insightpulseai.net
```

---

**[T0.5] Deploy Traefik Ingress** - **TODO** - **P0** - **INFRA**

**Dependencies**: T0.2

**Acceptance Criteria**:
- Traefik deployed as ingress controller
- SSL certificates provisioned via Let's Encrypt
- Routing rules configured (n8n, workbench, etc.)
- HTTPS enforced (HTTP → HTTPS redirect)

**Commands**:
```bash
helm repo add traefik https://traefik.github.io/charts
helm install traefik traefik/traefik \
  --set ports.websecure.tls.enabled=true \
  --set certmanager.email=admin@insightpulseai.net
```

---

**[T0.6] Initialize Next.js App** - **TODO** - **P0** - **INFRA**

**Dependencies**: T0.1

**Acceptance Criteria**:
- Next.js 14 app created with TypeScript
- Material Web + Tailwind CSS configured
- Supabase Auth integration added
- App deployed to Vercel (staging environment)

**Commands**:
```bash
npx create-next-app@latest ai-workbench \
  --typescript \
  --tailwind \
  --app \
  --no-src-dir

cd ai-workbench
npm install @supabase/supabase-js @material/web
```

---

**[T0.7] Configure Development Environment** - **TODO** - **P1** - **INFRA**

**Dependencies**: T0.3, T0.6

**Acceptance Criteria**:
- `.env.local` file with all required secrets
- VSCode workspace settings configured
- ESLint + Prettier setup
- Pre-commit hooks (husky) enabled

**Files**:
- `.env.local`: Supabase URL, keys, n8n webhook URL
- `.vscode/settings.json`: Format on save, linting
- `.eslintrc.json`: TypeScript + Next.js rules
- `.husky/pre-commit`: Lint staged files

---

### T1: Metadata Schema (Week 1-2)

**Objective**: Create Supabase metadata schema for Workbench.

---

**[T1.1] Design Schema (DDL)** - **TODO** - **P0** - **CATALOG**

**Dependencies**: T0.3

**Acceptance Criteria**:
- DDL script for all `ip_workbench.*` tables
- Foreign key relationships defined
- RLS policies drafted (separate file)
- Migration script ready (schema v1)

**Files**:
- `packages/db/sql/01_workbench_schema.sql`
- `packages/db/sql/02_workbench_rls.sql`

---

**[T1.2] Create Core Tables** - **TODO** - **P0** - **CATALOG**

**Dependencies**: T1.1

**Acceptance Criteria**:
- Tables created: `agents`, `agent_runs`, `pipelines`, `job_runs`, `tables`, `table_metadata`, `lineage`, `llm_requests`, `dq_test_results`, `sql_snippets`, `query_history`, `cost_tracker`
- All columns have correct types and constraints
- Indexes added for performance (id, created_at, status)

**Commands**:
```bash
psql "$SUPABASE_URL" -f packages/db/sql/01_workbench_schema.sql
```

---

**[T1.3] Enable RLS Policies** - **TODO** - **P0** - **CATALOG**

**Dependencies**: T1.2

**Acceptance Criteria**:
- RLS enabled on all tables
- Policies created for Viewer, Engineer, Admin, Service roles
- Test users created for each role
- Policies validated (users can only access allowed data)

**Commands**:
```bash
psql "$SUPABASE_URL" -f packages/db/sql/02_workbench_rls.sql
```

---

**[T1.4] Create RPC Functions** - **TODO** - **P1** - **CATALOG**

**Dependencies**: T1.2

**Acceptance Criteria**:
- `execute_sql(sql text)` function created (execute queries)
- `search_tables(query text)` function created (vector search)
- `get_table_lineage(table_id uuid)` function created (Neo4j query)
- Functions accessible via PostgREST

**Files**:
- `packages/db/sql/03_workbench_functions.sql`

---

**[T1.5] Seed Test Data** - **TODO** - **P2** - **CATALOG**

**Dependencies**: T1.2

**Acceptance Criteria**:
- 50+ test tables inserted into `ip_workbench.tables`
- Table metadata populated (columns, types)
- Test agents, pipelines, job runs inserted
- Test data covers Bronze/Silver/Gold schemas

**Files**:
- `packages/db/sql/04_workbench_seed.sql`

---

### T2: Web App Shell & Auth (Week 2)

**Objective**: Build Next.js app shell with authentication.

---

**[T2.1] Setup Supabase Auth** - **TODO** - **P0** - **CATALOG**

**Dependencies**: T0.6, T0.3

**Acceptance Criteria**:
- Supabase Auth client initialized
- Login/signup pages created
- Session management implemented (cookies)
- Protected routes (redirect to login if unauthenticated)

**Files**:
- `app/auth/login/page.tsx`
- `app/auth/signup/page.tsx`
- `lib/supabase.ts` (client setup)
- `middleware.ts` (auth middleware)

---

**[T2.2] Create App Layout** - **TODO** - **P0** - **CATALOG**

**Dependencies**: T2.1

**Acceptance Criteria**:
- Root layout with Material Web header
- Sidebar navigation (Catalog, SQL Editor, Pipelines, etc.)
- User avatar menu (profile, logout)
- Responsive design (mobile drawer menu)

**Files**:
- `app/layout.tsx`
- `components/Header.tsx`
- `components/Sidebar.tsx`

---

**[T2.3] Build Home Dashboard** - **TODO** - **P1** - **CATALOG**

**Dependencies**: T2.2

**Acceptance Criteria**:
- KPI cards (total tables, pipelines, agents, DQ score)
- Recent activity feed (last 10 events)
- Quick action buttons (New Pipeline, Run Query, Ask Genie)
- Alert banner (failed jobs, low DQ scores)

**Files**:
- `app/page.tsx`
- `components/KPICard.tsx`
- `components/ActivityFeed.tsx`

---

**[T2.4] Configure Roles & Permissions** - **TODO** - **P0** - **CATALOG**

**Dependencies**: T2.1

**Acceptance Criteria**:
- User roles stored in `auth.users` metadata
- Role-based UI rendering (hide/show features)
- RLS policies enforced on all data access
- Test users for each role (viewer, engineer, admin, service)

**Files**:
- `lib/permissions.ts` (role checking)

---

### T3: Catalog & SQL Editor (Week 3)

**Objective**: Build catalog and SQL editor pages.

---

**[T3.1] Create Catalog Page** - **TODO** - **P0** - **CATALOG**

**Dependencies**: T2.2, T1.2

**Acceptance Criteria**:
- Schema tree navigation (Bronze/Silver/Gold/Platinum)
- Table list with Material Data Table
- Search bar with autocomplete
- Table detail panel (schema, stats, lineage preview)

**Files**:
- `app/catalog/page.tsx`
- `components/SchemaTree.tsx`
- `components/TableList.tsx`
- `components/TableDetail.tsx`

---

**[T3.2] Integrate Qdrant Vector Search** - **TODO** - **P1** - **CATALOG**

**Dependencies**: T3.1, T0.2

**Acceptance Criteria**:
- Qdrant deployed to DOKS
- Table/column names indexed in Qdrant
- Search API endpoint created (`/api/search`)
- Search returns results in <1s

**Commands**:
```bash
helm repo add qdrant https://qdrant.github.io/qdrant-helm
helm install qdrant qdrant/qdrant
```

**Files**:
- `app/api/search/route.ts`

---

**[T3.3] Build SQL Editor** - **TODO** - **P0** - **SQL**

**Dependencies**: T2.2, T1.2

**Acceptance Criteria**:
- Monaco editor integrated (SQL syntax highlighting)
- Schema-aware autocomplete (table/column names)
- Run button (execute queries via Supabase RPC)
- Results displayed in Material Data Table

**Files**:
- `app/sql/page.tsx`
- `components/MonacoEditor.tsx`
- `components/ResultsTable.tsx`

---

**[T3.4] Add Query History & Snippets** - **TODO** - **P1** - **SQL**

**Dependencies**: T3.3

**Acceptance Criteria**:
- Query history saved to `ip_workbench.query_history`
- Saved snippets stored in `ip_workbench.sql_snippets`
- History sidebar (last 50 queries)
- Snippet sidebar (filter by tags)

**Files**:
- `components/QueryHistory.tsx`
- `components/SnippetList.tsx`

---

**[T3.5] Implement Export Results** - **TODO** - **P1** - **SQL**

**Dependencies**: T3.3

**Acceptance Criteria**:
- Export to CSV (up to 10k rows)
- Export to Excel (up to 10k rows)
- Export to JSON (raw data)
- Download progress indicator

**Files**:
- `lib/export.ts` (export logic)

---

### T4: Pipelines (Week 4-6)

**Objective**: Build pipeline canvas and orchestration.

---

**[T4.1] Setup React Flow Canvas** - **TODO** - **P0** - **PIPELINE**

**Dependencies**: T2.2

**Acceptance Criteria**:
- React Flow library integrated
- Canvas with drag-drop nodes
- Node types: Bronze, Silver, Gold, Custom
- Edges (connections between nodes)

**Files**:
- `app/pipelines/page.tsx`
- `components/PipelineCanvas.tsx`

---

**[T4.2] Create Node Config Forms** - **TODO** - **P0** - **PIPELINE**

**Dependencies**: T4.1

**Acceptance Criteria**:
- Bronze node form (source, destination table)
- Silver node form (SQL transformation, schedule)
- Gold node form (SQL aggregation, owner)
- Custom node form (Python/JS code)

**Files**:
- `components/NodeConfigForm.tsx`

---

**[T4.3] Integrate Guardian Validation** - **TODO** - **P0** - **PIPELINE**

**Dependencies**: T4.2

**Acceptance Criteria**:
- Guardian validation API endpoint created
- 8-step validation cycle implemented
- Validation panel shows test results
- Failed tests block pipeline save

**Files**:
- `app/api/validate/route.ts`
- `components/ValidationPanel.tsx`

---

**[T4.4] Create n8n Webhook Integration** - **TODO** - **P0** - **PIPELINE**

**Dependencies**: T4.3, T0.4

**Acceptance Criteria**:
- n8n workflow template created (pipeline trigger)
- Webhook URL generated on pipeline save
- Pipeline execution triggers n8n workflow
- Job logs sent back to Supabase

**Files**:
- `lib/n8n.ts` (webhook creation)
- `workflows/pipeline-trigger.json` (n8n workflow)

---

**[T4.5] Build Job Log Viewer** - **TODO** - **P0** - **PIPELINE**

**Dependencies**: T4.4

**Acceptance Criteria**:
- Job logs displayed in Material Timeline
- Status badges (pending, running, completed, failed)
- Error messages shown for failed jobs
- Retry/cancel buttons for failed jobs

**Files**:
- `app/pipelines/[id]/logs/page.tsx`
- `components/JobLogTimeline.tsx`

---

**[T4.6] Implement Pipeline Scheduling** - **TODO** - **P1** - **PIPELINE**

**Dependencies**: T4.4

**Acceptance Criteria**:
- Cron expression builder UI
- Schedule stored in `ip_workbench.pipelines`
- n8n webhook triggered by schedule
- Schedule can be paused/resumed

**Files**:
- `components/ScheduleForm.tsx`

---

### T5: Data Quality (Week 7-8)

**Objective**: Build data quality monitoring and alerts.

---

**[T5.1] Integrate Guardian Framework** - **TODO** - **P0** - **QUALITY**

**Dependencies**: T1.2

**Acceptance Criteria**:
- Guardian validation framework deployed
- 8-step validation cycle implemented
- Validation results stored in `ip_workbench.dq_test_results`
- Daily cron job runs validations

**Commands**:
```bash
# Deploy Guardian to DOKS
kubectl apply -f k8s/guardian-deployment.yaml
```

---

**[T5.2] Build DQ Scorecard Page** - **TODO** - **P0** - **QUALITY**

**Dependencies**: T5.1, T2.2

**Acceptance Criteria**:
- Scorecard grid displays all Gold tables
- Each card shows DQ score (0-100)
- Click card → view detailed test results
- Color-coded badges (green >90%, yellow 70-90%, red <70%)

**Files**:
- `app/quality/page.tsx`
- `components/ScorecardCard.tsx`

---

**[T5.3] Create Test Results Table** - **TODO** - **P1** - **QUALITY**

**Dependencies**: T5.2

**Acceptance Criteria**:
- Test results displayed in Material Data Table
- Filter by test type (completeness, uniqueness, consistency)
- View test SQL and failure reason
- Link to table detail page

**Files**:
- `app/quality/[table_id]/page.tsx`
- `components/TestResultsTable.tsx`

---

**[T5.4] Implement DQ Alerts** - **TODO** - **P1** - **QUALITY**

**Dependencies**: T5.2

**Acceptance Criteria**:
- Alert config form (Mattermost/Slack/Email)
- Threshold setting (score < 80% → alert)
- Alert recipients (user emails)
- Alerts sent via n8n webhook

**Files**:
- `app/quality/alerts/page.tsx`
- `components/AlertForm.tsx`
- `workflows/dq-alert.json` (n8n workflow)

---

**[T5.5] Add DQ Trend Chart** - **TODO** - **P2** - **QUALITY**

**Dependencies**: T5.2

**Acceptance Criteria**:
- ECharts line chart (30 days of DQ scores)
- Hover tooltip shows date + score
- Chart updates daily (after validation runs)
- Export chart as PNG

**Files**:
- `components/DQTrendChart.tsx`

---

### T6: Lineage & Knowledge Graph (Week 9-10)

**Objective**: Build lineage tracking with Neo4j.

---

**[T6.1] Setup Neo4j Database** - **TODO** - **P0** - **LINEAGE**

**Dependencies**: T0.2

**Acceptance Criteria**:
- Neo4j deployed to DOKS or Neo4j Aura
- Database accessible via Bolt protocol
- Sample graph data loaded (nodes, relationships)
- Cypher queries tested

**Commands**:
```bash
# Self-hosted option
helm repo add neo4j https://helm.neo4j.com/neo4j
helm install neo4j neo4j/neo4j

# Or use Neo4j Aura (managed service)
```

---

**[T6.2] Implement Lineage Ingestion** - **TODO** - **P0** - **LINEAGE**

**Dependencies**: T6.1, T1.2

**Acceptance Criteria**:
- SQL parser extracts table dependencies (sqlglot)
- Pipeline runs → lineage records in Supabase
- Lineage synced to Neo4j (nodes + edges)
- Cron job runs daily (sync new lineage)

**Files**:
- `lib/lineage-parser.ts` (SQL parsing)
- `lib/neo4j.ts` (Neo4j client)

---

**[T6.3] Build Graph Viewer** - **TODO** - **P0** - **LINEAGE**

**Dependencies**: T6.2, T2.2

**Acceptance Criteria**:
- Graph viewer displays table relationships
- Click node → view table detail
- Zoom, pan, fit-to-screen controls
- Color-coded nodes (Bronze/Silver/Gold)

**Files**:
- `app/lineage/page.tsx`
- `components/LineageGraph.tsx` (D3 or Neo4j Bloom embed)

---

**[T6.4] Add Filter Panel** - **TODO** - **P1** - **LINEAGE**

**Dependencies**: T6.3

**Acceptance Criteria**:
- Filter by schema (Bronze/Silver/Gold)
- Filter by table (autocomplete)
- Filter by depth (1-5 levels)
- Filters update graph in real-time

**Files**:
- `components/LineageFilterPanel.tsx`

---

**[T6.5] Implement Impact Analysis** - **TODO** - **P1** - **LINEAGE**

**Dependencies**: T6.3

**Acceptance Criteria**:
- Click table → show downstream tables
- Impact card displays affected tables (count)
- Highlight impacted nodes in graph
- Export impact report (CSV)

**Files**:
- `components/ImpactCard.tsx`

---

**[T6.6] Add Column Lineage** - **TODO** - **P2** - **LINEAGE**

**Dependencies**: T6.3

**Acceptance Criteria**:
- Parse SELECT statements to extract column mappings
- Column tree shows source → target columns
- Click column → view transformation SQL
- Column lineage stored in Supabase JSONB

**Files**:
- `lib/column-parser.ts`
- `components/ColumnTree.tsx`

---

### T7: AI Assist & Agent Binding (Week 11-13)

**Objective**: Build AI assist features with agent runtime.

---

**[T7.1] Setup LiteLLM Gateway** - **TODO** - **P0** - **AI**

**Dependencies**: T0.2

**Acceptance Criteria**:
- LiteLLM deployed to DOKS
- Multi-model configuration (Claude, OpenAI, Gemini)
- Fallback routing (GPT-4 → GPT-3.5)
- Rate limiting (500 req/min)

**Commands**:
```bash
# Deploy to DOKS
kubectl apply -f k8s/litellm-deployment.yaml
```

**Files**:
- `k8s/litellm-deployment.yaml`
- `litellm-config.yaml` (model routing)

---

**[T7.2] Integrate Langfuse** - **TODO** - **P0** - **AI**

**Dependencies**: T7.1

**Acceptance Criteria**:
- Langfuse deployed to DOKS
- LiteLLM → Langfuse tracing enabled
- Traces visible in Langfuse UI
- Cost tracking enabled (token usage)

**Commands**:
```bash
# Deploy to DOKS
kubectl apply -f k8s/langfuse-deployment.yaml
```

---

**[T7.3] Build Genie Chat Interface** - **TODO** - **P0** - **AI**

**Dependencies**: T7.1, T2.2

**Acceptance Criteria**:
- Material Chat UI component
- Send message → LiteLLM API call
- Display response with syntax highlighting
- Copy SQL button (for generated queries)

**Files**:
- `app/ai/page.tsx`
- `components/ChatInterface.tsx`

---

**[T7.4] Create Agent Registry Page** - **TODO** - **P0** - **AI**

**Dependencies**: T2.2, T1.2

**Acceptance Criteria**:
- Agent list displayed in Material Data Table
- Create agent form (name, tools, model, budget)
- Edit agent (update config)
- Delete agent (confirmation modal)

**Files**:
- `app/ai/agents/page.tsx`
- `components/AgentTable.tsx`
- `components/AgentForm.tsx`

---

**[T7.5] Implement Tool Library** - **TODO** - **P0** - **AI**

**Dependencies**: T7.4

**Acceptance Criteria**:
- Tools: Supabase Query, Odoo XML-RPC, Calculator, Web Search
- Tools stored in `ip_workbench.tools` table
- Agent → tool binding (many-to-many)
- Test tool execution (dry run)

**Files**:
- `lib/tools/supabase-query.ts`
- `lib/tools/odoo-xmlrpc.ts`
- `lib/tools/calculator.ts`
- `lib/tools/web-search.ts`

---

**[T7.6] Build LangGraph Agent Runtime** - **TODO** - **P0** - **AI**

**Dependencies**: T7.5

**Acceptance Criteria**:
- LangGraph agent runtime (Python FastAPI)
- Agent execution API endpoint (`/api/agents/run`)
- Tool invocation logic (call Supabase, Odoo, etc.)
- Agent deployed to DO App Platform

**Commands**:
```bash
# Deploy to DO App Platform
doctl apps create --spec infra/do/agent-runtime.yaml
```

**Files**:
- `services/agent-runtime/main.py` (FastAPI)
- `services/agent-runtime/agents.py` (LangGraph)
- `infra/do/agent-runtime.yaml` (DO App Platform spec)

---

**[T7.7] Create Agent Run Timeline** - **TODO** - **P1** - **AI**

**Dependencies**: T7.6

**Acceptance Criteria**:
- Agent runs displayed in Material Timeline
- Status badges (pending, running, completed, failed)
- Click run → view trace in Langfuse (iframe embed)
- Retry/cancel buttons

**Files**:
- `app/ai/agents/[id]/runs/page.tsx`
- `components/AgentRunTimeline.tsx`

---

**[T7.8] Build Cost Tracking Dashboard** - **TODO** - **P1** - **AI**

**Dependencies**: T7.7

**Acceptance Criteria**:
- ECharts bar chart (cost per agent, per day)
- Total cost today (KPI card)
- Cost breakdown by model
- Budget alerts (Mattermost notification)

**Files**:
- `app/ai/costs/page.tsx`
- `components/CostDashboard.tsx`

---

**[T7.9] Implement Budget Alerts** - **TODO** - **P1** - **AI**

**Dependencies**: T7.8

**Acceptance Criteria**:
- Budget threshold setting (per agent, per user)
- Alert when threshold exceeded
- Pause agent if budget exceeded
- Mattermost notification sent

**Files**:
- `workflows/budget-alert.json` (n8n workflow)

---

### T8: Odoo Smart Delta Domain (Week 14-16)

**Objective**: Integrate Odoo Finance domain with Workbench.

---

**[T8.1] Design Smart Delta Architecture** - **TODO** - **P0** - **ODOO**

**Dependencies**: None

**Acceptance Criteria**:
- Architecture diagram (Odoo → Workbench → Superset)
- Smart Delta approach documented (no forks)
- Integration points identified (XML-RPC, n8n)
- Finance domain scope defined (BIR, expenses)

**Files**:
- `docs/ODOO_SMART_DELTA.md`

---

**[T8.2] Create Finance PPM Module** - **TODO** - **P0** - **ODOO**

**Dependencies**: T8.1

**Acceptance Criteria**:
- Odoo module `ipai_finance_ppm` created
- Logframe model (Goal → Outcome → IM → Outputs → Activities)
- BIR schedule model (forms, deadlines, status)
- ECharts dashboard (BIR timeline, completion tracking)

**Files**:
- `addons/ipai_finance_ppm/__manifest__.py`
- `addons/ipai_finance_ppm/models/finance_logframe.py`
- `addons/ipai_finance_ppm/models/finance_bir_schedule.py`
- `addons/ipai_finance_ppm/views/ppm_dashboard.xml`

---

**[T8.3] Build BIR Workflow Integration** - **TODO** - **P0** - **ODOO**

**Dependencies**: T8.2

**Acceptance Criteria**:
- n8n workflow: Odoo BIR task → Workbench metadata
- BIR forms auto-generated (1601-C, 2550Q)
- Task status synced to Workbench
- Mattermost notifications (deadlines, approvals)

**Files**:
- `workflows/bir-sync.json` (n8n workflow)

---

**[T8.4] Implement Expense Automation** - **TODO** - **P1** - **ODOO**

**Dependencies**: T8.2

**Acceptance Criteria**:
- OCR service integrated (PaddleOCR-VL)
- Expense records created in Odoo
- Expense data synced to Workbench (Bronze schema)
- Policy validation (thresholds, categories)

**Files**:
- `workflows/expense-ocr.json` (n8n workflow)

---

**[T8.5] Create Analytics Bridge** - **TODO** - **P1** - **ODOO**

**Dependencies**: T8.2

**Acceptance Criteria**:
- Odoo data exported to Supabase (Bronze schema)
- dbt transformations (Silver/Gold schemas)
- Superset dashboards display Odoo data
- Real-time sync (15-min intervals)

**Files**:
- `workflows/odoo-sync.json` (n8n workflow)
- `packages/dbt/models/finance/*.sql` (dbt models)

---

**[T8.6] Add Visual Parity Tests** - **TODO** - **P1** - **ODOO**

**Dependencies**: T8.2

**Acceptance Criteria**:
- Playwright screenshots (mobile + desktop)
- SSIM comparison (baseline vs current)
- CI job runs on PR merge
- Visual parity gates (SSIM ≥0.97 mobile, ≥0.98 desktop)

**Files**:
- `tests/visual/odoo-parity.spec.ts` (Playwright)
- `scripts/ssim.ts` (SSIM calculation)

---

### T9: UAT & Go-Live (Week 15-16)

**Objective**: User acceptance testing and production launch.

---

**[T9.1] Write UAT Test Plan** - **TODO** - **P0** - **UAT**

**Dependencies**: All previous tasks

**Acceptance Criteria**:
- 10+ test scenarios documented
- Test data prepared (users, tables, pipelines)
- Test environment setup (staging)
- UAT checklist created

**Files**:
- `docs/UAT_PLAN.md`

---

**[T9.2] Execute UAT** - **TODO** - **P0** - **UAT**

**Dependencies**: T9.1

**Acceptance Criteria**:
- All scenarios executed by stakeholders
- Bugs logged in GitHub Issues
- Critical bugs (P0) fixed before launch
- UAT sign-off obtained

---

**[T9.3] Security Audit** - **TODO** - **P0** - **UAT**

**Dependencies**: T9.2

**Acceptance Criteria**:
- Penetration testing conducted
- Vulnerabilities identified and fixed
- OWASP Top 10 compliance verified
- Security audit report published

**Files**:
- `docs/SECURITY_AUDIT.md`

---

**[T9.4] Load Testing** - **TODO** - **P0** - **UAT**

**Dependencies**: T9.2

**Acceptance Criteria**:
- Load test simulates 100 concurrent users
- >95% requests complete in <3s
- No memory leaks or crashes
- Load test report published

**Commands**:
```bash
# Using k6
k6 run tests/load/workbench-load.js
```

**Files**:
- `tests/load/workbench-load.js` (k6 script)
- `docs/LOAD_TEST_REPORT.md`

---

**[T9.5] User Documentation** - **TODO** - **P0** - **UAT**

**Dependencies**: T9.2

**Acceptance Criteria**:
- User guides for all features
- Video tutorials (5-10 min each)
- FAQ page
- API documentation (Swagger/OpenAPI)

**Files**:
- `docs/user-guide/*.md`
- `docs/api/*.yaml` (OpenAPI specs)

---

**[T9.6] Production Monitoring** - **TODO** - **P0** - **UAT**

**Dependencies**: T9.2

**Acceptance Criteria**:
- Grafana dashboards (infra, app, LLMs)
- Prometheus metrics (uptime, latency, errors)
- Alerts configured (Mattermost/Slack)
- On-call rotation setup

**Files**:
- `infra/monitoring/grafana-dashboards/*.json`
- `infra/monitoring/prometheus-rules.yaml`

---

**[T9.7] Backup & Restore** - **TODO** - **P0** - **UAT**

**Dependencies**: T9.2

**Acceptance Criteria**:
- Supabase daily backups enabled
- DOKS PVC backups (Velero)
- Restore procedure tested
- RTO <1 hour, RPO <1 day

**Commands**:
```bash
# Install Velero for DOKS backups
velero install --provider digitalocean
```

---

**[T9.8] Production Deployment** - **TODO** - **P0** - **UAT**

**Dependencies**: T9.2, T9.3, T9.4, T9.5, T9.6, T9.7

**Acceptance Criteria**:
- Production environment deployed (DOKS + Traefik)
- DNS configured (workbench.insightpulseai.net)
- SSL certificates provisioned
- Smoke tests passed (all features working)

**Commands**:
```bash
# Deploy all services to production DOKS
kubectl apply -f k8s/production/

# Verify deployments
kubectl get deployments -n production
```

---

## Section 3: Dependency Graph

### Critical Path (P0 Tasks)

```
T0.1 → T0.2 → T0.4 → T0.5
       ↓       ↓
     T0.3 → T0.6 → T2.1 → T2.2 → T3.1 → T3.3 → T4.1 → T4.2 → T4.3 → T4.4 → T4.5
               ↓                   ↓       ↓       ↓       ↓       ↓       ↓
             T1.1 → T1.2 → T1.3   (SQL)  (CATALOG)        (PIPELINE)
                     ↓
                   T5.1 → T5.2
                     ↓
                   T6.1 → T6.2 → T6.3
                     ↓
                   T7.1 → T7.2 → T7.3 → T7.4 → T7.5 → T7.6
                                                         ↓
                                                       T8.1 → T8.2 → T8.3
                                                                       ↓
                                                                     T9.1 → T9.2 → T9.8
```

### Parallel Tracks

**Track 1: Catalog + SQL** (Weeks 1-3)
- T0.1 → T0.3 → T0.6 → T1.1 → T1.2 → T1.3 → T2.1 → T2.2 → T3.1 → T3.3

**Track 2: Infrastructure** (Weeks 1-2)
- T0.1 → T0.2 → T0.4 → T0.5

**Track 3: Pipelines** (Weeks 4-6)
- T4.1 → T4.2 → T4.3 → T4.4 → T4.5

**Track 4: Data Quality** (Weeks 7-8)
- T5.1 → T5.2 → T5.3 → T5.4

**Track 5: Lineage** (Weeks 9-10)
- T6.1 → T6.2 → T6.3

**Track 6: AI Assist** (Weeks 11-13)
- T7.1 → T7.2 → T7.3 → T7.4 → T7.5 → T7.6 → T7.7

**Track 7: Odoo** (Weeks 14-16)
- T8.1 → T8.2 → T8.3 → T8.4 → T8.5

**Track 8: UAT** (Weeks 15-16)
- T9.1 → T9.2 → T9.3 → T9.4 → T9.5 → T9.6 → T9.7 → T9.8

---

## Section 4: Quick Reference

### Task Summary by Area

| Area | Total Tasks | P0 | P1 | P2 | P3 |
|------|-------------|----|----|----|----|
| **INFRA** | 7 | 6 | 1 | 0 | 0 |
| **CATALOG** | 10 | 6 | 3 | 1 | 0 |
| **SQL** | 5 | 1 | 3 | 0 | 1 |
| **PIPELINE** | 6 | 5 | 1 | 0 | 0 |
| **QUALITY** | 5 | 2 | 2 | 1 | 0 |
| **LINEAGE** | 6 | 3 | 2 | 1 | 0 |
| **AI** | 9 | 5 | 4 | 0 | 0 |
| **ODOO** | 6 | 3 | 3 | 0 | 0 |
| **UAT** | 8 | 8 | 0 | 0 | 0 |
| **TOTAL** | **62** | **39** | **19** | **3** | **1** |

### Weekly Task Targets

| Week | Target Tasks | Priority | Focus |
|------|--------------|----------|-------|
| **1** | T0.1 - T0.7 | P0 | Setup & repo |
| **2** | T1.1 - T2.4 | P0 | Schema & auth |
| **3** | T3.1 - T3.5 | P0 + P1 | Catalog + SQL |
| **4-6** | T4.1 - T4.6 | P0 + P1 | Pipelines |
| **7-8** | T5.1 - T5.5 | P0 + P1 | Data quality |
| **9-10** | T6.1 - T6.6 | P0 + P1 | Lineage |
| **11-13** | T7.1 - T7.9 | P0 + P1 | AI Assist |
| **14-16** | T8.1 - T8.6 | P0 + P1 | Odoo |
| **15-16** | T9.1 - T9.8 | P0 | UAT & launch |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-12-08 | Initial task breakdown | InsightPulseAI Engineering |

---

**Status**: Ready for implementation kickoff
**Next Action**: Begin T0.1 (Initialize Git Repository)
