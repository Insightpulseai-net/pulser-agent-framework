"""
Scout Data Transformation DAG
Bronze → Silver → Gold transformations using dbt
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.utils.dates import days_ago

import logging

# Default arguments
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email': ['alerts@insightpulseai.net'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=60),
}

# DAG definition
dag = DAG(
    dag_id='scout_transformation',
    default_args=default_args,
    description='Bronze → Silver → Gold transformations',
    schedule_interval='0 */1 * * *',  # Every hour
    start_date=days_ago(1),
    catchup=False,
    tags=['scout', 'transformation', 'dbt'],
)


def check_bronze_freshness(**context):
    """
    Check if Bronze layer has fresh data (last 1 hour)
    """
    pg_hook = PostgresHook(postgres_conn_id='supabase')

    result = pg_hook.get_first("""
        SELECT COUNT(*) FROM scout.bronze_transactions
        WHERE ingested_at >= NOW() - INTERVAL '1 hour'
    """)

    fresh_count = result[0] if result else 0

    logging.info(f"Found {fresh_count} fresh Bronze records")

    if fresh_count > 0:
        return 'run_dbt_silver'
    else:
        return 'skip_transformation'


def validate_silver_quality(**context):
    """
    Validate Silver layer data quality
    """
    pg_hook = PostgresHook(postgres_conn_id='supabase')

    # Check for nulls in critical fields
    result = pg_hook.get_first("""
        SELECT COUNT(*) FROM scout.silver_validated_transactions
        WHERE transaction_date IS NULL
           OR amount IS NULL
           OR category IS NULL
        AND validated_at >= NOW() - INTERVAL '1 hour'
    """)

    null_count = result[0] if result else 0

    if null_count > 0:
        raise ValueError(f"Found {null_count} Silver records with NULL critical fields")

    # Check for negative amounts
    result = pg_hook.get_first("""
        SELECT COUNT(*) FROM scout.silver_validated_transactions
        WHERE amount <= 0
        AND validated_at >= NOW() - INTERVAL '1 hour'
    """)

    negative_count = result[0] if result else 0

    if negative_count > 0:
        raise ValueError(f"Found {negative_count} Silver records with negative amounts")

    logging.info("Silver layer quality validation passed")


def validate_gold_completeness(**context):
    """
    Validate Gold layer completeness (all months present)
    """
    pg_hook = PostgresHook(postgres_conn_id='supabase')

    # Check if current month exists in Gold
    result = pg_hook.get_first("""
        SELECT COUNT(*) FROM scout.gold_monthly_summary
        WHERE month = DATE_TRUNC('month', CURRENT_DATE)
    """)

    current_month_count = result[0] if result else 0

    if current_month_count == 0:
        logging.warning("Current month not yet in Gold layer")
    else:
        logging.info(f"Current month has {current_month_count} category summaries")

    # Check for data gaps
    result = pg_hook.get_first("""
        WITH expected_months AS (
            SELECT generate_series(
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months'),
                DATE_TRUNC('month', CURRENT_DATE),
                '1 month'::interval
            )::DATE AS month
        )
        SELECT COUNT(*) FROM expected_months em
        LEFT JOIN scout.gold_monthly_summary g ON g.month = em.month
        WHERE g.month IS NULL
    """)

    missing_months = result[0] if result else 0

    if missing_months > 0:
        logging.warning(f"Missing {missing_months} months in Gold layer")

    logging.info("Gold layer completeness validation passed")


# Task: Check Bronze freshness (branching)
check_freshness = BranchPythonOperator(
    task_id='check_bronze_freshness',
    python_callable=check_bronze_freshness,
    provide_context=True,
    dag=dag,
)

# Task: Run dbt Silver layer
run_dbt_silver = BashOperator(
    task_id='run_dbt_silver',
    bash_command='cd /opt/airflow/dbt-workbench && dbt run --models silver --target prod',
    dag=dag,
)

# Task: Test dbt Silver layer
test_dbt_silver = BashOperator(
    task_id='test_dbt_silver',
    bash_command='cd /opt/airflow/dbt-workbench && dbt test --models silver --target prod',
    dag=dag,
)

# Task: Validate Silver quality
validate_silver = PythonOperator(
    task_id='validate_silver_quality',
    python_callable=validate_silver_quality,
    provide_context=True,
    dag=dag,
)

# Task: Run dbt Gold layer
run_dbt_gold = BashOperator(
    task_id='run_dbt_gold',
    bash_command='cd /opt/airflow/dbt-workbench && dbt run --models gold --target prod',
    dag=dag,
)

# Task: Test dbt Gold layer
test_dbt_gold = BashOperator(
    task_id='test_dbt_gold',
    bash_command='cd /opt/airflow/dbt-workbench && dbt test --models gold --target prod',
    dag=dag,
)

# Task: Validate Gold completeness
validate_gold = PythonOperator(
    task_id='validate_gold_completeness',
    python_callable=validate_gold_completeness,
    provide_context=True,
    dag=dag,
)

# Task: Skip transformation if no fresh data
skip_transformation = BashOperator(
    task_id='skip_transformation',
    bash_command='echo "No fresh Bronze data, skipping transformation"',
    dag=dag,
)

# Task: Update metadata table
update_metadata = PostgresOperator(
    task_id='update_metadata',
    postgres_conn_id='supabase',
    sql="""
        INSERT INTO ip_workbench.job_runs (id, pipeline_id, status, started_at, completed_at, rows_processed)
        VALUES (
            gen_random_uuid(),
            (SELECT id FROM ip_workbench.pipelines WHERE name = 'scout_transformation' LIMIT 1),
            'completed',
            NOW() - INTERVAL '1 hour',
            NOW(),
            (SELECT COUNT(*) FROM scout.silver_validated_transactions WHERE validated_at >= NOW() - INTERVAL '1 hour')
        )
    """,
    dag=dag,
)

# Task: Notify success
notify_success = BashOperator(
    task_id='notify_success',
    bash_command="""
    curl -X POST https://mattermost.insightpulseai.net/hooks/... \
      -H 'Content-Type: application/json' \
      -d '{"text": "Scout transformation completed: {{ execution_date }}"}'
    """,
    dag=dag,
)

# Task dependencies
check_freshness >> [run_dbt_silver, skip_transformation]
run_dbt_silver >> test_dbt_silver >> validate_silver >> run_dbt_gold
run_dbt_gold >> test_dbt_gold >> validate_gold >> update_metadata >> notify_success
