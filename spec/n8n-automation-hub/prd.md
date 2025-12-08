# n8n Automation Hub - Product Requirements Document

## Document Control
- **Version**: 1.0.0
- **Status**: Draft
- **Last Updated**: 2025-12-08
- **Author**: InsightPulseAI Platform Team

---

## 1. Executive Summary

### 1.1 Vision
Deploy a self-hosted n8n instance as the central automation hub for InsightPulseAI, enabling visual workflow design, Odoo integration, AI agent orchestration, and Medallion pipeline automation.

### 1.2 Problem Statement
Currently, data flows between Odoo, Supabase, and AI agents require custom scripting, lack visibility into execution status, and have no standardized error handling. Teams need a visual, low-code platform to design, deploy, and monitor automated workflows.

### 1.3 Proposed Solution
Deploy n8n as a self-hosted automation platform with:
- Pre-built integrations for Odoo CE/OCA 18
- Custom nodes for MCP agent orchestration
- Medallion pipeline triggers and transformations
- Enterprise monitoring and alerting

### 1.4 Success Criteria
- 10+ production workflows automated within 30 days
- < 5 minute latency for Odoo sync workflows
- 99%+ workflow execution success rate
- 50% reduction in manual data transfer tasks

---

## 2. User Personas

### 2.1 Integration Developer
**Profile**: Backend developer building system integrations
**Goals**: Create reliable data pipelines between Odoo and Supabase
**Pain Points**: Custom scripts hard to maintain, no visibility into failures
**Needs**: Visual workflow designer, version control, testing tools

### 2.2 Business Analyst
**Profile**: Non-technical user automating business processes
**Goals**: Automate repetitive tasks without writing code
**Pain Points**: Dependent on engineering for simple automations
**Needs**: Low-code interface, pre-built templates, clear documentation

### 2.3 Data Engineer
**Profile**: Technical user managing Medallion pipelines
**Goals**: Orchestrate Bronze → Silver → Gold transformations
**Pain Points**: Cron jobs scattered, no centralized pipeline view
**Needs**: Scheduling, dependency management, lineage tracking

### 2.4 DevOps Engineer
**Profile**: Platform administrator
**Goals**: Ensure automation platform reliability and security
**Pain Points**: Multiple automation tools to manage
**Needs**: Centralized monitoring, credential management, backup/restore

---

## 3. Use Cases

### UC-001: Odoo Partner Sync
**Actor**: Integration Developer
**Trigger**: Odoo webhook on partner creation/update
**Flow**:
1. Receive webhook from Odoo
2. Validate payload and extract partner data
3. Transform to Supabase schema
4. Upsert to Supabase `odoo.res_partner`
5. Trigger downstream workflows if needed
6. Log execution status

**Success Criteria**: Partner available in Supabase within 2 minutes

### UC-002: Document OCR Processing
**Actor**: Business Analyst
**Trigger**: File upload webhook
**Flow**:
1. Receive file upload notification
2. Download file from MinIO
3. Send to OCR service
4. Parse OCR results
5. Create Odoo expense record
6. Attach processed document
7. Notify user via Slack

**Success Criteria**: Expense created within 5 minutes of upload

### UC-003: Agent Task Orchestration
**Actor**: Integration Developer
**Trigger**: Manual or scheduled
**Flow**:
1. Prepare task payload
2. Route to MCP coordinator
3. Monitor agent execution
4. Handle agent response
5. Execute follow-up actions
6. Store results in Supabase

**Success Criteria**: Agent tasks complete with proper error handling

### UC-004: Medallion Pipeline Refresh
**Actor**: Data Engineer
**Trigger**: Scheduled (hourly/daily)
**Flow**:
1. Trigger Bronze data ingestion
2. Wait for completion
3. Execute Silver transformations
4. Validate data quality
5. Execute Gold aggregations
6. Update pipeline metadata
7. Alert on failures

**Success Criteria**: Gold tables refreshed on schedule

### UC-005: Month-End Financial Close
**Actor**: Business Analyst
**Trigger**: Scheduled (monthly) + manual
**Flow**:
1. Extract GL entries from Odoo
2. Extract AP/AR balances
3. Calculate period metrics
4. Generate Superset datasets
5. Trigger dashboard refresh
6. Send summary to Slack

**Success Criteria**: Financial dashboards updated by 1st business day

### UC-006: Error Alerting and Recovery
**Actor**: DevOps Engineer
**Trigger**: Workflow failure
**Flow**:
1. Capture error details
2. Categorize error type
3. Execute retry if applicable
4. Send alert to appropriate channel
5. Create incident ticket if critical
6. Log for analysis

**Success Criteria**: Critical errors alerted within 5 minutes

---

## 4. Functional Requirements

