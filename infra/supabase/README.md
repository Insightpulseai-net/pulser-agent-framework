# Supabase Configuration

Complete Supabase metadata schema and RLS policies for AI Workbench.

## Directory Structure

```
infra/supabase/
├── migrations/           # SQL migration scripts
│   ├── 001_metadata_schema.sql      # Core workbench tables
│   └── 002_medallion_schemas.sql    # Bronze/Silver/Gold/Platinum
├── rls-policies/         # Row-Level Security policies
│   └── workbench_policies.sql       # Role-based access control
├── edge-functions/       # Supabase Edge Functions (serverless)
└── supabase.toml         # Supabase CLI configuration
```

## Prerequisites

1. **Supabase CLI**
   ```bash
   brew install supabase/tap/supabase
   ```

2. **PostgreSQL Client** (`psql`)
   ```bash
   brew install postgresql
   ```

3. **Supabase Project**
   - Project created at https://supabase.com
   - Project ref: `xkxyvboeubffxxbebsll`
   - PostgreSQL 15 enabled

## Quick Start

### 1. Configure Environment Variables

```bash
# Add to ~/.zshrc
export SUPABASE_PROJECT_REF="xkxyvboeubffxxbebsll"
export SUPABASE_URL="https://xkxyvboeubffxxbebsll.supabase.co"
export SUPABASE_ANON_KEY="<your-anon-key>"
export SUPABASE_SERVICE_ROLE_KEY="<your-service-role-key>"
export POSTGRES_URL="postgresql://postgres:[password]@aws-1-us-east-1.pooler.supabase.com:6543/postgres"

# Reload shell
source ~/.zshrc
```

### 2. Run Migrations

```bash
cd migrations/

# Run metadata schema migration
psql "$POSTGRES_URL" -f 001_metadata_schema.sql

# Run medallion schemas migration
psql "$POSTGRES_URL" -f 002_medallion_schemas.sql

# Verify tables created
psql "$POSTGRES_URL" -c "\dt ip_workbench.*"
psql "$POSTGRES_URL" -c "\dt bronze.*"
psql "$POSTGRES_URL" -c "\dt silver.*"
psql "$POSTGRES_URL" -c "\dt gold.*"
psql "$POSTGRES_URL" -c "\dt platinum.*"
```

### 3. Enable RLS Policies

```bash
cd ../rls-policies/

# Apply RLS policies
psql "$POSTGRES_URL" -f workbench_policies.sql

# Verify policies
psql "$POSTGRES_URL" -c "\d ip_workbench.tables"
```

### 4. Create Test Users

```bash
# Via Supabase dashboard: Authentication → Users → Invite user

# Or via SQL
psql "$POSTGRES_URL" <<EOF
-- Create test viewer
INSERT INTO auth.users (email, raw_user_meta_data)
VALUES ('viewer@test.com', '{"role": "viewer"}');

-- Create test engineer
INSERT INTO auth.users (email, raw_user_meta_data)
VALUES ('engineer@test.com', '{"role": "engineer"}');

-- Create test admin
INSERT INTO auth.users (email, raw_user_meta_data)
VALUES ('admin@test.com', '{"role": "admin"}');
EOF
```

## Schema Overview

### Core Metadata (ip_workbench)

#### Catalog Tables
- `domains` - Business domains (Finance, Retail, Creative, HR)
- `tables` - Table catalog with DQ scores
- `table_metadata` - Column definitions

#### Pipeline Tables
- `pipelines` - Pipeline definitions (React Flow JSON)
- `pipeline_steps` - Ordered transformation steps
- `jobs` - Scheduled executions
- `job_runs` - Execution history with logs

#### Data Quality Tables
- `tests` - DQ test definitions
- `test_runs` - Validation results

#### Lineage Tables
- `lineage_edges` - Source→target table relationships

#### AI Assist Tables
- `agents` - AI agent definitions
- `agent_bindings` - Agent→table bindings
- `agent_runs` - Execution history
- `llm_requests` - Token usage tracking

