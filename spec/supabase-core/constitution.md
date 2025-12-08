# Supabase Core Platform - Constitution

## Document Control
- **Version**: 1.0.0
- **Status**: Active
- **Last Updated**: 2025-12-08
- **Owner**: InsightPulseAI Platform Team

---

## 1. Purpose & Scope

This constitution defines the non-negotiable principles for the **Supabase Core Platform** - an "open Firebase" model serving as the default multi-tenant app backend for the InsightPulseAI ecosystem, with schemas synced to Odoo 18 CE/OCA and Medallion (bronze/silver/gold) tables.

### 1.1 Mission Statement

> To provide a self-hosted, PostgreSQL-powered backend-as-a-service that unifies authentication, real-time subscriptions, storage, and edge functions while maintaining seamless data synchronization with Odoo CE/OCA 18 and the Medallion data warehouse.

### 1.2 Scope

| In Scope | Out of Scope |
|----------|--------------|
| Multi-tenant authentication (Auth) | Front-end UI frameworks |
| Real-time database subscriptions | Mobile native SDKs (v1) |
| Row-Level Security (RLS) | ML model training |
| Storage (S3-compatible) | Video streaming |
| Edge Functions (Deno) | Payment processing |
| Odoo CE/OCA 18 sync | Third-party SaaS integrations (use n8n) |
| Medallion schema management | - |

---

## 2. Non-Negotiable Principles

### 2.1 Self-Hosted & PostgreSQL-Native
```
RULE: PostgreSQL is the single source of truth. No proprietary database lock-in.
```
- All data stored in PostgreSQL 15+
- pgvector for embeddings, PostGIS for geo (if needed)
- Direct SQL access always available
- No abstraction layers that prevent raw SQL

### 2.2 Multi-Tenant by Default
```
RULE: Every deployment supports multiple tenants with data isolation.
```
- Tenant isolation via RLS policies
- Shared infrastructure, isolated data
- Tenant context in every request
- Cross-tenant queries forbidden at application layer

### 2.3 Odoo CE/OCA 18 as ERP Master
```
RULE: Odoo is the master for business entities (partners, products, invoices).
```
- Supabase mirrors Odoo data, not vice versa
- Changes to master entities flow Odoo → Supabase
- Supabase owns app-specific entities (sessions, preferences, logs)
- Bi-directional sync for transactional data with conflict resolution

### 2.4 Medallion Architecture Integration
```
RULE: All synced data flows through Bronze → Silver → Gold layers.
```
- Bronze: Raw Odoo extracts, raw API payloads
- Silver: Cleaned, typed, deduplicated records
- Gold: Business-ready aggregates, joined views
- Direct writes to Gold forbidden (except computed aggregates)

### 2.5 No Secrets in Git
```
RULE: All credentials via environment variables or vault.
```
- Database URLs, API keys, JWT secrets in `.env`
- Service role keys rotated quarterly
- Anon keys safe for client exposure
- Row-level security enforces access

---

## 3. Architecture Constraints

### 3.1 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Database | PostgreSQL 15+ | Supabase native, proven |
| Auth | Supabase Auth (GoTrue) | JWT, OAuth, SAML |
| Realtime | Supabase Realtime | Postgres LISTEN/NOTIFY |
| Storage | Supabase Storage (S3) | MinIO compatible |
| Functions | Deno Edge Functions | Low latency, TypeScript |
| API | PostgREST + GraphQL | Auto-generated from schema |
| Sync | Custom CDC + n8n | Odoo ↔ Supabase |

### 3.2 Schema Organization

```
┌─────────────────────────────────────────────────────────────────┐
│                    SUPABASE POSTGRESQL                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PUBLIC SCHEMA (App-owned entities)                            │
│  ├── profiles          # User profiles extending auth.users    │
│  ├── organizations     # Multi-tenant orgs                     │
│  ├── memberships       # User ↔ Org relationships              │
│  ├── app_settings      # Per-tenant configuration              │
│  └── audit_logs        # Application audit trail               │
│                                                                 │
│  ODOO SCHEMA (Synced from Odoo CE/OCA 18)                      │
│  ├── res_partner       # Partners/contacts                     │
│  ├── res_company       # Companies                             │
│  ├── product_product   # Products                              │
│  ├── account_move      # Invoices/bills                        │
│  ├── hr_employee       # Employees                             │
│  └── ...               # Other synced models                   │
│                                                                 │
│  BRONZE SCHEMA (Raw ingestion)                                 │
│  ├── raw_odoo_*        # Raw Odoo API responses                │
│  ├── raw_webhook_*     # Inbound webhook payloads              │
│  └── raw_import_*      # File imports                          │
│                                                                 │
│  SILVER SCHEMA (Cleaned data)                                  │
│  ├── clean_partners    # Validated partners                    │
│  ├── clean_products    # Standardized products                 │
│  └── ...               # Transformed entities                  │
│                                                                 │
│  GOLD SCHEMA (Business-ready)                                  │
│  ├── dim_*             # Dimension tables                      │
│  ├── fact_*            # Fact tables                           │
│  └── agg_*             # Pre-computed aggregates               │
│                                                                 │
│  AUTH SCHEMA (Supabase-managed)                                │
│  └── users, sessions, identities, etc.                         │
│                                                                 │
│  STORAGE SCHEMA (Supabase-managed)                             │
│  └── buckets, objects, etc.                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Data Flow Boundaries

```
┌─────────────┐     CDC/Webhook      ┌─────────────┐
│   Odoo 18   │────────────────────▶│   Bronze    │
│   (Master)  │                      │   Schema    │
└─────────────┘                      └──────┬──────┘
                                            │
                                    Transform/Clean
                                            │
                                            ▼
