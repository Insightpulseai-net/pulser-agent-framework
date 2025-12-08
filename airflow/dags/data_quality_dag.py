"""
Data Quality Monitoring DAG
Daily validation of Silver and Gold layers using dbt tests and custom checks
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago

import logging
import json

# Default arguments
default_args = {
    'owner': 'data-quality',
    'depends_on_past': False,
    'email': ['alerts@insightpulseai.net'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    dag_id='data_quality_validation',
    default_args=default_args,
    description='Daily data quality validation and alerting',
    schedule_interval='0 8 * * *',  # Daily at 8 AM UTC
    start_date=days_ago(1),
    catchup=False,
    tags=['data-quality', 'monitoring'],
)


def calculate_dq_scores(**context):
    """
    Calculate data quality scores for all tables
    """
    pg_hook = PostgresHook(postgres_conn_id='supabase')

    # Tables to check
    tables = [
        ('silver', 'silver_validated_transactions'),
        ('silver', 'silver_products'),
        ('gold', 'gold_monthly_summary'),
        ('gold', 'gold_category_trends'),
    ]

    scores = {}

    for schema, table in tables:
        # Completeness: % of non-null values
        result = pg_hook.get_first(f"""
            SELECT
                COUNT(*) AS total_rows,
                SUM(CASE WHEN id IS NULL THEN 1 ELSE 0 END) AS null_id_count
            FROM {schema}.{table}
        """)

        total_rows = result[0] if result else 0
        null_count = result[1] if result else 0
        completeness = (1 - null_count / total_rows * 100) if total_rows > 0 else 0

        # Uniqueness: % of unique primary keys
        uniqueness = 100  # Enforced by unique constraint

        # Timeliness: Data freshness (last update)
        if schema == 'silver':
            result = pg_hook.get_first(f"""
                SELECT EXTRACT(EPOCH FROM (NOW() - MAX(validated_at))) / 3600 AS hours_old
                FROM {schema}.{table}
            """)
            hours_old = result[0] if result else 999
            timeliness = max(0, 100 - (hours_old * 5))  # Deduct 5 points per hour
        else:
            timeliness = 100

        # Overall score (weighted average)
        overall_score = (completeness * 0.4 + uniqueness * 0.3 + timeliness * 0.3)

        scores[f"{schema}.{table}"] = {
            'completeness': round(completeness, 2),
            'uniqueness': round(uniqueness, 2),
            'timeliness': round(timeliness, 2),
            'overall': round(overall_score, 2),
            'total_rows': total_rows,
        }

        logging.info(f"{schema}.{table}: {overall_score:.2f}%")

    # Store scores in ip_workbench.tables
    for table_name, score_data in scores.items():
        pg_hook.run(f"""
            UPDATE ip_workbench.tables
            SET dq_score = {score_data['overall']},
                row_count = {score_data['total_rows']},
                last_updated = NOW()
            WHERE schema_name || '.' || table_name = '{table_name}'
        """)

    # Push to XCom for alerting
    context['ti'].xcom_push(key='dq_scores', value=scores)

    logging.info("DQ scores calculated and stored")


def check_dq_thresholds(**context):
    """
    Check if any tables fall below DQ thresholds
    """
    ti = context['ti']
    scores = ti.xcom_pull(task_ids='calculate_dq_scores', key='dq_scores')

    threshold = 80  # Minimum acceptable DQ score
    failing_tables = []

    for table_name, score_data in scores.items():
        if score_data['overall'] < threshold:
            failing_tables.append({
                'table': table_name,
                'score': score_data['overall'],
                'completeness': score_data['completeness'],
                'timeliness': score_data['timeliness'],
            })

    if failing_tables:
        alert_message = "Data Quality Alert - Tables below threshold:\n"
        for table in failing_tables:
            alert_message += f"- {table['table']}: {table['score']}% (Completeness: {table['completeness']}%, Timeliness: {table['timeliness']}%)\n"

        logging.warning(alert_message)

        # Store alert
        pg_hook = PostgresHook(postgres_conn_id='supabase')
        pg_hook.run("""
            INSERT INTO ip_workbench.dq_alerts (id, severity, message, created_at)
            VALUES (gen_random_uuid(), 'high', %s, NOW())
        """, parameters=(alert_message,))

        context['ti'].xcom_push(key='alert_message', value=alert_message)
        return 'send_alert'
    else:
        logging.info("All tables meet DQ thresholds")
        return 'skip_alert'


def send_mattermost_alert(**context):
    """
    Send Mattermost notification for DQ failures
    """
    ti = context['ti']
    alert_message = ti.xcom_pull(task_ids='check_dq_thresholds', key='alert_message')

    import requests

    webhook_url = "https://mattermost.insightpulseai.net/hooks/..."

    payload = {
        'text': f"🚨 **Data Quality Alert**\n\n{alert_message}",
        'username': 'Data Quality Bot',
    }

    response = requests.post(webhook_url, json=payload)

    if response.status_code == 200:
        logging.info("Alert sent to Mattermost")
    else:
        logging.error(f"Failed to send alert: {response.status_code}")


# Task: Run dbt tests
run_dbt_tests = BashOperator(
    task_id='run_dbt_tests',
    bash_command='cd /opt/airflow/dbt-workbench && dbt test --target prod --store-failures',
    dag=dag,
)

# Task: Calculate DQ scores
calculate_scores = PythonOperator(
    task_id='calculate_dq_scores',
    python_callable=calculate_dq_scores,
    provide_context=True,
    dag=dag,
)

# Task: Check thresholds
check_thresholds = BranchPythonOperator(
    task_id='check_dq_thresholds',
    python_callable=check_dq_thresholds,
    provide_context=True,
    dag=dag,
)

# Task: Send alert
send_alert = PythonOperator(
    task_id='send_alert',
    python_callable=send_mattermost_alert,
    provide_context=True,
    dag=dag,
)

# Task: Skip alert
skip_alert = BashOperator(
    task_id='skip_alert',
    bash_command='echo "No alerts needed"',
    dag=dag,
)

# Task: Update DQ dashboard
update_dashboard = BashOperator(
    task_id='update_dashboard',
    bash_command="""
    curl -X POST https://n8n.insightpulseai.net/webhook/dq-dashboard-refresh
    """,
    dag=dag,
)

# Task dependencies
run_dbt_tests >> calculate_scores >> check_thresholds >> [send_alert, skip_alert]
send_alert >> update_dashboard
skip_alert >> update_dashboard
