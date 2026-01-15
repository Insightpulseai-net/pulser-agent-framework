# @ipai/mcp-core

Canonical MCP (Model Context Protocol) tool surface for InsightPulse AI agents.

## Overview

This MCP server provides a unified tool interface for all IPAI agents:

| Agent | Primary Tools |
|-------|---------------|
| **Bolt Agent** (backend/infra) | `supabase.*`, `n8n.*`, `odoo.*`, `ops.*`, `github.*` |
| **Figma Agent** (design/system) | `figma.*`, `ces.*`, `supabase.sql_query`, `github.*` |
| **Ask Ces Agent** (creative effectiveness) | `ces.campaign_overview`, `scout.tx_insight`, `supabase.sql_query` |
| **Scout / Sari-Sari Expert** (retail analytics) | `scout.tx_insight`, `scout.gold_health`, `supabase.table_select` |
| **FeedMe Agent** (content/data) | `supabase.*`, `github.*`, `n8n.*` |

## Tool Namespaces

### `supabase.*` - Database & SaaS Core

| Tool | Description |
|------|-------------|
| `supabase.sql_query` | Execute read-only SQL (SELECT only) |
| `supabase.rpc_call` | Call Postgres functions |
| `supabase.table_select` | Structured queries without raw SQL |
| `supabase.health_check` | Verify DB connectivity and critical views |

### `odoo.*` - Odoo 18 CE/OCA

| Tool | Description |
|------|-------------|
| `odoo.nav_health` | Check Odoo navigation and basic functionality |
| `odoo.search_records` | Generic XML-RPC search for any model |
| `odoo.trigger_mirror_sync` | Kick off Odoo → Supabase mirror flow |

### `n8n.*` - Workflow Orchestration

| Tool | Description |
|------|-------------|
| `n8n.run_workflow` | Execute workflow by ID or name |
| `n8n.get_execution` | Poll execution status and result |
| `n8n.list_workflows` | List available workflows |
| `n8n.health_check` | Check n8n instance health |

### `figma.*` - Design System

| Tool | Description |
|------|-------------|
| `figma.sync_project` | Sync Figma project to Supabase |
| `figma.audit_design_system` | Audit design system alignment |
| `figma.health_check` | Check Figma integration health |

### `github.*` - Version Control

| Tool | Description |
|------|-------------|
| `github.create_pr` | Create a pull request |
| `github.comment_pr` | Add comment to PR |
| `github.get_file` | Get file content from repo |
| `github.list_repos` | List repositories |

### `scout.*` - Retail Analytics

| Tool | Description |
|------|-------------|
| `scout.tx_insight` | Natural language query on Scout Gold schema |
| `scout.gold_health` | Check Scout Gold schema health |
| `scout.seed_demo_data` | Seed demo data for tenants |

### `ces.*` - Creative Effectiveness

| Tool | Description |
|------|-------------|
| `ces.campaign_overview` | Fetch campaign with scores and explanations |
| `ces.link_figma_asset` | Connect campaign to Figma asset |
| `ces.list_campaigns` | List campaigns with filters |
| `ces.health_check` | Check CES schema health |

### `ops.*` - Operations & Health

| Tool | Description |
|------|-------------|
| `ops.stack_health` | Single "is everything ok?" check |
| `ops.db_lint_summary` | Surface db-linter results |
| `ops.self_heal_recommendations` | Suggest patches for issues |

## Installation

```bash
npm install @ipai/mcp-core
# or
pnpm add @ipai/mcp-core
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD`
- `N8N_BASE_URL`, `N8N_API_KEY`
- `FIGMA_ACCESS_TOKEN`
- `GITHUB_TOKEN`

## Usage

### As MCP Server (Claude Desktop / Claude Code)

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ipai-core": {
      "command": "npx",
      "args": ["-y", "@ipai/mcp-core"],
      "env": {
        "SUPABASE_URL": "https://spdtwktxdalcfigzeqrz.supabase.co",
        "SUPABASE_ANON_KEY": "your_key",
        "SUPABASE_SERVICE_ROLE_KEY": "your_key",
        "N8N_BASE_URL": "https://n8n.insightpulseai.net",
        "N8N_API_KEY": "your_key",
        "GITHUB_TOKEN": "your_token"
      }
    }
  }
}
```

### Programmatic Usage

```typescript
import { allTools, toolMap } from '@ipai/mcp-core';

// List all tools
console.log(allTools.map(t => t.name));

// Execute a tool directly
const result = await toolMap.get('supabase.health_check')?.execute();
console.log(result);
```

## Development

```bash
# Install dependencies
pnpm install

# Build
pnpm build

# Run in development mode
pnpm dev

# Type check
pnpm typecheck

# Run tests
pnpm test
```

## Architecture

```
src/
├── index.ts          # MCP server entry point, tool aggregation
├── config.ts         # Configuration management
├── types.ts          # Zod schemas and TypeScript types
└── tools/
    ├── supabase.ts   # Supabase tools
    ├── odoo.ts       # Odoo tools
    ├── n8n.ts        # n8n tools
    ├── figma.ts      # Figma tools
    ├── github.ts     # GitHub tools
    ├── scout.ts      # Scout analytics tools
    ├── ces.ts        # CES tools
    └── ops.ts        # Operations/health tools
```

## Security Notes

- **Read-only by default**: `supabase.sql_query` only allows SELECT statements
- **Service role key**: Used for admin operations, not exposed to clients
- **RLS enforcement**: All tools respect Supabase RLS policies
- **No direct writes**: Writes go through Edge Functions or n8n workflows

## License

Apache-2.0
