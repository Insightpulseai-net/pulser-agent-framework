-- Null Rate Validation Tests
-- Ensures critical fields have acceptable null rates

-- Test 1: Silver transactions - critical fields null rate < 5%
WITH null_stats AS (
    SELECT
        COUNT(*) AS total_rows,
        SUM(CASE WHEN transaction_date IS NULL THEN 1 ELSE 0 END) AS null_date,
        SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) AS null_amount,
        SUM(CASE WHEN category IS NULL THEN 1 ELSE 0 END) AS null_category,
        SUM(CASE WHEN vendor_name IS NULL THEN 1 ELSE 0 END) AS null_vendor
    FROM scout.silver_validated_transactions
    WHERE validated_at >= CURRENT_DATE - INTERVAL '1 day'
)
SELECT
    'silver_null_rate' AS test_name,
    null_date::FLOAT / NULLIF(total_rows, 0) * 100 AS date_null_pct,
    null_amount::FLOAT / NULLIF(total_rows, 0) * 100 AS amount_null_pct,
    null_category::FLOAT / NULLIF(total_rows, 0) * 100 AS category_null_pct,
    null_vendor::FLOAT / NULLIF(total_rows, 0) * 100 AS vendor_null_pct,
    CASE
        WHEN (null_date + null_amount + null_category + null_vendor)::FLOAT / NULLIF(total_rows, 0) * 100 < 5
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM null_stats;

-- Test 2: Gold monthly summary - no nulls allowed
SELECT
    'gold_no_nulls' AS test_name,
    COUNT(*) AS null_count,
    CASE
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM scout.gold_monthly_summary
WHERE month IS NULL
   OR category IS NULL
   OR total_amount IS NULL
   OR transaction_count IS NULL;
