{{
    config(
        materialized='table',
        schema='gold',
        tags=['gold', 'scout', 'mart', 'monthly'],
        post_hook=[
            "COMMENT ON TABLE {{ this }} IS 'Monthly transaction summary by category - Business intelligence mart'",
            "CREATE INDEX IF NOT EXISTS idx_gold_monthly_month ON {{ this }} (month DESC)",
            "CREATE INDEX IF NOT EXISTS idx_gold_monthly_category ON {{ this }} (category)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_gold_monthly_unique ON {{ this }} (month, category)"
        ]
    )
}}

-- Gold layer: Monthly summary aggregation
-- Business logic: Aggregated by month and category for executive reporting

WITH monthly_aggregates AS (
    SELECT
        DATE_TRUNC('month', transaction_date)::DATE AS month,
        category,
        COUNT(*) AS transaction_count,
        COUNT(DISTINCT vendor_id) AS unique_vendors,
        SUM(amount) AS total_amount,
        AVG(amount) AS avg_amount,
        MIN(amount) AS min_amount,
        MAX(amount) AS max_amount,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) AS median_amount,
        SUM(tax_amount) AS total_tax,
        COUNT(DISTINCT employee_id) AS unique_employees,
        COUNT(DISTINCT cost_center) AS unique_cost_centers
    FROM {{ ref('silver_validated_transactions') }}
    WHERE transaction_date >= CURRENT_DATE - INTERVAL '24 months'
    GROUP BY 1, 2
),

enriched_summary AS (
    SELECT
        gen_random_uuid() AS id,
        month,
        category,
        transaction_count,
        unique_vendors,
        total_amount,
        avg_amount,
        min_amount,
        max_amount,
        median_amount,
        total_tax,
        unique_employees,
        unique_cost_centers,
        -- Month-over-month growth
        LAG(total_amount) OVER (PARTITION BY category ORDER BY month) AS prev_month_amount,
        (total_amount - LAG(total_amount) OVER (PARTITION BY category ORDER BY month)) /
            NULLIF(LAG(total_amount) OVER (PARTITION BY category ORDER BY month), 0) * 100 AS mom_growth_pct,
        -- Year-over-year growth
        LAG(total_amount, 12) OVER (PARTITION BY category ORDER BY month) AS prev_year_amount,
        (total_amount - LAG(total_amount, 12) OVER (PARTITION BY category ORDER BY month)) /
            NULLIF(LAG(total_amount, 12) OVER (PARTITION BY category ORDER BY month), 0) * 100 AS yoy_growth_pct,
        CURRENT_TIMESTAMP AS calculated_at
    FROM monthly_aggregates
)

SELECT * FROM enriched_summary
ORDER BY month DESC, category
