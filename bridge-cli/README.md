# Bridge Kit CLI

CLI wrapper for Bridge Kit n8n router with HMAC authentication.

## Prerequisites

- Node.js >= 18.0.0
- `BRIDGE_HMAC_SECRET` environment variable set

## Setup

```bash
# Set required environment variables
export BRIDGE_HMAC_SECRET='your-secret-here'

# Optional: override defaults
export BRIDGE_ROUTER_URL='https://your-n8n-instance.com/webhook/bridge-router'
export BRIDGE_VERSION='1.0.0'

# Enable debug output
export BRIDGE_DEBUG=1
```

## Usage

```bash
# Make executable
chmod +x bridge.js

# Show help
node bridge.js --help

# Capture context
node bridge.js context.capture --payload '{"text":"hello world","url":"https://example.com"}'

# Summarize text
node bridge.js ai.summarize --payload '{"text":"long text to summarize"}'

# Create GitHub issue
node bridge.js github.issue_create --payload '{"repo":"owner/repo","title":"Bug","body":"Description"}'

# Use payload file
node bridge.js github.pr_open --payload-file pr-payload.json

# With correlation ID for tracing
node bridge.js context.capture --payload '{"text":"test"}' --correlation-id "trace-123"
```

## Supported Actions

| Action | Description |
|--------|-------------|
| `context.capture` | Capture and process context |
| `ai.summarize` | Summarize content with AI |
| `github.issue_create` | Create a GitHub issue |
| `github.branch_create` | Create a GitHub branch |
| `github.file_upsert` | Create or update a file |
| `github.commit_create` | Create a commit |
| `github.pr_open` | Open a pull request |
| `drive.file_list` | List Google Drive files |
| `drive.file_read` | Read a Google Drive file |
| `docs.text_append` | Append text to Google Doc |
| `docs.create` | Create a new Google Doc |
| `sheets.row_append` | Append row to Google Sheet |
| `sheets.update` | Update Google Sheet |
| `slack.message_send` | Send a Slack message |

## Envelope Format

All requests use the `ContextRouterEnvelope` schema:

```json
{
  "version": "1.0.0",
  "action": "context.capture",
  "source": "claude-code-cli",
  "timestamp": "2025-01-01T00:00:00.000Z",
  "idempotencyKey": "bk_1234567890_abc123",
  "correlationId": "optional-trace-id",
  "payload": { ... }
}
```

## Security

The CLI signs all requests with HMAC-SHA256:

```
x-bridge-signature: sha256=<hex-digest>
```

The signature is computed over the raw JSON body string.
