# dbt Workbench - Scout Retail Medallion Architecture

Production-ready dbt project implementing Bronze → Silver → Gold → Platinum data transformation layers for Scout Retail domain.

## Architecture

### Medallion Layers

| Layer | Purpose | Materialization | Refresh |
|-------|---------|-----------------|---------|
| **Bronze** | Raw ingestion, no transformation | Table | Real-time + daily batch |
| **Silver** | Validated, cleaned, deduplicated | Table | Every 1 hour |
| **Gold** | Business marts, aggregated | Table | Every 6 hours |
| **Platinum** | AI-ready, embeddings | View | On-demand |

### Data Flow

```
Google Drive/CSV/Webhooks
    ↓
Bronze (Raw JSONB)
    ↓ dbt run --models bronze
Silver (Validated schema)
    ↓ dbt run --models silver
Gold (Business aggregates)
    ↓ dbt run --models gold
Platinum (AI features)
    ↓ Used by LLM/RAG systems
```

## Models

### Bronze Layer

- **`bronze_transactions`**: Raw transaction data (JSONB)
- **`bronze_products`**: Raw product catalog (JSONB)

### Silver Layer

- **`silver_validated_transactions`**: Validated transactions with schema enforcement
- **`silver_products`**: Deduplicated product catalog with standardization

### Gold Layer

- **`gold_monthly_summary`**: Monthly aggregates by category (MoM/YoY growth)
- **`gold_category_trends`**: Weekly trends with anomaly detection

### Platinum Layer

- **`platinum_transaction_embeddings`**: Transaction text for embedding generation
- **`platinum_product_recommendations`**: ML features for product recommendations

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (Supabase)
- dbt-postgres adapter

### Installation

```bash
# Install dbt
pip install dbt-postgres dbt-utils

# Copy profile template
cp profiles.yml.example ~/.dbt/profiles.yml

# Edit with your credentials
nano ~/.dbt/profiles.yml

# Set environment variables
export SUPABASE_HOST=aws-1-us-east-1.pooler.supabase.com
export SUPABASE_PORT=6543
export POSTGRES_USER=postgres.xkxyvboeubffxxbebsll
export POSTGRES_PASSWORD=your_password
export POSTGRES_DB=postgres
```

### Testing Connection

```bash
# Test connection
dbt debug

# Install dependencies
dbt deps

# Compile models
dbt compile
```

## Usage

### Full Refresh

```bash
# Run all models
dbt run

# Run with full refresh
dbt run --full-refresh
```

### Incremental Runs

```bash
# Run Bronze layer only
dbt run --models bronze

# Run Silver layer
dbt run --models silver

# Run Gold layer
dbt run --models gold

# Run specific model
dbt run --models silver_validated_transactions
```

### Testing

```bash
# Run all tests
dbt test

# Run tests for specific layer
dbt test --models silver

# Run specific test
dbt test --models silver_validated_transactions
```

### Documentation

```bash
# Generate documentation
dbt docs generate

# Serve documentation site
dbt docs serve
```

## Data Quality Tests

### Built-in Tests

- **Uniqueness**: Primary keys in all layers
- **Not Null**: Critical fields (id, dates, amounts)
- **Relationships**: Foreign keys between layers
- **Accepted Values**: Categorical fields (category, status)

### Custom Tests

- **Recency**: Data freshness (validated_at within 1 day)
- **Positive Amounts**: amount > 0 for all transactions
- **Date Range**: transaction_date <= CURRENT_DATE
- **Expression Tests**: Complex business rule validation

### Running Tests

```bash
# Run all tests
dbt test

# Store test failures
dbt test --store-failures

# View failures
SELECT * FROM test_failures.silver_validated_transactions;
```

## Deployment

### Production Workflow

```bash
# 1. Validate models
dbt compile

# 2. Run tests
dbt test

# 3. Deploy to production
dbt run --target prod

# 4. Generate fresh docs
dbt docs generate

# 5. Upload docs to S3/Spaces
aws s3 sync target/ s3://dbt-docs-bucket/
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run dbt
  run: |
    dbt deps
    dbt run --target prod
    dbt test
```

## Maintenance

### Daily Tasks

```bash
# Run incremental refresh
dbt run --models silver+ gold+

# Check test results
dbt test --models silver gold
```

### Weekly Tasks

```bash
# Full refresh (weekends)
dbt run --full-refresh

# Generate fresh documentation
dbt docs generate
```

### Monitoring

```sql
-- Check row counts
SELECT
    'bronze_transactions' AS table_name,
    COUNT(*) AS row_count
FROM bronze.bronze_transactions
UNION ALL
SELECT 'silver_validated_transactions', COUNT(*)
FROM silver.silver_validated_transactions;

-- Check data freshness
SELECT MAX(validated_at) AS last_refresh
FROM silver.silver_validated_transactions;
```

## Troubleshooting

### Common Issues

**Connection Timeout**:
```bash
# Use pooler port 6543, not direct port 5432
export SUPABASE_PORT=6543
```

**RLS Blocking Queries**:
```bash
# Use service role key for dbt operations
export POSTGRES_PASSWORD=$SUPABASE_SERVICE_ROLE_KEY
```

**Out of Memory**:
```bash
# Reduce thread count
dbt run --threads 2
```

**Schema Not Found**:
```sql
-- Create schemas manually
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS platinum;
```

## Performance Optimization

### Indexes

Indexes are automatically created via post-hooks:
- Date columns for time-series queries
- Foreign keys for joins
- Category columns for grouping
- Unique constraints for deduplication

### Incremental Models

Future enhancement:
```sql
{{
    config(
        materialized='incremental',
        unique_key='id',
        on_schema_change='sync_all_columns'
    )
}}

SELECT * FROM {{ ref('bronze_transactions') }}
{% if is_incremental() %}
WHERE ingested_at > (SELECT MAX(validated_at) FROM {{ this }})
{% endif %}
```

## Integration Points

### Airflow

```python
# Airflow DAG calls dbt
BashOperator(
    task_id='dbt_run_silver',
    bash_command='dbt run --models silver'
)
```

### n8n

```json
{
  "name": "Run dbt",
  "type": "n8n-nodes-base.executeCommand",
  "parameters": {
    "command": "dbt run --models silver"
  }
}
```

### Supabase Edge Functions

```typescript
// Trigger dbt after data ingestion
await fetch('https://n8n.insightpulseai.net/webhook/dbt-refresh', {
  method: 'POST',
  body: JSON.stringify({ layer: 'silver' })
});
```

## References

- [dbt Documentation](https://docs.getdbt.com/)
- [dbt-utils Package](https://github.com/dbt-labs/dbt-utils)
- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
- [AI Workbench PRD](../spec/ai-workbench/prd.md)
