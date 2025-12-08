# Airflow ETL Orchestration

Apache Airflow DAGs for Scout Retail data pipeline orchestration.

## DAG Overview

### 1. `scout_ingestion_dag.py`
**Schedule**: Daily at 2 AM UTC  
**Purpose**: Batch ingestion from Google Drive and CSV files  
**Duration**: ~15 minutes  
**Dependencies**: Google Drive API, Supabase connection

**Tasks**:
1. `fetch_google_drive` - Fetch transaction exports from Google Drive
2. `fetch_csv` - Process CSV files from staging directory
3. `validate_ingestion` - Validate row counts and data quality
4. `trigger_dbt_bronze` - Run dbt Bronze layer models
5. `notify_success` - Send Mattermost notification

**Trigger Manually**:
```bash
airflow dags trigger scout_ingestion
```

### 2. `scout_transformation_dag.py`
**Schedule**: Every hour  
**Purpose**: Bronze → Silver → Gold transformations  
**Duration**: ~30 minutes  
**Dependencies**: dbt-workbench project, Supabase connection

**Tasks**:
1. `check_bronze_freshness` - Check for new Bronze data (branching)
2. `run_dbt_silver` - Transform Bronze → Silver
3. `test_dbt_silver` - Run dbt tests on Silver layer
4. `validate_silver_quality` - Custom quality checks
5. `run_dbt_gold` - Transform Silver → Gold
6. `test_dbt_gold` - Run dbt tests on Gold layer
7. `validate_gold_completeness` - Ensure all months present
8. `update_metadata` - Update ip_workbench.job_runs
9. `notify_success` - Send Mattermost notification

**Trigger Manually**:
```bash
airflow dags trigger scout_transformation
```

### 3. `data_quality_dag.py`
**Schedule**: Daily at 8 AM UTC  
**Purpose**: Comprehensive data quality validation  
**Duration**: ~10 minutes  
**Dependencies**: dbt tests, custom SQL checks

**Tasks**:
1. `run_dbt_tests` - Execute all dbt tests with failure storage
2. `calculate_dq_scores` - Calculate completeness/timeliness scores
3. `check_dq_thresholds` - Branch on threshold violations
4. `send_alert` - Mattermost notification if thresholds violated
5. `skip_alert` - No action if all thresholds met
6. `update_dashboard` - Refresh DQ dashboard via n8n webhook

**Trigger Manually**:
```bash
airflow dags trigger data_quality_validation
```

## Setup

### Prerequisites

- Apache Airflow 2.8+
- Python 3.11+
- PostgreSQL provider (`apache-airflow-providers-postgres`)
- dbt installed in Airflow environment

### Installation

```bash
# Install Airflow
pip install apache-airflow==2.8.0 \
  apache-airflow-providers-postgres \
  psycopg2-binary

# Initialize database
airflow db init

# Create admin user
airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@insightpulseai.net
```

### Configuration

#### Connections

**Supabase Connection** (`supabase`):
```bash
airflow connections add supabase \
  --conn-type postgres \
  --conn-host aws-1-us-east-1.pooler.supabase.com \
  --conn-port 6543 \
  --conn-login postgres.xkxyvboeubffxxbebsll \
  --conn-password $SUPABASE_SERVICE_ROLE_KEY \
  --conn-schema postgres
```

**Google Drive Connection** (`google_drive`):
```bash
airflow connections add google_drive \
  --conn-type google_cloud_platform \
  --conn-extra '{"key_path": "/opt/airflow/keys/gdrive-service-account.json"}'
```

#### Variables

```bash
# Set Airflow variables
airflow variables set dbt_project_path /opt/airflow/dbt-workbench
airflow variables set mattermost_webhook_url https://mattermost.insightpulseai.net/hooks/...
airflow variables set staging_dir /opt/airflow/staging
```

### Deployment

#### Local Development

```bash
# Start Airflow webserver
airflow webserver --port 8080

# Start scheduler (separate terminal)
airflow scheduler

# Access UI: http://localhost:8080
```

