# Supabase Core Platform - Task Breakdown

## Document Control
- **Version**: 1.0.0
- **Status**: Active
- **Last Updated**: 2025-12-08
- **Author**: InsightPulseAI Platform Team

---

## Epic Overview

| Epic ID | Epic Name | Phase | Status |
|---------|-----------|-------|--------|
| EPIC-001 | PostgreSQL Foundation | 1 | TODO |
| EPIC-002 | Authentication (GoTrue) | 1 | TODO |
| EPIC-003 | REST API (PostgREST) | 1 | TODO |
| EPIC-004 | Odoo Sync Pipeline | 2 | TODO |
| EPIC-005 | Medallion Transformations | 2 | TODO |
| EPIC-006 | Real-Time Subscriptions | 3 | TODO |
| EPIC-007 | File Storage | 3 | TODO |
| EPIC-008 | Edge Functions | 4 | TODO |
| EPIC-009 | Search & Vectors | 4 | TODO |
| EPIC-010 | Admin Dashboard | 4 | TODO |
| EPIC-011 | Documentation & Training | All | TODO |

---

## Phase 1: Foundation

### EPIC-001: PostgreSQL Foundation

| ID | Title | Type | Scope Notes | Effort | Priority | Status |
|----|-------|------|-------------|--------|----------|--------|
| PG-001 | Provision PostgreSQL 15 container | infra | Docker with persistent volume | S | P0 | TODO |
| PG-002 | Install required extensions | infra | pgvector, pg_cron, pgsodium, postgis | S | P0 | TODO |
| PG-003 | Create Medallion schema structure | schema | bronze, silver, gold schemas | S | P0 | TODO |
| PG-004 | Create public schema for app entities | schema | organizations, memberships, profiles | M | P0 | TODO |
| PG-005 | Create odoo schema for synced data | schema | res_partner, product_product, etc. | M | P0 | TODO |
| PG-006 | Set up pgBouncer connection pooling | infra | Configure pool sizes, timeouts | S | P1 | TODO |
| PG-007 | Configure automatic backups | infra | Hourly dumps + continuous archiving | M | P0 | TODO |
| PG-008 | Set up read replica (optional) | infra | For analytics workloads | L | P2 | TODO |
| PG-009 | Create database monitoring views | schema | pg_stat_* dashboards | S | P1 | TODO |
| PG-010 | Document connection strings | docs | All access patterns | XS | P0 | TODO |

### EPIC-002: Authentication (GoTrue)

| ID | Title | Type | Scope Notes | Effort | Priority | Status |
|----|-------|------|-------------|--------|----------|--------|
| AUTH-001 | Deploy GoTrue container | infra | Configure with PostgreSQL | M | P0 | TODO |
| AUTH-002 | Configure JWT settings | config | Secret, algorithm, expiry | S | P0 | TODO |
| AUTH-003 | Set up email provider | config | SMTP for verification emails | S | P0 | TODO |
| AUTH-004 | Enable Google OAuth | config | OAuth client configuration | S | P0 | TODO |
| AUTH-005 | Enable GitHub OAuth | config | OAuth app setup | S | P1 | TODO |
| AUTH-006 | Enable Azure AD OAuth | config | Enterprise SSO | M | P2 | TODO |
| AUTH-007 | Implement magic link auth | feature | Passwordless option | S | P1 | TODO |
| AUTH-008 | Create auth.users trigger for profiles | schema | Auto-create profile on signup | S | P0 | TODO |
| AUTH-009 | Implement custom JWT claims | feature | Add org_id, role to token | M | P0 | TODO |
| AUTH-010 | Build password reset flow | feature | Email-based reset | S | P0 | TODO |
| AUTH-011 | Implement MFA (TOTP) | feature | Two-factor authentication | M | P1 | TODO |
| AUTH-012 | Create auth documentation | docs | Integration guide | M | P0 | TODO |

### EPIC-003: REST API (PostgREST)

| ID | Title | Type | Scope Notes | Effort | Priority | Status |
|----|-------|------|-------------|--------|----------|--------|
| API-001 | Deploy PostgREST container | infra | Connect to pgBouncer | S | P0 | TODO |
| API-002 | Configure schema exposure | config | public, odoo, gold schemas | S | P0 | TODO |
| API-003 | Set up OpenAPI generation | config | Auto-generate docs | S | P1 | TODO |
| API-004 | Deploy Kong API gateway | infra | Rate limiting, auth forwarding | M | P0 | TODO |
| API-005 | Configure CORS policies | config | Allow app origins | S | P0 | TODO |
| API-006 | Implement rate limiting | config | Per-user limits | S | P0 | TODO |
| API-007 | Create RLS policy for organizations | schema | Tenant isolation | M | P0 | TODO |
| API-008 | Create RLS policy for memberships | schema | User-org access | M | P0 | TODO |
| API-009 | Create RLS policy for odoo schema | schema | Tenant-aware sync data | M | P0 | TODO |
| API-010 | Build bulk insert endpoints | feature | Batch operations | M | P1 | TODO |
| API-011 | Create API usage tracking | feature | Request logging | M | P1 | TODO |
| API-012 | Document API endpoints | docs | Full reference | L | P0 | TODO |

