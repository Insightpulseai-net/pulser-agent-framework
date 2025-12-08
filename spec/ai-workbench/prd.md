# AI Workbench PRD (Product Requirements Document)

**Project**: InsightPulseAI Multi-Agent AI Workbench
**Version**: 1.0.0
**Last Updated**: 2025-12-08
**Owner**: InsightPulseAI Engineering

---

## Section 0: Assumptions

### Explicit Architectural Assumptions

| Category | Assumption | Impact if Wrong | Mitigation |
|----------|-----------|-----------------|------------|
| **Database** | Supabase PostgreSQL handles 100GB+ with <3s query latency | Query timeouts, poor UX | Add read replicas, implement caching |
| **Orchestration** | n8n executes 1000+ workflows/day reliably | Missed schedules, backlog | Add Airflow for batch jobs, queue management |
| **AI Gateway** | LiteLLM proxy handles 500 requests/min without rate limit errors | Agent failures, poor UX | Implement circuit breakers, fallback models |
| **Frontend** | Next.js SSR + Material Web renders <2s on 3G networks | Slow mobile experience | Add static generation, CDN, lazy loading |
| **Odoo** | Odoo 18 CE handles 50k+ transactions/day with proper indexing | Slow dashboards, timeouts | Optimize queries, add caching layer |
| **Vector Search** | Qdrant handles 10M+ vectors with <100ms search latency | Slow catalog search | Use HNSW indexing, add filters |
| **Lineage** | Neo4j tracks 1000+ table dependencies without memory issues | Graph visualization fails | Optimize Cypher queries, add pagination |
| **Cost** | Total stack costs <$500/month at baseline load | Budget overruns | Track costs per component, set alerts |
| **Security** | Supabase RLS policies enforce all access control | Data leaks, compliance violations | Audit policies, add RBAC tests |
| **Deployment** | DigitalOcean App Platform auto-scales to handle 10x traffic spikes | Downtime during peak usage | Add load testing, configure autoscaling |

### Data Assumptions

| Assumption | Validation Method | Fallback |
|-----------|-------------------|----------|
| **Bronze**: All source data arrives in valid JSON format | Schema validation on ingestion | Reject + alert on malformed data |
| **Silver**: dbt transformations run in <10 min for full refresh | Performance testing | Incremental models only |
| **Gold**: Star schemas denormalize without exceeding storage budget | Cost tracking | Add archival strategy |
| **Lineage**: SQL queries can be parsed to extract table dependencies | sqlglot parser testing | Manual lineage entry |

### Integration Assumptions

| External System | Assumption | Verification | Risk |
|-----------------|-----------|--------------|------|
| **Odoo API** | XML-RPC handles 100 requests/min | Load test | Rate limiting |
| **n8n Webhooks** | Webhook URLs remain stable across deployments | Version control | Breaking changes |
| **LLM APIs** | Claude/GPT-4 availability >99% | Monitor uptime | Fallback to GPT-3.5 |
| **Supabase** | Edge Functions execute in <5s | Performance monitoring | Move to App Platform |

---

## Section 1: App Snapshot

### Platforms & Access

| Platform | URL | Auth Method | Roles |
|----------|-----|-------------|-------|
| **Web App** | `https://workbench.insightpulseai.net` | Supabase Auth (email/password) | Viewer, Engineer, Admin, Service |
| **Mobile** (v2.0) | N/A | N/A | N/A |
| **API** | `https://workbench.insightpulseai.net/api` | API Key (Supabase JWT) | Service only |
| **Admin Console** | `https://workbench.insightpulseai.net/admin` | Supabase Auth (admin role) | Admin only |

### User Roles

| Role | Permissions | Use Cases |
|------|-------------|-----------|
| **Viewer** | Read catalog, run saved queries, view dashboards | BI Analyst, Finance Manager |
| **Engineer** | Create pipelines, edit SQL, bind agents, deploy jobs | Data Engineer, AI Orchestrator |
| **Admin** | Manage users, approve pipelines, configure costs, audit logs | Architect, Platform Lead |
| **Service** | API-only access for automation (n8n, Odoo) | Automated workflows |

### Core User Flows

#### Flow 1: Data Engineer Creates Pipeline
1. Navigate to **Pipelines** page
2. Click **New Pipeline** → Visual editor opens (React Flow)
3. Drag nodes: **Bronze Ingestion** → **Silver Transform (dbt)** → **Gold Mart**
4. Configure each node (SQL, schedule, owner)
5. Click **Validate** → Guardian runs 8-step quality check
6. Click **Save** → Pipeline stored in `ip_workbench.pipelines`
7. Click **Schedule** → n8n webhook created, cron enabled
8. Monitor execution in **Job Logs** tab

#### Flow 2: BI Engineer Queries Data
1. Navigate to **SQL Editor** page
2. Browse **Catalog** sidebar → Find `gold.finance_expenses`
3. Click table → Schema autocompletes in editor
4. Write SQL: `SELECT vendor, SUM(amount) FROM gold.finance_expenses GROUP BY vendor`
5. Click **Run** → Query executes via PostgREST
6. Results displayed in table (export to CSV/Excel)
7. Click **Save Snippet** → Stored in `ip_workbench.sql_snippets`

