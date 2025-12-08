# InsightPulseAI Workbench UI

Next.js 14 AI Workbench UI with catalog, SQL editor, pipeline manager, and knowledge graph visualization.

## Features

- **Home Dashboard**: KPI cards, recent activity feed, quick actions
- **Data Catalog**: Browse and search all tables with schema filtering
- **SQL Editor**: Monaco editor with syntax highlighting and query execution
- **Pipelines**: Visual DAG editor with React Flow for pipeline creation
- **Data Quality**: Scorecard dashboard with quality metrics
- **Knowledge Graph**: Interactive lineage visualization (Neo4j + D3.js)
- **Genie (NL2SQL)**: Chat interface for natural language to SQL conversion
- **Notebooks**: JupyterHub iframe integration

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Material Web Components
- **Database**: Supabase PostgreSQL
- **State Management**: Zustand
- **Charts**: ECharts
- **Graph**: D3.js / Neo4j
- **Editor**: Monaco Editor
- **Pipeline Canvas**: React Flow

## Installation

### Prerequisites

- Node.js 18+ and npm
- Supabase account
- Access to LiteLLM gateway
- Neo4j database (optional for lineage)

### Setup

1. **Clone and Install**

```bash
cd ai-workbench-ui
npm install
```

2. **Environment Variables**

Copy `.env.local.example` to `.env.local` and fill in your credentials:

```bash
cp .env.local.example .env.local
```

Required variables:
- `NEXT_PUBLIC_SUPABASE_URL`: Your Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key for admin operations
- `NEXT_PUBLIC_LITELLM_URL`: LiteLLM gateway URL
- `LITELLM_API_KEY`: API key for LiteLLM
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: Neo4j credentials (optional)

3. **Database Schema**

Run the schema migration in Supabase:

```sql
-- See packages/db/sql/01_workbench_schema.sql
```

4. **Run Development Server**

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
ai-workbench-ui/
├── app/                      # Next.js 14 App Router
│   ├── api/                  # API routes
│   │   ├── catalog/          # Catalog endpoints
│   │   └── genie/            # NL2SQL endpoints
│   ├── catalog/              # Catalog page
│   ├── sql/                  # SQL Editor page
│   ├── pipelines/            # Pipelines page
│   ├── quality/              # Data Quality page
│   ├── graph/                # Knowledge Graph page
│   ├── genie/                # Genie (NL2SQL) page
│   ├── notebooks/            # Notebooks page
│   ├── layout.tsx            # Root layout
│   ├── page.tsx              # Home dashboard
│   └── globals.css           # Global styles
├── components/               # Reusable components
│   ├── Header.tsx            # App header
│   ├── Sidebar.tsx           # Navigation sidebar
│   ├── KPICard.tsx           # KPI card component
│   ├── ActivityFeed.tsx      # Activity feed
│   ├── TableBrowser.tsx      # Table list
│   ├── ChatInterface.tsx     # Chat UI
│   ├── PipelineCanvas.tsx    # React Flow canvas
│   └── DQScorecard.tsx       # Data quality scorecard
├── lib/                      # Utilities and integrations
│   └── supabase/
│       └── client.ts         # Supabase client
├── styles/                   # Additional styles
├── public/                   # Static assets
├── package.json              # Dependencies
├── tsconfig.json             # TypeScript config
├── tailwind.config.ts        # Tailwind config
├── next.config.js            # Next.js config
└── README.md                 # This file
```

## Pages

### Home Dashboard (`/`)
- KPI cards (tables, pipelines, agents, DQ score)
- Recent activity feed
- Quick actions (New Pipeline, Run Query, Ask Genie)

### Data Catalog (`/catalog`)
- Schema tree navigation (Bronze/Silver/Gold/Platinum)
- Table list with search and filtering
- Table detail panel with metadata

### SQL Editor (`/sql`)
- Monaco editor with SQL syntax highlighting
- Schema-aware autocomplete
- Query execution with results table
- Export results (CSV, JSON)

### Pipelines (`/pipelines`)
- Pipeline list with status indicators
- Visual DAG editor (React Flow)
- Node configuration forms
- Job logs and run history

### Data Quality (`/quality`)
- Scorecard grid with quality metrics
- Test results table
- Trend charts
- Alert configuration

### Knowledge Graph (`/graph`)
- Interactive graph visualization (D3.js/Cytoscape)
- Table lineage tracking
- Column-level lineage
- Impact analysis

### Genie (`/genie`)
- Chat interface for NL2SQL
- SQL query generation with Claude API
- Query execution and results
- Feedback mechanism

### Notebooks (`/notebooks`)
- JupyterHub iframe integration
- Interactive data analysis

## API Routes

### Catalog API (`/api/catalog`)
**GET**: Fetch tables with optional schema filtering

```bash
curl http://localhost:3000/api/catalog?schema=gold
```

### NL2SQL API (`/api/genie/nl2sql`)
**POST**: Convert natural language to SQL

```bash
curl -X POST http://localhost:3000/api/genie/nl2sql \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Show me top 5 vendors by expense amount"}'
```

## Supabase Integration

### Tables

- `ip_workbench.tables` - Table metadata
- `ip_workbench.pipelines` - Pipeline definitions
- `ip_workbench.agents` - AI agent configurations
- `ip_workbench.agent_runs` - Agent execution history
- `ip_workbench.job_runs` - Pipeline run logs
- `ip_workbench.dq_test_results` - Data quality tests
- `ip_workbench.sql_snippets` - Saved SQL queries
- `ip_workbench.query_history` - Query execution history

### RLS Policies

All tables have Row-Level Security (RLS) policies enforcing role-based access:
- **Viewer**: Read-only access
- **Engineer**: CRUD on own resources
- **Admin**: Full access
- **Service**: API-only access

## Authentication

Google OAuth via Supabase Auth (planned):

```typescript
import { createClient } from '@/lib/supabase/client'

