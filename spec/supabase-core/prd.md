# Supabase Core Platform - Product Requirements Document

## Document Control
- **Version**: 1.0.0
- **Status**: Draft
- **Last Updated**: 2025-12-08
- **Author**: InsightPulseAI Platform Team

---

## 0. Executive Summary

The **Supabase Core Platform** is a self-hosted, PostgreSQL-powered backend-as-a-service that serves as the default multi-tenant app backend for the InsightPulseAI ecosystem. It provides authentication, real-time subscriptions, storage, and edge functions while maintaining seamless data synchronization with Odoo CE/OCA 18 and the Medallion data warehouse.

### Key Value Propositions
1. **Unified Backend**: Single platform for auth, database, storage, and functions
2. **Odoo Integration**: Seamless sync with ERP master data
3. **Medallion Native**: Bronze → Silver → Gold data architecture built-in
4. **Multi-Tenant**: Isolated data with shared infrastructure
5. **Real-Time**: Live subscriptions for collaborative apps

---

## 1. Problem Statement

### Current Pain Points
1. **Fragmented Authentication**: Multiple auth systems across apps
2. **Data Silos**: App data disconnected from Odoo master data
3. **Manual Sync**: ETL jobs require custom coding for each integration
4. **No Real-Time**: Polling-based updates create lag and load
5. **Storage Scattered**: Files across multiple services without unified access

### Business Impact
- Slower app development (weeks vs days)
- Data inconsistencies between systems
- Higher infrastructure costs (multiple databases)
- Poor user experience (stale data, multiple logins)

---

## 2. User Personas

### 2.1 App Developer
**Name**: Maya - Full-Stack Developer
**Goals**:
- Build apps quickly with minimal backend setup
- Access Odoo data without learning Odoo APIs
- Implement real-time features easily

**Pain Points**:
- Setting up auth from scratch
- Syncing data between systems manually
- Building custom APIs for each app

**Success Metrics**:
- Time to first API call: < 5 minutes
- Auth integration: < 1 hour
- Odoo data access: < 30 minutes

---

### 2.2 Data Engineer
**Name**: Luis - Data Engineer
**Goals**:
- Ensure data quality across all schemas
- Build reliable ETL pipelines
- Monitor data freshness and lineage

**Pain Points**:
- Multiple database systems to manage
- Inconsistent data formats
- No visibility into data flow

**Success Metrics**:
- Single database for all app data
- Automated Medallion transformations
- Full data lineage tracking

---

### 2.3 Finance Operations
**Name**: Ana - Finance SSC Lead
**Goals**:
- Access real-time financial data in apps
- Ensure data matches Odoo
- Self-serve on basic data queries

**Pain Points**:
- Waiting for IT to build reports
- Data discrepancies between systems
- No access to raw data

**Success Metrics**:
- < 5 minute data latency from Odoo
- 100% match with Odoo source
- Direct SQL access for analysts

---

### 2.4 Platform Admin
**Name**: Carlos - DevOps Engineer
**Goals**:
- Manage infrastructure efficiently
- Ensure security and compliance
- Scale as demand grows

**Pain Points**:
- Multiple services to maintain
- Complex networking
- Backup/recovery complexity

**Success Metrics**:
- Single platform to manage
- Automated backups and failover
- Clear security model

---

## 3. Core Use Cases

### UC-001: Multi-Tenant Authentication
**Priority**: P0 (Critical)
**Persona**: App Developer, Platform Admin

**Flow**:
```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│   App/UI     │────▶│ Supabase Auth │────▶│  PostgreSQL  │
│              │     │   (GoTrue)    │     │ auth.users   │
└──────────────┘     └───────────────┘     └──────────────┘
       │                    │
       │                    ▼
       │            ┌───────────────┐
       └───────────▶│  JWT Token    │
                    │  (RLS-ready)  │
                    └───────────────┘
```

