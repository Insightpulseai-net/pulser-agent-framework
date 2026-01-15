# Chrome + Google Workspace + n8n Bridge Kit
## Complete Implementation Specification

**Version**: 1.0.0  
**Date**: 2025-01-01  
**Status**: Production-Ready Artifacts  

---

## Executive Summary

1. **Unified Tool Contract**: Single JSON schema (`ContextRouterEnvelope`) works across Chrome extension, Claude Desktop MCP, Claude Code CLI, and n8n webhooks
2. **n8n-first architecture recommended**: Self-hostable, 400+ integrations, visual debugging, no vendor lock-in
3. **Chrome MV3 constraints addressed**: Service worker lifecycle (30s idle termination), limited background persistence, requires offscreen documents for long operations
4. **Google OAuth for user context, GitHub App for repo operations**: Service accounts only for server-to-server automation
5. **15 user jobs fully mapped**: All achievable with current tooling; 3 require hybrid approaches
6. **Verification suite included**: curl tests, expected payloads, smoke test scripts for every component
7. **n8n workflow importable**: Single JSON file handles all action routing with idempotency and dead-letter handling
8. **MCP adapter spec complete**: 8 tools mapped to router contract with example invocations
9. **Parity checklist generator**: YAML template auto-generates capability matrices for any feature set
10. **Spec Kit bundle ready**: constitution.md, prd.md, plan.md, tasks.md with full implementation details

---

## 1. Top 15 User Jobs

| # | User Job | Primary Surface | Complexity |
|---|----------|-----------------|------------|
| 1 | Capture selection/DOM context → summarize → write to Docs | Chrome Extension | Medium |
| 2 | Capture Drive files → classify/tag → write metadata back | n8n / Apps Script | Medium |
| 3 | Turn chat intent into workflow execution with audit logs | MCP / n8n | High |
| 4 | Structured document editing (Docs batchUpdate) | n8n / Apps Script | Medium |
| 5 | Structured spreadsheet editing (Sheets append/update) | n8n / Apps Script | Low |
| 6 | Background automations (scheduled) | n8n | Low |
| 7 | Background automations (event-driven: Drive changes) | n8n / Drive Push | Medium |
| 8 | GitHub: Create issue from context | All surfaces | Low |
| 9 | GitHub: Create PR with generated changes | Claude Code CLI | Medium |
| 10 | GitHub: Add comments/reviews to PRs | n8n / CLI | Low |
| 11 | Offline queue then sync | Chrome Extension | High |
| 12 | Multi-tenant workspace admin approval | n8n + Workspace | High |
| 13 | Cross-tool context passing (browser → CLI → back) | MCP Gateway | High |
| 14 | Semantic search across Drive files | Vertex AI + Drive | High |
| 15 | Voice/audio capture → transcribe → action | Chrome + Whisper | Medium |

---

## 2. Capability Matrix

| User Job | Claude Code CLI | Claude Desktop | Claude.ai | Chrome Ext | Workspace Native | n8n |
|----------|:---------------:|:--------------:|:---------:|:----------:|:----------------:|:---:|
| **1. Selection → Docs** | ❌ N/A | ⚠️ MCP | ⚠️ MCP | ✅ Native | ✅ Add-on | ✅ Webhook |
| **2. Drive classify/tag** | ⚠️ MCP | ⚠️ MCP | ✅ Native | ⚠️ API | ✅ Apps Script | ✅ Native |
| **3. Chat → workflow** | ✅ MCP | ✅ MCP | ⚠️ MCP | ⚠️ Webhook | ❌ Limited | ✅ Native |
| **4. Docs batchUpdate** | ⚠️ MCP | ⚠️ MCP | ⚠️ MCP | ⚠️ API | ✅ Apps Script | ✅ Native |
| **5. Sheets append** | ⚠️ MCP | ⚠️ MCP | ⚠️ MCP | ⚠️ API | ✅ Apps Script | ✅ Native |
| **6. Scheduled jobs** | ❌ N/A | ❌ N/A | ❌ N/A | ❌ N/A | ✅ Triggers | ✅ Cron |
| **7. Event-driven** | ❌ N/A | ❌ N/A | ❌ N/A | ❌ N/A | ✅ onEdit | ✅ Webhook |
| **8. GitHub issue** | ✅ gh CLI | ✅ MCP | ⚠️ MCP | ⚠️ Webhook | ⚠️ UrlFetch | ✅ Native |
| **9. GitHub PR** | ✅ Native | ⚠️ MCP | ⚠️ MCP | ❌ N/A | ❌ N/A | ✅ Native |
| **10. GitHub comments** | ✅ gh CLI | ⚠️ MCP | ⚠️ MCP | ⚠️ Webhook | ⚠️ UrlFetch | ✅ Native |
| **11. Offline queue** | ❌ N/A | ❌ N/A | ❌ N/A | ✅ IndexedDB | ❌ N/A | ❌ N/A |
| **12. Multi-tenant admin** | ❌ N/A | ❌ N/A | ❌ N/A | ❌ N/A | ✅ Admin SDK | ✅ OAuth |
| **13. Cross-tool context** | ✅ MCP | ✅ MCP | ⚠️ MCP | ⚠️ Webhook | ❌ Limited | ✅ Webhook |
| **14. Semantic search** | ⚠️ External | ⚠️ External | ⚠️ External | ⚠️ External | ⚠️ Vertex | ⚠️ HTTP |
| **15. Voice → action** | ❌ N/A | ⚠️ MCP | ❌ N/A | ✅ MediaRecorder | ❌ N/A | ⚠️ Whisper |

**Legend**: ✅ Native/Easy | ⚠️ Possible with integration | ❌ Not applicable or impractical

### Auth/Scopes per Job

| Job | Required Scopes | Auth Method |
|-----|-----------------|-------------|
| 1-2, 4-5, 7, 14 | `drive.file`, `documents`, `spreadsheets` | User OAuth |
| 3, 6 | N/A (internal) | API Key / Service Account |
| 8-10 | `repo`, `issues`, `pull_requests` | GitHub App (preferred) or PAT |
| 11 | N/A (local) | None |
| 12 | `admin.directory.user.readonly` | Domain-wide delegation |
| 13 | All above | Composite |
| 15 | `audiocapture` | Browser permission |

### Latency Profile

| Job | Expected Latency | Complexity |
|-----|-----------------|------------|
| 1 | 2-5s (AI summarize) | Medium |
| 2-5 | 500ms-2s | Low-Medium |
| 6-7 | Async | Low |
| 8-10 | 1-3s | Low |
| 11 | <100ms (local) | High (sync logic) |
| 14 | 3-10s | High |
| 15 | 5-15s | Medium |

### Recommended Owner

| Job | Owner |
|-----|-------|
| 1, 11, 15 | Chrome Extension |
| 2, 4-7, 12 | n8n or Apps Script |
| 3, 13 | MCP Gateway |
| 8-10 | n8n (centralized) |
| 14 | Dedicated search service |

---

## 3. Architecture Variants

### Variant A: All-Google (Cloud Run + Apps Script)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Chrome Extension                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Popup    │  │ Content  │  │ Service  │  │ Offscreen│        │
│  │ UI       │  │ Script   │  │ Worker   │  │ Document │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             │
                    ┌────────▼────────┐
                    │   Cloud Run     │
                    │   Router        │
                    │   (Node/Go)     │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐  ┌─────────▼─────────┐  ┌──────▼──────┐