#### Flow 3: AI Orchestrator Binds Agent
1. Navigate to **AI Assist** page
2. Click **Agent Registry** → View available agents (SQL Generator, Pipeline Validator, etc.)
3. Click **New Agent** → Fill form:
   - Name: "BIR Tax Calculator"
   - Tools: [Supabase Query, Odoo XML-RPC, Calculator]
   - Model: Claude Sonnet 4.5
   - Budget: $0.50/run
4. Click **Test** → Run sample query (NL → SQL)
5. Click **Deploy** → n8n workflow created
6. Monitor in **Agent Runs** tab (Langfuse integration)

#### Flow 4: Architect Audits Data Quality
1. Navigate to **Data Quality** page
2. View **Scorecard** (all Gold tables, aggregated DQ score)
3. Click table → View detailed metrics:
   - Completeness: 98% (2% nulls in `vendor_id`)
   - Uniqueness: 100% (no duplicate IDs)
   - Consistency: 95% (5% mismatched categories)
4. Click **Failed Tests** → dbt test logs displayed
5. Click **Lineage** → Neo4j graph shows upstream sources
6. Click **Assign Owner** → Slack notification sent

---

## Section 2: Page Inventory

### Navigation Structure

```
Home (Dashboard)
├── Catalog
│   ├── Tables
│   ├── Columns
│   └── Schemas
├── SQL Editor
│   ├── Query Tab
│   ├── Saved Snippets
│   └── History
├── Pipelines
│   ├── Pipeline List
│   ├── Visual Editor
│   ├── Job Logs
│   └── Schedules
├── Notebooks (v1.2)
│   ├── Jupyter Integration
│   └── Observable-style cells
├── Data Quality
│   ├── Scorecards
│   ├── Test Results
│   └── Alerts
├── Lineage & Graph
│   ├── Table Graph (Neo4j)
│   ├── Column Lineage
│   └── Query Impact Analysis
├── AI Assist
│   ├── Genie (NL2SQL)
│   ├── Agent Registry
│   ├── Agent Runs
│   └── Observability (Langfuse)
└── Settings
    ├── Users & Roles
    ├── Cost Tracking
    ├── Integrations (Odoo, n8n)
    └── Audit Logs
```

### Page Hierarchy Table

| Level 1 | Level 2 | Level 3 | Auth Required | Role |
|---------|---------|---------|---------------|------|
| Home | - | - | ✅ | Viewer+ |
| Catalog | Tables | Table Detail | ✅ | Viewer+ |
| Catalog | Columns | Column Detail | ✅ | Viewer+ |
| Catalog | Schemas | Schema Detail | ✅ | Viewer+ |
| SQL Editor | Query Tab | - | ✅ | Viewer+ |
| SQL Editor | Saved Snippets | Snippet Detail | ✅ | Viewer+ |
| SQL Editor | History | Query History | ✅ | Viewer+ |
| Pipelines | Pipeline List | - | ✅ | Engineer+ |
| Pipelines | Visual Editor | Node Config | ✅ | Engineer+ |
| Pipelines | Job Logs | Run Detail | ✅ | Engineer+ |
| Pipelines | Schedules | Cron Config | ✅ | Engineer+ |
| Data Quality | Scorecards | Table Scorecard | ✅ | Engineer+ |
| Data Quality | Test Results | Test Detail | ✅ | Engineer+ |
| Data Quality | Alerts | Alert Config | ✅ | Admin |
| Lineage & Graph | Table Graph | Graph Viewer | ✅ | Viewer+ |
| Lineage & Graph | Column Lineage | Column Detail | ✅ | Viewer+ |
| AI Assist | Genie | NL2SQL Interface | ✅ | Engineer+ |
| AI Assist | Agent Registry | Agent Detail | ✅ | Engineer+ |
| AI Assist | Agent Runs | Run Detail | ✅ | Engineer+ |
| AI Assist | Observability | Langfuse Embed | ✅ | Admin |
| Settings | Users & Roles | User Detail | ✅ | Admin |
| Settings | Cost Tracking | Cost Dashboard | ✅ | Admin |
| Settings | Integrations | Integration Config | ✅ | Admin |
| Settings | Audit Logs | Log Viewer | ✅ | Admin |

---

## Section 3: Page Specs

### 3.1 Home (Dashboard)

**Layout**: 3-column grid (left: KPIs, center: recent activity, right: quick actions)

**Zones**:

| Zone | Components | Data Source |
|------|-----------|-------------|
| **Header** | Workbench logo, user avatar, search bar | Supabase auth |
| **KPI Cards** | Total tables, pipelines, agents, DQ score | `ip_workbench.kpi_summary` (view) |
| **Recent Activity** | Last 10 pipeline runs, queries, agent executions | `ip_workbench.activity_log` |
| **Quick Actions** | New Pipeline, Run Query, Ask Genie | Navigation links |
| **Alerts** | Failed jobs, low DQ scores, cost overruns | `ip_workbench.alerts` |

