# Docs2Code Automation Pipeline - Constitution

**Version**: 1.0.0
**Status**: Active
**Last Updated**: 2025-01-01

## Purpose

The Docs2Code Automation Pipeline transforms static, read-only architectural blueprints from enterprise documentation platforms (SAP Help Portal, Microsoft Learn, Odoo Core, OCA, BIR regulatory forms, Databricks) into executable, production-ready ERP systems with automated compliance validation, type-safe code generation, and 90%+ test coverage.

## Core Principles (Non-Negotiable)

### 1. Source Fidelity
- All generated code MUST trace back to official documentation sources
- No creative interpretation of regulatory requirements (BIR, PFRS, DOLE)
- Citations required for every business rule extraction

### 2. Bounded Agent Architecture
- Exactly 6 specialized agents with strict SKILL.md boundaries
- Agents CANNOT exceed their defined scope
- Handoffs between agents are explicit and traceable
- Order: Parser → Compliance → CodeGen → SQL → Validation → Deploy

### 3. Compliance-First Generation
- Code generation BLOCKED until compliance validation passes
- BIR 36 forms (1700, 1601-C, 2550-Q, etc.) are enforced, not suggested
- 2024 Philippine progressive tax brackets are hardcoded constraints
- PFRS/IAS standards are validation gates, not recommendations

### 4. Quality Gates (Hard Thresholds)
- Unit test coverage: ≥90% (deployment blocked below)
- Integration test coverage: ≥80% (deployment blocked below)
- p99 latency: <2000ms for all database operations
- Security scan: Must pass before code generation completes

### 5. Odoo 80/15/5 Rule
- 80% of solution MUST use native Odoo 18 CE functionality
- 15% MAX can use OCA community modules
- 5% MAX for custom code
- Violations require documented justification

### 6. Lineage & Traceability
- Every generated artifact has a provenance chain
- doc_chunk → compliance_rule → generated_code → test → deployment
- No orphan code (all code traceable to requirements)

### 7. Zero-Downtime Deployment
- Blue/green deployments only
- Automatic rollback on health check failure
- <30 second maximum service interruption

### 8. Continuous Hardening
- All test failures generate DPO/ORPO preference pairs
- Agents are retrained on failure patterns
- Weekly hardening cycles are mandatory

## Guardrails

### MUST
- Store all knowledge in Supabase with pgvector + RLS
- Use medallion architecture (Bronze/Silver/Gold)
- Validate against official BIR sources (bir.gov.ph)
- Generate typed Python code (3.10+)
- Document all compliance decisions

### MUST NOT
- Generate code without compliance approval
- Deploy without passing quality gates
- Interpret tax law beyond official documentation
- Skip test coverage requirements
- Allow direct database access without RLS

### SHOULD
- Cache documentation extractions for 7 days
- Generate learning paths for complex workflows
- Provide remediation guidance for compliance failures
- Log all agent decisions for audit

### SHOULD NOT
- Require manual intervention for standard workflows
- Create circular dependencies between modules
- Over-customize when OCA modules exist
- Ignore performance SLAs

## Agent Boundaries Summary

| Agent | Can | Cannot |
|-------|-----|--------|
| DocumentationParser | Extract, parse, structure | Validate, generate, deploy |
| ComplianceValidator | Validate rules, block non-compliant | Generate code, deploy |
| CodeGenerator | Generate code, scaffold modules | Validate compliance, deploy |
| SQLAgent | Design schemas, write migrations | Generate business logic, deploy |
| ValidationAgent | Run tests, measure coverage | Generate code, fix failures |
| DeploymentOrchestrator | Deploy, rollback, health check | Modify code, skip tests |

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Documentation extraction accuracy | ≥95% | TBD |
| Compliance validation accuracy | 100% | TBD |
| Code generation success rate | ≥90% | TBD |
| Test coverage (unit) | ≥90% | TBD |
| Test coverage (integration) | ≥80% | TBD |
| Deployment success rate | ≥99% | TBD |
| Mean time to rollback | <30s | TBD |