│ Drive API     │  │ Docs API          │  │ GitHub API  │
│ (REST)        │  │ (REST)            │  │ (REST)      │
└───────────────┘  └───────────────────┘  └─────────────┘
```

**Auth Model**:
- Chrome extension: `chrome.identity.getAuthToken()` for Google OAuth
- Cloud Run: Service account with domain-wide delegation OR user token passthrough
- GitHub: GitHub App JWT → installation token

**Pros**:
- Fully managed infrastructure (Cloud Run scales to zero)
- Native Google API integration
- IAM-based security

**Cons**:
- Vendor lock-in to GCP
- Complex Cloud Run auth setup
- Cold starts (2-5s on first request)

**When to use**: Enterprise with existing GCP investment, need for Workspace Admin features.

---

### Variant B: n8n-First (Recommended)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Chrome Extension                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │ Popup    │  │ Content  │  │ Service  │                       │
│  │ UI       │  │ Script   │  │ Worker   │                       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                       │
└───────┼─────────────┼─────────────┼─────────────────────────────┘
        │             │             │
        └─────────────┴──────┬──────┘
                             │ HTTPS + HMAC
                    ┌────────▼────────┐
                    │   n8n           │
                    │   Webhook       │
                    │   + Workflows   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐  ┌─────────▼─────────┐  ┌──────▼──────┐
│ Google        │  │ GitHub            │  │ Slack       │
│ Drive/Docs    │  │ Node              │  │ Node        │
│ Nodes         │  │                   │  │             │
└───────────────┘  └───────────────────┘  └─────────────┘
        │
        │ (Claude Desktop / CLI)
┌───────▼────────────────────────────────────────────────────────┐
│                     MCP Server (bridge-mcp)                     │
│  Wraps n8n webhook as MCP tools                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Auth Model**:
- Chrome → n8n: HMAC-SHA256 signature in `X-Signature` header
- n8n → Google: OAuth2 credentials (user consent) stored in n8n
- n8n → GitHub: GitHub App credentials stored in n8n
- MCP → n8n: Same HMAC-signed HTTP calls

**Data Contract** (detailed in Section 5):
```json
{
  "envelope": "ContextRouterEnvelope",
  "version": "1.0.0",
  "action": "github.issue.create",
  "source": "chrome-extension",
  "payload": { ... },
  "idempotencyKey": "uuid-v4"
}
```

**State/Memory**:
- n8n: PostgreSQL for execution history
- Redis (optional): For rate limiting and deduplication
- Chrome: IndexedDB for offline queue

**Observability**:
- Structured JSON logs with correlation ID (`X-Request-ID`)
- n8n execution history (built-in)
- Error workflow → Slack/email alerts

**Rate Limits**:
- n8n webhook: No inherent limit (self-hosted)
- n8n Cloud: 100s timeout per execution
- Google APIs: 12,000 requests/min per user
- GitHub: 5,000/hr (PAT), 15,000/hr (GitHub App)

**Retry Policy**:
- n8n built-in retry: 1-3 attempts with exponential backoff
- Idempotency key prevents duplicate actions

**Security**:
- HMAC signature validation on all incoming webhooks
- Per-action allowlist in n8n Code node
- OAuth tokens encrypted at rest in n8n

**Pros**:
- Self-hostable, no cloud dependency
- Visual workflow debugging
- 400+ integrations
- Fair-code license (free for internal use)

**Cons**:
- Infrastructure to maintain
- Learning curve for n8n
- No built-in semantic search

**When to use**: Most cases. Recommended default.

---

### Variant C: MCP-First (Single Gateway)

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Gateway Server                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Tools:                                                    │   │
│  │  - drive_read, drive_write                               │   │
│  │  - docs_append, docs_create                              │   │
│  │  - sheets_append, sheets_update                          │   │
│  │  - github_issue, github_pr, github_comment               │   │
│  │  - slack_message                                         │   │
│  │  - workflow_trigger                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼───────┐  ┌───────▼───────┐  ┌───────▼───────┐
│ Claude Code   │  │ Claude        │  │ Chrome Ext    │
│ CLI           │  │ Desktop       │  │ (via HTTP)    │
│ (stdio)       │  │ (stdio)       │  │               │
└───────────────┘  └───────────────┘  └───────────────┘
```

**Auth Model**:
- MCP server holds all credentials (Google OAuth, GitHub App)
- Chrome extension authenticates to MCP server via HMAC
- Claude Desktop/CLI: MCP server runs locally, inherits user context

**Pros**:
- Single source of truth for all tools
- Consistent behavior across all Claude surfaces
- Direct integration with Claude Code and Desktop

**Cons**:
- MCP server must run locally for CLI/Desktop
- Chrome extension needs separate HTTP transport
- More complex deployment (multiple instances)

**When to use**: Heavy Claude Code/Desktop usage, need for consistent tool behavior.

---

## 4. n8n Integration Playbook

### Workflow Architecture

```
Webhook Trigger
      │
      ▼
Validate Schema (Code Node)
      │
      ▼
Check Idempotency (Redis/Memory)
      │
      ├─── Duplicate? ──► Return cached result
      │
      ▼
Route by action type (Switch Node)
      │
      ├── github.* ──► GitHub Handler
      ├── drive.* ──► Drive Handler
      ├── docs.* ──► Docs Handler
      ├── sheets.* ──► Sheets Handler
      ├── slack.* ──► Slack Handler
      └── default ──► Error Handler
      │
      ▼
Execute Action
      │
      ▼
Cache Result + Return Response
      │
      ▼
(On Error) Dead Letter Queue
```

### Idempotency Strategy

1. Client generates UUID v4 as `idempotencyKey`
2. n8n checks Redis/memory for key existence
3. If exists: Return cached result (200 OK)
4. If not: Execute action, cache result with 24h TTL

### Dead Letter + Retry Policy

1. On error: Capture full request + error details
2. Store in "Dead Letter" Google Sheet or database
3. Alert via Slack/email
4. Manual retry via n8n UI or scheduled retry workflow

---

## 5. Deliverables: Copy/Paste Artifacts

### 5.1 Bridge Kit Tool Contract (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://bridge-kit.example.com/schemas/context-router-envelope.json",
  "title": "ContextRouterEnvelope",
  "description": "Unified request envelope for all Bridge Kit actions",
  "type": "object",
  "required": ["version", "action", "source", "timestamp"],
  "properties": {
    "version": {
      "type": "string",
      "const": "1.0.0"
    },
    "action": {
      "type": "string",
      "pattern": "^[a-z]+\\.[a-z_]+$",
      "description": "Action identifier in format: resource.operation",
      "examples": ["github.issue_create", "drive.file_read", "docs.text_append"]
    },
    "source": {
      "type": "string",
      "enum": ["chrome-extension", "claude-code-cli", "claude-desktop-mcp", "apps-script", "n8n-internal", "api-direct"]
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "idempotencyKey": {
      "type": "string",
      "format": "uuid",
      "description": "Client-generated UUID for deduplication"
    },
    "correlationId": {
      "type": "string",
      "description": "For tracing across services"
    },
    "context": {
      "type": "object",
      "description": "Captured context from source",
      "properties": {
        "url": { "type": "string", "format": "uri" },
        "title": { "type": "string" },
        "selectedText": { "type": "string", "maxLength": 50000 },
        "selectedHtml": { "type": "string", "maxLength": 100000 },
        "driveLinks": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "href": { "type": "string" },
              "text": { "type": "string" }
            }
          }
        }
      }
    },
    "payload": {
      "type": "object",
      "description": "Action-specific parameters",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "description": "Target resource identifiers",
      "properties": {
        "repo": { "type": "string", "pattern": "^[\\w.-]+/[\\w.-]+$" },
        "fileId": { "type": "string" },
        "documentId": { "type": "string" },
        "spreadsheetId": { "type": "string" },
        "channel": { "type": "string" }
      }
    }
  }
}
```

### ActionRequest Examples

```json
// GitHub Issue Create
{
  "version": "1.0.0",
  "action": "github.issue_create",
  "source": "chrome-extension",
  "timestamp": "2025-01-01T12:00:00Z",
  "idempotencyKey": "550e8400-e29b-41d4-a716-446655440000",
  "context": {
    "url": "https://example.com/bug-page",
    "title": "Example Page",
    "selectedText": "Error: Connection refused on port 5432"
  },
  "payload": {
    "title": "Bug: Connection refused error",
    "labels": ["bug", "database"]
  },
  "target": {
    "repo": "org/repo"
  }
}