**Component Table**:

| Component | Type | Props | Events |
|-----------|------|-------|--------|
| KPICard | Material Card | `{title, value, trend, icon}` | onClick → navigate |
| ActivityFeed | List | `{items: Array<Activity>}` | onItemClick → detail |
| QuickActionButton | Material Button | `{label, icon, route}` | onClick → navigate |
| AlertBanner | Material Banner | `{severity, message}` | onDismiss |

**Modals**: None

**Navigation**: Header → All pages

---

### 3.2 Catalog

**Layout**: 2-column (left: tree nav, right: detail panel)

**Zones**:

| Zone | Components | Data Source |
|------|-----------|-------------|
| **Schema Tree** | Collapsible tree (Bronze/Silver/Gold/Platinum) | `ip_workbench.tables` |
| **Search Bar** | Autocomplete (table/column names) | Qdrant vector search |
| **Table List** | Material Data Table | `ip_workbench.tables` |
| **Detail Panel** | Table schema, stats, lineage preview | `ip_workbench.table_metadata` |
| **Actions** | Query, View Lineage, Export DDL | Buttons |

**Component Table**:

| Component | Type | Props | Events |
|-----------|------|-------|--------|
| SchemaTree | Material Tree | `{schemas: Array<Schema>}` | onNodeClick → loadTable |
| SearchBar | Material Autocomplete | `{placeholder, suggestions}` | onSearch → filter |
| TableList | Material Data Table | `{columns, rows, pagination}` | onRowClick → detail |
| DetailPanel | Material Card | `{table: TableMetadata}` | - |
| ActionButton | Material Button | `{label, icon}` | onClick → action |

**Modals**:
- **Export DDL Modal**: Download SQL CREATE statements
- **Add to Favorites Modal**: Save table to user favorites

**Navigation**: Header → Catalog → Table Detail → Lineage

---

### 3.3 SQL Editor

**Layout**: 3-panel (top: editor, middle: results, bottom: history)

**Zones**:

| Zone | Components | Data Source |
|------|-----------|-------------|
| **Editor** | Monaco SQL editor with autocomplete | Local state |
| **Toolbar** | Run, Save, Export, Format buttons | - |
| **Results Table** | Material Data Table | PostgREST response |
| **Query History** | Collapsible list | `ip_workbench.query_history` |
| **Saved Snippets** | Sidebar list | `ip_workbench.sql_snippets` |

**Component Table**:

| Component | Type | Props | Events |
|-----------|------|-------|--------|
| MonacoEditor | Monaco React | `{language: 'sql', value, onChange}` | onChange |
| RunButton | Material FAB | `{icon: 'play'}` | onClick → executeQuery |
| ResultsTable | Material Data Table | `{rows, columns, pagination}` | onPageChange |
| HistoryList | Material List | `{items: Array<Query>}` | onItemClick → loadQuery |
| SnippetList | Material List | `{items: Array<Snippet>}` | onItemClick → loadSnippet |

**Modals**:
- **Save Snippet Modal**: Name, description, tags
- **Export Results Modal**: CSV, Excel, JSON format selection

**Navigation**: Header → SQL Editor → Query History → Saved Snippets

---

### 3.4 Pipelines

**Layout**: Canvas (React Flow) + sidebar (node config)

**Zones**:

| Zone | Components | Data Source |
|------|-----------|-------------|
| **Pipeline List** | Material Data Table | `ip_workbench.pipelines` |
| **Canvas** | React Flow diagram | Pipeline definition JSON |
| **Node Config** | Material Form (SQL, schedule, owner) | Node state |
| **Job Logs** | Material Timeline | `ip_workbench.job_runs` |
| **Validation Panel** | Guardian test results | Real-time validation |

**Component Table**:

| Component | Type | Props | Events |
|-----------|------|-------|--------|
| PipelineCanvas | React Flow | `{nodes, edges, onNodeClick}` | onNodesChange |
| NodeConfigForm | Material Form | `{nodeType, config}` | onSubmit → updateNode |
| JobLogTimeline | Material Timeline | `{runs: Array<JobRun>}` | onItemClick → runDetail |
| ValidationPanel | Material Card | `{tests: Array<Test>}` | - |
| ScheduleButton | Material Button | `{label: 'Schedule'}` | onClick → createN8nWebhook |

**Modals**:
- **New Pipeline Modal**: Name, description, domain
- **Schedule Config Modal**: Cron expression, timezone, alerts
- **Delete Pipeline Modal**: Confirmation with impact analysis

**Navigation**: Header → Pipelines → Pipeline Detail → Job Logs

---

### 3.5 Data Quality

**Layout**: Dashboard (scorecard grid + detail panel)

**Zones**:

