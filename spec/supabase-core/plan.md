# Supabase Core Platform - Implementation Plan

## Document Control
- **Version**: 1.0.0
- **Status**: Draft
- **Last Updated**: 2025-12-08
- **Author**: InsightPulseAI Platform Team

---

## 1. Target Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPABASE CORE PLATFORM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          EDGE LAYER                                  │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │   │  nginx   │  │ Kong API │  │Supabase  │  │  Deno    │          │   │
│  │   │  Proxy   │  │ Gateway  │  │  Studio  │  │Functions │          │   │
│  │   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │   │
│  │        │             │             │             │                 │   │
│  └────────┼─────────────┼─────────────┼─────────────┼─────────────────┘   │
│           │             │             │             │                      │
│  ┌────────┼─────────────┼─────────────┼─────────────┼─────────────────┐   │
│  │        ▼             ▼             ▼             ▼                 │   │
│  │                       API LAYER                                     │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │   │PostgREST │  │ GoTrue   │  │ Realtime │  │ Storage  │          │   │
│  │   │  (REST)  │  │  (Auth)  │  │  Server  │  │   API    │          │   │
│  │   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │   │
│  │        │             │             │             │                 │   │
│  └────────┼─────────────┼─────────────┼─────────────┼─────────────────┘   │
│           │             │             │             │                      │
│  ┌────────┼─────────────┼─────────────┼─────────────┼─────────────────┐   │
│  │        ▼             ▼             ▼             ▼                 │   │
│  │                      DATA LAYER                                     │   │
│  │   ┌─────────────────────────────────────────────────────────────┐  │   │
│  │   │                    PostgreSQL 15+                            │  │   │
│  │   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │  │   │
│  │   │  │  auth   │  │ public  │  │  odoo   │  │ storage │        │  │   │
│  │   │  │ schema  │  │ schema  │  │ schema  │  │ schema  │        │  │   │
│  │   │  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │  │   │
│  │   │  ┌─────────┐  ┌─────────┐  ┌─────────┐                      │  │   │
│  │   │  │ bronze  │  │ silver  │  │  gold   │  (Medallion)        │  │   │
│  │   │  │ schema  │  │ schema  │  │ schema  │                      │  │   │
│  │   │  └─────────┘  └─────────┘  └─────────┘                      │  │   │
│  │   └─────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐                        │   │
│  │   │pgBouncer │  │  Redis   │  │  MinIO   │                        │   │
│  │   │ (Pool)   │  │ (Cache)  │  │(Storage) │                        │   │
│  │   └──────────┘  └──────────┘  └──────────┘                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
            │   Odoo 18     │ │     n8n       │ │  Workbench    │
            │   (ERP)       │ │ (Automation)  │ │   (Data)      │
            └───────────────┘ └───────────────┘ └───────────────┘
```

### 1.2 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA FLOW (MEDALLION)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SOURCES                    BRONZE                      SILVER              │
│  ═══════                    ══════                      ══════              │
│                                                                             │
│  ┌─────────────┐     ┌─────────────────────┐     ┌─────────────────────┐   │
│  │ Odoo CE/18  │────▶│ bronze.raw_partners │────▶│ silver.partners     │   │
│  │             │     │ bronze.raw_products │────▶│ silver.products     │   │
│  │             │     │ bronze.raw_invoices │────▶│ silver.invoices     │   │
│  └─────────────┘     └─────────────────────┘     └──────────┬──────────┘   │
│                                                              │              │
│  ┌─────────────┐     ┌─────────────────────┐                │              │
│  │   Webhooks  │────▶│ bronze.raw_events   │────────────────┤              │
│  │             │     │                     │                │              │
│  └─────────────┘     └─────────────────────┘                │              │
│                                                              │              │
│  ┌─────────────┐     ┌─────────────────────┐                │              │
│  │ File Uploads│────▶│ bronze.raw_documents│────────────────┤              │
│  │             │     │                     │                │              │
│  └─────────────┘     └─────────────────────┘                │              │
│                                                              │              │
│                                                              ▼              │
│                                                 ┌─────────────────────┐    │
│                           GOLD                  │   gold.dim_partner  │    │
│                           ════                  │   gold.dim_product  │    │
│                                                 │   gold.fact_invoice │    │
│                                                 │   gold.agg_revenue  │    │
│                                                 └─────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Database | PostgreSQL | 15+ | Primary data store |
| Extensions | pgvector, pg_cron, pgsodium | Latest | Vector search, scheduling, encryption |
| API Gateway | Kong | 3.x | Rate limiting, auth forwarding |
| REST API | PostgREST | 12.x | Auto-generated REST |
| Auth | GoTrue | 2.x | Authentication service |
| Realtime | Supabase Realtime | Latest | WebSocket subscriptions |
| Storage | Supabase Storage | Latest | S3-compatible |
| Functions | Deno Deploy | Latest | Edge functions |
| Pooling | pgBouncer | 1.21+ | Connection pooling |
| Cache | Redis | 7.x | Session cache |
| Object Storage | MinIO | Latest | S3-compatible backend |
| Proxy | nginx | 1.24+ | TLS termination |

---

## 2. Component Design

### 2.1 PostgreSQL Schema Design

```sql
-- Schema Organization
CREATE SCHEMA IF NOT EXISTS auth;      -- Supabase Auth (managed)
CREATE SCHEMA IF NOT EXISTS public;    -- App-owned entities
CREATE SCHEMA IF NOT EXISTS odoo;      -- Synced Odoo entities
CREATE SCHEMA IF NOT EXISTS bronze;    -- Raw ingestion
CREATE SCHEMA IF NOT EXISTS silver;    -- Cleaned data
CREATE SCHEMA IF NOT EXISTS gold;      -- Business-ready
CREATE SCHEMA IF NOT EXISTS storage;   -- File metadata

