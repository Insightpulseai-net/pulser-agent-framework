# Experience Layer - AI Workbench UI

Next.js 14 frontend for the InsightPulseAI Multi-Agent AI Workbench.

## Overview

The Experience Layer is a production-ready Next.js application providing a modern web interface for the AI Workbench platform. It includes:

- **Data Catalog**: Browse and search tables across Bronze, Silver, Gold, and Platinum schemas
- **SQL Editor**: Monaco editor with syntax highlighting and query execution
- **Pipeline Manager**: Visual DAG editor using React Flow for pipeline orchestration
- **Data Quality Dashboard**: Scorecard view with quality metrics and test results
- **Knowledge Graph**: Interactive lineage visualization (Neo4j integration)
- **Genie (NL2SQL)**: Chat interface for natural language to SQL conversion
- **Notebooks**: JupyterHub integration for interactive data analysis

## Quick Start

```bash
cd ai-workbench-ui
npm install
cp .env.local.example .env.local
# Edit .env.local with your credentials
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
experience-layer/
├── ai-workbench-ui/          # Next.js application
│   ├── app/                  # App Router pages
│   │   ├── api/              # API routes
│   │   ├── catalog/          # Catalog page
│   │   ├── sql/              # SQL Editor
│   │   ├── pipelines/        # Pipeline Manager
│   │   ├── quality/          # Data Quality
│   │   ├── graph/            # Knowledge Graph
│   │   ├── genie/            # NL2SQL
│   │   ├── notebooks/        # Jupyter integration
│   │   ├── layout.tsx        # Root layout
│   │   └── page.tsx          # Home dashboard
│   ├── components/           # Reusable components
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   ├── KPICard.tsx
│   │   ├── ActivityFeed.tsx
│   │   ├── TableBrowser.tsx
│   │   ├── ChatInterface.tsx
│   │   ├── PipelineCanvas.tsx
│   │   └── DQScorecard.tsx
│   ├── lib/                  # Utilities
│   │   └── supabase/
│   │       └── client.ts     # Supabase integration
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── README.md
└── README.md                 # This file
```

## Features

### 1. Home Dashboard (`/`)

**KPI Cards**:
- Total tables count with trend
- Active pipelines count
- AI agents count
- Average data quality score

**Recent Activity**:
- Pipeline runs (last 10)
- Query executions
- Agent runs

**Quick Actions**:
- Create new pipeline
- Run SQL query
- Ask Genie

### 2. Data Catalog (`/catalog`)

**Features**:
- Schema tree navigation (Bronze → Silver → Gold → Platinum)
- Full-text search across table names and descriptions
- Schema filtering
- Table metadata display (row count, DQ score)
- Direct query button

**Table Browser**:
- Sortable columns
- Color-coded schema badges
- DQ score indicators
- Action buttons (View, Query)

### 3. SQL Editor (`/sql`)

**Features**:
- Monaco editor with SQL syntax highlighting
- Schema-aware autocomplete (tables, columns)
- Query execution via Supabase RPC
- Results table with pagination
- Query history
- Saved snippets
- Export results (CSV, JSON)

**Editor Shortcuts**:
- `Ctrl+Enter`: Execute query
- `Ctrl+S`: Save snippet
- `Ctrl+/`: Toggle comment

### 4. Pipeline Manager (`/pipelines`)

**Features**:
- Pipeline list with status indicators
- Visual DAG editor using React Flow
- Node types: Bronze (ingestion), Silver (transform), Gold (mart)
- Drag-and-drop node placement
- Edge connections for data flow
- Node configuration forms (SQL, schedule, owner)
- Job log viewer with timestamps
- Schedule configuration (cron, timezone)

**Pipeline Canvas**:
- Zoom, pan, fit-to-screen controls
- Background grid
- Mini-map navigation

### 5. Data Quality Dashboard (`/quality`)

**Features**:
- Scorecard grid for all tables
- Quality metrics: Completeness, Uniqueness, Consistency
- Color-coded scores (green >90%, yellow 70-90%, red <70%)
- Test results table
- Failed test details
- Trend charts (30-day history)
- Alert configuration

**Scorecard Details**:
- Click card → view detailed test results
- Filter by schema
- Sort by score

### 6. Knowledge Graph (`/graph`)

**Features** (Planned):
- Interactive graph visualization using D3.js or Cytoscape
- Node types: Source, Bronze, Silver, Gold, Dashboard, Agent
- Edge types: Ingests, Transforms, Consumes
- Filter by schema and depth
- Click node → show table details
- Column-level lineage
- Impact analysis (downstream tables)

**Integration**:
- Neo4j graph database
- Lineage parsing from SQL queries (sqlglot)
- Real-time updates from pipeline runs

### 7. Genie (NL2SQL) (`/genie`)

**Features**:
- Chat interface for natural language questions
- SQL generation using Claude Sonnet 4.5 via LiteLLM
- Query execution and results display
- Copy SQL button
- Feedback mechanism (thumbs up/down)
- Query history

**Example Queries**:
- "Show me top 5 vendors by expense amount"
- "What's the average transaction value by category?"
- "Find all transactions over $1000 in the last 30 days"

### 8. Notebooks (`/notebooks`)

**Features**:
- JupyterHub iframe integration
- Interactive Python/SQL cells
- Data visualization
- Export notebooks

## Technical Stack

