# n8n Automation Hub - Constitution

## Document Control
- **Version**: 1.0.0
- **Status**: Active
- **Last Updated**: 2025-12-08
- **Author**: InsightPulseAI Platform Team

---

## 1. Purpose Statement

The n8n Automation Hub is the **central workflow automation engine** for the InsightPulseAI ecosystem. It orchestrates data flows between Odoo CE/OCA 18, Supabase, AI agents, and external services through a visual, low-code interface while maintaining enterprise-grade reliability and auditability.

---

## 2. Guiding Principles

### 2.1 Self-Hosted Sovereignty
RULE: All workflow definitions, execution history, and credentials MUST remain within our infrastructure.
- No workflow data leaves DigitalOcean without explicit export
- Credentials stored encrypted in PostgreSQL (never external vaults without approval)
- All executions logged locally with full audit trails

### 2.2 Odoo CE/OCA 18 as Business System of Record
RULE: Odoo is the authoritative source for business operations data.
- Workflows MUST respect Odoo as master for partners, products, invoices
- Bidirectional sync patterns require explicit approval in workflow design
- Odoo webhook handlers take priority in conflict scenarios

### 2.3 Medallion Pipeline Integration
RULE: Data transformation workflows MUST follow Bronze → Silver → Gold architecture.
- Raw data ingestion lands in Bronze (no transformation)
- Cleaning and validation workflows produce Silver
- Business aggregations produce Gold
- Lineage tracked via workflow execution metadata

### 2.4 Agent-First Orchestration
RULE: AI agents are first-class workflow participants, not afterthoughts.
- MCP coordinator integration for agent task routing
- Structured agent outputs feed downstream workflows
- Human-in-the-loop approval gates where required
- Agent failures trigger defined escalation paths

### 2.5 Spec-Driven Workflow Development
RULE: Complex workflows require specification before implementation.
- Workflows affecting production data need documented design
- Test workflows (prefixed `[TEST]`) exempt from full spec
- Workflow changes versioned alongside code changes

---

## 3. Non-Negotiable Requirements

### 3.1 Security

| Requirement | Implementation |
|-------------|----------------|
| Credential encryption | AES-256 for all stored credentials |
| Webhook authentication | HMAC signatures or API keys required |
| Execution isolation | No cross-tenant workflow visibility |
| Audit logging | All executions logged with user attribution |
| Secret management | Environment variables, never hardcoded |

### 3.2 Reliability

| Requirement | Implementation |
|-------------|----------------|
| Workflow persistence | PostgreSQL-backed execution state |
| Retry policies | Configurable per-node with exponential backoff |
| Dead letter handling | Failed executions preserved for investigation |
| Queue management | Redis-backed execution queue |
| Health monitoring | `/healthz` endpoint with dependency checks |

### 3.3 Compliance

| Requirement | Implementation |
|-------------|----------------|
| Execution history | 90-day retention minimum |
| Data lineage | Source-to-target tracking in workflow metadata |
| Change audit | Workflow version history maintained |
| Access control | Role-based workflow access |

---

## 4. Integration Boundaries

### 4.1 Required Integrations

| System | Integration Type | Purpose |
|--------|------------------|---------|
| Odoo CE/OCA 18 | XML-RPC + Webhooks | Business data sync |
| Supabase | REST + Realtime | Application data |
| PostgreSQL | Direct connection | Medallion layer writes |
| MCP Coordinator | HTTP API | Agent orchestration |
| MinIO/S3 | SDK | File handling |

### 4.2 Optional Integrations

| System | Integration Type | Purpose |
|--------|------------------|---------|
| Superset | REST API | Dashboard triggers |
| Slack | Webhook + Bot | Notifications |
| Email (SMTP) | SMTP | Alerts and reports |
| GitHub | API + Webhooks | DevOps automation |

### 4.3 Prohibited Without Approval

- Direct production database writes bypassing application APIs
- External SaaS workflow storage (Zapier, Make cloud)
- Unencrypted credential storage
- Workflows without error handling

---

## 5. Decision Rights

### 5.1 Workflow Governance

| Decision | Authority | Escalation |
|----------|-----------|------------|
| New integration category | Platform Team | Architecture Review |
| Production workflow deployment | Workflow Owner + Review | Platform Team |
| Credential provisioning | DevOps | Security Team |
| Retention policy changes | Platform Team | Compliance |

### 5.2 Change Management

| Change Type | Process |
|-------------|---------|
| New workflow | Design → Review → Test → Deploy |
| Workflow modification | Version → Test → Review → Deploy |
| Credential rotation | Automated with notification |
| Integration addition | Architecture review required |

---

## 6. Success Metrics

### 6.1 Operational KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| Workflow success rate | > 99% | Successful / Total executions |
| Execution latency P95 | < 30s | Per-workflow timing |
| Error resolution time | < 4h | Alert to resolution |
| Credential rotation | Monthly | Automated tracking |

### 6.2 Business KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| Odoo sync latency | < 5 min | Webhook to Supabase |
| Agent task completion | > 95% | MCP coordinator metrics |
| Data pipeline freshness | < 1h | Gold layer staleness |
| Manual intervention rate | < 5% | Human-in-loop triggers |

---

## 7. Amendment Process

1. Propose change via RFC document
2. Platform Team review (5 business days)
3. Security review for credential/integration changes
4. Approval requires Platform Lead + Security sign-off
5. Document in constitution changelog

---

## Appendix A: Workflow Naming Convention

```
[ENV]_[SYSTEM]_[ACTION]_[ENTITY]

Examples:
- PROD_odoo_sync_partners
- PROD_agent_process_documents
- TEST_supabase_export_reports
- DEV_medallion_transform_invoices
```

## Appendix B: Node Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| Trigger | Start workflow | Webhook, Cron, Manual |
| Transform | Data manipulation | Set, Code, Merge |
| Integration | External systems | HTTP, Odoo, PostgreSQL |
| Control | Flow logic | IF, Switch, Loop |
| Utility | Helpers | Wait, Error Trigger |