-- Enable Row Level Security
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;

-- Multi-tenant RLS Pattern
CREATE TABLE public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES public.organizations(id),
    user_id UUID REFERENCES auth.users(id),
    role TEXT DEFAULT 'member',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id, user_id)
);

-- RLS Policy Example
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "org_member_access" ON public.organizations
    USING (
        id IN (
            SELECT org_id FROM public.memberships
            WHERE user_id = auth.uid()
        )
    );
```

### 2.2 Authentication Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AUTHENTICATION FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │  Client  │────▶│   GoTrue     │────▶│  PostgreSQL  │        │
│  │   App    │     │   (Auth)     │     │  auth.users  │        │
│  └──────────┘     └──────┬───────┘     └──────────────┘        │
│       │                  │                                      │
│       │                  ▼                                      │
│       │          ┌──────────────┐                              │
│       │          │  JWT Token   │                              │
│       │          │  ┌────────┐  │                              │
│       │          │  │ sub    │──│──▶ User ID                   │
│       │          │  │ role   │──│──▶ authenticated/anon        │
│       │          │  │ org_id │──│──▶ Tenant context            │
│       │          │  │ claims │──│──▶ Custom attributes         │
│       │          │  └────────┘  │                              │
│       │          └──────┬───────┘                              │
│       │                 │                                       │
│       ▼                 ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    PostgREST / Realtime                   │  │
│  │  request.jwt.claims -> current_setting('request.jwt...')  │  │
│  │  RLS policies use: auth.uid(), auth.jwt()->>'org_id'      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Odoo Sync Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       ODOO SYNC FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ODOO CE/OCA 18                    SUPABASE                    │
│                                                                 │
│  ┌──────────────┐                                              │
│  │ res.partner  │──────┐                                       │
│  │ product.prod │──────┤                                       │
│  │ account.move │──────┤    n8n Workflow                       │
│  └──────────────┘      │    ┌──────────────────────────┐       │
│        │               └───▶│  1. Poll/Webhook         │       │
│        │ (Webhook)          │  2. Extract raw data     │       │
│        ▼                    │  3. Insert to bronze     │       │
│  ┌──────────────┐          │  4. Trigger transform    │       │
│  │  ir.cron     │──────────▶│                          │       │
│  │  (Schedule)  │           └──────────────┬───────────┘       │
│  └──────────────┘                          │                   │
│                                            ▼                   │
│                              ┌──────────────────────────┐      │
│                              │ bronze.raw_odoo_partners │      │
│                              │ bronze.raw_odoo_products │      │
│                              │ bronze.raw_odoo_invoices │      │
│                              └──────────────┬───────────┘      │
│                                             │                  │
│                              dbt / SQL Transform               │
│                                             │                  │
│                                             ▼                  │
│                              ┌──────────────────────────┐      │
│                              │ silver.partners          │      │
│                              │ silver.products          │      │
│                              │ silver.invoices          │      │
│                              └──────────────┬───────────┘      │
│                                             │                  │
│                              Aggregate / Materialize           │
│                                             │                  │
│                                             ▼                  │
│                              ┌──────────────────────────┐      │
│                              │ gold.dim_partner         │      │
│                              │ gold.fact_invoice        │      │
│                              │ gold.agg_revenue_daily   │      │
│                              └──────────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation Phases

### Phase 1: Foundation (4 weeks)

```
Week 1: PostgreSQL Setup
├── Deploy PostgreSQL 15 container
├── Install extensions (pgvector, pg_cron, pgsodium)
├── Create Medallion schemas (bronze/silver/gold)
├── Set up pgBouncer for connection pooling
└── Configure backups (hourly + PITR)