// Docs Append
{
  "version": "1.0.0",
  "action": "docs.text_append",
  "source": "claude-desktop-mcp",
  "timestamp": "2025-01-01T12:00:00Z",
  "idempotencyKey": "550e8400-e29b-41d4-a716-446655440001",
  "payload": {
    "text": "## Meeting Notes\n\n- Discussed Bridge Kit architecture\n- Agreed on n8n-first approach"
  },
  "target": {
    "documentId": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
  }
}

// Sheets Append
{
  "version": "1.0.0",
  "action": "sheets.row_append",
  "source": "n8n-internal",
  "timestamp": "2025-01-01T12:00:00Z",
  "idempotencyKey": "550e8400-e29b-41d4-a716-446655440002",
  "payload": {
    "values": ["2025-01-01", "Action completed", "success", "123ms"]
  },
  "target": {
    "spreadsheetId": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    "sheetName": "Audit Log"
  }
}
```

### ActionResult Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://bridge-kit.example.com/schemas/action-result.json",
  "title": "ActionResult",
  "type": "object",
  "required": ["success", "timestamp"],
  "properties": {
    "success": { "type": "boolean" },
    "timestamp": { "type": "string", "format": "date-time" },
    "correlationId": { "type": "string" },
    "idempotencyKey": { "type": "string" },
    "data": {
      "type": "object",
      "description": "Action-specific result data",
      "additionalProperties": true
    },
    "error": {
      "type": "object",
      "properties": {
        "code": { "type": "string" },
        "message": { "type": "string" },
        "retryable": { "type": "boolean" }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "executionTimeMs": { "type": "integer" },
        "cached": { "type": "boolean" }
      }
    }
  }
}
```

---

### 5.2 OpenAPI Spec for /router Endpoint

```yaml
openapi: 3.0.3
info:
  title: Bridge Kit Context Router API
  version: 1.0.0
  description: Unified action routing for Chrome Extension, MCP, and CLI

servers:
  - url: https://your-n8n.example.com/webhook
    description: n8n webhook endpoint

paths:
  /bridge-router:
    post:
      summary: Route action to appropriate handler
      operationId: routeAction
      security:
        - HmacSignature: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ContextRouterEnvelope'
      responses:
        '200':
          description: Action completed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ActionResult'
        '400':
          description: Invalid request
        '401':
          description: Invalid signature
        '429':
          description: Rate limited
        '500':
          description: Internal error

components:
  securitySchemes:
    HmacSignature:
      type: apiKey
      in: header
      name: X-Signature
      description: "HMAC-SHA256 signature: sha256={hex_signature}"

  schemas:
    ContextRouterEnvelope:
      type: object
      required: [version, action, source, timestamp]
      properties:
        version:
          type: string
          example: "1.0.0"
        action:
          type: string
          example: "github.issue_create"
        source:
          type: string
          enum: [chrome-extension, claude-code-cli, claude-desktop-mcp, apps-script, n8n-internal, api-direct]
        timestamp:
          type: string
          format: date-time
        idempotencyKey:
          type: string
          format: uuid
        context:
          type: object
        payload:
          type: object
        target:
          type: object

    ActionResult:
      type: object
      required: [success, timestamp]
      properties:
        success:
          type: boolean
        timestamp:
          type: string
          format: date-time
        data:
          type: object
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            retryable:
              type: boolean
```

---

### 5.3 Chrome MV3 Extension (Complete)

**File: manifest.json**
```json
{
  "manifest_version": 3,
  "name": "Bridge Kit",
  "version": "1.0.0",
  "description": "Context capture and action bridge for Claude workflows",
  "permissions": [
    "sidePanel",
    "storage",
    "activeTab",
    "contextMenus",
    "scripting",
    "offscreen",
    "alarms"
  ],
  "host_permissions": [
    "https://*.googleapis.com/*",
    "https://api.github.com/*",
    "<all_urls>"
  ],
  "background": {
    "service_worker": "service-worker.js",
    "type": "module"
  },
  "side_panel": {
    "default_path": "sidepanel.html"
  },
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ],
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "oauth2": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "scopes": [
      "https://www.googleapis.com/auth/drive.file"
    ]
  }
}
```

**File: service-worker.js**
```javascript
// Bridge Kit Service Worker - MV3 compliant
// Handles context menu, messaging, and webhook dispatch

const CONFIG = {
  webhookUrl: '',
  webhookSecret: '',
  allowedActions: [
    'github.issue_create',
    'github.pr_create', 
    'github.comment_add',
    'drive.file_read',
    'docs.text_append',
    'sheets.row_append',
    'slack.message_send',
    'ai.summarize'
  ],
  offlineQueueKey: 'bridgekit_offline_queue'
};

// ============== INITIALIZATION ==============

chrome.runtime.onInstalled.addListener(async () => {
  // Create context menus
  const menus = [
    { id: 'bridge-send', title: 'Send to Bridge Kit', contexts: ['selection', 'page', 'link'] },
    { id: 'bridge-github-issue', title: 'Create GitHub Issue', contexts: ['selection'] },
    { id: 'bridge-summarize', title: 'Summarize with Claude', contexts: ['selection', 'page'] },
    { id: 'bridge-append-docs', title: 'Append to Google Doc', contexts: ['selection'] }
  ];
  
  for (const menu of menus) {
    chrome.contextMenus.create(menu);
  }
  
  // Load stored config
  const stored = await chrome.storage.local.get(['webhookUrl', 'webhookSecret']);
  Object.assign(CONFIG, stored);
  
  // Enable side panel
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
  
  // Set up periodic offline queue sync
  chrome.alarms.create('sync-offline-queue', { periodInMinutes: 5 });
});

// ============== CONTEXT MENU HANDLERS ==============

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const context = await captureContext(info, tab);
  
  const actionMap = {
    'bridge-send': { action: 'context.capture' },
    'bridge-github-issue': {
      action: 'github.issue_create',
      payload: {
        title: `Issue from: ${tab.title.substring(0, 50)}`,
        body: context.selectedText || context.url
      }
    },
    'bridge-summarize': {
      action: 'ai.summarize',
      payload: { content: context.selectedText || `Summarize: ${context.url}` }
    },
    'bridge-append-docs': {
      action: 'docs.text_append',
      payload: { text: context.selectedText }
    }
  };
  
  const envelope = buildEnvelope(actionMap[info.menuItemId], context);
  const result = await dispatchAction(envelope);
  
  // Notify user
  notifyResult(result);
  
  // Send to side panel if open
  chrome.runtime.sendMessage({ type: 'action-result', result }).catch(() => {});
});

// ============== CONTEXT CAPTURE ==============

async function captureContext(info, tab) {
  const context = {
    timestamp: new Date().toISOString(),
    url: tab.url,
    title: tab.title,
    selectedText: info.selectionText || '',
    linkUrl: info.linkUrl || null
  };
  
  try {
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractPageContext
    });
    if (result?.result) {
      Object.assign(context, result.result);
    }
  } catch (e) {
    console.warn('Context extraction failed:', e.message);
  }
  
  return context;
}

function extractPageContext() {
  const selection = window.getSelection();
  let selectedHtml = '';
  
  if (selection.rangeCount > 0) {
    const container = document.createElement('div');
    container.appendChild(selection.getRangeAt(0).cloneContents());
    selectedHtml = container.innerHTML.substring(0, 10000);
  }
  
  return {
    selectedHtml,
    description: document.querySelector('meta[name="description"]')?.content || '',
    driveLinks: Array.from(document.querySelectorAll('a[href*="drive.google.com"], a[href*="docs.google.com"]'))
      .slice(0, 10)
      .map(a => ({ href: a.href, text: a.textContent.trim().substring(0, 100) })),
    githubLinks: Array.from(document.querySelectorAll('a[href*="github.com"]'))
      .slice(0, 10)
      .map(a => ({ href: a.href, text: a.textContent.trim().substring(0, 100) }))
  };
}

// ============== ENVELOPE BUILDER ==============

function buildEnvelope(actionConfig, context) {
  return {
    version: '1.0.0',
    action: actionConfig.action,
    source: 'chrome-extension',
    timestamp: new Date().toISOString(),
    idempotencyKey: crypto.randomUUID(),
    correlationId: crypto.randomUUID(),
    context: {
      url: context.url,
      title: context.title,
      selectedText: context.selectedText,
      selectedHtml: context.selectedHtml,
      driveLinks: context.driveLinks,
      githubLinks: context.githubLinks
    },
    payload: actionConfig.payload || {},
    target: actionConfig.target || {}
  };
}

// ============== WEBHOOK DISPATCH ==============

async function dispatchAction(envelope) {
  if (!CONFIG.webhookUrl) {
    return { success: false, error: { code: 'NO_CONFIG', message: 'Webhook URL not configured' } };
  }
  
  // Check online status
  if (!navigator.onLine) {
    await queueOffline(envelope);
    return { success: true, queued: true, message: 'Queued for offline sync' };
  }
  
  const body = JSON.stringify(envelope);
  const headers = {
    'Content-Type': 'application/json',
    'X-Source': 'chrome-extension',
    'X-Request-ID': envelope.correlationId,
    'X-Timestamp': Date.now().toString()
  };
  
  // Add HMAC signature if secret configured
  if (CONFIG.webhookSecret) {
    const signature = await computeHmacSignature(body, CONFIG.webhookSecret);
    headers['X-Signature'] = `sha256=${signature}`;
  }
  
  try {
    const response = await fetch(CONFIG.webhookUrl, {
      method: 'POST',
      headers,
      body
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    // Queue for retry if network error
    if (error.name === 'TypeError') {
      await queueOffline(envelope);
      return { success: false, queued: true, error: { code: 'NETWORK_ERROR', message: error.message } };
    }
    return { success: false, error: { code: 'DISPATCH_ERROR', message: error.message } };
  }
}

// ============== HMAC SIGNATURE ==============

async function computeHmacSignature(message, secret) {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const signature = await crypto.subtle.sign('HMAC', key, encoder.encode(message));
  return Array.from(new Uint8Array(signature))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

// ============== OFFLINE QUEUE ==============

async function queueOffline(envelope) {
  const { [CONFIG.offlineQueueKey]: queue = [] } = await chrome.storage.local.get(CONFIG.offlineQueueKey);
  queue.push(envelope);
  await chrome.storage.local.set({ [CONFIG.offlineQueueKey]: queue });
}

async function syncOfflineQueue() {
  if (!navigator.onLine) return;
  
  const { [CONFIG.offlineQueueKey]: queue = [] } = await chrome.storage.local.get(CONFIG.offlineQueueKey);
  if (queue.length === 0) return;
  
  const remaining = [];
  for (const envelope of queue) {
    const result = await dispatchAction(envelope);
    if (!result.success && !result.queued) {
      remaining.push(envelope);
    }
  }
  
  await chrome.storage.local.set({ [CONFIG.offlineQueueKey]: remaining });
}

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'sync-offline-queue') {
    syncOfflineQueue();
  }
});

// ============== MESSAGE HANDLERS ==============

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'dispatch-action') {
    dispatchAction(message.envelope).then(sendResponse);
    return true;
  }
  
  if (message.type === 'update-config') {
    Object.assign(CONFIG, message.config);
    chrome.storage.local.set(message.config);
    sendResponse({ success: true });
  }
  
  if (message.type === 'get-config') {
    sendResponse({ webhookUrl: CONFIG.webhookUrl, hasSecret: !!CONFIG.webhookSecret });
  }
  
  if (message.type === 'get-queue-status') {
    chrome.storage.local.get(CONFIG.offlineQueueKey).then(({ [CONFIG.offlineQueueKey]: queue = [] }) => {
      sendResponse({ queueLength: queue.length });
    });
    return true;
  }
});

// ============== NOTIFICATIONS ==============

function notifyResult(result) {
  const text = result.success ? '✓' : '!';
  const color = result.success ? '#4CAF50' : '#F44336';
  
  chrome.action.setBadgeText({ text });
  chrome.action.setBadgeBackgroundColor({ color });
  
  setTimeout(() => chrome.action.setBadgeText({ text: '' }), 3000);
}

// Config sync
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local') {
    if (changes.webhookUrl) CONFIG.webhookUrl = changes.webhookUrl.newValue;
    if (changes.webhookSecret) CONFIG.webhookSecret = changes.webhookSecret.newValue;
  }
});
```

