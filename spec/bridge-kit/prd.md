# Bridge Kit Product Requirements Document

## Overview

**Product**: Bridge Kit  
**Version**: 1.0.0  
**Status**: Implementation Ready  
**Owner**: InsightPulse AI Engineering  

## Problem Statement

Developers using Claude across multiple surfaces (CLI, Desktop, Web, Browser) face fragmented workflows:

1. **Context isolation**: Browser context unavailable in CLI; CLI context unavailable in browser
2. **Duplicated setup**: OAuth configured separately per tool
3. **No unified automation**: Can't trigger same workflow from browser and CLI
4. **Lost intent**: Failed actions disappear instead of queuing

## Solution

A unified "Bridge Kit" that:

1. **Captures context** from any surface (Chrome, CLI, Desktop)
2. **Routes actions** through a single n8n-based gateway
3. **Exposes MCP tools** for Claude Desktop/CLI
4. **Queues offline** and syncs on reconnect

## User Stories

### P0 - Must Have

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-001 | Developer | Create GitHub issue from selected text in browser | I can capture bugs without context switching |
| US-002 | Developer | Append notes to Google Docs from CLI | Meeting notes flow directly to shared docs |
| US-003 | Developer | Use same tools in Claude Desktop and CLI | Workflow is consistent across surfaces |
| US-004 | Developer | Have failed actions queue and retry | I don't lose work when offline |

### P1 - Should Have

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-005 | Developer | Summarize page content with Claude | I can quickly extract key points |
| US-006 | Developer | Send Slack messages from any surface | Team communication is unified |
| US-007 | Developer | Append rows to Google Sheets | Logs and tracking stay updated |

### P2 - Nice to Have

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-008 | Developer | Search Drive files semantically | I find relevant docs faster |
| US-009 | Developer | Voice capture to action | Hands-free operation |

## Functional Requirements

### FR-001: Context Capture (Chrome Extension)

| Requirement | Details |
|-------------|---------|
| Selection capture | Extract selected text and HTML |
| Page metadata | URL, title, description |
| Drive links | Extract `drive.google.com` and `docs.google.com` links |
| GitHub links | Extract `github.com` links |
| Offline queue | Store failed requests in IndexedDB |

### FR-002: Action Routing (n8n Gateway)

| Requirement | Details |
|-------------|---------|
| Webhook endpoint | `POST /webhook/bridge-router` |
| Schema validation | Reject invalid `ContextRouterEnvelope` |
| Allowlist enforcement | Only permitted actions execute |
| Action routing | Switch by `action` prefix (github.*, drive.*, etc.) |
| Idempotency | Deduplicate by `idempotencyKey` |
| Error handling | Dead-letter queue for failed actions |

### FR-003: MCP Tools (Desktop/CLI)

| Requirement | Details |
|-------------|---------|
| Tool definitions | 8 tools matching router actions |
| HTTP dispatch | POST to n8n webhook |
| HMAC signing | Sign requests with shared secret |
| Response parsing | Return structured results |

### FR-004: Auth & Security

| Requirement | Details |
|-------------|---------|
| HMAC validation | Verify `X-Signature` header |
| OAuth tokens | n8n credential store (AES-256 encrypted) |
| GitHub App | JWT → installation token flow |
| Correlation ID | `X-Request-ID` on all requests |

## Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| Performance | Webhook latency (p50) | < 200ms |
| Performance | End-to-end action | < 5s |
| Availability | n8n uptime | > 99.5% |
| Security | Token rotation | GitHub tokens < 1hr |
| Security | Secret storage | Environment variables only |
| Reliability | Offline queue | 100% local persistence |
| Observability | Log format | Structured JSON |

## Technical Stack

### Required Components

| Component | Technology | Justification |
|-----------|------------|---------------|
| Chrome Extension | MV3 + JavaScript | Browser context capture |
| n8n | Self-hosted (Docker) | Automation backbone |
| MCP Server | TypeScript + @modelcontextprotocol/sdk | Claude Desktop/CLI tools |
| Database | PostgreSQL (n8n) | Execution history |

### Optional Components

| Component | Technology | When Needed |
|-----------|------------|-------------|
| Redis | Self-hosted | Rate limiting, caching |
| Vault | HashiCorp Vault | Enterprise secret management |

## Installation Dependencies

### Install Pulser SDK

For workflow orchestration and event handling, install the Pulser SDK:

```bash
# npm
npm install @anthropic/pulser-sdk

# yarn
yarn add @anthropic/pulser-sdk

# pnpm
pnpm add @anthropic/pulser-sdk
```

### Core Dependencies

```bash
# n8n (self-hosted)
docker pull n8nio/n8n:latest

# MCP Server
cd mcp-server && npm install

# Chrome Extension
# Load unpacked from chrome-extension/ directory
```

## API Contract

### ContextRouterEnvelope

```typescript
interface ContextRouterEnvelope {
  version: "1.0.0";
  action: string;  // e.g., "github.issue_create"
  source: "chrome-extension" | "claude-code-cli" | "claude-desktop-mcp" | "apps-script" | "n8n-internal" | "api-direct";
  timestamp: string;  // ISO 8601
  idempotencyKey?: string;  // UUID v4
  correlationId?: string;
  context?: {
    url?: string;
    title?: string;
    selectedText?: string;
    selectedHtml?: string;
    driveLinks?: Array<{ href: string; text: string }>;
    githubLinks?: Array<{ href: string; text: string }>;
  };
  payload?: Record<string, unknown>;
  target?: {
    repo?: string;  // "owner/repo"
    fileId?: string;
    documentId?: string;
    spreadsheetId?: string;
    channel?: string;
  };
}
```

### ActionResult

```typescript
interface ActionResult {
  success: boolean;
  timestamp: string;
  correlationId?: string;
  idempotencyKey?: string;
  data?: Record<string, unknown>;
  error?: {
    code: string;
    message: string;
    retryable: boolean;
  };
  metadata?: {
    executionTimeMs: number;
    cached: boolean;
  };
}
```

## Acceptance Criteria

### AC-001: Context Capture

- [ ] Right-click on selection shows "Create GitHub Issue" option
- [ ] Selected text appears in issue body
- [ ] Page URL included in issue body
- [ ] Badge shows success/failure indicator

### AC-002: GitHub Integration

- [ ] Issue created within 5 seconds
- [ ] Issue has correct title and body
- [ ] Issue labeled with `bridge-kit`
- [ ] Response includes issue URL

### AC-003: Offline Queue

- [ ] Failed requests stored in IndexedDB
- [ ] Queue syncs when online
- [ ] User sees queue status in popup

### AC-004: MCP Tools

- [ ] `github_create_issue` tool available in Claude Desktop
- [ ] Tool call creates issue via n8n
- [ ] Response returned to Claude

## Out of Scope (v1.0)

- Multi-tenant workspace admin features
- Semantic search across Drive
- Voice capture and transcription
- Google Calendar integration
- Real-time collaboration features

## Timeline

| Milestone | Deliverable | Target |
|-----------|-------------|--------|
| M1 | MVP (webhook + basic extension) | 1-2 days |
| M2 | MCP integration | +2 days |
| M3 | Full n8n workflow | +3 days |
| M4 | Production hardening | +2 weeks |

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Chrome MV3 service worker termination | High | Use alarms; implement retry |
| n8n timeout on long operations | Medium | Self-host; async pattern |
| GitHub rate limiting | Medium | GitHub App; queuing |