Week 2: Auth Integration
├── Deploy GoTrue container
├── Configure JWT settings
├── Set up OAuth providers (Google, GitHub)
├── Create auth.users triggers
└── Implement basic RLS policies

Week 3: API Layer
├── Deploy PostgREST container
├── Configure OpenAPI generation
├── Set up Kong API gateway
├── Implement rate limiting
└── Create API documentation

Week 4: Testing & Hardening
├── End-to-end auth testing
├── API performance testing
├── Security audit
├── Documentation
└── Staging deployment
```

**Deliverables**:
- Working PostgreSQL with Medallion schemas
- GoTrue authentication
- PostgREST API with RLS
- Basic admin dashboard

---

### Phase 2: Odoo Integration (3 weeks)

```
Week 5: Core Sync
├── Create bronze schema tables for Odoo models
├── Build n8n workflow for res.partner sync
├── Build n8n workflow for product.product sync
├── Implement webhook handler for real-time updates
└── Create silver transformation functions

Week 6: Financial Data
├── Build account.move sync workflow
├── Create invoice line items sync
├── Implement payment sync
├── Build reconciliation checks
└── Create gold aggregates for finance

Week 7: Testing & Monitoring
├── Data quality validation
├── Sync latency monitoring
├── Conflict resolution testing
├── Documentation
└── Production deployment
```

**Deliverables**:
- Automated Odoo → Supabase sync
- Bronze → Silver → Gold transformations
- Sync status dashboard
- Conflict resolution logs

---

### Phase 3: Real-Time & Storage (3 weeks)

```
Week 8: Realtime Server
├── Deploy Supabase Realtime container
├── Configure PostgreSQL NOTIFY
├── Implement RLS-aware subscriptions
├── Build reconnection handling
└── Test at scale (10K connections)

Week 9: Storage Service
├── Deploy MinIO for S3-compatible storage
├── Build Storage API service
├── Implement signed URL generation
├── Configure RLS for file access
└── Integrate with Odoo attachments

Week 10: Integration Testing
├── Realtime performance testing
├── Storage stress testing
├── Cross-feature integration
├── Documentation
└── Production deployment
```

**Deliverables**:
- Real-time subscriptions working
- File storage with RLS
- Odoo attachment sync
- Performance benchmarks

---

### Phase 4: Advanced Features (4 weeks)

```
Week 11-12: Edge Functions
├── Deploy Deno runtime
├── Build function deployment pipeline
├── Create database triggers for functions
├── Implement scheduled functions
└── Build function logging

Week 13-14: Polish & Scale
├── Full-text search implementation
├── Vector search with pgvector
├── Admin dashboard enhancements
├── Horizontal scaling setup
└── Documentation & training
```

**Deliverables**:
- Edge Functions runtime
- Full-text search
- Vector search (for RAG)
- Complete documentation

---

## 4. Infrastructure Requirements

### 4.1 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DIGITALOCEAN DEPLOYMENT                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    supabase-droplet                        │ │
│  │                    (8 vCPU, 16GB RAM)                      │ │
│  │                                                            │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │ │
│  │  │   nginx     │  │   Kong      │  │   GoTrue    │       │ │
│  │  │   :80/443   │  │   :8000     │  │   :9999     │       │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │ │
│  │                                                            │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │ │
│  │  │ PostgREST   │  │  Realtime   │  │  Storage    │       │ │
│  │  │   :3000     │  │   :4000     │  │   :5000     │       │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │ │
│  │                                                            │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │ │
│  │  │ PostgreSQL  │  │  pgBouncer  │  │   Redis     │       │ │
│  │  │   :5432     │  │   :6432     │  │   :6379     │       │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │ │
│  │                                                            │ │
│  │  ┌─────────────┐  ┌─────────────┐                        │ │
│  │  │   MinIO     │  │    Deno     │                        │ │
│  │  │ :9000/9001  │  │   :8080     │                        │ │
│  │  └─────────────┘  └─────────────┘                        │ │
│  │                                                            │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                     DO Managed Volume                           │
│                     ┌───────────────┐                          │
│                     │   500GB SSD   │                          │
│                     │  (PostgreSQL) │                          │
│                     └───────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Resource Estimates

| Phase | CPU | Memory | Storage | Monthly Cost |
|-------|-----|--------|---------|--------------|
| Phase 1 | 4 vCPU | 8 GB | 100 GB | ~$80 |
| Phase 2 | 4 vCPU | 8 GB | 200 GB | ~$90 |
| Phase 3 | 8 vCPU | 16 GB | 300 GB | ~$160 |
| Phase 4 | 8 vCPU | 16 GB | 500 GB | ~$200 |

### 4.3 DNS Configuration

Add to Squarespace DNS:
```
supabase.insightpulseai.net     A     [DROPLET_IP]
auth.supabase.insightpulseai.net    CNAME supabase.insightpulseai.net
api.supabase.insightpulseai.net     CNAME supabase.insightpulseai.net
storage.supabase.insightpulseai.net CNAME supabase.insightpulseai.net
```

---

## 5. Security Implementation

### 5.1 Network Security

```bash
# UFW rules
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 5432/tcp   # PostgreSQL (internal only)
ufw deny 6379/tcp   # Redis (internal only)
```

### 5.2 Secret Management

| Secret | Storage | Rotation |
|--------|---------|----------|
| Database password | .env | Quarterly |
| JWT secret | .env | Annually |
| Anon key | Public | Never |
| Service role key | .env | Quarterly |
| OAuth secrets | .env | On change |

### 5.3 RLS Policy Framework

```sql
-- Base tenant isolation function
CREATE OR REPLACE FUNCTION auth.org_id()
RETURNS uuid AS $$
  SELECT COALESCE(
    (current_setting('request.jwt.claims', true)::json->>'org_id')::uuid,
    '00000000-0000-0000-0000-000000000000'::uuid
  );
