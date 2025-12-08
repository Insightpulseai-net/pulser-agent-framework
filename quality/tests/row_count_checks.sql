-- Row Count Validation Tests
-- Ensures all layers have expected data volumes

-- Test 1: Bronze layer has data from last 24 hours
SELECT
    'bronze_transactions_daily_volume' AS test_name,
    COUNT(*) AS actual_count,
    CASE
        WHEN COUNT(*) > 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM scout.bronze_transactions
WHERE ingested_at >= CURRENT_DATE - INTERVAL '1 day';

-- Test 2: Silver layer has at least 80% of Bronze volume
WITH bronze_count AS (
    SELECT COUNT(*) AS bronze_rows
    FROM scout.bronze_transactions
    WHERE ingested_at >= CURRENT_DATE - INTERVAL '1 day'
),
silver_count AS (
    SELECT COUNT(*) AS silver_rows
    FROM scout.silver_validated_transactions
    WHERE validated_at >= CURRENT_DATE - INTERVAL '1 day'
)
SELECT
    'silver_bronze_ratio' AS test_name,
    s.silver_rows AS actual_count,
    b.bronze_rows * 0.8 AS expected_minimum,
    CASE
        WHEN s.silver_rows >= b.bronze_rows * 0.8 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM bronze_count b, silver_count s;

-- Test 3: Gold monthly summary exists for current month
SELECT
    'gold_current_month_exists' AS test_name,
    COUNT(*) AS actual_count,
    CASE
        WHEN COUNT(*) > 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM scout.gold_monthly_summary
WHERE month = DATE_TRUNC('month', CURRENT_DATE);

-- Test 4: No orphaned Silver records (all have Bronze source)
WITH orphaned AS (
    SELECT s.id
    FROM scout.silver_validated_transactions s
    LEFT JOIN scout.bronze_transactions b ON b.id = s.bronze_id
    WHERE b.id IS NULL
    AND s.validated_at >= CURRENT_DATE - INTERVAL '1 day'
)
SELECT
    'silver_no_orphans' AS test_name,
    COUNT(*) AS orphan_count,
    CASE
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM orphaned;
