-- InsightPulseAI AI Workbench Medallion Schemas
-- Migration 002: Bronze/Silver/Gold/Platinum schemas for Scout domain
-- Run: psql "$SUPABASE_URL" -f 002_medallion_schemas.sql

BEGIN;

-- ============================================================
-- BRONZE SCHEMA (Raw Scout Data)
-- ============================================================

CREATE SCHEMA IF NOT EXISTS bronze;

-- Raw Scout transactions (JSON dumps from Google Drive exports)
CREATE TABLE bronze.scout_transactions_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_file TEXT NOT NULL,
    raw_data JSONB NOT NULL,
    ingested_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_bronze_scout_source ON bronze.scout_transactions_raw(source_file);
CREATE INDEX idx_bronze_scout_ingested ON bronze.scout_transactions_raw(ingested_at DESC);
CREATE INDEX idx_bronze_scout_processed ON bronze.scout_transactions_raw(processed);

-- Raw expense data (OCR outputs)
CREATE TABLE bronze.expenses_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ocr_provider TEXT NOT NULL, -- 'paddleocr-vl', 'google-vision', etc.
    image_url TEXT NOT NULL,
    raw_ocr_output JSONB NOT NULL,
    confidence NUMERIC(5, 4),
    ingested_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_bronze_expenses_provider ON bronze.expenses_raw(ocr_provider);
CREATE INDEX idx_bronze_expenses_confidence ON bronze.expenses_raw(confidence);
CREATE INDEX idx_bronze_expenses_ingested ON bronze.expenses_raw(ingested_at DESC);

-- ============================================================
-- SILVER SCHEMA (Cleaned & Validated)
-- ============================================================

CREATE SCHEMA IF NOT EXISTS silver;

