{{
    config(
        materialized='table',
        schema='gold',
        tags=['gold', 'scout', 'mart', 'trends'],
        post_hook=[
            "COMMENT ON TABLE {{ this }} IS 'Weekly category trend analysis with statistical measures'",
            "CREATE INDEX IF NOT EXISTS idx_gold_trends_week ON {{ this }} (week DESC)",
            "CREATE INDEX IF NOT EXISTS idx_gold_trends_category ON {{ this }} (category)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_gold_trends_unique ON {{ this }} (week, category)"
        ]
    )
}}

-- Gold layer: Weekly category trends with statistical analysis
-- Business logic: Track spending patterns and anomalies for proactive management

WITH weekly_data AS (
    SELECT
        DATE_TRUNC('week', transaction_date)::DATE AS week,
        category,
        COUNT(*) AS transaction_count,
        SUM(amount) AS total_amount,
        AVG(amount) AS avg_amount,
        STDDEV(amount) AS stddev_amount,
        COUNT(DISTINCT vendor_id) AS unique_vendors
    FROM {{ ref('silver_validated_transactions') }}
    WHERE transaction_date >= CURRENT_DATE - INTERVAL '52 weeks'
    GROUP BY 1, 2
),

trend_analysis AS (
    SELECT
        gen_random_uuid() AS id,
        week,
        category,
        transaction_count,
        total_amount,
        avg_amount,
        stddev_amount,
        unique_vendors,
        -- Week-over-week change
        LAG(total_amount) OVER (PARTITION BY category ORDER BY week) AS prev_week_amount,
        (total_amount - LAG(total_amount) OVER (PARTITION BY category ORDER BY week)) /
            NULLIF(LAG(total_amount) OVER (PARTITION BY category ORDER BY week), 0) * 100 AS wow_pct_change,
        -- 4-week moving average
        AVG(total_amount) OVER (
            PARTITION BY category
            ORDER BY week
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ) AS ma_4week,
        -- Anomaly detection (>2 std deviations from mean)
        CASE
            WHEN ABS(
                total_amount - AVG(total_amount) OVER (PARTITION BY category)
            ) > 2 * STDDEV(total_amount) OVER (PARTITION BY category)
            THEN true
            ELSE false
        END AS is_anomaly,
        CURRENT_TIMESTAMP AS calculated_at
    FROM weekly_data
)

SELECT * FROM trend_analysis
ORDER BY week DESC, category