### Frontend
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 3.4
- **Components**: Material Web Components
- **State**: Zustand (global state management)
- **Charts**: ECharts (quality trends, costs)
- **Graph**: D3.js (lineage visualization)
- **Editor**: Monaco Editor (SQL syntax)
- **Pipeline**: React Flow (visual DAG)

### Backend Integration
- **Database**: Supabase PostgreSQL 15
- **Auth**: Supabase Auth (Google OAuth planned)
- **API**: Supabase PostgREST (auto-generated REST API)
- **RPC**: Custom PostgreSQL functions
- **Storage**: Supabase Storage (file uploads)

### External Services
- **LiteLLM**: Multi-model gateway (Claude, OpenAI, Gemini)
- **Langfuse**: LLM observability and tracing
- **Neo4j**: Graph database for lineage
- **Qdrant**: Vector search for catalog
- **n8n**: Workflow orchestration

## API Routes

### Catalog API
**Endpoint**: `GET /api/catalog?schema={schema}`

**Response**:
```json
{
  "tables": [
    {
      "id": "uuid",
      "schema_name": "gold",
      "table_name": "finance_expenses",
      "description": "Aggregated expense records",
      "row_count": 15234,
      "dq_score": 97.5
    }
  ]
}
```

### NL2SQL API
**Endpoint**: `POST /api/genie/nl2sql`

**Request**:
```json
{
  "prompt": "Show me top 5 vendors by expense amount"
}
```

**Response**:
```json
{
  "sql": "SELECT vendor, SUM(amount) AS total FROM gold.finance_expenses GROUP BY vendor ORDER BY total DESC LIMIT 5",
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 32,
    "total_tokens": 77
  }
}
```

## Authentication & Authorization

### Roles
- **Viewer**: Read-only access (catalog, SQL queries, dashboards)
- **Engineer**: CRUD on pipelines, agents, queries
- **Admin**: User management, cost tracking, system configuration
- **Service**: API-only access for automation

### RLS Policies
All Supabase tables have Row-Level Security (RLS) enforced:

```sql
-- Viewers can read all tables
CREATE POLICY "viewers_read_tables" ON ip_workbench.tables
FOR SELECT USING (true);

-- Engineers can update their own pipelines
CREATE POLICY "engineers_manage_own_pipelines" ON ip_workbench.pipelines
FOR ALL USING (owner = auth.uid());

-- Admins have full access
CREATE POLICY "admins_all" ON ip_workbench.pipelines
FOR ALL USING (auth.role() = 'admin');
```

## Deployment

### Local Development
```bash
npm run dev     # Start dev server at http://localhost:3000
npm run build   # Build for production
npm start       # Run production build
```

### Vercel (Recommended)
```bash
vercel --prod
```

Environment variables managed in Vercel dashboard.

### DigitalOcean App Platform
```bash
doctl apps create --spec infra/do/workbench-ui.yaml
```

## Environment Variables

Required in `.env.local`:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xkxyvboeubffxxbebsll.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# LiteLLM Gateway
NEXT_PUBLIC_LITELLM_URL=https://litellm.insightpulseai.net/v1
LITELLM_API_KEY=your_api_key

# Langfuse (optional)
NEXT_PUBLIC_LANGFUSE_URL=https://langfuse.insightpulseai.net

# Neo4j (optional)
NEO4J_URI=bolt://neo4j.insightpulseai.net:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Qdrant (optional)
QDRANT_URL=http://qdrant.insightpulseai.net:6333
QDRANT_API_KEY=your_api_key
```

## Performance Optimizations

- **Server-Side Rendering**: Dynamic pages with SSR
- **Static Generation**: Catalog pages cached at build time
- **Code Splitting**: Monaco and React Flow loaded dynamically
- **Image Optimization**: Next.js Image component
- **Font Optimization**: Next.js Font loader
- **API Caching**: Supabase query results cached
- **Lazy Loading**: Components loaded on demand

## Testing

```bash
# Unit tests (planned)
npm test

# E2E tests (planned)
npm run test:e2e

# Linting
npm run lint
```

## Troubleshooting

### Common Issues

**Monaco Editor Not Loading**:
- Ensure dynamic import is used
- Check SSR is disabled

**Supabase Connection Errors**:
- Verify `.env.local` credentials
- Check Supabase project status
- Verify RLS policies

**React Flow Canvas Issues**:
- Import CSS: `import 'reactflow/dist/style.css'`
- Check parent div has height

**API Route 500 Errors**:
- Check server logs in console
- Verify API keys are set
- Test LiteLLM gateway directly

## Roadmap

### v1.1 (Q1 2026)
- [ ] Google OAuth authentication
- [ ] User profile management
- [ ] Advanced search with Qdrant
- [ ] Column-level lineage
- [ ] Real-time notifications

### v1.2 (Q2 2026)
- [ ] Observable-style notebooks
- [ ] Collaborative editing
- [ ] Custom dashboards
- [ ] Export to PowerBI/Tableau
- [ ] Mobile responsive design

### v2.0 (Q3 2026)
- [ ] Multi-tenant support
- [ ] RBAC fine-grained permissions
- [ ] Audit logging
- [ ] Cost optimization insights
- [ ] AI agent marketplace

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

Proprietary - InsightPulseAI

## Support

- **Email**: engineering@insightpulseai.net
- **Slack**: #workbench-support
- **Docs**: https://docs.insightpulseai.net

---

**Built with ❤️ by InsightPulseAI Engineering**