#### SQL Editor Tables
- `sql_snippets` - Saved queries
- `query_history` - Execution log

#### Cost Tracking Tables
- `cost_tracker` - Service-level costs
- `activity_log` - User actions audit log

### Medallion Architecture

#### Bronze (Raw)
- `scout_transactions_raw` - Raw Scout JSON dumps
- `expenses_raw` - Raw OCR outputs

#### Silver (Cleaned)
- `scout_transactions` - Cleaned transactions
- `expenses` - Validated expense records

#### Gold (Business Marts)
- `finance_expenses` - Aggregated expense mart
- `scout_sales` - Aggregated sales mart

#### Platinum (AI/Genie Views)
- `monthly_expenses_by_agency` - Materialized view
- `scout_sales_trends` - Materialized view

## Role-Based Access Control (RLS)

### User Roles

| Role | Permissions | Use Cases |
|------|-------------|-----------|
| **viewer** | Read catalog, run queries | BI Analyst, Finance Manager |
| **engineer** | Create pipelines, edit SQL | Data Engineer, AI Orchestrator |
| **admin** | Full access, manage users | Architect, Platform Lead |
| **service** | API-only access | n8n workflows, Odoo integration |

### Setting User Roles

```bash
# Via Supabase dashboard
# Users → Select user → Raw User Meta Data → Add: {"role": "engineer"}

# Or via SQL
psql "$POSTGRES_URL" <<EOF
UPDATE auth.users
SET raw_user_meta_data = jsonb_set(raw_user_meta_data, '{role}', '"engineer"')
WHERE email = 'user@example.com';
EOF
```

### Testing RLS Policies

```bash
# Test as viewer (should succeed)
psql "$POSTGRES_URL" -c "SET LOCAL role TO 'authenticated'; SELECT * FROM ip_workbench.tables LIMIT 5;"

# Test as engineer (should succeed)
psql "$POSTGRES_URL" -c "SET LOCAL role TO 'authenticated'; INSERT INTO ip_workbench.pipelines (name, description, definition, owner) VALUES ('test', 'test', '{}'::jsonb, '<user-uuid>');"

# Test unauthorized access (should fail)
psql "$POSTGRES_URL" -c "SET LOCAL role TO 'anon'; DELETE FROM ip_workbench.tables WHERE id = '<uuid>';"
```

## Database Functions (RPC)

### Execute SQL Query

```sql
CREATE OR REPLACE FUNCTION ip_workbench.execute_sql(sql_query TEXT)
RETURNS TABLE(result JSONB) AS $$
BEGIN
    RETURN QUERY EXECUTE sql_query;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Usage
SELECT * FROM ip_workbench.execute_sql('SELECT * FROM gold.finance_expenses LIMIT 10');
```

### Search Tables (Vector Search)

```sql
-- Requires pg_trgm extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE OR REPLACE FUNCTION ip_workbench.search_tables(search_query TEXT)
RETURNS TABLE(
    id UUID,
    schema_name TEXT,
    table_name TEXT,
    description TEXT,
    similarity REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.schema_name,
        t.table_name,
        t.description,
        SIMILARITY(t.table_name, search_query) AS similarity
    FROM ip_workbench.tables t
    WHERE t.table_name % search_query OR t.description % search_query
    ORDER BY similarity DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- Usage
SELECT * FROM ip_workbench.search_tables('expense');
```

### Get Table Lineage