---

## Phase 2: Odoo Integration

### EPIC-004: Odoo Sync Pipeline

| ID | Title | Type | Scope Notes | Effort | Priority | Status |
|----|-------|------|-------------|--------|----------|--------|
| SYNC-001 | Create bronze.raw_odoo_partners table | schema | Raw Odoo partner data | S | P0 | TODO |
| SYNC-002 | Create bronze.raw_odoo_products table | schema | Raw Odoo product data | S | P0 | TODO |
| SYNC-003 | Create bronze.raw_odoo_invoices table | schema | Raw Odoo invoice data | S | P0 | TODO |
| SYNC-004 | Create odoo.res_partner view | schema | Clean partner reference | S | P0 | TODO |
| SYNC-005 | Create odoo.product_product view | schema | Clean product reference | S | P0 | TODO |
| SYNC-006 | Build n8n workflow: partner sync | workflow | Scheduled + webhook | M | P0 | TODO |
| SYNC-007 | Build n8n workflow: product sync | workflow | Scheduled sync | M | P0 | TODO |
| SYNC-008 | Build n8n workflow: invoice sync | workflow | Real-time webhook | M | P0 | TODO |
| SYNC-009 | Implement webhook receiver | api | Handle Odoo notifications | M | P0 | TODO |
| SYNC-010 | Create sync status table | schema | Track last sync, errors | S | P0 | TODO |
| SYNC-011 | Build conflict resolution logic | feature | Odoo wins strategy | M | P1 | TODO |
| SYNC-012 | Create sync monitoring dashboard | feature | Latency, errors | M | P1 | TODO |

### EPIC-005: Medallion Transformations

| ID | Title | Type | Scope Notes | Effort | Priority | Status |
|----|-------|------|-------------|--------|----------|--------|
| MED-001 | Create silver.partners transform | transform | Clean, dedupe, validate | M | P0 | TODO |
| MED-002 | Create silver.products transform | transform | Standardize, enrich | M | P0 | TODO |
| MED-003 | Create silver.invoices transform | transform | Normalize, type | M | P0 | TODO |
| MED-004 | Create gold.dim_partner | transform | SCD Type 2 | M | P1 | TODO |
| MED-005 | Create gold.dim_product | transform | Product dimension | M | P1 | TODO |
| MED-006 | Create gold.fact_invoice | transform | Invoice fact table | M | P1 | TODO |
| MED-007 | Create gold.agg_revenue_daily | transform | Daily revenue aggregate | S | P1 | TODO |
| MED-008 | Set up pg_cron for transforms | config | Scheduled refresh | S | P0 | TODO |
| MED-009 | Build data quality checks | feature | Validation rules | M | P1 | TODO |
| MED-010 | Create lineage tracking | feature | Source → target mapping | M | P2 | TODO |

---

## Phase 3: Real-Time & Storage

### EPIC-006: Real-Time Subscriptions

| ID | Title | Type | Scope Notes | Effort | Priority | Status |
|----|-------|------|-------------|--------|----------|--------|
| RT-001 | Deploy Realtime server | infra | WebSocket service | M | P0 | TODO |
| RT-002 | Configure PostgreSQL NOTIFY | config | Publication setup | S | P0 | TODO |
| RT-003 | Implement RLS-aware filtering | feature | Security enforcement | M | P0 | TODO |
| RT-004 | Build reconnection handling | feature | Auto-resubscribe | M | P0 | TODO |
| RT-005 | Create broadcast channels | feature | Non-DB messages | M | P1 | TODO |
| RT-006 | Implement presence tracking | feature | Online users | M | P2 | TODO |
| RT-007 | Load test 10K connections | test | Performance validation | M | P0 | TODO |
| RT-008 | Create realtime JS client | sdk | TypeScript wrapper | M | P0 | TODO |
| RT-009 | Document realtime patterns | docs | Best practices | M | P1 | TODO |

### EPIC-007: File Storage

| ID | Title | Type | Scope Notes | Effort | Priority | Status |
|----|-------|------|-------------|--------|----------|--------|
| STR-001 | Deploy MinIO for S3 backend | infra | Object storage | M | P0 | TODO |
| STR-002 | Deploy Storage API service | infra | File management | M | P0 | TODO |
| STR-003 | Create storage.buckets table | schema | Bucket metadata | S | P0 | TODO |
| STR-004 | Create storage.objects table | schema | File metadata | S | P0 | TODO |
| STR-005 | Implement signed URL generation | feature | Pre-signed access | M | P0 | TODO |
| STR-006 | Create RLS policies for storage | schema | Bucket-level security | M | P0 | TODO |
| STR-007 | Build image transformation | feature | Resize, crop | M | P2 | TODO |
| STR-008 | Integrate with Odoo attachments | feature | Sync ir.attachment | M | P1 | TODO |
| STR-009 | Create storage client SDK | sdk | Upload/download helpers | M | P0 | TODO |