**Requirements**:
- Email/password authentication
- OAuth (Google, GitHub, Azure AD)
- Magic link (passwordless)
- Multi-tenant organization support
- Role-based permissions
- Session management

**Acceptance Criteria**:
- [ ] Sign up flow works with email verification
- [ ] OAuth login redirects correctly
- [ ] JWT contains tenant and role claims
- [ ] RLS policies enforce tenant isolation
- [ ] Session refresh works seamlessly

---

### UC-002: Odoo Data Sync
**Priority**: P0 (Critical)
**Persona**: Data Engineer, Finance Operations

**Flow**:
```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│   Odoo 18    │────▶│   n8n/CDC     │────▶│    Bronze    │
│   (Master)   │     │   Workflow    │     │   (Raw)      │
└──────────────┘     └───────────────┘     └──────┬───────┘
                                                  │
                           Transform              │
                                                  ▼
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│   App/API    │◀────│    Odoo       │◀────│    Silver    │
│   (Read)     │     │   Schema      │     │   (Clean)    │
└──────────────┘     └───────────────┘     └──────────────┘
```

**Requirements**:
- Sync res.partner (customers/vendors)
- Sync product.product (products)
- Sync account.move (invoices)
- Sync hr.employee (employees)
- Real-time webhook for critical updates
- Batch sync for bulk data

**Acceptance Criteria**:
- [ ] Partners sync within 5 minutes of Odoo change
- [ ] Products have all required fields mapped
- [ ] Invoices include line items
- [ ] Conflict resolution logs created
- [ ] Data passes quality checks

---

### UC-003: Real-Time Subscriptions
**Priority**: P1 (High)
**Persona**: App Developer

**Flow**:
```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│   App/UI     │◀────│   Realtime    │◀────│  PostgreSQL  │
│   (Subscribe)│     │   Server      │     │  (NOTIFY)    │
└──────────────┘     └───────────────┘     └──────────────┘
```

**Requirements**:
- Subscribe to table changes
- Filter by RLS policies
- Broadcast to multiple clients
- Handle reconnection gracefully
- Scale to 10K+ concurrent subscriptions

**Acceptance Criteria**:
- [ ] Changes arrive within 100ms
- [ ] RLS filters applied to subscriptions
- [ ] Reconnection auto-resubscribes
- [ ] Memory usage bounded
- [ ] Horizontal scaling works

---

### UC-004: File Storage
**Priority**: P1 (High)
**Persona**: App Developer

**Requirements**:
- Upload files via API
- Organize in buckets/folders
- Generate signed URLs
- Apply RLS to file access
- Integrate with Odoo attachments

**Acceptance Criteria**:
- [ ] Upload/download works via API
- [ ] Signed URLs expire correctly
- [ ] RLS prevents unauthorized access
- [ ] Large files (100MB+) supported
- [ ] Image transformations available

---

### UC-005: Edge Functions
**Priority**: P2 (Medium)
**Persona**: App Developer

**Requirements**:
- Deploy TypeScript/Deno functions
- Access database from functions
- Trigger on database events
- HTTP endpoint invocation
- Scheduled execution

**Acceptance Criteria**:
- [ ] Functions deploy in < 30 seconds
- [ ] Database access via service role
- [ ] Webhook triggers work
- [ ] Cron scheduling available
- [ ] Logs accessible

---

### UC-006: Medallion Data Management
**Priority**: P1 (High)
**Persona**: Data Engineer

**Requirements**:
- Automated Bronze → Silver transformation
- Silver → Gold aggregation
- Data quality checks at each layer
- Lineage tracking
- Scheduled refresh

**Acceptance Criteria**:
- [ ] Bronze captures all raw data
- [ ] Silver applies cleaning rules
- [ ] Gold aggregates computed correctly
- [ ] Data quality dashboard available
- [ ] Lineage queryable

---

## 4. Functional Requirements

### 4.1 Authentication & Authorization