const supabase = createClient()
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google',
})
```

## Development Workflow

1. **Start Development Server**
   ```bash
   npm run dev
   ```

2. **Make Changes**
   - Edit components in `components/`
   - Add pages in `app/`
   - Create API routes in `app/api/`

3. **Lint and Type Check**
   ```bash
   npm run lint
   ```

4. **Build for Production**
   ```bash
   npm run build
   ```

5. **Run Production Build**
   ```bash
   npm start
   ```

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

Environment variables are managed in Vercel dashboard.

### DigitalOcean App Platform

```bash
# Create App Platform spec
doctl apps create --spec infra/do/workbench-ui.yaml
```

## Troubleshooting

### Monaco Editor Not Loading

Ensure dynamic import is used:

```typescript
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false })
```

### Supabase Connection Errors

1. Check `.env.local` has correct credentials
2. Verify Supabase project is active
3. Check RLS policies allow access

### React Flow Canvas Issues

Ensure CSS is imported:

```typescript
import 'reactflow/dist/style.css'
```

### API Route Errors

1. Check CORS settings in Next.js config
2. Verify API keys are set
3. Check LiteLLM gateway is accessible

## Testing

```bash
# Run tests (when implemented)
npm test

# Run E2E tests (when implemented)
npm run test:e2e
```

## Performance

- **Server-Side Rendering**: Next.js 14 App Router
- **Static Generation**: Catalog pages cached
- **Code Splitting**: Dynamic imports for Monaco, React Flow
- **Image Optimization**: Next.js Image component
- **Font Optimization**: Next.js Font loader

## Security

- Environment variables not exposed to client
- RLS policies enforce access control
- API routes use server-side authentication
- HTTPS enforced in production

## Contributing

1. Create feature branch
2. Make changes with tests
3. Run linting and type checking
4. Submit pull request

## License

Proprietary - InsightPulseAI

## Support

For issues and questions, contact: engineering@insightpulseai.net

---

**Built with ❤️ by InsightPulseAI Engineering Team**