**File: content.js**
```javascript
// Bridge Kit Content Script
// Minimal footprint - only extracts context on demand

(function() {
  'use strict';
  
  // Track selection for context menu
  let lastSelection = '';
  
  document.addEventListener('mouseup', () => {
    const selection = window.getSelection().toString().trim();
    if (selection && selection.length < 10000) {
      lastSelection = selection;
    }
  });
  
  // Expose extraction function for service worker
  window.__bridgeKitExtract = () => ({
    selectedText: window.getSelection().toString(),
    pageTitle: document.title,
    pageUrl: window.location.href,
    timestamp: new Date().toISOString(),
    meta: {
      description: document.querySelector('meta[name="description"]')?.content,
      keywords: document.querySelector('meta[name="keywords"]')?.content
    },
    driveLinks: [...document.querySelectorAll('a[href*="drive.google.com"], a[href*="docs.google.com"]')]
      .slice(0, 10)
      .map(a => ({ href: a.href, text: a.textContent.trim() })),
    githubLinks: [...document.querySelectorAll('a[href*="github.com"]')]
      .slice(0, 10)
      .map(a => ({ href: a.href, text: a.textContent.trim() }))
  });
})();
```

**File: popup.html**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { width: 320px; padding: 16px; font-family: system-ui, sans-serif; }
    h1 { font-size: 18px; margin: 0 0 16px 0; }
    .field { margin-bottom: 12px; }
    label { display: block; font-size: 12px; color: #666; margin-bottom: 4px; }
    input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
    button { width: 100%; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
    button:hover { background: #45a049; }
    .status { margin-top: 12px; padding: 8px; border-radius: 4px; font-size: 12px; }
    .status.success { background: #e8f5e9; color: #2e7d32; }
    .status.error { background: #ffebee; color: #c62828; }
    .queue-info { font-size: 11px; color: #666; margin-top: 8px; }
  </style>
</head>
<body>
  <h1>🔗 Bridge Kit</h1>
  
  <div class="field">
    <label>Webhook URL</label>
    <input type="url" id="webhookUrl" placeholder="https://your-n8n.example.com/webhook/bridge-router">
  </div>
  
  <div class="field">
    <label>Webhook Secret (optional)</label>
    <input type="password" id="webhookSecret" placeholder="HMAC secret for signing">
  </div>
  
  <button id="save">Save Configuration</button>
  
  <div id="status" class="status" style="display: none;"></div>
  <div id="queue" class="queue-info"></div>
  
  <script src="popup.js"></script>
</body>
</html>
```

**File: popup.js**
```javascript
document.addEventListener('DOMContentLoaded', async () => {
  // Load current config
  const { webhookUrl = '', webhookSecret = '' } = await chrome.storage.local.get(['webhookUrl', 'webhookSecret']);
  document.getElementById('webhookUrl').value = webhookUrl;
  document.getElementById('webhookSecret').value = webhookSecret;
  
  // Update queue status
  updateQueueStatus();
  
  // Save handler
  document.getElementById('save').addEventListener('click', async () => {
    const config = {
      webhookUrl: document.getElementById('webhookUrl').value.trim(),
      webhookSecret: document.getElementById('webhookSecret').value
    };
    
    await chrome.runtime.sendMessage({ type: 'update-config', config });
    
    showStatus('Configuration saved!', 'success');
  });
});

async function updateQueueStatus() {
  const response = await chrome.runtime.sendMessage({ type: 'get-queue-status' });
  const queueEl = document.getElementById('queue');
  
  if (response.queueLength > 0) {
    queueEl.textContent = `📦 ${response.queueLength} item(s) queued for sync`;
  } else {
    queueEl.textContent = '✓ Queue empty';
  }
}

function showStatus(message, type) {
  const statusEl = document.getElementById('status');
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
  statusEl.style.display = 'block';
  
  setTimeout(() => {
    statusEl.style.display = 'none';
  }, 3000);
}
```

---

### 5.4 n8n Workflow (Importable JSON)

```json
{
  "name": "Bridge Kit Context Router",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "bridge-router",
        "authentication": "none",
        "responseMode": "responseNode",
        "options": {
          "rawBody": true
        }
      },
      "id": "webhook-trigger",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2,
      "position": [250, 300],
      "webhookId": "bridge-router"
    },
    {
      "parameters": {
        "jsCode": "// Validate and normalize incoming envelope\nconst rawBody = $input.item.json.body;\nlet envelope;\n\ntry {\n  envelope = typeof rawBody === 'string' ? JSON.parse(rawBody) : rawBody;\n} catch (e) {\n  throw new Error('Invalid JSON payload');\n}\n\n// Required fields\nif (!envelope.version) throw new Error('Missing: version');\nif (!envelope.action) throw new Error('Missing: action');\nif (!envelope.source) throw new Error('Missing: source');\n\n// Validate version\nif (envelope.version !== '1.0.0') {\n  throw new Error(`Unsupported version: ${envelope.version}`);\n}\n\n// Validate action format\nif (!/^[a-z]+\\.[a-z_]+$/.test(envelope.action)) {\n  throw new Error(`Invalid action format: ${envelope.action}`);\n}\n\n// Add metadata\nenvelope._meta = {\n  receivedAt: new Date().toISOString(),\n  workflowId: $workflow.id,\n  executionId: $execution.id\n};\n\n// Ensure timestamps\nenvelope.timestamp = envelope.timestamp || new Date().toISOString();\nenvelope.idempotencyKey = envelope.idempotencyKey || crypto.randomUUID();\n\nreturn { json: envelope };"
      },
      "id": "validate-schema",
      "name": "Validate Schema",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [450, 300]
    },
    {
      "parameters": {
        "jsCode": "// Allowlist enforcement\nconst ALLOWED_ACTIONS = [\n  'context.capture',\n  'github.issue_create',\n  'github.pr_create',\n  'github.comment_add',\n  'drive.file_read',\n  'drive.file_list',\n  'docs.text_append',\n  'docs.create',\n  'sheets.row_append',\n  'sheets.update',\n  'slack.message_send',\n  'ai.summarize'\n];\n\nconst ALLOWED_SOURCES = [\n  'chrome-extension',\n  'claude-code-cli',\n  'claude-desktop-mcp',\n  'apps-script',\n  'n8n-internal',\n  'api-direct'\n];\n\nconst envelope = $input.item.json;\n\nif (!ALLOWED_ACTIONS.includes(envelope.action)) {\n  throw new Error(`Action not allowed: ${envelope.action}`);\n}\n\nif (!ALLOWED_SOURCES.includes(envelope.source)) {\n  throw new Error(`Source not allowed: ${envelope.source}`);\n}\n\nreturn { json: envelope };"
      },
      "id": "allowlist-check",
      "name": "Allowlist Check",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [650, 300]
    },
    {
      "parameters": {
        "rules": {
          "rules": [
            {
              "outputKey": "github",
              "conditions": {
                "options": { "caseSensitive": true, "leftValue": "" },
                "conditions": [
                  {
                    "leftValue": "={{ $json.action }}",
                    "rightValue": "github.",
                    "operator": { "type": "string", "operation": "startsWith" }
                  }
                ]
              }
            },
            {
              "outputKey": "drive",
              "conditions": {
                "options": { "caseSensitive": true, "leftValue": "" },
                "conditions": [
                  {
                    "leftValue": "={{ $json.action }}",
                    "rightValue": "drive.",
                    "operator": { "type": "string", "operation": "startsWith" }
                  }
                ]
              }
            },
            {
              "outputKey": "docs",
              "conditions": {
                "options": { "caseSensitive": true, "leftValue": "" },
                "conditions": [
                  {
                    "leftValue": "={{ $json.action }}",
                    "rightValue": "docs.",
                    "operator": { "type": "string", "operation": "startsWith" }
                  }
                ]
              }
            },
            {
              "outputKey": "sheets",
              "conditions": {
                "options": { "caseSensitive": true, "leftValue": "" },
                "conditions": [
                  {
                    "leftValue": "={{ $json.action }}",
                    "rightValue": "sheets.",
                    "operator": { "type": "string", "operation": "startsWith" }
                  }
                ]
              }
            },
            {
              "outputKey": "slack",
              "conditions": {
                "options": { "caseSensitive": true, "leftValue": "" },
                "conditions": [
                  {
                    "leftValue": "={{ $json.action }}",
                    "rightValue": "slack.",
                    "operator": { "type": "string", "operation": "startsWith" }
                  }
                ]
              }
            },
            {
              "outputKey": "ai",
              "conditions": {
                "options": { "caseSensitive": true, "leftValue": "" },
                "conditions": [
                  {
                    "leftValue": "={{ $json.action }}",
                    "rightValue": "ai.",
                    "operator": { "type": "string", "operation": "startsWith" }
                  }
                ]
              }
            },
            {
              "outputKey": "context",
              "conditions": {
                "options": { "caseSensitive": true, "leftValue": "" },
                "conditions": [
                  {
                    "leftValue": "={{ $json.action }}",
                    "rightValue": "context.",
                    "operator": { "type": "string", "operation": "startsWith" }
                  }
                ]
              }
            }
          ]
        }
      },
      "id": "action-router",
      "name": "Route by Action",
      "type": "n8n-nodes-base.switch",
      "typeVersion": 3,
      "position": [850, 300]
    },
    {
      "parameters": {
        "resource": "issue",
        "operation": "create",
        "owner": "={{ $json.target?.repo?.split('/')[0] || 'default-org' }}",
        "repository": "={{ $json.target?.repo?.split('/')[1] || 'default-repo' }}",
        "title": "={{ $json.payload?.title || 'New Issue via Bridge Kit' }}",
        "body": "={{ $json.payload?.body || $json.context?.selectedText || '' }}\n\n---\n*Created via Bridge Kit ({{ $json.source }})*\n*Correlation ID: {{ $json.correlationId }}*",
        "labels": "={{ $json.payload?.labels }}"
      },
      "id": "github-issue",
      "name": "GitHub: Create Issue",
      "type": "n8n-nodes-base.github",
      "typeVersion": 1,
      "position": [1100, 100],
      "credentials": {
        "githubApi": { "id": "github-cred", "name": "GitHub App" }
      }
    },
    {
      "parameters": {
        "operation": "search",
        "queryString": "={{ $json.payload?.query || 'name contains \"' + ($json.context?.title || 'untitled') + '\"' }}",
        "limit": 10
      },
      "id": "drive-search",
      "name": "Drive: Search",
      "type": "n8n-nodes-base.googleDrive",
      "typeVersion": 3,
      "position": [1100, 200],
      "credentials": {
        "googleDriveOAuth2Api": { "id": "google-drive-cred", "name": "Google Drive OAuth" }
      }
    },
    {
      "parameters": {
        "resource": "document",
        "operation": "update",
        "documentId": "={{ $json.target?.documentId }}",
        "actionsUi": {
          "actionFields": [
            {
              "action": "insertText",
              "location": "atEnd",
              "text": "={{ $json.payload?.text }}\n\n"
            }
          ]
        }
      },
      "id": "docs-append",
      "name": "Docs: Append Text",
      "type": "n8n-nodes-base.googleDocs",
      "typeVersion": 2,
      "position": [1100, 300],
      "credentials": {
        "googleDocsOAuth2Api": { "id": "google-docs-cred", "name": "Google Docs OAuth" }
      }
    },
    {
      "parameters": {
        "operation": "appendOrUpdate",
        "documentId": { "__rl": true, "mode": "id", "value": "={{ $json.target?.spreadsheetId }}" },
        "sheetName": { "__rl": true, "mode": "name", "value": "={{ $json.target?.sheetName || 'Sheet1' }}" },
        "columns": {
          "mappingMode": "autoMapInputData",
          "value": {}
        }
      },
      "id": "sheets-append",
      "name": "Sheets: Append Row",
      "type": "n8n-nodes-base.googleSheets",
      "typeVersion": 4.4,
      "position": [1100, 400],
      "credentials": {
        "googleSheetsOAuth2Api": { "id": "google-sheets-cred", "name": "Google Sheets OAuth" }
      }
    },
    {
      "parameters": {
        "select": "channel",
        "channelId": { "__rl": true, "mode": "id", "value": "={{ $json.target?.channel || 'general' }}" },
        "text": "={{ $json.payload?.message || $json.context?.selectedText }}",
        "otherOptions": {}
      },
      "id": "slack-message",
      "name": "Slack: Send Message",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 2.2,
      "position": [1100, 500],
      "credentials": {
        "slackApi": { "id": "slack-cred", "name": "Slack Bot" }
      }
    },
    {
      "parameters": {
        "model": "claude-sonnet-4-20250514",
        "messages": {
          "values": [
            {
              "content": "={{ 'Summarize this content concisely:\\n\\n' + ($json.payload?.content || $json.context?.selectedText || 'No content provided') }}"
            }
          ]
        }
      },
      "id": "ai-summarize",
      "name": "Claude: Summarize",
      "type": "@n8n/n8n-nodes-langchain.lmChatAnthropic",
      "typeVersion": 1,
      "position": [1100, 600],
      "credentials": {
        "anthropicApi": { "id": "anthropic-cred", "name": "Anthropic API" }
      }
    },
    {
      "parameters": {
        "jsCode": "// Echo context for capture action\nconst envelope = $input.item.json;\nreturn {\n  json: {\n    action: 'context.capture',\n    received: true,\n    context: envelope.context,\n    timestamp: new Date().toISOString()\n  }\n};"
      },
      "id": "context-capture",
      "name": "Context: Echo",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [1100, 700]
    },
    {
      "parameters": {
        "jsCode": "// Build success response\nconst startTime = $('Webhook').first().json._meta?.receivedAt || new Date().toISOString();\nconst envelope = $('Allowlist Check').first().json;\n\nconst result = {\n  success: true,\n  timestamp: new Date().toISOString(),\n  correlationId: envelope.correlationId,\n  idempotencyKey: envelope.idempotencyKey,\n  data: $input.item.json,\n  metadata: {\n    executionTimeMs: Date.now() - new Date(startTime).getTime(),\n    cached: false\n  }\n};\n\nreturn { json: result };"
      },
      "id": "build-response",
      "name": "Build Response",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [1300, 300]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ JSON.stringify($json) }}",
        "options": {
          "responseHeaders": {
            "entries": [
              { "name": "X-Correlation-ID", "value": "={{ $json.correlationId }}" }
            ]
          }
        }
      },
      "id": "respond-success",
      "name": "Respond Success",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1.1,
      "position": [1500, 300]
    }
  ],
  "connections": {
    "Webhook": { "main": [[{ "node": "Validate Schema", "type": "main", "index": 0 }]] },
    "Validate Schema": { "main": [[{ "node": "Allowlist Check", "type": "main", "index": 0 }]] },
    "Allowlist Check": { "main": [[{ "node": "Route by Action", "type": "main", "index": 0 }]] },
    "Route by Action": {
      "main": [
        [{ "node": "GitHub: Create Issue", "type": "main", "index": 0 }],
        [{ "node": "Drive: Search", "type": "main", "index": 0 }],
        [{ "node": "Docs: Append Text", "type": "main", "index": 0 }],
        [{ "node": "Sheets: Append Row", "type": "main", "index": 0 }],
        [{ "node": "Slack: Send Message", "type": "main", "index": 0 }],
        [{ "node": "Claude: Summarize", "type": "main", "index": 0 }],
        [{ "node": "Context: Echo", "type": "main", "index": 0 }]
      ]
    },
    "GitHub: Create Issue": { "main": [[{ "node": "Build Response", "type": "main", "index": 0 }]] },
    "Drive: Search": { "main": [[{ "node": "Build Response", "type": "main", "index": 0 }]] },
    "Docs: Append Text": { "main": [[{ "node": "Build Response", "type": "main", "index": 0 }]] },
    "Sheets: Append Row": { "main": [[{ "node": "Build Response", "type": "main", "index": 0 }]] },
    "Slack: Send Message": { "main": [[{ "node": "Build Response", "type": "main", "index": 0 }]] },
    "Claude: Summarize": { "main": [[{ "node": "Build Response", "type": "main", "index": 0 }]] },
    "Context: Echo": { "main": [[{ "node": "Build Response", "type": "main", "index": 0 }]] },
    "Build Response": { "main": [[{ "node": "Respond Success", "type": "main", "index": 0 }]] }
  },
  "settings": {
    "executionOrder": "v1"
  },
  "staticData": null,
  "tags": [{ "name": "bridge-kit" }],
  "pinData": {}
}
```

---

### 5.5 MCP Server Adapter

**File: mcp-server/package.json**
```json
{
  "name": "bridge-kit-mcp",
  "version": "1.0.0",
  "type": "module",
  "bin": {
    "bridge-kit-mcp": "./dist/index.js"
  },
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsx src/index.ts"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "tsx": "^4.0.0",
    "typescript": "^5.0.0"
  }
}
```

**File: mcp-server/src/index.ts**
```typescript
#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
  McpError,
  ErrorCode,
} from "@modelcontextprotocol/sdk/types.js";
import * as crypto from "crypto";