| ID | Requirement | Priority |
|----|-------------|----------|
| AUTH-001 | Email/password signup and login | P0 |
| AUTH-002 | OAuth provider support (Google, GitHub, Azure AD) | P0 |
| AUTH-003 | Magic link (passwordless) authentication | P1 |
| AUTH-004 | Multi-factor authentication (TOTP) | P1 |
| AUTH-005 | Organization/tenant management | P0 |
| AUTH-006 | Role-based access control | P0 |
| AUTH-007 | JWT with custom claims | P0 |
| AUTH-008 | Session management and refresh | P0 |
| AUTH-009 | Password reset flow | P0 |
| AUTH-010 | SAML/SSO integration | P2 |

### 4.2 Database & API

| ID | Requirement | Priority |
|----|-------------|----------|
| DB-001 | PostgreSQL 15+ with extensions | P0 |
| DB-002 | Auto-generated REST API (PostgREST) | P0 |
| DB-003 | Auto-generated GraphQL API | P2 |
| DB-004 | Row-Level Security policies | P0 |
| DB-005 | Database migrations management | P0 |
| DB-006 | Connection pooling (pgBouncer) | P1 |
| DB-007 | Read replicas support | P2 |
| DB-008 | Full-text search | P1 |
| DB-009 | Vector search (pgvector) | P2 |

### 4.3 Real-Time

| ID | Requirement | Priority |
|----|-------------|----------|
| RT-001 | Table change subscriptions | P0 |
| RT-002 | RLS-aware filtering | P0 |
| RT-003 | Presence (online users) | P2 |
| RT-004 | Broadcast channels | P1 |
| RT-005 | Automatic reconnection | P0 |

### 4.4 Storage

| ID | Requirement | Priority |
|----|-------------|----------|
| STR-001 | File upload/download API | P0 |
| STR-002 | Bucket management | P0 |
| STR-003 | Signed URL generation | P0 |
| STR-004 | RLS for file access | P0 |
| STR-005 | Image transformations | P2 |
| STR-006 | S3-compatible API | P1 |

### 4.5 Odoo Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| ODOO-001 | res.partner sync | P0 |
| ODOO-002 | product.product sync | P0 |
| ODOO-003 | account.move sync | P0 |
| ODOO-004 | hr.employee sync | P1 |
| ODOO-005 | Real-time webhook triggers | P0 |
| ODOO-006 | Batch sync scheduling | P0 |
| ODOO-007 | Conflict resolution | P0 |
| ODOO-008 | Sync status dashboard | P1 |

### 4.6 Medallion Architecture

| ID | Requirement | Priority |
|----|-------------|----------|
| MED-001 | Bronze schema with raw tables | P0 |
| MED-002 | Silver schema with clean tables | P0 |
| MED-003 | Gold schema with aggregates | P0 |
| MED-004 | Automated transformations | P1 |
| MED-005 | Data quality checks | P1 |
| MED-006 | Lineage tracking | P2 |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| API response time | < 100ms | P95 latency |
| Real-time latency | < 100ms | Message delivery |
| Auth operations | < 500ms | Login/signup |
| File upload | > 10MB/s | Throughput |
| Database queries | < 200ms | P95 latency |

### 5.2 Availability

| Metric | Target |
|--------|--------|
| Uptime | 99.9% |
| Planned maintenance | Sunday 02:00-04:00 UTC |
| RTO | < 1 hour |
| RPO | < 15 minutes |

### 5.3 Scalability

| Dimension | Initial | Scale Target |
|-----------|---------|--------------|
| Concurrent users | 1,000 | 50,000 |
| Database size | 100GB | 5TB |
| Realtime subscriptions | 5,000 | 100,000 |
| API requests/sec | 100 | 10,000 |

### 5.4 Security

| Requirement | Implementation |
|-------------|----------------|
| Encryption at rest | AES-256 |
| Encryption in transit | TLS 1.3 |
| Authentication | JWT + RLS |
| Key rotation | Quarterly |
| Audit logging | All admin actions |

---

## 6. Integration Specifications

