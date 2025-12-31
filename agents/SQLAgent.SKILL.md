# SQLAgent - SKILL Definition

**Agent ID**: agent_004
**Version**: 1.0.0
**Status**: Active
**Dependencies**: CodeGenerator (agent_003)

## Purpose

Design and generate optimized database schemas, migrations, and RLS policies for Supabase PostgreSQL 16 following the Medallion Architecture (Bronze/Silver/Gold). Ensure p99 latency <2000ms and proper multi-tenant isolation.

## Scope & Boundaries

### CAN DO

**Schema Design**
- [x] Design Bronze layer tables (raw data)
- [x] Design Silver layer tables (cleansed, normalized)
- [x] Design Gold layer tables (business-ready views)
- [x] Create pgvector indexes for semantic search
- [x] Design partitioning strategies for large tables

**Migration Generation**
- [x] Generate versioned SQL migrations
- [x] Create up/down migration scripts
- [x] Generate seed data scripts
- [x] Create rollback procedures

**Security**
- [x] Implement Row-Level Security (RLS) policies
- [x] Create role-based access controls
- [x] Design multi-tenant isolation patterns
- [x] Audit access patterns

**Performance Optimization**
- [x] Create indexes for common queries
- [x] Design materialized views for analytics
- [x] Optimize for p99 latency <2000ms
- [x] Implement query caching strategies

### CANNOT DO (Hard Boundaries)

**NO Business Logic**
- [ ] Cannot implement application logic
- [ ] Cannot create stored procedures with business rules
- [ ] Task delegated to: **CodeGenerator (agent_003)**

**NO Direct Execution**
- [ ] Cannot execute migrations directly
- [ ] Can only generate SQL scripts
- [ ] Task delegated to: **DeploymentOrchestrator (agent_006)**

**NO Compliance Decisions**
- [ ] Cannot determine what data to store
- [ ] Must follow schemas from CodeGenerator
- [ ] Compliance from: **ComplianceValidator (agent_002)**

## Input Interface

```typescript
interface SQLAgentInput {
  generation_id: string;  // From CodeGenerator

  data_models: {
    name: string;
    layer: 'bronze' | 'silver' | 'gold';
    columns: {
      name: string;
      type: string;  // PostgreSQL types
      nullable: boolean;
      default?: string;
      references?: {
        table: string;
        column: string;
        on_delete: 'CASCADE' | 'SET NULL' | 'RESTRICT';
      };
    }[];
    indexes: {
      columns: string[];
      type: 'btree' | 'hash' | 'gin' | 'gist' | 'ivfflat';
      unique: boolean;
    }[];
    partitioning?: {
      type: 'range' | 'list' | 'hash';
      column: string;
    };
  }[];

  rls_requirements: {
    table: string;
    policies: {
      name: string;
      operation: 'SELECT' | 'INSERT' | 'UPDATE' | 'DELETE' | 'ALL';
      using_expression: string;  // SQL expression
      with_check_expression?: string;
    }[];
  }[];

  performance_sla: {
    target_p99_latency_ms: number;  // 2000
    expected_row_count: number;
    concurrent_users: number;
  };

  supabase_connection: {
    url: string;
    anon_key: string;
  };

  output_dir: string;
}
```

## Output Interface

```typescript
interface SQLAgentOutput {
  sql_generation_id: string;  // UUID
  generation_id: string;  // Reference to CodeGenerator
  generated_at: string;  // ISO8601

  migrations: {
    version: string;  // '001', '002', etc.
    filename: string;
    description: string;
    up_script: string;  // SQL for applying
    down_script: string;  // SQL for rollback
    estimated_duration_ms: number;
  }[];

  performance_analysis: {
    estimated_p99_latency_ms: number;
    indexes_recommended: number;
    indexes_created: number;
    partitioning_recommended: boolean;
    materialized_views_count: number;
  };

  rls_policies: {
    table: string;
    policy_name: string;
    policy_sql: string;
  }[];

  seed_data: {
    filename: string;
    table: string;
    row_count: number;
  }[];

  warnings: string[];
}
```

## Medallion Architecture Schema

### Bronze Layer (Raw)

```sql
-- Raw ingested data, immutable after write
CREATE TABLE bronze.{table_name} (
    id BIGSERIAL PRIMARY KEY,
    source_system TEXT NOT NULL,
    source_id TEXT,
    raw_data JSONB NOT NULL,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    ingestion_batch_id UUID NOT NULL,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Partition by ingestion date for efficient pruning
CREATE TABLE bronze.{table_name} PARTITION BY RANGE (ingested_at);
```

### Silver Layer (Cleansed)