$$ LANGUAGE SQL STABLE;

-- Standard policy template
CREATE POLICY "tenant_read_policy" ON schema.table
    FOR SELECT
    USING (org_id = auth.org_id() OR org_id IS NULL);

CREATE POLICY "tenant_write_policy" ON schema.table
    FOR INSERT
    WITH CHECK (org_id = auth.org_id());
```

---

## 6. Monitoring & Observability

### 6.1 Key Metrics

| Service | Metrics |
|---------|---------|
| PostgreSQL | Connections, query time, replication lag |
| PostgREST | Request rate, latency, errors |
| GoTrue | Auth rate, failures, sessions |
| Realtime | Subscriptions, messages/sec |
| Storage | Upload/download rate, storage used |

### 6.2 Alerting Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| DB Connection Pool | > 80% used | Warning |
| Query Latency | P95 > 500ms | Warning |
| Auth Failures | > 10/min | Critical |
| Realtime Disconnects | > 100/min | Warning |
| Disk Usage | > 80% | Critical |

---

## 7. Success Criteria

### Phase 1 Criteria
- [ ] Auth flow works end-to-end
- [ ] RLS policies enforce isolation
- [ ] API responds in < 100ms P95
- [ ] Staging environment deployed

### Phase 2 Criteria
- [ ] Odoo partners sync within 5 minutes
- [ ] Odoo products sync correctly
- [ ] Invoices include line items
- [ ] Medallion transformations automated

### Phase 3 Criteria
- [ ] Realtime subscriptions work at scale
- [ ] Storage upload/download functional
- [ ] RLS applied to storage
- [ ] Latency < 100ms for realtime

### Phase 4 Criteria
- [ ] Edge functions deployable
- [ ] Full-text search working
- [ ] Documentation complete
- [ ] Production ready

---

## Appendix A: Docker Compose Reference

```yaml
# docker-compose.supabase.yml structure
services:
  postgres:      # PostgreSQL 15 with extensions
  gotrue:        # Authentication
  postgrest:     # REST API
  realtime:      # WebSocket server
  storage:       # File storage API
  imgproxy:      # Image transformations
  kong:          # API gateway
  pgbouncer:     # Connection pooling
  redis:         # Session cache
  minio:         # S3-compatible storage
  deno:          # Edge functions runtime
```

## Appendix B: Environment Variables

```bash
# Core
POSTGRES_PASSWORD=
JWT_SECRET=
ANON_KEY=
SERVICE_ROLE_KEY=

# Auth
GOTRUE_JWT_SECRET=
GOTRUE_EXTERNAL_GOOGLE_ENABLED=
GOTRUE_EXTERNAL_GOOGLE_CLIENT_ID=
GOTRUE_EXTERNAL_GOOGLE_SECRET=

# Storage
STORAGE_BACKEND=s3
S3_BUCKET=supabase-storage
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=
S3_SECRET_KEY=

# Realtime
REALTIME_IP_VERSION=IPv4
```
