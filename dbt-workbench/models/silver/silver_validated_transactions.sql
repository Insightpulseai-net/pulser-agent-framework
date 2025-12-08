{{
    config(
        materialized='table',
        schema='silver',
        tags=['silver', 'scout', 'validated'],
        post_hook=[
            "COMMENT ON TABLE {{ this }} IS 'Validated and cleaned Scout transactions - Schema enforced, nulls handled, types validated'",
            "CREATE INDEX IF NOT EXISTS idx_silver_transactions_date ON {{ this }} (transaction_date DESC)",
            "CREATE INDEX IF NOT EXISTS idx_silver_transactions_category ON {{ this }} (category)",
            "CREATE INDEX IF NOT EXISTS idx_silver_transactions_vendor ON {{ this }} (vendor_id)",
            "CREATE INDEX IF NOT EXISTS idx_silver_transactions_validated ON {{ this }} (validated_at DESC)"
        ]
    )
}}

-- Silver layer: Validated and cleaned transactions
-- Quality gates: Schema validation, null handling, type enforcement, business rules

WITH source_data AS (
    SELECT
        id AS bronze_id,
        raw_data,
        source,
        ingested_at
    FROM {{ ref('bronze_transactions') }}
    WHERE ingested_at >= CURRENT_DATE - INTERVAL '30 days'
),

parsed_data AS (
    SELECT
        bronze_id,
        source,
        ingested_at,
        -- Parse JSON fields
        (raw_data->>'transaction_id')::TEXT AS transaction_id,
        (raw_data->>'date')::DATE AS transaction_date,
        (raw_data->>'amount')::NUMERIC(15,2) AS amount,
        (raw_data->>'currency')::TEXT AS currency,
        (raw_data->>'category')::TEXT AS category,
        (raw_data->>'subcategory')::TEXT AS subcategory,
        (raw_data->>'vendor_name')::TEXT AS vendor_name,
        (raw_data->>'vendor_id')::TEXT AS vendor_id,
        (raw_data->>'tax_code')::TEXT AS tax_code,
        (raw_data->>'tax_amount')::NUMERIC(15,2) AS tax_amount,
        (raw_data->>'description')::TEXT AS description,
        (raw_data->>'receipt_url')::TEXT AS receipt_url,
        (raw_data->>'payment_method')::TEXT AS payment_method,
        (raw_data->>'employee_id')::TEXT AS employee_id,
        (raw_data->>'cost_center')::TEXT AS cost_center,
        (raw_data->>'project_code')::TEXT AS project_code
    FROM source_data
),

validated_data AS (
    SELECT
        gen_random_uuid() AS id,
        bronze_id,
        transaction_id,
        transaction_date,
        amount,
        COALESCE(currency, 'PHP') AS currency,
        COALESCE(category, 'Uncategorized') AS category,
        subcategory,
        COALESCE(vendor_name, 'Unknown Vendor') AS vendor_name,
        vendor_id,
        tax_code,
        COALESCE(tax_amount, 0) AS tax_amount,
        TRIM(description) AS description,
        receipt_url,
        payment_method,
        employee_id,
        cost_center,
        project_code,
        source,
        ingested_at,
        CURRENT_TIMESTAMP AS validated_at,
        -- Quality flags
        CASE
            WHEN transaction_date IS NULL THEN 'missing_date'
            WHEN amount IS NULL THEN 'missing_amount'
            WHEN amount <= 0 THEN 'invalid_amount'
            WHEN vendor_id IS NULL THEN 'missing_vendor'
            ELSE NULL
        END AS validation_issue
    FROM parsed_data
    WHERE 1=1
        -- Business rule validations
        AND transaction_date IS NOT NULL
        AND transaction_date <= CURRENT_DATE
        AND transaction_date >= CURRENT_DATE - INTERVAL '365 days'
        AND amount IS NOT NULL
        AND amount > 0
        AND amount < 10000000 -- Reasonable upper limit
)

SELECT * FROM validated_data
WHERE validation_issue IS NULL