| Zone | Components | Data Source |
|------|-----------|-------------|
| **Scorecard Grid** | Material Card Grid | `ip_workbench.dq_scorecards` |
| **Test Results** | Material Data Table | `ip_workbench.dq_test_results` |
| **Alerts Config** | Material Form | `ip_workbench.dq_alerts` |
| **Trend Chart** | ECharts line chart | Historical DQ scores |

**Component Table**:

| Component | Type | Props | Events |
|-----------|------|-------|--------|
| ScorecardCard | Material Card | `{table, score, tests}` | onClick → detail |
| TestResultsTable | Material Data Table | `{tests: Array<Test>}` | onRowClick → testDetail |
| AlertForm | Material Form | `{channel, threshold, recipients}` | onSubmit → createAlert |
| TrendChart | ECharts | `{data: Array<{date, score}>}` | - |

**Modals**:
- **Test Detail Modal**: Test SQL, failure reason, remediation steps
- **Alert Config Modal**: Mattermost/Slack/Email settings

**Navigation**: Header → Data Quality → Scorecard Detail → Test Results

---

### 3.6 Lineage & Graph

**Layout**: Full-screen graph (Neo4j visualization)

**Zones**:

| Zone | Components | Data Source |
|------|-----------|-------------|
| **Graph Viewer** | Neo4j Bloom embed or custom D3 | Neo4j graph database |
| **Filter Panel** | Material Form (schema, table, depth) | - |
| **Impact Analysis** | Material Card (downstream tables) | Neo4j query |
| **Column Lineage** | Material Tree (column → column) | Parsed SQL metadata |

**Component Table**:

| Component | Type | Props | Events |
|-----------|------|-------|--------|
| GraphViewer | Neo4j Bloom | `{graphId, query}` | onNodeClick → detail |
| FilterForm | Material Form | `{schema, table, depth}` | onSubmit → updateGraph |
| ImpactCard | Material Card | `{affected: Array<Table>}` | - |
| ColumnTree | Material Tree | `{columns: Array<Column>}` | onNodeClick → detail |

**Modals**:
- **Graph Export Modal**: PNG, SVG, JSON export
- **Lineage Detail Modal**: Full table/column path

**Navigation**: Header → Lineage → Table Graph → Column Lineage

---

### 3.7 AI Assist

**Layout**: Chat interface (left) + agent config (right)

**Zones**:

| Zone | Components | Data Source |
|------|-----------|-------------|
| **Genie Chat** | Material Chat UI | Langfuse traces |
| **Agent Registry** | Material Data Table | `ip_workbench.agents` |
| **Agent Runs** | Material Timeline | `ip_workbench.agent_runs` |
| **Observability** | Langfuse embed iframe | Langfuse API |
| **Cost Tracker** | ECharts bar chart | `ip_workbench.llm_costs` |

**Component Table**:

| Component | Type | Props | Events |
|-----------|------|-------|--------|
| ChatInterface | Material Chat | `{messages: Array<Message>}` | onSend → callLLM |
| AgentTable | Material Data Table | `{agents: Array<Agent>}` | onRowClick → agentDetail |
| RunTimeline | Material Timeline | `{runs: Array<Run>}` | onItemClick → runDetail |
| LangfuseEmbed | iframe | `{src: langfuseUrl}` | - |
| CostChart | ECharts | `{data: Array<{date, cost}>}` | - |

**Modals**:
- **New Agent Modal**: Name, tools, model, budget
- **Test Agent Modal**: Sample queries, expected outputs
- **Agent Config Modal**: System prompt, temperature, max_tokens

**Navigation**: Header → AI Assist → Genie → Agent Registry → Observability

---

## Section 4: Component Library

### Shared Components (Material Web + Custom)

| Component | Type | Description | Props | Events |
|-----------|------|-------------|-------|--------|
| **AgentRunPanel** | Material Card | Shows agent execution status, logs, cost | `{run: AgentRun}` | onRetry, onCancel |
| **PipelineCanvas** | React Flow | Visual DAG editor for pipelines | `{nodes, edges}` | onNodesChange, onEdgesChange |
| **JobLogViewer** | Material Timeline | Displays job execution logs with timestamps | `{logs: Array<Log>}` | onItemClick |
| **LLMGatewayMonitor** | Material Card | Real-time LiteLLM stats (requests, latency, costs) | `{stats: GatewayStats}` | - |
| **DQScorecard** | Material Card | Data quality metrics for a table | `{table, score, tests}` | onClick |
| **LineageGraph** | D3/Neo4j | Interactive table lineage graph | `{graph: Graph}` | onNodeClick |
| **SchemaTreeNav** | Material Tree | Collapsible schema navigation | `{schemas: Array<Schema>}` | onNodeClick |
| **SQLAutocomplete** | Monaco | SQL editor with schema-aware autocomplete | `{value, onChange}` | onChange |
| **CostDashboard** | ECharts | Cost breakdown by service, pipeline, agent | `{costs: Array<Cost>}` | - |
| **AlertBanner** | Material Banner | Dismissible alert notifications | `{severity, message}` | onDismiss |

