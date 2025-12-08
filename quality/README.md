# Data Quality Framework

Comprehensive data quality testing and validation for Scout Medallion architecture.

## Test Categories

### 1. Volume Tests (`tests/row_count_checks.sql`)
- Daily ingestion volume thresholds
- Bronze→Silver conversion rate (≥80%)
- Gold completeness (current month exists)
- No orphaned Silver records

### 2. Completeness Tests (`tests/null_checks.sql`)
- Critical field null rate <5% (Silver)
- Zero nulls in Gold layer
- Required field validation

### 3. Uniqueness Tests (`tests/unique_checks.sql`)
- Primary key uniqueness (all layers)
- Transaction ID uniqueness (Silver)
- SKU uniqueness (products)

### 4. Referential Integrity (`tests/referential_integrity.sql`)
- Bronze→Silver foreign keys
- Silver→Gold source traceability
- No dangling references

## Quality Gates (8-Step Cycle)

Based on Guardian framework from PRD:

### Step 1: Syntax Validation
**Check**: JSON structure valid, types correct
**Tool**: dbt compile + PostgreSQL constraints
**Threshold**: 0 syntax errors

### Step 2: Type Validation
**Check**: amount > 0, dates valid, categories in allowed list
**Tool**: dbt tests + custom SQL
**Threshold**: 0 type errors

### Step 3: Lint Validation
**Check**: SQL style, naming conventions
**Tool**: sqlfluff, dbt conventions
**Threshold**: 0 lint errors

### Step 4: Security Validation
**Check**: RLS policies enforced, no exposed PII
**Tool**: Supabase RLS audit
**Threshold**: 0 policy violations

### Step 5: Test Validation
**Check**: All dbt tests pass
**Tool**: dbt test --store-failures
**Threshold**: ≥80% tests pass (Silver), 100% (Gold)

### Step 6: Performance Validation
**Check**: Query latency <3s, no table scans
**Tool**: EXPLAIN ANALYZE, pg_stat_statements
**Threshold**: <3s for 95th percentile

### Step 7: Documentation Validation
**Check**: All models documented, columns described
**Tool**: dbt docs generate
**Threshold**: 100% model coverage

### Step 8: Integration Validation
**Check**: End-to-end pipeline success
**Tool**: Airflow DAG status, n8n workflow logs
**Threshold**: >95% success rate (7 days)

## Running Tests

### dbt Tests (Automated)
```bash
# Run all tests
cd dbt-workbench
dbt test --target prod

# Run specific layer
dbt test --models silver

# Store failures for analysis
dbt test --store-failures

# View failures
psql "$POSTGRES_URL" -c "SELECT * FROM test_failures.silver_validated_transactions;"
```

### SQL Tests (Manual)
```bash
# Row count checks
psql "$POSTGRES_URL" -f quality/tests/row_count_checks.sql

# Null checks
psql "$POSTGRES_URL" -f quality/tests/null_checks.sql

# All tests
for test in quality/tests/*.sql; do
    echo "Running $test..."
    psql "$POSTGRES_URL" -f "$test"
done
```

### Airflow DQ DAG (Scheduled)
```bash
# Trigger manually
airflow dags trigger data_quality_validation

# Check status
airflow dags list-runs -d data_quality_validation
```

## Quality Metrics Dashboard

### Current Scores (Example)
| Table | Completeness | Uniqueness | Timeliness | Overall |
|-------|--------------|------------|------------|---------|
| bronze_transactions | 99.8% | N/A | <5 min | N/A |
| silver_validated_transactions | 97.5% | 100% | <1 hour | 98.5% |
| gold_monthly_summary | 100% | 100% | <6 hours | 100% |

### Alerts Configuration
```yaml
thresholds:
  silver_completeness: 95%
  silver_timeliness: 1 hour
  gold_completeness: 100%
  gold_timeliness: 6 hours

channels:
  - mattermost: https://mattermost.insightpulseai.net/hooks/...
  - email: alerts@insightpulseai.net
```

## Great Expectations (Future)

Directory structure prepared for Great Expectations:
```
quality/great_expectations/
├── great_expectations.yml
├── expectations/
│   ├── scout_silver_suite.json
│   └── scout_gold_suite.json
└── checkpoints/
    └── daily_validation.yml
```

**TODO**: Implement GE integration
- Install: `pip install great-expectations`
- Init: `great_expectations init`
- Create expectations for each layer
- Add to Airflow DAG

## References

- [dbt Testing Best Practices](https://docs.getdbt.com/docs/building-a-dbt-project/tests)
- [Guardian Framework (PRD Section 7)](../../spec/ai-workbench/prd.md#section-7-edge-cases--constraints)
- [Airflow DQ DAG](../../airflow/dags/data_quality_dag.py)
