# Bridge Kit Constitution

## Purpose

Bridge Kit enables seamless developer workflows across Claude Code CLI, Claude Desktop (MCP), Claude.ai, Chrome extensions, Google Workspace, and n8n automation—with GitHub as the version control backbone.

## Core Principles

### 1. Unified Contract First

All components communicate via a single `ContextRouterEnvelope` JSON schema. No surface-specific protocols.

### 2. Self-Hostable by Default

Every component must be deployable without cloud vendor dependencies. Commercial services are fallbacks, not requirements.

### 3. Least Privilege Auth

- User OAuth for user-initiated operations
- GitHub Apps over PATs (1hr tokens, higher rate limits)
- Service accounts only for scheduled/server-to-server operations with explicit scoping

### 4. Offline-First Resilience

Chrome extension queues failed requests locally. Sync on reconnect. Never lose user intent.

### 5. Observable by Design

Every request carries `correlationId`. All components emit structured JSON logs. Errors trigger alerts.

## Non-Negotiable Constraints

| Constraint | Rationale |
|------------|-----------|
| Chrome MV3 only | MV2 deprecated 2024; MV3 is the future |
| HMAC-signed webhooks | Prevent spoofing; simple to implement |
| n8n Fair-code license | Free for internal use; clear commercial terms |
| No secrets in code | Environment variables or vault only |
| Idempotency keys required | Enable safe retries; prevent duplicates |

## Decision Records

### DR-001: n8n over Cloud Functions

**Decision**: Use n8n as the primary automation backbone instead of Google Cloud Functions or AWS Lambda.

**Rationale**:
- Self-hostable (no vendor lock-in)
- Visual debugging (faster troubleshooting)
- 400+ integrations (Google, GitHub, Slack built-in)
- Fair-code license (free for internal use)

**Trade-offs**:
- Additional infrastructure to maintain
- Learning curve for n8n
- 100s timeout on n8n Cloud (mitigated by self-hosting)

### DR-002: MCP over Custom Protocol

**Decision**: Use Model Context Protocol (MCP) for Claude Desktop/CLI integration instead of custom REST APIs.

**Rationale**:
- Anthropic's official standard
- Consistent tool behavior across surfaces
- Growing ecosystem (1000+ community servers)
- stdio transport for local execution (no network overhead)

**Trade-offs**:
- Chrome extension requires HTTP bridge (no stdio)
- MCP spec still evolving

### DR-003: GitHub Apps over PATs

**Decision**: Use GitHub Apps for all GitHub API operations instead of Personal Access Tokens.

**Rationale**:
- 1-hour token expiry (reduced blast radius)
- 15,000 req/hr vs 5,000 req/hr
- Fine-grained permissions per repository
- Centralized webhook configuration

**Trade-offs**:
- More complex initial setup
- JWT → installation token exchange required

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Webhook latency (p50) | < 200ms | n8n execution logs |
| End-to-end GitHub issue | < 5s | Smoke test suite |
| Offline queue sync success | > 99% | Chrome extension telemetry |
| Error rate | < 0.1% | n8n error workflow |

## Governance

- **Spec changes**: Require PR with rationale
- **Breaking changes**: Major version bump + migration guide
- **Security issues**: Immediate hotfix path