---

## Phase 4: Advanced Features

### EPIC-008: Edge Functions

| ID | Title | Type | Scope Notes | Effort | Priority | Status |
|----|-------|------|-------------|--------|----------|--------|
| FN-001 | Deploy Deno runtime | infra | Edge function executor | M | P1 | TODO |
| FN-002 | Build function deployment pipeline | ci | Git push → deploy | M | P1 | TODO |
| FN-003 | Implement database triggers | feature | DB event → function | M | P1 | TODO |
| FN-004 | Create HTTP invocation | feature | API endpoint per function | S | P1 | TODO |
| FN-005 | Implement scheduled functions | feature | Cron-based execution | M | P2 | TODO |
| FN-006 | Build function logging | feature | Structured logs | M | P1 | TODO |
| FN-007 | Create function templates | docs | Starter examples | M | P1 | TODO |

### EPIC-009: Search & Vectors

| ID | Title | Type | Scope Notes | Effort | Priority | Status |
|----|-------|------|-------------|--------|----------|--------|
| SRCH-001 | Enable pg_trgm for fuzzy search | config | Trigram matching | S | P1 | TODO |
| SRCH-002 | Create full-text search indexes | schema | tsvector columns | M | P1 | TODO |
| SRCH-003 | Build search API endpoint | api | Unified search | M | P1 | TODO |
| SRCH-004 | Enable pgvector extension | config | Vector storage | S | P2 | TODO |
| SRCH-005 | Create embeddings table | schema | Vector storage | S | P2 | TODO |
| SRCH-006 | Build vector search API | api | Similarity search | M | P2 | TODO |
| SRCH-007 | Integrate with RAG pipeline | feature | Agent support | L | P2 | TODO |

### EPIC-010: Admin Dashboard

| ID | Title | Type | Scope Notes | Effort | Priority | Status |
|----|-------|------|-------------|--------|----------|--------|
| ADMIN-001 | Deploy Supabase Studio | infra | Admin web UI | M | P1 | TODO |
| ADMIN-002 | Configure auth for Studio | config | Admin-only access | S | P1 | TODO |
| ADMIN-003 | Build table editor views | feature | Schema browser | M | P1 | TODO |
| ADMIN-004 | Create SQL editor | feature | Direct query | M | P1 | TODO |
| ADMIN-005 | Build user management UI | feature | Auth user admin | M | P1 | TODO |
| ADMIN-006 | Create storage browser | feature | File management | M | P2 | TODO |

### EPIC-011: Documentation & Training

| ID | Title | Type | Scope Notes | Effort | Priority | Status |
|----|-------|------|-------------|--------|----------|--------|
| DOC-001 | Write architecture overview | docs | System design | M | P0 | TODO |
| DOC-002 | Create quickstart guide | docs | 5-minute setup | M | P0 | TODO |
| DOC-003 | Document auth integration | docs | SDK examples | M | P0 | TODO |
| DOC-004 | Document Odoo sync | docs | Configuration guide | M | P0 | TODO |
| DOC-005 | Create RLS best practices | docs | Security patterns | M | P1 | TODO |
| DOC-006 | Build video tutorials | docs | Walkthrough videos | L | P2 | TODO |

---

## UAT Scenarios

| ID | Scenario | Epic | Priority | Status |
|----|----------|------|----------|--------|
| UAT-001 | User can sign up with email | EPIC-002 | P0 | TODO |
| UAT-002 | User can login with Google OAuth | EPIC-002 | P0 | TODO |
| UAT-003 | RLS prevents cross-tenant data access | EPIC-003 | P0 | TODO |
| UAT-004 | Odoo partners sync within 5 minutes | EPIC-004 | P0 | TODO |
| UAT-005 | Realtime subscription receives updates | EPIC-006 | P0 | TODO |
| UAT-006 | File upload and signed URL work | EPIC-007 | P0 | TODO |
| UAT-007 | Edge function executes on DB trigger | EPIC-008 | P1 | TODO |
| UAT-008 | Full-text search returns results | EPIC-009 | P1 | TODO |

---

## Go-Live Checklist

### Pre-Production

| Item | Category | Owner | Status |
|------|----------|-------|--------|
| TLS certificates configured | Security | DevOps | TODO |
| All secrets in .env (not git) | Security | DevOps | TODO |
| RLS policies on all tables | Security | Backend | TODO |
| Backup tested with restore | Operations | DevOps | TODO |
| Rate limiting enabled | Security | DevOps | TODO |
| Monitoring dashboards ready | Operations | DevOps | TODO |
| Documentation published | Documentation | Team | TODO |
| Load testing completed | Performance | QA | TODO |

### Post-Go-Live

| Item | Category | Timeline | Status |
|------|----------|----------|--------|
| Monitor error rates 24h | Operations | Day 1 | TODO |
| Verify Odoo sync accuracy | Data | Day 1 | TODO |
| Collect developer feedback | Product | Week 1 | TODO |
| Performance review | Engineering | Week 1 | TODO |