-- Cleaned Scout transactions
CREATE TABLE silver.scout_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id TEXT UNIQUE NOT NULL,
    transaction_date DATE NOT NULL,
    brand TEXT NOT NULL,
    product TEXT NOT NULL,
    category TEXT,
    amount NUMERIC(12, 2) NOT NULL,
    vendor TEXT,
    agency TEXT,
    region TEXT,
    metadata JSONB,
    source_bronze_id UUID REFERENCES bronze.scout_transactions_raw(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_silver_scout_date ON silver.scout_transactions(transaction_date DESC);
CREATE INDEX idx_silver_scout_brand ON silver.scout_transactions(brand);
CREATE INDEX idx_silver_scout_product ON silver.scout_transactions(product);
CREATE INDEX idx_silver_scout_agency ON silver.scout_transactions(agency);

-- Cleaned expense records
CREATE TABLE silver.expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expense_id TEXT UNIQUE NOT NULL,
    expense_date DATE NOT NULL,
    vendor TEXT NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    category TEXT,
    employee TEXT,
    agency TEXT,
    tax_category TEXT, -- BIR tax code
    receipt_url TEXT,
    ocr_confidence NUMERIC(5, 4),
    policy_validated BOOLEAN DEFAULT FALSE,
    source_bronze_id UUID REFERENCES bronze.expenses_raw(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_silver_expenses_date ON silver.expenses(expense_date DESC);
CREATE INDEX idx_silver_expenses_vendor ON silver.expenses(vendor);
CREATE INDEX idx_silver_expenses_category ON silver.expenses(category);
CREATE INDEX idx_silver_expenses_employee ON silver.expenses(employee);

-- ============================================================
-- GOLD SCHEMA (Business Marts)
-- ============================================================

CREATE SCHEMA IF NOT EXISTS gold;

-- Finance expenses aggregated (star schema)
CREATE TABLE gold.finance_expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expense_date DATE NOT NULL,
    vendor TEXT NOT NULL,
    vendor_category TEXT,
    amount NUMERIC(12, 2) NOT NULL,
    tax_amount NUMERIC(12, 2),
    net_amount NUMERIC(12, 2),
    category TEXT,
    agency TEXT,
    employee TEXT,
    department TEXT,
    cost_center TEXT,
    tax_code TEXT, -- BIR code
    approval_status TEXT CHECK (approval_status IN ('pending', 'approved', 'rejected')),
    approved_by TEXT,
    approved_at TIMESTAMP,
    fiscal_year INT,
    fiscal_quarter INT,
    fiscal_month INT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_gold_expenses_date ON gold.finance_expenses(expense_date DESC);
CREATE INDEX idx_gold_expenses_vendor ON gold.finance_expenses(vendor);
CREATE INDEX idx_gold_expenses_agency ON gold.finance_expenses(agency);
CREATE INDEX idx_gold_expenses_fiscal ON gold.finance_expenses(fiscal_year, fiscal_quarter);

-- Scout sales aggregated
CREATE TABLE gold.scout_sales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_date DATE NOT NULL,
    brand TEXT NOT NULL,
    product TEXT NOT NULL,
    category TEXT,
    total_amount NUMERIC(12, 2) NOT NULL,
    quantity INT,
    average_price NUMERIC(12, 2),
    vendor TEXT,
    agency TEXT,
    region TEXT,
    fiscal_year INT,
    fiscal_quarter INT,
    fiscal_month INT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_gold_scout_date ON gold.scout_sales(transaction_date DESC);
CREATE INDEX idx_gold_scout_brand ON gold.scout_sales(brand);
CREATE INDEX idx_gold_scout_product ON gold.scout_sales(product);
CREATE INDEX idx_gold_scout_fiscal ON gold.scout_sales(fiscal_year, fiscal_quarter);

-- ============================================================
-- PLATINUM SCHEMA (Genie/AI Views)
-- ============================================================

CREATE SCHEMA IF NOT EXISTS platinum;

-- Materialized view: Monthly expense summary by agency
CREATE MATERIALIZED VIEW platinum.monthly_expenses_by_agency AS
SELECT
    DATE_TRUNC('month', expense_date) AS month,
    agency,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount,
    MIN(amount) AS min_amount,
    MAX(amount) AS max_amount,
    COUNT(DISTINCT vendor) AS unique_vendors,
    COUNT(DISTINCT employee) AS unique_employees
FROM gold.finance_expenses
GROUP BY DATE_TRUNC('month', expense_date), agency;

CREATE UNIQUE INDEX idx_platinum_monthly_expenses_pk ON platinum.monthly_expenses_by_agency(month, agency);
CREATE INDEX idx_platinum_monthly_expenses_month ON platinum.monthly_expenses_by_agency(month DESC);

-- Materialized view: Scout sales trends
CREATE MATERIALIZED VIEW platinum.scout_sales_trends AS
SELECT
    DATE_TRUNC('month', transaction_date) AS month,
    brand,
    category,
    SUM(total_amount) AS total_sales,
    AVG(total_amount) AS avg_sales,
    SUM(quantity) AS total_quantity,
    COUNT(*) AS transaction_count,
    STDDEV(total_amount) AS sales_volatility
FROM gold.scout_sales
GROUP BY DATE_TRUNC('month', transaction_date), brand, category;

CREATE UNIQUE INDEX idx_platinum_scout_trends_pk ON platinum.scout_sales_trends(month, brand, category);
CREATE INDEX idx_platinum_scout_trends_month ON platinum.scout_sales_trends(month DESC);

-- Refresh functions for materialized views
CREATE OR REPLACE FUNCTION platinum.refresh_all_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY platinum.monthly_expenses_by_agency;
    REFRESH MATERIALIZED VIEW CONCURRENTLY platinum.scout_sales_trends;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- Register tables in ip_workbench catalog
INSERT INTO ip_workbench.tables (schema_name, table_name, description, slo_freshness_hours, slo_completeness_pct)
VALUES
    ('bronze', 'scout_transactions_raw', 'Raw Scout transaction data from Google Drive exports', 24, 95.0),
    ('bronze', 'expenses_raw', 'Raw expense data from OCR processing', 1, 90.0),
    ('silver', 'scout_transactions', 'Cleaned and validated Scout transactions', 2, 98.0),
    ('silver', 'expenses', 'Cleaned and validated expense records', 1, 98.0),
    ('gold', 'finance_expenses', 'Aggregated finance expense mart with BIR tax codes', 4, 99.0),
    ('gold', 'scout_sales', 'Aggregated Scout sales mart', 4, 99.0),
    ('platinum', 'monthly_expenses_by_agency', 'Monthly expense summary by agency (materialized view)', 24, 100.0),
    ('platinum', 'scout_sales_trends', 'Scout sales trends with volatility metrics (materialized view)', 24, 100.0)
ON CONFLICT (schema_name, table_name) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Medallion schemas created successfully!';
    RAISE NOTICE 'Schemas: bronze, silver, gold, platinum';
    RAISE NOTICE 'Tables registered in ip_workbench.tables catalog';
END $$;