### 4.1 Core Platform

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-001 | Deploy n8n on DigitalOcean droplet | P0 | Docker-based deployment |
| FR-002 | PostgreSQL backend for workflow storage | P0 | Shared with Supabase or dedicated |
| FR-003 | Redis queue for execution management | P0 | Handles workflow queuing |
| FR-004 | Nginx reverse proxy with TLS | P0 | n8n.insightpulseai.net |
| FR-005 | Environment-based configuration | P0 | .env file for all settings |
| FR-006 | Webhook endpoint exposure | P0 | Public HTTPS endpoints |

### 4.2 Odoo Integration

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-010 | Odoo XML-RPC node | P0 | Read/write Odoo models |
| FR-011 | Odoo webhook receiver | P0 | Handle Odoo event notifications |
| FR-012 | Partner sync workflow template | P0 | Pre-built template |
| FR-013 | Product sync workflow template | P0 | Pre-built template |
| FR-014 | Invoice sync workflow template | P0 | Pre-built template |
| FR-015 | Odoo attachment handling | P1 | ir.attachment integration |

### 4.3 Agent Orchestration

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-020 | MCP coordinator HTTP node | P0 | Task submission/retrieval |
| FR-021 | Agent response parsing | P0 | Structured output handling |
| FR-022 | Multi-agent routing | P1 | Route to appropriate agent |
| FR-023 | Human-in-loop approval gates | P1 | Manual approval steps |
| FR-024 | Agent timeout handling | P0 | Configurable timeouts |

### 4.4 Medallion Pipeline

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-030 | PostgreSQL node for Bronze writes | P0 | Raw data ingestion |
| FR-031 | SQL execution node | P0 | Transform execution |
| FR-032 | Pipeline dependency chains | P1 | Wait for upstream |
| FR-033 | Data quality check nodes | P1 | Validation workflows |
| FR-034 | Lineage metadata capture | P2 | Source tracking |

### 4.5 Monitoring and Operations

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-040 | Execution history retention | P0 | 90 days minimum |
| FR-041 | Error alerting (Slack) | P0 | Real-time notifications |
| FR-042 | Metrics export (Prometheus) | P1 | Execution metrics |
| FR-043 | Backup/restore capability | P0 | Workflow + credential backup |
| FR-044 | Role-based access control | P1 | User permission levels |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Requirement | Target |
|-------------|--------|
| Workflow execution start | < 5 seconds from trigger |
| Webhook response time | < 2 seconds acknowledgment |
| Concurrent workflow limit | 50+ parallel executions |
| UI responsiveness | < 3 second page loads |

### 5.2 Reliability

| Requirement | Target |
|-------------|--------|
| Uptime | 99.5% monthly |
| Workflow execution success | > 99% |
| Data durability | No execution data loss |
| Recovery time | < 1 hour from failure |

### 5.3 Security

| Requirement | Implementation |
|-------------|----------------|
| Authentication | Email/password + optional OAuth |
| Credential storage | AES-256 encryption |
| Webhook security | HMAC verification |
| Network isolation | Private network for internal services |
| TLS | Required for all external traffic |

### 5.4 Scalability

| Requirement | Target |
|-------------|--------|
| Workflow count | 100+ active workflows |
| Daily executions | 10,000+ |
| User count | 20+ concurrent users |
| Data volume | 1TB+ execution history |

---

## 6. Technical Architecture

### 6.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      n8n Automation Hub                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   n8n Web    │  │   n8n Worker │  │   n8n Webhook│          │
│  │   (Editor)   │  │  (Executor)  │  │   (Trigger)  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └────────────┬────┴────────────────┘                   │
│                      │                                          │
│              ┌───────▼───────┐                                  │
│              │     Redis     │                                  │
│              │    (Queue)    │                                  │
│              └───────┬───────┘                                  │
│                      │                                          │
│              ┌───────▼───────┐                                  │
│              │  PostgreSQL   │                                  │
│              │  (Storage)    │                                  │
│              └───────────────┘                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Odoo CE     │    │   Supabase    │    │ MCP Coordinator│
│   (ERP)       │    │   (BaaS)      │    │   (Agents)    │
└───────────────┘    └───────────────┘    └───────────────┘
```

### 6.2 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DigitalOcean Droplet                         │
│                    (n8n.insightpulseai.net)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐                                                │
│  │   nginx     │◄─────── HTTPS (443)                           │
│  │  (proxy)    │                                                │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ├─────────► n8n-main (5678)                            │
│         │                                                       │
│  ┌──────┴──────────────────────────────────────────────┐       │
│  │                   Docker Network                     │       │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐       │       │
│  │  │  n8n-main  │ │ n8n-worker │ │   redis    │       │       │
│  │  └────────────┘ └────────────┘ └────────────┘       │       │
│  │  ┌────────────┐ ┌────────────┐                      │       │
│  │  │ postgresql │ │   backup   │                      │       │
│  │  └────────────┘ └────────────┘                      │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                 │
│  Volumes: n8n-data, postgres-data, redis-data                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Workflow Templates

### 7.1 Odoo Partner Sync Template

```
[Webhook Trigger]
    │
    ▼