### Agent Run Panel Spec

```typescript
interface AgentRunPanelProps {
  run: {
    id: string;
    agent_name: string;
    status: 'running' | 'completed' | 'failed';
    started_at: string;
    completed_at: string | null;
    input_prompt: string;
    output: string | null;
    tokens_used: number;
    cost_usd: number;
    model: string;
    trace_url: string; // Langfuse
  };
  onRetry?: (runId: string) => void;
  onCancel?: (runId: string) => void;
}
```

**Visual Layout**:
- Header: Agent name, status badge, timestamp
- Body: Input prompt (truncated), output (with copy button)
- Footer: Tokens, cost, model, trace link

---

### Pipeline Canvas Spec

```typescript
interface PipelineCanvasProps {
  nodes: Array<{
    id: string;
    type: 'bronze' | 'silver' | 'gold' | 'custom';
    data: {
      label: string;
      sql?: string;
      schedule?: string;
      owner?: string;
    };
    position: { x: number; y: number };
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
  }>;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
}
```

**Node Types**:
- **Bronze**: Raw ingestion (JSON blob → table)
- **Silver**: dbt transformation (SQL → cleaned table)
- **Gold**: Business mart (star schema)
- **Custom**: User-defined Python/JavaScript logic

---

### LLM Gateway Monitor Spec

```typescript
interface LLMGatewayMonitorProps {
  stats: {
    requests_per_min: number;
    avg_latency_ms: number;
    error_rate: number;
    cost_today_usd: number;
    models: Array<{
      name: string;
      requests: number;
      tokens: number;
    }>;
  };
}
```

**Visual Layout**:
- KPI Row: Requests/min, latency, error rate, cost
- Model Breakdown: Bar chart (requests per model)
- Real-time log stream: Last 10 requests

---

## Section 5: Data Model & API Contracts

### Database Schema (Supabase `ip_workbench`)

#### Core Entities

**`ip_workbench.agents`**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | uuid | PK | Unique agent ID |
| name | text | NOT NULL, UNIQUE | Agent display name |
| description | text | - | Purpose of agent |
| tools | jsonb | NOT NULL | Array of tool names |
| model | text | NOT NULL | LLM model (e.g., "claude-sonnet-4.5") |
| system_prompt | text | - | Custom system prompt |
| temperature | numeric | DEFAULT 0.7 | LLM temperature |
| max_tokens | int | DEFAULT 4000 | Max response tokens |
| budget_usd | numeric | DEFAULT 1.0 | Cost limit per run |
| created_by | uuid | FK(auth.users) | Creator user ID |
| created_at | timestamp | DEFAULT now() | Creation time |
| updated_at | timestamp | DEFAULT now() | Last update |

**`ip_workbench.agent_runs`**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | uuid | PK | Unique run ID |
| agent_id | uuid | FK(agents) | Agent reference |
| status | text | NOT NULL | 'pending', 'running', 'completed', 'failed' |
| input_prompt | text | NOT NULL | User query |
| output | text | - | Agent response |
| tokens_used | int | - | Total tokens consumed |
| cost_usd | numeric | - | Actual cost |
| model | text | - | Model used (may differ from agent default) |
| trace_url | text | - | Langfuse trace link |
| started_at | timestamp | DEFAULT now() | Start time |
| completed_at | timestamp | - | Completion time |
| error_message | text | - | Error if failed |

**`ip_workbench.pipelines`**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | uuid | PK | Unique pipeline ID |
| name | text | NOT NULL, UNIQUE | Pipeline name |
| description | text | - | Purpose |
| definition | jsonb | NOT NULL | React Flow nodes/edges |
| schedule | text | - | Cron expression |
| owner | uuid | FK(auth.users) | Owner user ID |
| domain | text | - | Business domain (e.g., "finance") |
| enabled | boolean | DEFAULT true | Active/inactive |
| n8n_webhook_url | text | - | n8n trigger URL |
| created_at | timestamp | DEFAULT now() | Creation time |
| updated_at | timestamp | DEFAULT now() | Last update |

**`ip_workbench.job_runs`**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | uuid | PK | Unique run ID |
| pipeline_id | uuid | FK(pipelines) | Pipeline reference |
| status | text | NOT NULL | 'pending', 'running', 'completed', 'failed' |
| started_at | timestamp | DEFAULT now() | Start time |
| completed_at | timestamp | - | Completion time |
| logs | text | - | Execution logs |
| rows_processed | int | - | Number of rows |
| error_message | text | - | Error if failed |

**`ip_workbench.tables`**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | uuid | PK | Unique table ID |
| schema_name | text | NOT NULL | Schema (bronze/silver/gold/platinum) |
| table_name | text | NOT NULL | Table name |
| description | text | - | Table purpose |
| owner | uuid | FK(auth.users) | Owner user ID |
| row_count | bigint | - | Approximate row count |
| size_bytes | bigint | - | Storage size |
| last_updated | timestamp | - | Last data refresh |
| dq_score | numeric | - | Data quality score (0-100) |
| slo_freshness_hours | int | - | Freshness SLO |
| slo_completeness_pct | numeric | - | Completeness SLO |

