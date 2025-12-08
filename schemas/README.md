# Data Layer Schema Documentation

Complete documentation of the Medallion architecture (Bronze → Silver → Gold → Platinum) for Scout Retail domain.

## Schema Layers

### Bronze Layer (Raw Ingestion)
- **Purpose**: Unvalidated raw data from all sources
- **Format**: JSONB blobs with metadata
- **Retention**: 30-90 days
- **Documentation**: [bronze_schema.md](./bronze_schema.md)

### Silver Layer (Validated & Cleaned)
- **Purpose**: Schema-enforced, validated, deduplicated data
- **Format**: Structured relational tables
- **Retention**: 2 years
- **Documentation**: [silver_schema.md](./silver_schema.md)

### Gold Layer (Business Marts)
- **Purpose**: Pre-aggregated analytics tables
- **Format**: Star schema denormalized
- **Retention**: 5 years
- **Documentation**: [gold_schema.md](./gold_schema.md)

### Platinum Layer (AI-Ready)
- **Purpose**: Embeddings and ML features
- **Format**: Views with vector columns
- **Retention**: 90 days (regenerated)
- **Documentation**: [platinum_schema.md](./platinum_schema.md)

## Entity Relationships

See [entity_relationships.md](./entity_relationships.md) for ER diagrams and foreign key relationships.

## Data Quality Standards

| Layer | Completeness | Uniqueness | Timeliness | Consistency |
|-------|--------------|------------|------------|-------------|
| Bronze | ≥99% | N/A | <5 min | N/A |
| Silver | ≥95% | 100% | <1 hour | ≥95% |
| Gold | 100% | 100% | <6 hours | 100% |
| Platinum | 100% | 100% | On-demand | 100% |

## Quick Reference

### Connection Details
```bash
# Supabase Pooler (recommended for dbt/Airflow)
Host: aws-1-us-east-1.pooler.supabase.com
Port: 6543
Database: postgres
User: postgres.xkxyvboeubffxxbebsll
SSL: required

# Direct Connection (for admin operations)
Port: 5432
```

### Schema Sizes (Estimated)

| Schema | Tables | Columns | Rows | Size |
|--------|--------|---------|------|------|
| bronze | 2 | 14 | 1M+ | 5GB |
| silver | 2 | 35 | 800K | 3GB |
| gold | 2 | 28 | 50K | 500MB |
| platinum | 2 | 15 | 10K | 2GB (vectors) |

### Access Patterns

**Read-Heavy**:
- Gold layer (BI dashboards)
- Platinum layer (LLM context)

**Write-Heavy**:
- Bronze layer (real-time ingestion)

**Balanced**:
- Silver layer (hourly refresh)