[Validate Payload]
    │
    ├─── Invalid ──► [Log Error] ──► [End]
    │
    ▼
[Transform to Supabase Schema]
    │
    ▼
[Upsert to bronze.raw_odoo_partners]
    │
    ▼
[Trigger Silver Transform]
    │
    ▼
[Log Success] ──► [End]
```

### 7.2 Agent Task Template

```
[Manual/Schedule Trigger]
    │
    ▼
[Prepare Task Payload]
    │
    ▼
[Submit to MCP Coordinator]
    │
    ▼
[Wait for Response] ◄────┐
    │                    │
    ├─── Pending ────────┘
    │
    ├─── Success ──► [Process Results] ──► [Store in Supabase]
    │
    ├─── Failed ──► [Log Error] ──► [Alert Slack]
    │
    ▼
[End]
```

---

## 8. Data Model

### 8.1 Core Tables (n8n Internal)

| Table | Purpose |
|-------|---------|
| `workflow_entity` | Workflow definitions |
| `execution_entity` | Execution history |
| `credentials_entity` | Encrypted credentials |
| `user` | User accounts |
| `settings` | Instance configuration |

### 8.2 Custom Audit Tables

```sql
-- Custom execution audit log
CREATE TABLE audit.n8n_execution_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id VARCHAR(255) NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,
    workflow_name VARCHAR(255),
    status VARCHAR(50),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    duration_ms INTEGER,
    error_message TEXT,
    trigger_type VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflow version history
CREATE TABLE audit.n8n_workflow_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL,
    workflow_json JSONB NOT NULL,
    changed_by VARCHAR(255),
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    change_description TEXT
);
```

---

## 9. API Specifications

### 9.1 Webhook Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/webhook/{workflow-id}` | POST | Trigger workflow via webhook |
| `/webhook-test/{workflow-id}` | POST | Test webhook (returns response) |

### 9.2 Internal API (for admin)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/workflows` | GET | List all workflows |
| `/api/v1/executions` | GET | List executions |
| `/api/v1/credentials` | GET | List credential types |
| `/healthz` | GET | Health check |

---

## 10. Dependencies

### 10.1 Infrastructure

| Dependency | Version | Purpose |
|------------|---------|---------|
| Docker | 24+ | Container runtime |
| Docker Compose | 2.20+ | Container orchestration |
| nginx | 1.24+ | Reverse proxy |
| Certbot | Latest | TLS certificates |

### 10.2 Services

| Dependency | Version | Purpose |
|------------|---------|---------|
| n8n | 1.70+ | Automation platform |
| PostgreSQL | 15+ | Workflow storage |
| Redis | 7+ | Execution queue |

### 10.3 Integrations

| System | API Version | Credentials |
|--------|-------------|-------------|
| Odoo CE/OCA 18 | XML-RPC | API key |
| Supabase | REST API | Service role key |
| MCP Coordinator | HTTP API | Internal token |
| Slack | Webhook | Bot token |

---

## 11. Acceptance Criteria

### 11.1 MVP (Phase 1)

- [ ] n8n deployed and accessible at https://n8n.insightpulseai.net
- [ ] Odoo partner sync workflow operational
- [ ] Basic error alerting via Slack
- [ ] Credential encryption verified
- [ ] Backup/restore tested

### 11.2 Phase 2

- [ ] 5+ production workflows deployed
- [ ] Agent orchestration workflows operational
- [ ] Medallion pipeline triggers working
- [ ] Role-based access configured

### 11.3 Phase 3

- [ ] 10+ production workflows
- [ ] < 5 minute sync latency achieved
- [ ] 99%+ execution success rate
- [ ] Full monitoring dashboard

---

## 12. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Credential exposure | High | Low | Encryption + access control |
| Workflow loops | Medium | Medium | Loop detection + rate limiting |
| Resource exhaustion | Medium | Medium | Container limits + monitoring |
| Integration failures | Medium | Medium | Retry logic + alerting |
| Data inconsistency | High | Low | Idempotent operations + validation |

---

## 13. Glossary

| Term | Definition |
|------|------------|
| Workflow | Automated sequence of nodes (actions) |
| Node | Single action in a workflow |
| Execution | Single run of a workflow |
| Trigger | Event that starts a workflow |
| Credential | Stored authentication for external services |
| Webhook | HTTP endpoint that triggers workflows |