```sql
CREATE OR REPLACE FUNCTION ip_workbench.get_table_lineage(
    table_uuid UUID,
    direction TEXT DEFAULT 'downstream' -- 'upstream' or 'downstream'
)
RETURNS TABLE(
    source_id UUID,
    source_name TEXT,
    target_id UUID,
    target_name TEXT,
    transformation_sql TEXT
) AS $$
BEGIN
    IF direction = 'downstream' THEN
        RETURN QUERY
        SELECT
            le.source_table_id,
            st.table_name,
            le.target_table_id,
            tt.table_name,
            le.transformation_sql
        FROM ip_workbench.lineage_edges le
        JOIN ip_workbench.tables st ON le.source_table_id = st.id
        JOIN ip_workbench.tables tt ON le.target_table_id = tt.id
        WHERE le.source_table_id = table_uuid;
    ELSE
        RETURN QUERY
        SELECT
            le.source_table_id,
            st.table_name,
            le.target_table_id,
            tt.table_name,
            le.transformation_sql
        FROM ip_workbench.lineage_edges le
        JOIN ip_workbench.tables st ON le.source_table_id = st.id
        JOIN ip_workbench.tables tt ON le.target_table_id = tt.id
        WHERE le.target_table_id = table_uuid;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Usage
SELECT * FROM ip_workbench.get_table_lineage('<table-uuid>', 'downstream');
```

## Scheduled Jobs (pg_cron)

### Enable pg_cron Extension

```sql
-- Via Supabase dashboard: Database → Extensions → pg_cron

-- Verify
SELECT * FROM pg_extension WHERE extname = 'pg_cron';
```

### Schedule Materialized View Refresh

```sql
-- Refresh platinum views daily at 2 AM
SELECT cron.schedule(
    'refresh_platinum_views',
    '0 2 * * *',
    $$SELECT platinum.refresh_all_views()$$
);

-- Verify scheduled jobs
SELECT * FROM cron.job;
```

## Backup & Restore

### Supabase Automatic Backups

Supabase provides automatic backups (see dashboard):
- **Point-in-time recovery**: 7 days (Pro plan)
- **Daily backups**: Retained for 7 days
- **Manual snapshots**: On-demand via dashboard

### Manual Backup

```bash
# Dump entire database
pg_dump "$POSTGRES_URL" > backup_$(date +%Y%m%d).sql

# Dump specific schema
pg_dump "$POSTGRES_URL" -n ip_workbench > ip_workbench_backup.sql

# Restore from backup
psql "$POSTGRES_URL" < backup_20251208.sql
```

## Monitoring & Performance

### Query Performance

```sql
-- Enable pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slow queries
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Table Statistics

```sql
-- View table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS size
FROM pg_tables
WHERE schemaname IN ('ip_workbench', 'bronze', 'silver', 'gold', 'platinum')
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC;
```

### Index Usage

```sql
-- View index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'ip_workbench'
ORDER BY idx_scan DESC;
```

## Troubleshooting

### Connection Issues

```bash
# Test connection
psql "$POSTGRES_URL" -c "SELECT version();"

# Check pooler status
psql "$POSTGRES_URL" -c "SHOW pool_mode;"

# Use direct connection (port 5432) for migrations
export POSTGRES_DIRECT_URL="postgresql://postgres:[password]@aws-1-us-east-1.connect.supabase.com:5432/postgres"
psql "$POSTGRES_DIRECT_URL" -f migrations/001_metadata_schema.sql
```

### RLS Policy Issues

```bash
# Check if RLS is enabled
psql "$POSTGRES_URL" -c "\d ip_workbench.tables"

# View policies
psql "$POSTGRES_URL" -c "SELECT * FROM pg_policies WHERE schemaname = 'ip_workbench';"

# Test policy as specific user
psql "$POSTGRES_URL" -c "SET LOCAL role TO 'authenticated'; SET LOCAL request.jwt.claims TO '{\"sub\": \"<user-uuid>\"}'; SELECT * FROM ip_workbench.tables;"
```

## Next Steps

1. Deploy frontend: `packages/web/README.md`
2. Setup n8n workflows: `services/n8n/README.md`
3. Configure LiteLLM: `services/litellm-proxy/README.md`

## Resources

- **Supabase Docs**: https://supabase.com/docs
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **RLS Guide**: https://supabase.com/docs/guides/auth/row-level-security