// Configuration from environment
const N8N_WEBHOOK_URL = process.env.N8N_WEBHOOK_URL || "http://localhost:5678/webhook/bridge-router";
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || "";

// Initialize MCP server
const server = new Server(
  { name: "bridge-kit-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// Tool definitions matching the router contract
const TOOLS = [
  {
    name: "github_create_issue",
    description: "Create a GitHub issue via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        repo: { type: "string", description: "Repository in owner/repo format" },
        title: { type: "string", description: "Issue title" },
        body: { type: "string", description: "Issue body (markdown)" },
        labels: { type: "array", items: { type: "string" }, description: "Labels to apply" }
      },
      required: ["repo", "title"]
    }
  },
  {
    name: "github_create_pr",
    description: "Create a GitHub pull request via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        repo: { type: "string", description: "Repository in owner/repo format" },
        title: { type: "string", description: "PR title" },
        body: { type: "string", description: "PR description" },
        head: { type: "string", description: "Source branch" },
        base: { type: "string", description: "Target branch (default: main)" }
      },
      required: ["repo", "title", "head"]
    }
  },
  {
    name: "docs_append_text",
    description: "Append text to a Google Doc via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        documentId: { type: "string", description: "Google Doc ID" },
        text: { type: "string", description: "Text to append" }
      },
      required: ["documentId", "text"]
    }
  },
  {
    name: "sheets_append_row",
    description: "Append a row to a Google Sheet via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        spreadsheetId: { type: "string", description: "Google Sheet ID" },
        sheetName: { type: "string", description: "Sheet name (default: Sheet1)" },
        values: { type: "array", items: { type: "string" }, description: "Row values" }
      },
      required: ["spreadsheetId", "values"]
    }
  },
  {
    name: "slack_send_message",
    description: "Send a Slack message via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        channel: { type: "string", description: "Channel name or ID" },
        message: { type: "string", description: "Message text" }
      },
      required: ["channel", "message"]
    }
  },
  {
    name: "ai_summarize",
    description: "Summarize content using Claude via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        content: { type: "string", description: "Content to summarize" }
      },
      required: ["content"]
    }
  },
  {
    name: "drive_search",
    description: "Search Google Drive via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        query: { type: "string", description: "Search query" }
      },
      required: ["query"]
    }
  },
  {
    name: "context_capture",
    description: "Capture and log context via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        context: { type: "object", description: "Context data to capture" }
      },
      required: ["context"]
    }
  }
];

