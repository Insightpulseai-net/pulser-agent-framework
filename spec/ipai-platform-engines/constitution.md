# InsightPulseAI Platform Engines - Constitution

## Document Control
- **Version**: 1.0.0
- **Status**: Active
- **Last Updated**: 2025-12-08
- **Owner**: InsightPulseAI Platform Team

---

## 1. Purpose & Scope

This constitution defines the non-negotiable principles, guardrails, and governance rules for the **InsightPulseAI Platform Engines** - a Databricks-style, unified engine architecture that serves as the foundation for all verticals (TE-Cheq, Scout, SariCoach, CES/LIONS) within the InsightPulseAI ecosystem.

### 1.1 Mission Statement

> To provide a unified, tenant-aware, RBAC-aware engine platform that enables all InsightPulseAI products to be compositions of reusable engines rather than bespoke stacks - powering intelligent agents that serve "different needs with equal opportunities."

### 1.2 Scope

This constitution covers:
- **Platform Engines (H1-H8)**: Horizontals that all products share
- **Domain Engines**: Vertical-specific engines (TE-Cheq, Retail, Creative)
- **Agent Architecture**: How AI agents interact with engines
- **Data Governance**: How data flows, who can access what
- **Integration Boundaries**: What connects to what, and how

---

## 2. Core Philosophy: Ka Sangkap AI

### 2.1 Different Needs, Equal Opportunities

```
PRINCIPLE: Every agent serves specific needs but all agents have equal
           access to platform capabilities.
```

Ka Sangkap AI ("Bespoke AI") is the guiding philosophy:

- **Specialized by domain**: A Tax Agent is different from a Creative Agent
- **Equal in platform access**: Both use the same engine infrastructure
- **Certified by capability**: Agents perform real tasks at certifiable levels
- **Tenant-aware**: Each agent knows its organizational context
- **RBAC-aware**: Each agent respects permission boundaries

This means:
- A Finance agent isn't "better" than a Retail agent - they're *different*
- A creative expert's agent is not useless for tax work; it's simply *not designed* for it
- All agents are trained, evaluated, and certified for their specific domain

### 2.2 Engines Over Bespoke

```
PRINCIPLE: Build engines once, compose products many times.
```

- No product should be a one-off build
- Every feature should ask: "Which engine does this belong to?"
- New verticals should be achievable by composing existing engines
- Domain engines should extend, not duplicate, platform engines

---

## 3. Non-Negotiable Principles

### 3.1 Self-Hosted Only

```
RULE: No SaaS dependencies for core platform functionality.
```

- All engines run on DigitalOcean + Supabase infrastructure
- No data leaves fin-workspace without explicit approval
- External integrations (Figma, GitHub) are read-only or webhook-based
- Model APIs (Claude, Gemini) are the only external AI dependencies

### 3.2 No Secrets in Git

```
RULE: Zero plaintext secrets in any repository.
```

- All credentials via `.env` files (not committed)
- Secrets mounted as Docker secrets or environment variables
- API keys rotated quarterly minimum
- Audit log for all secret access

### 3.3 Spec-Driven Development (SDD)

```
RULE: No engine without specs. No deployment without plan.
```

- Every engine requires PRD entry before implementation
- Every API requires documented contract
- Every change requires task reference in `tasks.md`
- Every agent requires skill definition in registry

### 3.4 Tenant Isolation is Non-Negotiable

```
RULE: Data never crosses tenant boundaries without explicit consent.
```

- Every data table must have `tenant_id` or equivalent
- RLS policies required on ALL tenant-scoped tables
- No "SELECT *" queries that span tenants
- Audit logging for any cross-tenant operations

### 3.5 RBAC Flows Through Everything

```
RULE: Every request carries identity context.
```

- Every API call must include authenticated user context
- Every agent call must resolve roles and permissions
- Every data query must respect role-based access
- No anonymous operations on production data

### 3.6 Agents Must Be Grounded

```
RULE: No hallucinated responses in production agents.
```

- Every agent response must cite source data
- Every recommendation must reference actual metrics
- Every action must be traceable to an engine
- "I don't know" is an acceptable answer

---

## 4. Architecture Constraints

### 4.1 Engine Ownership Model

| Engine Type | Ownership | Change Process |
|-------------|-----------|----------------|
| Platform (H1-H8) | Platform Team | PRD + 2 reviewers |
| Domain (TE-Cheq) | Finance Team | PRD + domain lead |
| Domain (Retail) | Retail Team | PRD + domain lead |
| Domain (Creative) | Creative Team | PRD + domain lead |
| Shared (PH Intel) | Platform Team | PRD + all stakeholders |

### 4.2 Data Architecture

```
Bronze (Raw) --> Silver (Cleaned) --> Gold (Business-Ready)
```

- **Bronze**: Raw ingestion, immutable, partitioned by date
- **Silver**: Validated, deduplicated, typed, tenant-scoped
- **Gold**: Business aggregates, analytics-ready, role-scoped

### 4.3 Schema Namespacing

| Namespace | Owner | Purpose |
|-----------|-------|---------|
| `identity.*` | H1 Engine | Tenants, users, roles |
| `teq.*` | TE-Cheq | Finance/PPM domain |
| `scout.*` | Scout | Retail analytics |
| `saricoach.*` | SariCoach | Micro-retail coaching |
| `ces.*` | CES | Creative effectiveness |
| `ph_intel.*` | Platform | PH data intelligence |
| `ai.*` | H7 Engine | Agents, sessions, messages |
| `analytics.*` | H3 Engine | Cross-domain views |
| `governance.*` | H8 Engine | Audit, policies, costs |

### 4.4 API Contract Standards

All engine APIs must follow:

