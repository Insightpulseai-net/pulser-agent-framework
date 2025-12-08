# Bronze Layer Schema Documentation

## Overview

The Bronze layer stores raw, unprocessed data ingested from various sources. No validation or transformation is applied at this stage - data is stored as-is in JSONB format for maximum flexibility.

## Tables

### `bronze.bronze_transactions`

**Purpose**: Raw Scout transaction data from multiple sources

**Ingestion Sources**:
- Google Drive exports (daily batch)
- CSV uploads (manual via UI)
- Real-time webhooks (POS systems, mobile apps)

**Schema**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK, NOT NULL | Unique Bronze record identifier |
| `raw_data` | jsonb | NOT NULL | Complete transaction payload |
| `source` | text | NOT NULL | Source system identifier |
| `source_filename` | text | | Original filename or webhook URL |
| `ingested_at` | timestamptz | NOT NULL, DEFAULT NOW() | Ingestion timestamp |
| `ingestion_batch_id` | text | | Batch identifier for tracking |
| `created_at` | timestamptz | DEFAULT NOW() | Record creation timestamp |

**Indexes**:
- `idx_bronze_transactions_ingested` on `ingested_at DESC`
- `idx_bronze_transactions_source` on `source`

**raw_data Structure** (example):
```json
{
  "transaction_id": "TXN-2025-001",
  "date": "2025-12-08",
  "amount": 1500.00,
  "currency": "PHP",
  "category": "Travel",
  "subcategory": "Ground Transport",
  "vendor_name": "Grab Philippines",
  "vendor_id": "VENDOR-123",
  "tax_code": "VAT-12",
  "tax_amount": 180.00,
  "description": "Airport pickup - client meeting",
  "receipt_url": "https://storage.supabase.co/receipts/txn-001.pdf",
  "payment_method": "Corporate Card",
  "employee_id": "EMP-456",
  "cost_center": "CC-789",
  "project_code": "PRJ-2025-Q4"
}
```

**Retention**: 30 days (configurable)

**Quality Metrics**:
- Null rate: <1% (raw_data must not be null)
- Ingestion lag: <5 minutes for real-time sources
- Batch completeness: 100% of source files processed

---

### `bronze.bronze_products`

**Purpose**: Raw Scout product catalog data

**Ingestion Sources**:
- Product master data exports
- Inventory system feeds
- E-commerce platform APIs

**Schema**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK, NOT NULL | Unique Bronze record identifier |
| `raw_data` | jsonb | NOT NULL | Complete product payload |
| `source` | text | NOT NULL | Source system identifier |
| `source_filename` | text | | Original filename |
| `ingested_at` | timestamptz | NOT NULL | Ingestion timestamp |
| `ingestion_batch_id` | text | | Batch identifier |
| `created_at` | timestamptz | DEFAULT NOW() | Record creation |

**Indexes**:
- `idx_bronze_products_ingested` on `ingested_at DESC`
- `idx_bronze_products_source` on `source`

**raw_data Structure** (example):
```json
{
  "sku": "SKU-ABC-123",
  "name": "Office Chair Executive",
  "description": "Ergonomic executive office chair with lumbar support",
  "category": "Office Furniture",
  "brand": "Steelcase",
  "price": 25000.00,
  "cost": 18000.00,
  "stock_quantity": 45,
  "unit_of_measure": "EA",
  "barcode": "1234567890123",
  "is_active": true
}
```

**Retention**: 90 days

---

## Data Lineage

```
External Sources → Bronze Tables → Silver Validation → Gold Aggregation → Platinum AI Features
```

**Bronze Dependencies**:
- **Upstream**: External systems (Google Drive, CSV, webhooks)
- **Downstream**: Silver layer models (`silver_validated_transactions`, `silver_products`)

---

## Ingestion Patterns

### Daily Batch (Airflow)

```python
# scout_ingestion_dag.py
fetch_google_drive → fetch_csv → validate → trigger_dbt_bronze
```

Schedule: Daily at 2 AM UTC

### Real-Time (n8n)

```
Webhook Event → Insert Bronze → Validate → Trigger dbt Silver
```

Trigger: HTTP POST to `/webhook/scout-transactions`

---

## Monitoring

### Key Metrics

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Ingestion lag | <5 min | Mattermost |
| Null raw_data | 0 rows | Email + Mattermost |
| Batch completeness | 100% | Mattermost |
| Row count growth | >0 daily | Email if 0 |

### Health Checks

```sql
-- Check recent ingestion
SELECT
    source,
    COUNT(*) AS row_count,
    MAX(ingested_at) AS last_ingestion
FROM bronze.bronze_transactions
WHERE ingested_at >= NOW() - INTERVAL '1 hour'
GROUP BY source;

-- Check for null raw_data
SELECT COUNT(*)
FROM bronze.bronze_transactions
WHERE raw_data IS NULL;
```

---

## Troubleshooting

### No data ingested

**Symptom**: `row_count = 0` for recent batches

**Causes**:
- Airflow DAG not running
- Google Drive API rate limit
- CSV staging directory empty

**Resolution**:
```bash
# Check Airflow DAG status
airflow dags list-runs -d scout_ingestion

# Verify Google Drive connection
python scripts/test_gdrive_connection.py

# Check CSV staging
ls -la /opt/airflow/staging/csv/
```

### Duplicate records

**Symptom**: Same transaction_id appears multiple times

**Causes**:
- Multiple sources sending same data
- Retry logic creating duplicates

**Resolution**:
```sql
-- Identify duplicates
SELECT
    raw_data->>'transaction_id' AS transaction_id,
    COUNT(*) AS duplicate_count
FROM bronze.bronze_transactions
GROUP BY raw_data->>'transaction_id'
HAVING COUNT(*) > 1;

-- Deduplicate in Silver layer (handled by ROW_NUMBER)
```

---

## References

- [AI Workbench PRD - Section 5](../../spec/ai-workbench/prd.md#section-5-data-model--api-contracts)
- [Airflow DAG: scout_ingestion_dag.py](../../airflow/dags/scout_ingestion_dag.py)
- [n8n Workflow: real-time-transactions.json](../../n8n-etl/workflows/real-time-transactions.json)
