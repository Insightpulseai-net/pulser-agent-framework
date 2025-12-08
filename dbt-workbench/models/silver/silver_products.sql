{{
    config(
        materialized='table',
        schema='silver',
        tags=['silver', 'scout', 'validated'],
        post_hook=[
            "COMMENT ON TABLE {{ this }} IS 'Validated Scout product catalog with deduplication and standardization'",
            "CREATE INDEX IF NOT EXISTS idx_silver_products_sku ON {{ this }} (sku)",
            "CREATE INDEX IF NOT EXISTS idx_silver_products_category ON {{ this }} (category)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_silver_products_sku_unique ON {{ this }} (sku)"
        ]
    )
}}

WITH source_data AS (
    SELECT
        id AS bronze_id,
        raw_data,
        source,
        ingested_at
    FROM {{ ref('bronze_products') }}
    WHERE ingested_at >= CURRENT_DATE - INTERVAL '90 days'
),

parsed_data AS (
    SELECT
        bronze_id,
        (raw_data->>'sku')::TEXT AS sku,
        (raw_data->>'name')::TEXT AS name,
        (raw_data->>'description')::TEXT AS description,
        (raw_data->>'category')::TEXT AS category,
        (raw_data->>'brand')::TEXT AS brand,
        (raw_data->>'price')::NUMERIC(15,2) AS price,
        (raw_data->>'cost')::NUMERIC(15,2) AS cost,
        (raw_data->>'stock_quantity')::INTEGER AS stock_quantity,
        (raw_data->>'unit_of_measure')::TEXT AS unit_of_measure,
        (raw_data->>'barcode')::TEXT AS barcode,
        (raw_data->>'is_active')::BOOLEAN AS is_active,
        source,
        ingested_at,
        ROW_NUMBER() OVER (
            PARTITION BY (raw_data->>'sku')
            ORDER BY ingested_at DESC
        ) AS row_num
    FROM source_data
    WHERE raw_data->>'sku' IS NOT NULL
),

validated_data AS (
    SELECT
        gen_random_uuid() AS id,
        bronze_id,
        sku,
        TRIM(name) AS name,
        TRIM(description) AS description,
        COALESCE(category, 'General') AS category,
        brand,
        COALESCE(price, 0) AS price,
        COALESCE(cost, 0) AS cost,
        COALESCE(stock_quantity, 0) AS stock_quantity,
        COALESCE(unit_of_measure, 'EA') AS unit_of_measure,
        barcode,
        COALESCE(is_active, true) AS is_active,
        source,
        ingested_at,
        CURRENT_TIMESTAMP AS validated_at
    FROM parsed_data
    WHERE row_num = 1  -- Deduplication: keep most recent
        AND sku IS NOT NULL
        AND name IS NOT NULL
        AND price >= 0
)

SELECT * FROM validated_data