### 6.1 Odoo CE/OCA 18

**Connection Type**: XML-RPC + PostgreSQL CDC
**Endpoint**: `erp.insightpulseai.net`

**Synced Models**:
```yaml
models:
  - name: res.partner
    supabase_table: odoo.res_partner
    sync_type: incremental
    key_field: id
    frequency: 5m

  - name: product.product
    supabase_table: odoo.product_product
    sync_type: incremental
    key_field: id
    frequency: 15m

  - name: account.move
    supabase_table: odoo.account_move
    sync_type: incremental
    key_field: id
    frequency: realtime
    webhook: true
```

### 6.2 n8n Automation Hub

**Connection Type**: REST API + Webhooks
**Endpoint**: `n8n.insightpulseai.net`

**Workflows**:
- `odoo-to-supabase-sync`: Scheduled sync
- `supabase-webhook-handler`: Inbound events
- `medallion-transform`: Bronze → Silver → Gold

### 6.3 Data Engineering Workbench

**Connection Type**: PostgreSQL direct
**Schemas**: `bronze.*`, `silver.*`, `gold.*`

**Use Cases**:
- Notebook queries against all schemas
- Pipeline definitions for transformations
- Data catalog entries

---

## 7. UI/UX Requirements

### 7.1 Supabase Studio (Admin Dashboard)

| Screen | Purpose | Priority |
|--------|---------|----------|
| Dashboard | Overview of projects and usage | P0 |
| Table Editor | Visual database management | P0 |
| SQL Editor | Direct SQL execution | P0 |
| Auth Users | User management | P0 |
| Storage | File browser | P0 |
| Functions | Edge function management | P1 |
| Settings | Project configuration | P0 |
| Logs | Real-time log viewer | P1 |

### 7.2 Client SDKs

| SDK | Priority |
|-----|----------|
| JavaScript/TypeScript | P0 |
| Python | P1 |
| Go | P2 |

---

## 8. Success Metrics & SLAs

### 8.1 Business Metrics

| Metric | Baseline | Target |
|--------|----------|--------|
| App development time | 2 weeks | 3 days |
| Data sync latency | 1 hour | 5 minutes |
| Auth integration time | 2 days | 2 hours |
| Developer satisfaction | - | > 4.0/5.0 |

### 8.2 Technical SLAs

| Metric | SLA | Penalty |
|--------|-----|---------|
| API availability | 99.9% | P1 escalation |
| Sync freshness | < 5 min | Alert |
| Auth uptime | 99.95% | P0 escalation |
| Data accuracy | 100% | Audit |

---

## 9. Release Plan

### Phase 1: Foundation (4 weeks)
- PostgreSQL setup with Medallion schemas
- Supabase Auth integration
- Basic PostgREST API
- RLS policy framework

### Phase 2: Odoo Integration (3 weeks)
- res.partner sync
- product.product sync
- account.move sync
- Webhook handlers

### Phase 3: Real-Time & Storage (3 weeks)
- Realtime subscriptions
- Storage buckets
- Signed URLs
- RLS for storage

### Phase 4: Advanced Features (4 weeks)
- Edge Functions
- Medallion transformations
- Full-text search
- Admin dashboard

---

## 10. Open Questions & Risks

### Open Questions
1. Should we use Supabase's hosted GoTrue or self-host?
2. What's the migration path from existing auth systems?
3. How do we handle Odoo field customizations in sync?

### Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Odoo API changes | Medium | High | Version-locked sync |
| Scale limits | Low | High | Horizontal sharding plan |
| RLS complexity | Medium | Medium | Policy templates |
| Real-time overload | Medium | Medium | Rate limiting |

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| PostgREST | REST API generator for PostgreSQL |
| GoTrue | Supabase authentication server |
| RLS | Row-Level Security |
| CDC | Change Data Capture |
| Medallion | Bronze → Silver → Gold data architecture |
| pgvector | PostgreSQL extension for vectors |