#### DigitalOcean Kubernetes (Production)

```yaml
# airflow-values.yaml
images:
  airflow:
    repository: apache/airflow
    tag: 2.8.0-python3.11

dags:
  gitSync:
    enabled: true
    repo: https://github.com/insightpulseai/ai-workbench.git
    branch: main
    subPath: data-layer/airflow/dags

postgresql:
  enabled: true
  persistence:
    size: 10Gi

redis:
  enabled: true

executor: CeleryExecutor
```

```bash
# Deploy to DOKS
helm repo add apache-airflow https://airflow.apache.org
helm install airflow apache-airflow/airflow -f airflow-values.yaml
```

## Monitoring

### DAG Status

```bash
# List all DAGs
airflow dags list

# List DAG runs
airflow dags list-runs -d scout_ingestion

# View task logs
airflow tasks logs scout_ingestion fetch_google_drive 2025-12-08
```

### Metrics

```sql
-- DAG success rate (last 7 days)
SELECT
    dag_id,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN state = 'success' THEN 1 ELSE 0 END) AS successful_runs,
    SUM(CASE WHEN state = 'success' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 AS success_rate
FROM dag_run
WHERE execution_date >= NOW() - INTERVAL '7 days'
GROUP BY dag_id;

-- Average DAG duration
SELECT
    dag_id,
    AVG(EXTRACT(EPOCH FROM (end_date - start_date))) / 60 AS avg_duration_min
FROM dag_run
WHERE state = 'success'
AND execution_date >= NOW() - INTERVAL '30 days'
GROUP BY dag_id;
```

### Alerts

**Mattermost Webhook**:
- DAG failures → `#data-engineering`
- DQ threshold violations → `#data-quality-alerts`
- Long-running tasks (>30 min) → `#data-engineering`

**Email Alerts**:
```python
# In default_args
'email': ['alerts@insightpulseai.net'],
'email_on_failure': True,
'email_on_retry': False,
```

## Troubleshooting

### DAG Import Errors

**Symptom**: DAG not appearing in UI

**Solution**:
```bash
# Check DAG errors
airflow dags list-import-errors

# Test DAG parsing
python /opt/airflow/dags/scout_ingestion_dag.py
```

### Connection Refused

**Symptom**: `psycopg2.OperationalError: could not connect`

**Solution**:
```bash
# Test connection
psql "postgresql://postgres.xkxyvboeubffxxbebsll:$PASSWORD@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"

# Verify Airflow connection
airflow connections get supabase
```

### Task Timeout

**Symptom**: Task fails with timeout error

**Solution**:
```python
# Increase execution_timeout in default_args
'execution_timeout': timedelta(minutes=60),
```

### dbt Command Not Found

**Symptom**: `BashOperator` fails with "dbt: command not found"

**Solution**:
```bash
# Install dbt in Airflow environment
docker exec -it airflow-webserver pip install dbt-postgres

# Or add to requirements.txt
echo "dbt-postgres" >> requirements.txt
```

## Best Practices

### DAG Development

1. **Use meaningful task IDs**: `fetch_google_drive` not `task1`
2. **Set execution_timeout**: Prevent zombie tasks
3. **Enable retries**: `retries: 2` for transient failures
4. **Add documentation**: Docstrings for each DAG
5. **Test locally**: `airflow dags test` before deploying

### Task Dependencies

```python
# Clear dependencies
task1 >> task2 >> task3

# Branching
[task1, task2] >> task3 >> [task4, task5]

# Use BranchPythonOperator for conditional logic
```

### Error Handling

```python
# Use on_failure_callback for custom alerts
def alert_on_failure(context):
    send_mattermost_alert(context)

default_args = {
    'on_failure_callback': alert_on_failure,
}
```

## References

- [Airflow Documentation](https://airflow.apache.org/docs/)
- [dbt + Airflow Integration](https://docs.getdbt.com/docs/deploy/airflow)
- [AI Workbench Tasks (T4.2)](../../spec-kit/spec/ai-workbench/tasks.md#t42-create-node-config-forms)
