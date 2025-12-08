{{
    config(
        materialized='table',
        schema='bronze',
        tags=['bronze', 'scout', 'raw'],
        post_hook=[
            "COMMENT ON TABLE {{ this }} IS 'Raw Scout transaction data from Google Drive/CSV/webhook sources'",
            "CREATE INDEX IF NOT EXISTS idx_bronze_transactions_ingested ON {{ this }} (ingested_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_bronze_transactions_source ON {{ this }} (source)"
        ]
    )
}}

-- Raw transaction ingestion from multiple sources
-- Sources: Google Drive exports, CSV uploads, real-time webhooks
-- No validation or transformation applied at this layer

SELECT
    gen_random_uuid() AS id,
    raw_data,
    source,
    source_filename,
    ingested_at,
    ingestion_batch_id,
    CURRENT_TIMESTAMP AS created_at
FROM {{ source('scout', 'raw_transaction_ingestion') }}
WHERE ingested_at >= CURRENT_DATE - INTERVAL '30 days'
  AND raw_data IS NOT NULL

-- Future state: This will be populated by:
-- 1. Airflow DAG: Daily batch from Google Drive
-- 2. n8n workflow: Real-time webhook ingestion
-- 3. Manual CSV uploads via UI