**`ip_workbench.table_metadata`**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | uuid | PK | Unique metadata ID |
| table_id | uuid | FK(tables) | Table reference |
| column_name | text | NOT NULL | Column name |
| data_type | text | NOT NULL | PostgreSQL data type |
| is_nullable | boolean | NOT NULL | Nullable flag |
| is_primary_key | boolean | DEFAULT false | PK flag |
| description | text | - | Column description |

**`ip_workbench.lineage`**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | uuid | PK | Unique lineage ID |
| source_table_id | uuid | FK(tables) | Source table |
| target_table_id | uuid | FK(tables) | Target table |
| transformation_sql | text | - | SQL that creates relationship |
| created_at | timestamp | DEFAULT now() | Creation time |

**`ip_workbench.llm_requests`**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | uuid | PK | Unique request ID |
| agent_run_id | uuid | FK(agent_runs) | Agent run reference |
| model | text | NOT NULL | Model name |
| prompt_tokens | int | NOT NULL | Input tokens |
| completion_tokens | int | NOT NULL | Output tokens |
| cost_usd | numeric | NOT NULL | Request cost |
| latency_ms | int | NOT NULL | Response time |
| created_at | timestamp | DEFAULT now() | Request time |

**`ip_workbench.dq_test_results`**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | uuid | PK | Unique test ID |
| table_id | uuid | FK(tables) | Table reference |
| test_name | text | NOT NULL | Test identifier |
| test_type | text | NOT NULL | 'uniqueness', 'completeness', 'consistency' |
| passed | boolean | NOT NULL | Pass/fail |
| details | jsonb | - | Failure details |
| executed_at | timestamp | DEFAULT now() | Execution time |

**`ip_workbench.sql_snippets`**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | uuid | PK | Unique snippet ID |
| name | text | NOT NULL | Snippet name |
| description | text | - | Snippet purpose |
| sql | text | NOT NULL | SQL query |
| owner | uuid | FK(auth.users) | Owner user ID |
| tags | text[] | - | Search tags |
| created_at | timestamp | DEFAULT now() | Creation time |

**`ip_workbench.query_history`**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | uuid | PK | Unique query ID |
| user_id | uuid | FK(auth.users) | User reference |
| sql | text | NOT NULL | Executed SQL |
| rows_returned | int | - | Result count |
| execution_time_ms | int | - | Query duration |
| executed_at | timestamp | DEFAULT now() | Execution time |

**`ip_workbench.cost_tracker`**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | uuid | PK | Unique cost ID |
| service | text | NOT NULL | 'llm', 'pipeline', 'storage', 'compute' |
| resource_id | uuid | - | Foreign key to related entity |
| cost_usd | numeric | NOT NULL | Cost amount |
| recorded_at | timestamp | DEFAULT now() | Cost record time |

---

### API Contracts

#### UI ↔ Supabase (PostgREST)

**Catalog Search**

```http
GET /rest/v1/tables?select=*&schema_name=eq.gold&order=table_name
Authorization: Bearer <JWT>
```

Response:
```json
[
  {
    "id": "uuid",
    "schema_name": "gold",
    "table_name": "finance_expenses",
    "description": "Aggregated expense records",
    "owner": "user-uuid",
    "row_count": 15234,
    "dq_score": 97.5
  }
]
```

**Execute SQL Query**

```http
POST /rest/v1/rpc/execute_sql
Authorization: Bearer <JWT>
Content-Type: application/json

{
  "sql": "SELECT * FROM gold.finance_expenses LIMIT 10"
}
```

Response:
```json
{
  "rows": [...],
  "columns": ["id", "vendor", "amount", "date"],
  "execution_time_ms": 145
}
```

---

#### UI ↔ n8n (Webhooks)

**Trigger Pipeline Run**

```http
POST https://n8n.insightpulseai.net/webhook/<pipeline-id>
Content-Type: application/json

{
  "pipeline_id": "uuid",
  "triggered_by": "user-uuid"
}
```

Response:
```json
{
  "job_run_id": "uuid",
  "status": "pending"
}
```

---

#### UI ↔ Odoo (XML-RPC)

**Fetch Expense Categories**

```python
# Python example (UI will use JS XML-RPC client)
url = "https://odoo.insightpulseai.net/xmlrpc/2/object"
models.execute_kw(db, uid, password,
    'hr.expense.category', 'search_read',
    [[]],
    {'fields': ['name', 'code']}
)
```

---

#### UI ↔ LiteLLM Gateway

**Query LLM**