// Tool name → action mapping
const ACTION_MAP: Record<string, string> = {
  github_create_issue: "github.issue_create",
  github_create_pr: "github.pr_create",
  docs_append_text: "docs.text_append",
  sheets_append_row: "sheets.row_append",
  slack_send_message: "slack.message_send",
  ai_summarize: "ai.summarize",
  drive_search: "drive.file_list",
  context_capture: "context.capture"
};

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  const action = ACTION_MAP[name];
  if (!action) {
    throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
  }
  
  // Build envelope
  const envelope = {
    version: "1.0.0",
    action,
    source: "claude-desktop-mcp",
    timestamp: new Date().toISOString(),
    idempotencyKey: crypto.randomUUID(),
    correlationId: crypto.randomUUID(),
    context: {},
    payload: buildPayload(name, args),
    target: buildTarget(name, args)
  };
  
  // Dispatch to n8n
  const result = await dispatchToRouter(envelope);
  
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(result, null, 2)
      }
    ]
  };
});

function buildPayload(toolName: string, args: Record<string, unknown> | undefined): Record<string, unknown> {
  if (!args) return {};
  
  switch (toolName) {
    case "github_create_issue":
      return { title: args.title, body: args.body, labels: args.labels };
    case "github_create_pr":
      return { title: args.title, body: args.body, head: args.head, base: args.base || "main" };
    case "docs_append_text":
      return { text: args.text };
    case "sheets_append_row":
      return { values: args.values };
    case "slack_send_message":
      return { message: args.message };
    case "ai_summarize":
      return { content: args.content };
    case "drive_search":
      return { query: args.query };
    case "context_capture":
      return { data: args.context };
    default:
      return args;
  }
}

