{{
    config(
        materialized='table',
        schema='bronze',
        tags=['bronze', 'scout', 'raw'],
        post_hook=[
            "COMMENT ON TABLE {{ this }} IS 'Raw Scout product catalog data'",
            "CREATE INDEX IF NOT EXISTS idx_bronze_products_ingested ON {{ this }} (ingested_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_bronze_products_source ON {{ this }} (source)"
        ]
    )
}}

-- Raw product catalog data from Scout system
-- Contains product master data, pricing, inventory

SELECT
    gen_random_uuid() AS id,
    raw_data,
    source,
    source_filename,
    ingested_at,
    ingestion_batch_id,
    CURRENT_TIMESTAMP AS created_at
FROM {{ source('scout', 'raw_product_ingestion') }}
WHERE ingested_at >= CURRENT_DATE - INTERVAL '90 days'
  AND raw_data IS NOT NULL