```http
POST https://litellm.insightpulseai.net/v1/chat/completions
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "model": "claude-sonnet-4.5",
  "messages": [
    {"role": "user", "content": "Generate SQL for top 5 vendors by expense amount"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

Response:
```json
{
  "id": "chatcmpl-...",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "SELECT vendor, SUM(amount) AS total FROM gold.finance_expenses GROUP BY vendor ORDER BY total DESC LIMIT 5"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 32,
    "total_tokens": 77
  }
}
```

---

## Section 6: Permissions/Roles Matrix

| Feature | Viewer | Engineer | Admin | Service |
|---------|--------|----------|-------|---------|
| **View Catalog** | ✅ | ✅ | ✅ | ✅ |
| **Run SQL Queries** | ✅ | ✅ | ✅ | ✅ |
| **Save SQL Snippets** | ✅ | ✅ | ✅ | ❌ |
| **View Pipelines** | ✅ | ✅ | ✅ | ✅ |
| **Create Pipelines** | ❌ | ✅ | ✅ | ✅ |
| **Edit Pipelines** | ❌ | ✅ | ✅ | ✅ |
| **Delete Pipelines** | ❌ | ❌ | ✅ | ❌ |
| **Schedule Pipelines** | ❌ | ✅ | ✅ | ✅ |
| **View Job Logs** | ✅ | ✅ | ✅ | ✅ |
| **Retry Failed Jobs** | ❌ | ✅ | ✅ | ✅ |
| **View Data Quality** | ✅ | ✅ | ✅ | ✅ |
| **Configure DQ Alerts** | ❌ | ❌ | ✅ | ❌ |
| **View Lineage** | ✅ | ✅ | ✅ | ✅ |
| **Edit Lineage** | ❌ | ✅ | ✅ | ❌ |
| **Use AI Assist (Genie)** | ❌ | ✅ | ✅ | ✅ |
| **Create Agents** | ❌ | ✅ | ✅ | ✅ |
| **Deploy Agents** | ❌ | ✅ | ✅ | ✅ |
| **Delete Agents** | ❌ | ❌ | ✅ | ❌ |
| **View Agent Runs** | ❌ | ✅ | ✅ | ✅ |
| **Access Langfuse** | ❌ | ❌ | ✅ | ❌ |
| **Manage Users** | ❌ | ❌ | ✅ | ❌ |
| **View Cost Tracking** | ❌ | ❌ | ✅ | ❌ |
| **Configure Integrations** | ❌ | ❌ | ✅ | ❌ |
| **View Audit Logs** | ❌ | ❌ | ✅ | ✅ |

### Supabase RLS Policies

**`ip_workbench.tables`**

```sql
-- Viewers can read all tables
CREATE POLICY "viewers_read_tables" ON ip_workbench.tables
FOR SELECT USING (true);

-- Engineers can update table metadata (owner, description)
CREATE POLICY "engineers_update_tables" ON ip_workbench.tables
FOR UPDATE USING (
  EXISTS (
    SELECT 1 FROM auth.users
    WHERE id = auth.uid()
    AND role IN ('engineer', 'admin')
  )
);

