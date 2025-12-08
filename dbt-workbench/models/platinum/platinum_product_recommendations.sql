{{
    config(
        materialized='view',
        schema='platinum',
        tags=['platinum', 'scout', 'ai-ready', 'recommendations'],
        post_hook=[
            "COMMENT ON VIEW {{ this }} IS 'Product recommendation data for collaborative filtering and ML models'"
        ]
    )
}}

-- Platinum layer: Product recommendation features
-- Purpose: ML models, collaborative filtering, personalization

WITH product_features AS (
    SELECT
        p.id AS product_id,
        p.sku,
        p.name,
        p.category,
        p.brand,
        p.price,
        -- Transaction frequency (last 90 days)
        COUNT(DISTINCT t.id) AS transaction_count,
        COUNT(DISTINCT t.employee_id) AS unique_buyers,
        SUM(t.amount) AS total_revenue,
        AVG(t.amount) AS avg_transaction_value,
        -- Co-purchase analysis (products bought together)
        ARRAY_AGG(DISTINCT t.vendor_id) FILTER (WHERE t.vendor_id IS NOT NULL) AS associated_vendors,
        CURRENT_TIMESTAMP AS calculated_at
    FROM {{ ref('silver_products') }} p
    LEFT JOIN {{ ref('silver_validated_transactions') }} t
        ON t.category = p.category
        AND t.transaction_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY 1, 2, 3, 4, 5, 6
),

similarity_scores AS (
    SELECT
        pf1.product_id,
        pf1.sku,
        pf1.name,
        -- Similar products (same category, similar price range)
        ARRAY_AGG(
            DISTINCT pf2.product_id
            ORDER BY ABS(pf2.price - pf1.price)
        ) FILTER (
            WHERE pf2.product_id != pf1.product_id
            AND pf2.category = pf1.category
            AND pf2.price BETWEEN pf1.price * 0.8 AND pf1.price * 1.2
        ) AS similar_products,
        -- Popularity score
        (pf1.transaction_count::FLOAT / NULLIF(MAX(pf1.transaction_count) OVER (), 0)) AS popularity_score,
        -- Revenue score
        (pf1.total_revenue::FLOAT / NULLIF(MAX(pf1.total_revenue) OVER (), 0)) AS revenue_score,
        pf1.transaction_count,
        pf1.unique_buyers,
        pf1.total_revenue,
        pf1.calculated_at
    FROM product_features pf1
    LEFT JOIN product_features pf2
        ON pf2.category = pf1.category
        AND pf2.product_id != pf1.product_id
    GROUP BY 1, 2, 3, pf1.transaction_count, pf1.unique_buyers, pf1.total_revenue, pf1.calculated_at
)

SELECT
    gen_random_uuid() AS id,
    product_id,
    sku,
    name,
    similar_products[1:5] AS top_5_similar_products,
    ARRAY[
        popularity_score,
        revenue_score,
        (unique_buyers::FLOAT / NULLIF(transaction_count, 0))
    ] AS recommendation_scores,
    popularity_score,
    revenue_score,
    transaction_count,
    unique_buyers,
    total_revenue,
    calculated_at
FROM similarity_scores
WHERE transaction_count > 0

-- Note: In production, this would feed into:
-- 1. Collaborative filtering model (ALS, matrix factorization)
-- 2. Content-based filtering (TF-IDF on product descriptions)
-- 3. Hybrid recommendation system combining both approaches
