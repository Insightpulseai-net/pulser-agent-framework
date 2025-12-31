# Docs2Code Automation Pipeline - Product Requirements Document

**Version**: 1.0.0
**Status**: Active
**Last Updated**: 2025-01-01

## Executive Summary

The Docs2Code Automation Pipeline is an enterprise-grade ecosystem that transforms static architectural documentation into executable, production-ready ERP systems. It bridges documentation platforms (SAP Help Portal, Microsoft Learn, Odoo, BIR) with operational environments (Odoo CE 18, Supabase) through automated extraction, compliance validation, and code generation.

## Problem Statement

Organizations maintain extensive documentation about business processes, regulatory requirements, and system architectures, but translating this documentation into working code is:

1. **Manual and Error-Prone**: Developers must read, interpret, and implement documentation manually
2. **Compliance-Risky**: Regulatory requirements (BIR, PFRS) are often misinterpreted
3. **Inconsistent**: Different developers implement the same spec differently
4. **Slow**: Documentation-to-code cycles take weeks or months
5. **Hard to Audit**: No clear lineage from requirement to implementation

## Solution Overview

A three-stage bounded agent pipeline that:

1. **INGEST**: Extracts knowledge from 6 documentation sources into semantic memory
2. **BUILD**: Validates compliance, generates type-safe code, runs tests
3. **RELEASE**: Deploys with zero downtime, auto-rollback, and hardening loops

## Documentation Ingestion Sources

### Primary Sources

| Source | URL | Extraction Method | Purpose |
|--------|-----|-------------------|---------|
| SAP S/4HANA AFC | help.sap.com/docs/s4hana-cloud-advanced-financial-closing | Web scraping + PDF | Financial closing workflows, GRC patterns |
| Microsoft Learn | learn.microsoft.com/en-us/azure/architecture/ | Web scraping | Well-Architected Framework, Landing Zones |
| Odoo Core | github.com/odoo/odoo (18.0) | GitHub API | Native module patterns, ORM structure |
| OCA Modules | github.com/OCA | GitHub API | Community module best practices |
| BIR Regulatory | bir.gov.ph/ebirforms | PDF + OCR | 36 official tax forms, 2024 brackets |
| Databricks Arch | databricks.com/resources/architectures | Web scraping | Medallion architecture patterns |

### Secondary Sources

| Source | Purpose |
|--------|---------|
| Figma API | Design tokens, theme variables |
| PFRS Standards | Accounting standards compliance |
| DOLE Labor Laws | Employment compliance rules |

## Bounded Agent Pipeline

### Agent 1: DocumentationParser

**Input**: URLs, GitHub repos, PDF documents
**Output**: Structured JSON AST in Supabase

Responsibilities:
- Recursively extract from all 6 sources
- Parse API specs, code examples, business rules
- Build semantic embeddings (pgvector)
- Map citations back to source URLs

### Agent 2: ComplianceValidator

**Input**: Extracted AST, business logic
**Output**: Compliance report (pass/fail + remediation)

Responsibilities:
- Validate against BIR 36 forms
- Check 2024 progressive tax brackets
- Enforce PFRS/IAS standards
- Block non-compliant code from generation

### Agent 3: CodeGenerator

**Input**: Validated AST, compliance-approved specs
**Output**: Production-ready Odoo modules, FastAPI endpoints

Responsibilities:
- Generate Odoo 18 CE modules (80% native)
- Reference OCA modules (15%)
- Custom code only where necessary (5%)
- Full type hints, docstrings, error handling

### Agent 4: SQLAgent

**Input**: Data models from CodeGenerator
**Output**: Supabase migrations, RLS policies, views

Responsibilities:
- Design medallion architecture (Bronze/Silver/Gold)
- Optimize for p99 latency <2s
- Implement RLS for multi-tenant isolation
- Create materialized views for analytics

### Agent 5: ValidationAgent

**Input**: Generated code + test requirements
**Output**: Test suites + coverage report

Responsibilities:
- Generate unit tests (≥90% coverage)
- Generate integration tests (≥80% coverage)
- Performance benchmarks
- Block deployment if thresholds not met

### Agent 6: DeploymentOrchestrator

**Input**: Validated code + deployment manifest
**Output**: Deployed system + rollback capability

Responsibilities:
- Blue/green deployment on DigitalOcean
- Health checks before cutover
- Automatic rollback on failure
- Emit DPO/ORPO pairs for hardening

## User Stories

### Epic 1: Documentation Ingestion

**US-001**: As a platform engineer, I want to run `./scripts/docs2code ingest` to extract knowledge from all 6 documentation sources into Supabase.

**US-002**: As a compliance officer, I want all extracted business rules to cite their source documentation for audit purposes.

**US-003**: As an AI engineer, I want extracted content converted to vector embeddings for semantic search.

### Epic 2: Compliance-First Code Generation

**US-004**: As a developer, I want code generation blocked until BIR compliance validation passes.

**US-005**: As a compliance officer, I want a detailed remediation report when compliance validation fails.

**US-006**: As an architect, I want generated code to follow the 80/15/5 Odoo rule.

### Epic 3: Quality-Gated Deployment

**US-007**: As a QA engineer, I want deployment blocked when unit test coverage falls below 90%.

**US-008**: As a DevOps engineer, I want automatic rollback when health checks fail.

**US-009**: As an AI engineer, I want test failures converted to DPO pairs for agent improvement.

## Non-Functional Requirements

### Performance

| Metric | Requirement |
|--------|-------------|
| Documentation extraction | <5 min per source |
| Compliance validation | <30s per module |
| Code generation | <2 min per module |
| Deployment (blue/green) | <30s downtime |
| Database p99 latency | <2000ms |

### Security

- All credentials stored in environment variables
- RLS enabled on all Supabase tables
- No raw SQL injection vectors
- Security scan before code generation

### Scalability

- Horizontal scaling via n8n workers
- Stateless agent execution
- Supabase handles data scaling
- Docker/K8s for compute scaling

## Integration Points

| System | Integration Type | Purpose |
|--------|-----------------|---------|
| Supabase | Primary database | Knowledge base, artifacts |
| n8n | Orchestration | Workflow automation |
| DigitalOcean | Deployment | Production hosting |
| Odoo CE 18 | Target platform | Generated modules |
| ipai-agentbench | Quality loop | DPO/ORPO hardening |

## Acceptance Criteria

### Definition of Done (per agent)

- [ ] SKILL.md definition complete and approved
- [ ] Input/output schemas defined
- [ ] Unit tests passing (≥90% coverage)
- [ ] Integration tests passing (≥80% coverage)
- [ ] Performance within SLA
- [ ] Security scan passed
- [ ] Documentation complete

### Definition of Done (pipeline)

- [ ] All 6 agents operational
- [ ] End-to-end flow from docs to deployment
- [ ] Compliance validation blocking generation
- [ ] Quality gates blocking deployment
- [ ] Rollback tested and verified
- [ ] Hardening loop active