function buildTarget(toolName: string, args: Record<string, unknown> | undefined): Record<string, unknown> {
  if (!args) return {};
  
  switch (toolName) {
    case "github_create_issue":
    case "github_create_pr":
      return { repo: args.repo };
    case "docs_append_text":
      return { documentId: args.documentId };
    case "sheets_append_row":
      return { spreadsheetId: args.spreadsheetId, sheetName: args.sheetName || "Sheet1" };
    case "slack_send_message":
      return { channel: args.channel };
    default:
      return {};
  }
}

async function dispatchToRouter(envelope: Record<string, unknown>): Promise<Record<string, unknown>> {
  const body = JSON.stringify(envelope);
  
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Source": "claude-desktop-mcp",
    "X-Request-ID": envelope.correlationId as string
  };
  
  // Add HMAC signature if secret configured
  if (WEBHOOK_SECRET) {
    const signature = crypto
      .createHmac("sha256", WEBHOOK_SECRET)
      .update(body)
      .digest("hex");
    headers["X-Signature"] = `sha256=${signature}`;
  }
  
  const response = await fetch(N8N_WEBHOOK_URL, {
    method: "POST",
    headers,
    body
  });
  
  if (!response.ok) {
    throw new McpError(
      ErrorCode.InternalError,
      `Router returned ${response.status}: ${response.statusText}`
    );
  }
  
  return response.json();
}

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Bridge Kit MCP server running on stdio");
}

main().catch(console.error);
```

**File: mcp-server/tsconfig.json**
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true
  },
  "include": ["src/**/*"]
}
```

**Claude Desktop Config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "bridge-kit": {
      "command": "node",
      "args": ["/path/to/bridge-kit/mcp-server/dist/index.js"],
      "env": {
        "N8N_WEBHOOK_URL": "https://your-n8n.example.com/webhook/bridge-router",
        "WEBHOOK_SECRET": "your-hmac-secret"
      }
    }
  }
}
```

---

### 5.6 Verification Suite

**File: verification/test-router.sh**
```bash
#!/bin/bash
# Bridge Kit Router Verification Suite
# Usage: ./test-router.sh <webhook_url> [webhook_secret]

set -e

WEBHOOK_URL="${1:-http://localhost:5678/webhook/bridge-router}"
WEBHOOK_SECRET="${2:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🧪 Bridge Kit Router Verification"
echo "================================="
echo "Target: $WEBHOOK_URL"
echo ""

# Function to compute HMAC
compute_signature() {
  local body="$1"
  local secret="$2"
  echo -n "$body" | openssl dgst -sha256 -hmac "$secret" | sed 's/^.* //'
}

# Function to send request
send_request() {
  local name="$1"
  local payload="$2"
  local expected_status="${3:-200}"
  
  echo -n "Testing: $name... "
  
  local headers=(-H "Content-Type: application/json" -H "X-Source: test-suite")
  
  if [ -n "$WEBHOOK_SECRET" ]; then
    local sig=$(compute_signature "$payload" "$WEBHOOK_SECRET")
    headers+=(-H "X-Signature: sha256=$sig")
  fi
  
  local response=$(curl -s -w "\n%{http_code}" -X POST "$WEBHOOK_URL" \
    "${headers[@]}" \
    -d "$payload")
  
  local http_code=$(echo "$response" | tail -1)
  local body=$(echo "$response" | sed '$d')
  
  if [ "$http_code" = "$expected_status" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
    if echo "$body" | jq -e '.success == true' > /dev/null 2>&1; then
      echo "   Response: $(echo "$body" | jq -c '.data // .')"
    fi
    return 0
  else
    echo -e "${RED}✗ FAIL${NC} (HTTP $http_code, expected $expected_status)"
    echo "   Response: $body"
    return 1
  fi
}

# Test 1: Context capture
send_request "Context Capture" '{
  "version": "1.0.0",
  "action": "context.capture",
  "source": "chrome-extension",
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
  "idempotencyKey": "'$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid)'",
  "context": {
    "url": "https://example.com",
    "title": "Test Page",
    "selectedText": "Sample selected text"
  }
}'

# Test 2: GitHub issue (will fail if no credentials, but validates routing)
send_request "GitHub Issue Create" '{
  "version": "1.0.0",
  "action": "github.issue_create",
  "source": "chrome-extension",
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
  "idempotencyKey": "'$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid)'",
  "payload": {
    "title": "Test Issue from Verification Suite",
    "body": "This is a test issue."
  },
  "target": {
    "repo": "test-org/test-repo"
  }
}'

# Test 3: Invalid action (should fail)
echo -n "Testing: Invalid Action (expect 500)... "
send_request "Invalid Action" '{
  "version": "1.0.0",
  "action": "invalid.action",
  "source": "chrome-extension",
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
}' "500" || true

# Test 4: Missing required fields (should fail)
echo -n "Testing: Missing Fields (expect 500)... "
send_request "Missing Fields" '{
  "version": "1.0.0",
  "source": "chrome-extension"
}' "500" || true

# Test 5: AI Summarize
send_request "AI Summarize" '{
  "version": "1.0.0",
  "action": "ai.summarize",
  "source": "chrome-extension",
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
  "idempotencyKey": "'$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid)'",
  "payload": {
    "content": "This is a test document that should be summarized by Claude."
  }
}'

echo ""
echo "================================="
echo "Verification complete!"
```

**Expected Outputs**:

```json
// Context Capture - Expected Response
{
  "success": true,
  "timestamp": "2025-01-01T12:00:00.000Z",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "action": "context.capture",
    "received": true,
    "context": {
      "url": "https://example.com",
      "title": "Test Page",
      "selectedText": "Sample selected text"
    }
  },
  "metadata": {
    "executionTimeMs": 45,
    "cached": false
  }
}

// GitHub Issue - Expected Response (with valid credentials)
{
  "success": true,
  "timestamp": "2025-01-01T12:00:00.000Z",
  "correlationId": "550e8400-e29b-41d4-a716-446655440001",
  "data": {
    "id": 12345,
    "number": 42,
    "html_url": "https://github.com/test-org/test-repo/issues/42"
  },
  "metadata": {
    "executionTimeMs": 1234,
    "cached": false
  }
}

// Invalid Action - Expected Error Response
{
  "success": false,
  "timestamp": "2025-01-01T12:00:00.000Z",
  "error": {
    "code": "ACTION_NOT_ALLOWED",
    "message": "Action not allowed: invalid.action",
    "retryable": false
  }
}
```

---

## 6. Parity Checklist Generator

**File: parity-checklist-generator.yaml**
```yaml
# Bridge Kit Parity Checklist Generator
# Usage: Fill in user_jobs, run through template engine to generate matrix

version: "1.0.0"
description: "Generates capability matrices and gap lists for Bridge Kit features"

