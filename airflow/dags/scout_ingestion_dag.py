"""
Scout Data Ingestion DAG
Daily batch ingestion from Google Drive, CSV files, and external sources
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago

import json
import logging
import requests
from pathlib import Path

# Default arguments
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email': ['alerts@insightpulseai.net'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}

# DAG definition
dag = DAG(
    dag_id='scout_ingestion',
    default_args=default_args,
    description='Daily Scout data ingestion from Google Drive and CSV',
    schedule_interval='0 2 * * *',  # Daily at 2 AM UTC
    start_date=days_ago(1),
    catchup=False,
    tags=['scout', 'bronze', 'ingestion'],
)


def fetch_google_drive_exports(**context):
    """
    Fetch transaction exports from Google Drive
    Assumes: Google Drive folder with daily export files
    """
    # This would use Google Drive API
    # For now, placeholder for the logic

    execution_date = context['execution_date']
    batch_id = f"gdrive_{execution_date.strftime('%Y%m%d_%H%M%S')}"

    logging.info(f"Fetching Google Drive exports for {execution_date}")

    # Mock data - replace with actual Google Drive API calls
    transactions = [
        {
            'transaction_id': 'TXN001',
            'date': '2025-12-08',
            'amount': 1500.00,
            'currency': 'PHP',
            'category': 'Travel',
            'vendor_name': 'Grab Philippines',
            'description': 'Airport pickup',
        },
        {
            'transaction_id': 'TXN002',
            'date': '2025-12-08',
            'amount': 850.50,
            'currency': 'PHP',
            'category': 'Meals',
            'vendor_name': 'Jollibee',
            'description': 'Team lunch',
        }
    ]

    # Insert into raw ingestion table
    pg_hook = PostgresHook(postgres_conn_id='supabase')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()

    for txn in transactions:
        cursor.execute("""
            INSERT INTO scout.raw_transaction_ingestion
                (raw_data, source, source_filename, ingested_at, ingestion_batch_id)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s)
        """, (
            json.dumps(txn),
            'google_drive',
            f'export_{execution_date.strftime("%Y%m%d")}.json',
            batch_id
        ))

    conn.commit()
    cursor.close()

    logging.info(f"Ingested {len(transactions)} transactions with batch_id={batch_id}")
    return batch_id


def fetch_csv_uploads(**context):
    """
    Process CSV file uploads from staging area
    """
    execution_date = context['execution_date']
    batch_id = f"csv_{execution_date.strftime('%Y%m%d_%H%M%S')}"

    logging.info(f"Processing CSV uploads for {execution_date}")

    # Check for CSV files in staging directory
    staging_dir = Path('/opt/airflow/staging/csv')
    csv_files = list(staging_dir.glob('*.csv'))

    if not csv_files:
        logging.info("No CSV files found in staging")
        return batch_id

    # Process each CSV file
    import csv
    pg_hook = PostgresHook(postgres_conn_id='supabase')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()

    total_rows = 0
    for csv_file in csv_files:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cursor.execute("""
                    INSERT INTO scout.raw_transaction_ingestion
                        (raw_data, source, source_filename, ingested_at, ingestion_batch_id)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s)
                """, (
                    json.dumps(row),
                    'csv_upload',
                    csv_file.name,
                    batch_id
                ))
                total_rows += 1

        # Archive processed file
        csv_file.rename(csv_file.parent.parent / 'archive' / csv_file.name)

    conn.commit()
    cursor.close()

    logging.info(f"Ingested {total_rows} rows from {len(csv_files)} CSV files")
    return batch_id


def validate_ingestion(**context):
    """
    Validate that ingestion completed successfully
    """
    ti = context['ti']
    gdrive_batch_id = ti.xcom_pull(task_ids='fetch_google_drive')
    csv_batch_id = ti.xcom_pull(task_ids='fetch_csv')

    pg_hook = PostgresHook(postgres_conn_id='supabase')

    # Check row counts
    for batch_id in [gdrive_batch_id, csv_batch_id]:
        result = pg_hook.get_first(f"""
            SELECT COUNT(*) FROM scout.raw_transaction_ingestion
            WHERE ingestion_batch_id = '{batch_id}'
        """)
        row_count = result[0] if result else 0

        logging.info(f"Batch {batch_id}: {row_count} rows ingested")

        if row_count == 0:
            logging.warning(f"No data ingested for batch {batch_id}")

    # Check data quality
    result = pg_hook.get_first("""
        SELECT COUNT(*) FROM scout.raw_transaction_ingestion
        WHERE raw_data IS NULL
        AND ingested_at >= CURRENT_DATE
    """)
    null_count = result[0] if result else 0

    if null_count > 0:
        raise ValueError(f"Found {null_count} rows with NULL raw_data")

    logging.info("Ingestion validation passed")


# Task definitions
fetch_gdrive = PythonOperator(
    task_id='fetch_google_drive',
    python_callable=fetch_google_drive_exports,
    provide_context=True,
    dag=dag,
)

fetch_csv = PythonOperator(
    task_id='fetch_csv',
    python_callable=fetch_csv_uploads,
    provide_context=True,
    dag=dag,
)

validate = PythonOperator(
    task_id='validate_ingestion',
    python_callable=validate_ingestion,
    provide_context=True,
    dag=dag,
)

# Trigger dbt Bronze run after successful ingestion
trigger_dbt_bronze = BashOperator(
    task_id='trigger_dbt_bronze',
    bash_command='cd /opt/airflow/dbt-workbench && dbt run --models bronze --target prod',
    dag=dag,
)

# Notify completion via Mattermost
notify_success = BashOperator(
    task_id='notify_success',
    bash_command="""
    curl -X POST https://mattermost.insightpulseai.net/hooks/... \
      -H 'Content-Type: application/json' \
      -d '{"text": "Scout ingestion completed: {{ execution_date }}"}'
    """,
    dag=dag,
)

# Task dependencies
[fetch_gdrive, fetch_csv] >> validate >> trigger_dbt_bronze >> notify_success