-- Admins can insert/delete tables
CREATE POLICY "admins_manage_tables" ON ip_workbench.tables
FOR ALL USING (
  EXISTS (
    SELECT 1 FROM auth.users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);
```

**`ip_workbench.pipelines`**

```sql
-- Engineers can CRUD their own pipelines
CREATE POLICY "engineers_manage_own_pipelines" ON ip_workbench.pipelines
FOR ALL USING (
  owner = auth.uid()
  AND EXISTS (
    SELECT 1 FROM auth.users
    WHERE id = auth.uid()
    AND role IN ('engineer', 'admin')
  )
);

-- Admins can manage all pipelines
CREATE POLICY "admins_manage_all_pipelines" ON ip_workbench.pipelines
FOR ALL USING (
  EXISTS (
    SELECT 1 FROM auth.users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);
```

---

## Section 7: Edge Cases & Constraints

### Timeouts

| Operation | Timeout | Retry Policy | Fallback |
|-----------|---------|--------------|----------|
| **SQL Query** | 30s | No retry | Error message |
| **Pipeline Run** | 10min | Auto-retry once | Alert admin |
| **LLM Request** | 60s | Retry with exponential backoff (3 attempts) | Cached response or error |
| **Lineage Graph** | 15s | No retry | Simplified view |
| **n8n Webhook** | 5s | No retry | Queue for later |

### Rate Limits

| Service | Limit | Enforcement | Handling |
|---------|-------|-------------|----------|
| **LiteLLM** | 500 req/min | Gateway-level | Return 429, suggest retry |
| **Supabase PostgREST** | 1000 req/min | PostgreSQL connection pool | Queue requests |
| **n8n Workflows** | 100 concurrent | n8n queue | Wait + notify |
| **Odoo XML-RPC** | 100 req/min | API rate limiter | Cache responses |

### Failed Runs

**Pipeline Failure Handling**:

1. **Detection**: Job status = 'failed' in `ip_workbench.job_runs`
2. **Alerting**: Mattermost notification to owner + admin
3. **Retry**: Auto-retry once after 5 min delay
4. **Escalation**: If retry fails, mark as 'blocked' and require manual intervention
5. **Logging**: Full error stack trace in `logs` column

**Agent Failure Handling**:

1. **Detection**: LLM returns error or times out
2. **Fallback**: Try secondary model (GPT-4 → GPT-3.5)
3. **Alerting**: Log to Langfuse, email admin if budget exceeded
4. **User Feedback**: Display error message with suggested fix

### Retries

**Retry Logic**:

```typescript
async function retryWithBackoff(fn, maxAttempts = 3) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxAttempts - 1) throw error;
      await sleep(Math.pow(2, i) * 1000); // 1s, 2s, 4s
    }
  }
}
```

### Circuit Breakers

**LLM Gateway Circuit Breaker**:

```typescript
const circuitBreaker = {
  state: 'closed', // closed, open, half-open
  failures: 0,
  threshold: 5,
  timeout: 60000, // 1 min

  async call(fn) {
    if (this.state === 'open') {
      throw new Error('Circuit breaker is open');
    }
    try {
      const result = await fn();
      this.reset();
      return result;
    } catch (error) {
      this.failures++;
      if (this.failures >= this.threshold) {
        this.state = 'open';
        setTimeout(() => { this.state = 'half-open'; }, this.timeout);
      }
      throw error;
    }
  },

  reset() {
    this.failures = 0;
    this.state = 'closed';
  }
};
```

---

## Section 8: Architecture Mapping Table

### Azure/Databricks → Self-Hosted Equivalents

| Azure/Databricks Component | Self-Hosted Equivalent | Implementation | Gaps/Trade-offs |
|----------------------------|------------------------|----------------|-----------------|
| **Azure Data Factory** | n8n + Airflow | n8n for real-time webhooks, Airflow for batch jobs | No drag-drop for Airflow DAGs (code-only) |
| **Databricks Unity Catalog** | Supabase + Neo4j + Qdrant | Supabase for metadata, Neo4j for lineage, Qdrant for search | No built-in access audit (must add Supabase logs) |
| **Databricks SQL Warehouse** | Supabase PostgreSQL | Direct SQL queries via PostgREST | No auto-scaling query clusters |
| **Databricks Notebooks** | JupyterHub + Observable (v1.2) | Jupyter for Python, Observable for interactive viz | No collaborative editing (v1 single-user) |
| **Azure OpenAI** | LiteLLM + Claude/OpenAI/Gemini | LiteLLM proxy for multi-model gateway | No Azure-specific features (whisper, dall-e) |
| **Azure Machine Learning** | External (Paperspace, RunPod) | Model training on GPU VMs, inference via DigitalOcean | No integrated experiment tracking (use MLflow) |
| **Azure Synapse Analytics** | dbt + Supabase | dbt for transformations, Supabase for storage | No distributed query engine (single PostgreSQL instance) |
| **Azure Monitor** | Grafana + Prometheus + Langfuse | Grafana for infra, Langfuse for LLMs | No unified dashboard (must combine sources) |
| **Azure Key Vault** | Supabase Vault + 1Password | Supabase Vault for secrets, 1Password for team access | No HSM-backed encryption |
| **Azure Active Directory** | Supabase Auth + RBAC | Supabase Auth for SSO, custom RBAC in RLS policies | No SAML/SCIM (OAuth only) |
| **PowerBI** | Apache Superset + Tableau | Superset for self-service, Tableau for enterprise BI | No PowerBI-specific DAX/M query language |
| **Azure Cosmos DB** | Supabase PostgreSQL | Relational model instead of document store | No multi-region auto-replication |
| **Azure Event Hub** | n8n webhooks + Supabase | n8n for event ingestion, Supabase for storage | No built-in streaming analytics (batch only) |
| **Azure Blob Storage** | Supabase Storage + DO Spaces | Supabase for files <50MB, DO Spaces for CDN | No tiered storage (hot/cool/archive) |

### Microsoft Foundry → Self-Hosted Mapping

| Foundry Component | Self-Hosted Equivalent | Implementation | Gaps/Trade-offs |
|-------------------|------------------------|----------------|-----------------|
| **Foundry Orchestration** | LangGraph + n8n | LangGraph for agent runtime, n8n for workflow triggers | No Foundry-specific agent templates |
| **Foundry Prompt Hub** | Supabase table + LangSmith | Store prompts in `ip_workbench.prompts`, track versions | No built-in A/B testing UI |
| **Foundry Model Gateway** | LiteLLM | Multi-model proxy with fallbacks, rate limiting | No Foundry-specific routing logic |
| **Foundry Observability** | Langfuse | LLM call tracing, cost tracking, latency analysis | No Foundry-specific metrics (agents, tools) |
| **Foundry Agents** | Custom LangGraph agents | Python LangGraph agents deployed to DO App Platform | No visual agent builder (code-only) |
| **Foundry Tools** | Supabase RPC + custom code | Tools as PostgreSQL functions or n8n workflows | No tool marketplace (must build custom) |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-12-08 | Initial PRD | InsightPulseAI Engineering |

---

**Next Document**: [Plan (Implementation Plan)](./plan.md)