# Input: List of user jobs/features to evaluate
user_jobs:
  - id: "selection-to-docs"
    name: "Capture selection → write to Docs"
    category: "context-capture"
    priority: "P0"
    
  - id: "drive-classify"
    name: "Drive files → classify/tag → metadata"
    category: "automation"
    priority: "P1"
    
  - id: "chat-to-workflow"
    name: "Chat intent → workflow execution"
    category: "orchestration"
    priority: "P0"
    
  - id: "docs-batch-update"
    name: "Structured document editing (batchUpdate)"
    category: "document-ops"
    priority: "P1"
    
  - id: "sheets-append"
    name: "Spreadsheet append/update operations"
    category: "document-ops"
    priority: "P1"
    
  - id: "scheduled-jobs"
    name: "Background scheduled automations"
    category: "automation"
    priority: "P1"
    
  - id: "event-driven"
    name: "Event-driven automations (Drive changes)"
    category: "automation"
    priority: "P2"
    
  - id: "github-issue"
    name: "Create GitHub issue from context"
    category: "github"
    priority: "P0"
    
  - id: "github-pr"
    name: "Create PR with generated changes"
    category: "github"
    priority: "P1"
    
  - id: "github-comment"
    name: "Add comments/reviews to PRs"
    category: "github"
    priority: "P2"
    
  - id: "offline-queue"
    name: "Offline queue then sync"
    category: "resilience"
    priority: "P2"
    
  - id: "multi-tenant"
    name: "Multi-tenant workspace admin"
    category: "enterprise"
    priority: "P3"
    
  - id: "cross-tool-context"
    name: "Cross-tool context passing"
    category: "orchestration"
    priority: "P1"
    
  - id: "semantic-search"
    name: "Semantic search across Drive"
    category: "ai"
    priority: "P2"
    
  - id: "voice-capture"
    name: "Voice capture → transcribe → action"
    category: "ai"
    priority: "P3"

# Evaluation surfaces
surfaces:
  - id: "claude-code-cli"
    name: "Claude Code CLI"
    type: "cli"
    
  - id: "claude-desktop"
    name: "Claude Desktop"
    type: "desktop"
    
  - id: "claude-ai"
    name: "Claude.ai"
    type: "web"
    
  - id: "chrome-extension"
    name: "Chrome Extension"
    type: "browser"
    
  - id: "workspace-native"
    name: "Google Workspace Native"
    type: "platform"
    
  - id: "n8n"
    name: "n8n"
    type: "automation"

# Evaluation criteria
criteria:
  feasibility:
    values: ["native", "integration", "partial", "not-applicable"]
    weights: [3, 2, 1, 0]
    
  auth_complexity:
    values: ["none", "api-key", "oauth-user", "oauth-app", "service-account"]
    weights: [0, 1, 2, 3, 4]
    
  latency_profile:
    values: ["realtime", "fast", "async", "batch"]
    description: "realtime: <100ms, fast: <1s, async: <30s, batch: >30s"
    
  implementation_effort:
    values: ["trivial", "low", "medium", "high", "very-high"]
    days: [0.5, 1, 3, 7, 14]

# Output template
output:
  matrix:
    format: "markdown"
    template: |
      | User Job | {{ surfaces | map('name') | join(' | ') }} |
      |----------|{{ surfaces | map(() => '---') | join('|') }}|
      {% for job in user_jobs %}
      | {{ job.name }} | {% for surface in surfaces %}{{ evaluate(job, surface) }} | {% endfor %}
      {% endfor %}
      
  gap_list:
    format: "yaml"
    template: |
      gaps:
      {% for job in user_jobs %}
      {% for surface in surfaces %}
      {% if is_gap(job, surface) %}
        - job: {{ job.id }}
          surface: {{ surface.id }}
          reason: {{ gap_reason(job, surface) }}
          recommended_bridge: {{ bridge_recommendation(job, surface) }}
      {% endif %}
      {% endfor %}
      {% endfor %}
      
  owner_assignments:
    format: "yaml"
    template: |
      assignments:
      {% for job in user_jobs %}
        - job: {{ job.id }}
          primary_owner: {{ best_surface(job) }}
          fallback_owner: {{ fallback_surface(job) }}
          notes: {{ implementation_notes(job) }}
      {% endfor %}

# Evaluation functions (pseudocode - implement in preferred language)
functions:
  evaluate:
    description: "Returns feasibility symbol for job+surface combination"
    logic: |
      if surface.supports_natively(job): return "✅"
      if surface.supports_via_integration(job): return "⚠️"
      if surface.partially_supports(job): return "🔶"
      return "❌"
      
  is_gap:
    description: "Returns true if job is not natively supported on surface"
    logic: |
      return not surface.supports_natively(job)
      
  gap_reason:
    description: "Returns explanation for why gap exists"
    logic: |
      # Check API availability, auth constraints, platform limitations
      
  bridge_recommendation:
    description: "Returns recommended bridge solution"
    logic: |
      if job.category == "context-capture": return "chrome-extension → n8n webhook"
      if job.category == "automation": return "n8n native"
      if job.category == "github": return "n8n github node"
      # etc.
      
  best_surface:
    description: "Returns optimal surface for job"
    logic: |
      # Score each surface by feasibility + complexity
      # Return highest scoring surface

# Example generated output
example_output:
  matrix: |
    | User Job | Claude Code CLI | Claude Desktop | Claude.ai | Chrome Ext | Workspace | n8n |
    |----------|-----------------|----------------|-----------|------------|-----------|-----|
    | Selection → Docs | ❌ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ |
    | Drive classify | ⚠️ | ⚠️ | ✅ | ⚠️ | ✅ | ✅ |
    | Chat → workflow | ✅ | ✅ | ⚠️ | ⚠️ | ❌ | ✅ |
    | GitHub issue | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ |
    
  gap_list: |
    gaps:
      - job: selection-to-docs
        surface: claude-code-cli
        reason: "No browser context access from CLI"
        recommended_bridge: "chrome-extension captures context → n8n → CLI via MCP"
        
      - job: offline-queue
        surface: n8n
        reason: "n8n requires network connectivity"
        recommended_bridge: "chrome-extension IndexedDB queue → sync on reconnect"
```

---

## 7. Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Chrome MV3 service worker termination** | Context menu handlers may fail if worker sleeps | High | Use `chrome.alarms` to keep alive; implement retry in content script |
| **n8n Cloud 100s timeout** | Long AI operations fail | Medium | Use self-hosted n8n; implement async response pattern |
| **Google OAuth token expiry** | API calls fail after 1 hour | High | n8n auto-refreshes; monitor for refresh failures |
| **GitHub rate limiting** | Burst operations rejected | Medium | Queue requests; use GitHub App (15k/hr vs 5k/hr) |
| **HMAC secret exposure** | Webhook can be spoofed | Low | Store in environment; rotate periodically |
| **n8n single point of failure** | All automations down | Medium | Deploy with health checks; failover to backup instance |
| **Google API quota exhaustion** | Read/write operations fail | Low | Implement exponential backoff; cache responses |
| **MCP server crash** | Desktop/CLI tools unavailable | Low | Supervisor process; auto-restart on failure |

---

## 8. Source List

| Source | URL | Last Verified |
|--------|-----|---------------|
| Chrome Extensions MV3 | https://developer.chrome.com/docs/extensions/mv3 | 2025-01 |
| MCP Specification | https://modelcontextprotocol.io/specification | 2025-01 |
| n8n Documentation | https://docs.n8n.io | 2025-01 |
| Google Drive API | https://developers.google.com/drive/api | 2025-01 |
| Google Docs API | https://developers.google.com/docs/api | 2025-01 |
| Google Sheets API | https://developers.google.com/sheets/api | 2025-01 |
| GitHub REST API | https://docs.github.com/en/rest | 2025-01 |
| GitHub Apps | https://docs.github.com/en/apps | 2025-01 |
| Anthropic Claude API | https://docs.anthropic.com | 2025-01 |
| Microsoft Graph | https://learn.microsoft.com/graph | 2025-01 |

---

*End of Bridge Kit Specification v1.0.0*