┌─────────────┐     RLS-Protected    ┌─────────────┐
│   Apps/UI   │◀────────────────────│   Silver    │
│   (Read)    │                      │   Schema    │
└─────────────┘                      └──────┬──────┘
      │                                     │
      │ Write                        Aggregate
      ▼                                     │
┌─────────────┐     Sync Back        ┌─────────────┐
│   Public    │────────────────────▶│   Gold      │
│   Schema    │                      │   Schema    │
└─────────────┘                      └─────────────┘
```

---

## 4. Security Policies

### 4.1 Authentication
- JWT-based authentication via Supabase Auth
- OAuth providers: Google, GitHub, Azure AD
- SAML for enterprise SSO (Phase 2)
- MFA required for admin roles
- Session timeout: 8 hours (configurable)

### 4.2 Authorization (Row-Level Security)

```sql
-- Example RLS policy for multi-tenant isolation
CREATE POLICY "tenant_isolation" ON public.organizations
    USING (id = current_setting('app.current_tenant_id')::uuid);

-- Example RLS policy for user-owned data
CREATE POLICY "user_owns_profile" ON public.profiles
    USING (auth.uid() = user_id);
```

### 4.3 API Security
| Key Type | Exposure | Capabilities |
|----------|----------|--------------|
| Anon Key | Client-safe | RLS-enforced reads/writes |
| Service Role | Server-only | Bypass RLS, admin operations |
| JWT Secret | Server-only | Token validation |

### 4.4 Network Security
- All connections via TLS 1.3
- Database port (5432) internal only
- PostgREST behind nginx reverse proxy
- Rate limiting: 100 req/min per user

---

## 5. Odoo Sync Rules

### 5.1 Master Data Direction
| Entity Type | Master | Direction |
|-------------|--------|-----------|
| Partners | Odoo | Odoo → Supabase |
| Products | Odoo | Odoo → Supabase |
| Invoices | Odoo | Odoo → Supabase |
| Users/Auth | Supabase | Supabase → Odoo (link) |
| App Data | Supabase | Supabase only |
| Analytics | Gold | Bi-directional reads |

### 5.2 Sync Frequency
| Data Type | Frequency | Method |
|-----------|-----------|--------|
| Critical (invoices) | Real-time | Webhook |
| Master data (partners) | 5 minutes | Poll + CDC |
| Reference data | 1 hour | Batch |
| Historical | Daily | Full sync |

### 5.3 Conflict Resolution
```
RULE: Odoo wins for master entities. Supabase wins for app entities.
```
- Last-write-wins for app data
- Odoo version takes precedence for synced entities
- Conflicts logged to audit table
- Manual review queue for critical conflicts

---

## 6. Coding Standards

### 6.1 SQL
- Use CTEs over subqueries
- Explicit column lists (no SELECT *)
- snake_case for all identifiers
- RLS policies on every tenant-scoped table
- Foreign keys with ON DELETE constraints

### 6.2 Edge Functions (Deno/TypeScript)
- TypeScript strict mode
- Zod for request validation
- Structured error responses
- Logging to structured JSON
- Timeout: 30 seconds max

### 6.3 Migrations
- Sequential numbered migrations
- Idempotent (can re-run safely)
- Rollback script for every migration
- Test in staging before production

---

## 7. Operational Guardrails

### 7.1 Data Retention
| Data Type | Retention | Archive |
|-----------|-----------|---------|
| Auth sessions | 30 days | Delete |
| Audit logs | 2 years | Compress |
| Bronze raw | 90 days | Glacier |
| Silver clean | 1 year | Glacier |
| Gold aggregates | Indefinite | Partition |

### 7.2 Backup Requirements
- Database: Hourly snapshots, 7-day PITR
- Storage: Daily backup, 30-day retention
- RPO: 15 minutes
- RTO: 1 hour

### 7.3 Scaling Triggers
| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU sustained | > 70% | Upgrade instance |
| Connections | > 80% max | Add pgBouncer |
| Storage | > 70% | Expand volume |
| Realtime subs | > 10K | Add replica |

---

## 8. Compliance & Governance

### 8.1 Data Classification
- **Public**: Aggregated reports, public APIs
- **Internal**: App data, operational metrics
- **Confidential**: PII, financial records
- **Restricted**: Auth secrets, encryption keys

### 8.2 Audit Requirements
- All schema changes logged
- All RLS policy changes logged
- Admin actions audited
- Data exports tracked

---

## 9. Amendment Process

Changes to this constitution require:
1. Written proposal with rationale
2. Review by Platform Team
3. Security review for auth/RLS changes
4. 48-hour comment period
5. Approval by technical lead
6. Version increment and changelog

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| RLS | Row-Level Security |
| CDC | Change Data Capture |
| PostgREST | REST API generator for PostgreSQL |
| GoTrue | Supabase Auth server |
| Anon Key | Public API key (RLS-enforced) |
| Service Role | Admin API key (bypasses RLS) |