```yaml
# Standard API Response
{
  "success": boolean,
  "data": object | array | null,
  "error": {
    "code": string,
    "message": string,
    "details": object | null
  } | null,
  "meta": {
    "request_id": string,
    "tenant_id": string,
    "timestamp": string
  }
}
```

---

## 5. Agent Governance

### 5.1 Agent Registry Requirements

Every production agent MUST have:

```yaml
agent:
  slug: "saricoach"           # Unique identifier
  name: "SariCoach"           # Display name
  description: "..."          # What the agent does
  vertical: "retail"          # Owning vertical
  tenant_scope: "cluster"     # Tenant level access
  skills: [...]               # Registered skills
  model: "gemini-1.5-flash"   # Backing model
  evaluation:
    judge_prompts: [...]      # AI evaluation prompts
    human_feedback: true      # Requires human feedback
    certification: "v1.0"     # Certification version
```

### 5.2 Skill Registration

Every tool/skill an agent can call MUST be registered:

```yaml
skill:
  name: "query_store_metrics"
  engine: "saricoach"
  input_schema: {...}
  output_schema: {...}
  required_roles: ["store_owner", "cluster_admin"]
  audit_level: "standard"
  rate_limit: "100/hour"
```

### 5.3 Agent Evaluation Framework

All agents must undergo:

1. **AI Judge Evaluation**
   - Factuality: Is the response grounded in data?
   - Actionability: Can the user act on the recommendation?
   - Safety: Does it avoid harmful/biased outputs?

2. **Human Feedback Loop**
   - Thumbs up/down on responses
   - Correction capability
   - Escalation path

3. **Certification Process**
   - Performance benchmarks met
   - Safety checks passed
   - Domain expert validation

### 5.4 Agent Cost Controls

```
RULE: Every agent call has a cost ceiling.
```

- Per-tenant monthly token budgets
- Per-agent call limits
- Automatic circuit breaker at 80% budget
- Alerts at 50% and 75% thresholds

---

## 6. Security Policies

### 6.1 Authentication

- All platform access requires authentication
- SSO integration with `auth.insightpulseai.net`
- Session timeout: 8 hours (configurable)
- MFA required for admin functions

### 6.2 Authorization Matrix

| Role | Platform Engines | Domain Engines | Agent Access |
|------|------------------|----------------|--------------|
| Viewer | Read analytics | Read own data | Query only |
| User | Read + limited write | Full own domain | Standard agents |
| Manager | Read all + reports | Approve workflows | All agents |
| Admin | Full platform access | Full domain access | Configure agents |

### 6.3 Network Security

- All endpoints behind nginx reverse proxy
- TLS 1.3 minimum
- Rate limiting: configurable per endpoint
- IP allowlist for admin functions

---

## 7. Data Quality Standards

### 7.1 Required Checks

Every data pipeline must implement:

- [ ] Schema validation on ingestion
- [ ] Null checks on required fields
- [ ] Referential integrity for foreign keys
- [ ] Duplicate detection
- [ ] Anomaly detection (volume +/- 20%)

### 7.2 Quality Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Completeness | > 99% | < 98% |
| Freshness | < 1 hour | > 2 hours |
| Accuracy | > 99.5% | < 99% |
| Consistency | 100% | Any drift |

---

## 8. Operational Guardrails

### 8.1 Change Management

- All production changes via PR
- Minimum 1 reviewer for code
- Minimum 2 reviewers for engine changes
- No direct production edits
- Rollback plan required for deployments

### 8.2 Incident Response

| Priority | Description | Response Time |
|----------|-------------|---------------|
| P1 | Data loss / security breach | 15 minutes |
| P2 | Engine down / major feature broken | 1 hour |
| P3 | Performance degradation | 4 hours |
| P4 | Enhancement / minor bug | Next sprint |

### 8.3 Data Retention

| Data Type | Retention | Archive |
|-----------|-----------|---------|
| Bronze (raw) | 90 days | Glacier after 30 |
| Silver (cleaned) | 1 year | Glacier after 90 |
| Gold (analytics) | 7 years | Per compliance |
| Agent logs | 2 years | Compressed after 30 |
| Audit logs | 7 years | Never delete |

---

## 9. Compliance & Ethics

### 9.1 Data Classification

| Level | Description | Examples |
|-------|-------------|----------|
| **Public** | Can be shared freely | Aggregated reports, dashboards |
| **Internal** | Organization only | Operational data, non-PII metrics |
| **Confidential** | Role-restricted | Financial records, vendor data |
| **Restricted** | Need-to-know only | PII, credentials, API keys |

### 9.2 PH Data Privacy Compliance

- Data Processing Agreement required for all vendors
- Consent capture for all personal data
- Right to deletion supported
- Data minimization enforced

### 9.3 AI Ethics

- No discriminatory algorithms
- Transparent AI decision explanations
- Human-in-the-loop for high-stakes decisions
- Regular bias audits

---

## 10. Amendment Process

Changes to this constitution require:

1. Written proposal with rationale
2. Review by Platform Team
3. 72-hour comment period
4. Approval by:
   - Technical Lead
   - Domain Lead (if domain-specific)
   - Security Lead (if security-related)
5. Version increment and changelog entry

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Ka Sangkap AI** | "Bespoke AI" - specialized agents for specific needs |
| **Engine** | Self-contained module providing specific capabilities |
| **Vertical** | Business domain (Finance, Retail, Creative) |
| **Horizontal** | Cross-cutting platform capability |
| **SDD** | Spec-Driven Development |
| **RLS** | Row-Level Security |
| **RBAC** | Role-Based Access Control |

## Appendix B: Related Documents

- [Product Requirements Document](./prd.md)
- [Implementation Plan](./plan.md)
- [Task Breakdown](./tasks.md)