```sql
-- Cleansed and normalized data
CREATE TABLE silver.{table_name} (
    id BIGSERIAL PRIMARY KEY,
    bronze_id BIGINT REFERENCES bronze.{source_table}(id),

    -- Business columns (typed)
    {column_definitions}

    -- Quality metadata
    is_valid BOOLEAN DEFAULT TRUE,
    validation_errors JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for common query patterns
CREATE INDEX idx_{table_name}_{column} ON silver.{table_name}({column});
```

### Gold Layer (Business-Ready)

```sql
-- Materialized views for analytics
CREATE MATERIALIZED VIEW gold.{view_name} AS
SELECT
    {aggregated_columns}
FROM silver.{source_table}
WHERE is_valid = TRUE
GROUP BY {group_columns}
WITH DATA;

-- Refresh schedule (handled by n8n)
CREATE UNIQUE INDEX idx_{view_name}_pk ON gold.{view_name}({primary_key});
```

## RLS Policy Templates

### Tenant Isolation

```sql
-- Enable RLS on table
ALTER TABLE {schema}.{table_name} ENABLE ROW LEVEL SECURITY;

-- Tenant isolation policy
CREATE POLICY tenant_isolation ON {schema}.{table_name}
    USING (tenant_id = auth.jwt() ->> 'tenant_id');

-- Admin bypass
CREATE POLICY admin_all ON {schema}.{table_name}
    TO admin
    USING (TRUE);
```

### Role-Based Access

```sql
-- Read-only for viewers
CREATE POLICY viewer_read ON {schema}.{table_name}
    FOR SELECT
    TO viewer
    USING (TRUE);

-- Full access for editors
CREATE POLICY editor_all ON {schema}.{table_name}
    FOR ALL
    TO editor
    USING (TRUE)
    WITH CHECK (TRUE);
```

## Performance Optimization

### Index Strategy

| Query Pattern | Index Type | Example |
|---------------|------------|---------|
| Equality lookup | B-tree | `CREATE INDEX idx_x ON t(x)` |
| Range queries | B-tree | `CREATE INDEX idx_date ON t(date DESC)` |
| Text search | GIN (pg_trgm) | `CREATE INDEX idx_text ON t USING gin(text gin_trgm_ops)` |
| Vector similarity | IVFFlat | `CREATE INDEX idx_embed ON t USING ivfflat(embed vector_cosine_ops)` |
| JSON queries | GIN | `CREATE INDEX idx_json ON t USING gin(data)` |

### Materialized View Refresh

```sql
-- Concurrent refresh (no lock)
REFRESH MATERIALIZED VIEW CONCURRENTLY gold.{view_name};

-- Schedule via n8n: every 15 minutes for hot data, daily for cold
```

## Failure Modes & Recovery

| Failure Type | Detection | Recovery Action |
|--------------|-----------|-----------------|
| Migration syntax error | SQL validation | Fix and regenerate |
| Index creation timeout | Duration check | Create CONCURRENTLY |
| RLS policy conflict | Policy test | Merge or rename policies |
| Performance SLA miss | pgbench test | Add indexes, partition |
| Foreign key violation | Constraint error | Fix data order |

## Performance Constraints

| Metric | Constraint |
|--------|------------|
| Migration generation | <1 minute |
| p99 latency target | <2000ms |
| Concurrent writes | Support 100+ |
| Query timeout | 30 seconds max |

## Dependencies

- **Upstream**: CodeGenerator (agent_003) generation_id required
- **Downstream**: ValidationAgent (agent_005), DeploymentOrchestrator (agent_006)

## Required Tools & Libraries

```python
# Database
psycopg2>=2.9.0  # PostgreSQL driver
sqlalchemy>=2.0.0  # ORM for validation
alembic>=1.12.0  # Migration management

# Supabase
supabase>=2.0.0

# Validation
sqlfluff>=2.3.0  # SQL linting
pgbench  # Performance testing (CLI)

# Utilities
jinja2>=3.1.0  # SQL templating
```

## Success Criteria

| Criteria | Target |
|----------|--------|
| All migrations valid SQL | 100% |
| RLS policies cover all tables | 100% |
| p99 latency under SLA | <2000ms |
| Rollback scripts functional | 100% |
| Multi-tenant isolation verified | 100% |

## Handoff to Next Agent

Upon successful generation:
1. Migration files written to output_dir
2. SQL scripts stored in Supabase
3. Lineage updated in `pipeline_lineage`
4. **ValidationAgent (agent_005)** uses migrations for test DB
5. **DeploymentOrchestrator (agent_006)** applies migrations
