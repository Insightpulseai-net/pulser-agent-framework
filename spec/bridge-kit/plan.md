# Bridge Kit Implementation Plan

## Overview

Two implementation paths:
1. **MVP (1-2 days)**: Minimal working system for validation
2. **Production (2-4 weeks)**: Hardened, monitored, scalable

---

## Phase 1: MVP (Days 1-2)

### Day 1: Core Infrastructure

#### Morning (4 hours)

**1.1 Set up n8n locally**
```bash
# Start n8n with Docker
docker run -it --rm -p 5678:5678 \
  -e N8N_HOST=localhost \
  -e WEBHOOK_URL=http://localhost:5678 \
  n8nio/n8n

# Access at http://localhost:5678
```

**1.2 Create webhook workflow**
- Import `n8n-workflows/context-router.json`
- Configure webhook path: `/webhook/bridge-router`
- Note the full webhook URL

**1.3 Test webhook**
```bash
curl -X POST http://localhost:5678/webhook/bridge-router \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0.0",
    "action": "context.capture",
    "source": "api-direct",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'
```

#### Afternoon (4 hours)

**1.4 Chrome extension setup**
```bash
# Create extension directory
mkdir -p chrome-extension/icons

# Copy manifest.json, service-worker.js, content.js, popup.html, popup.js
# Generate placeholder icons (16x16, 48x48, 128x128)
```

**1.5 Load unpacked extension**
1. Open `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `chrome-extension/` directory

**1.6 Configure extension**
1. Click extension icon
2. Enter webhook URL from step 1.2
3. Click "Save Configuration"

**1.7 Test context capture**
1. Navigate to any webpage
2. Select text
3. Right-click → "Create GitHub Issue"
4. Verify webhook receives request in n8n

### Day 2: GitHub Integration + MCP

#### Morning (4 hours)

**2.1 Configure GitHub credentials in n8n**
- Create GitHub App or generate PAT
- Add credentials in n8n: Settings → Credentials → GitHub

**2.2 Update n8n workflow**
- Connect GitHub Issue node to credentials
- Set default repo if not specified in request

**2.3 Test GitHub issue creation**
```bash
curl -X POST http://localhost:5678/webhook/bridge-router \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0.0",
    "action": "github.issue_create",
    "source": "api-direct",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "payload": {
      "title": "Test Issue from Bridge Kit",
      "body": "This is a test."
    },
    "target": {
      "repo": "your-org/your-repo"
    }
  }'
```

#### Afternoon (4 hours)

**2.4 Build MCP server**
```bash
cd mcp-server
npm install
npm run build
```

**2.5 Configure Claude Desktop**
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "bridge-kit": {
      "command": "node",
      "args": ["/path/to/mcp-server/dist/index.js"],
      "env": {
        "N8N_WEBHOOK_URL": "http://localhost:5678/webhook/bridge-router"
      }
    }
  }
}
```

**2.6 Test MCP tools**
1. Restart Claude Desktop
2. Ask: "List available bridge-kit tools"
3. Ask: "Create a GitHub issue titled 'Test from MCP' in org/repo"

### MVP Verification Checklist

- [ ] n8n webhook receives requests
- [ ] Chrome extension context menu works
- [ ] Selected text captured in requests
- [ ] GitHub issue created from browser
- [ ] GitHub issue created from MCP tool
- [ ] Extension badge shows success/failure

---

## Phase 2: Production Hardening (Weeks 1-4)

### Week 1: Infrastructure

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Deploy n8n to production server | Docker Compose with PostgreSQL |
| 3 | Configure HTTPS (Let's Encrypt) | Valid TLS certificate |
| 4 | Set up n8n credentials (Google, GitHub, Slack) | Working integrations |
| 5 | Implement HMAC signature validation | Secure webhook |

**Production Docker Compose**:
```yaml
version: '3.8'
services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=${N8N_HOST}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=${WEBHOOK_URL}
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=${POSTGRES_USER}
      - DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    restart: always
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=n8n
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  n8n_data:
  postgres_data:
```

### Week 2: Chrome Extension

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Implement side panel UI | Full sidepanel.html/js |
| 2 | Add Google OAuth integration | Drive file picker |
| 3 | Implement offline queue (IndexedDB) | Persistent queue |
| 4 | Add queue sync logic | Auto-retry on reconnect |
| 5 | Extension testing | All flows verified |

**Side Panel Features**:
- Action history (last 20 actions)
- Queue status indicator
- Google account connection
- Webhook configuration

### Week 3: MCP + Advanced Features

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Add remaining MCP tools | All 8 tools working |
| 2 | Implement error handling | Graceful failures |
| 3 | Add Google Docs/Sheets actions | Full document ops |
| 4 | Add Slack integration | Message sending |
| 5 | Cross-surface testing | End-to-end flows |

### Week 4: Observability + Security

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Structured logging | JSON logs with correlation ID |
| 2 | n8n error workflow | Slack alerts on failures |
| 3 | Rate limiting | Redis-based throttling |
| 4 | Security audit | HMAC, token rotation, allowlists |
| 5 | Load testing | Performance baselines |

**Error Workflow Pattern**:
```json
{
  "name": "Bridge Kit Error Handler",
  "nodes": [
    {
      "parameters": {
        "conditions": {
          "options": { "caseSensitive": true },
          "conditions": [
            {
              "leftValue": "={{ $json.execution?.error }}",
              "rightValue": "",
              "operator": { "type": "string", "operation": "isNotEmpty" }
            }
          ]
        }
      },
      "name": "Has Error",
      "type": "n8n-nodes-base.filter"
    },
    {
      "parameters": {
        "channel": "#bridge-kit-errors",
        "text": "🚨 Bridge Kit Error\n*Workflow*: {{ $json.workflow.name }}\n*Error*: {{ $json.execution.error.message }}\n*Execution*: {{ $json.execution.id }}"
      },
      "name": "Alert Slack",
      "type": "n8n-nodes-base.slack"
    }
  ]
}
```

---

## Verification Plan

### Smoke Tests (Run Daily)

```bash
#!/bin/bash
# smoke-test.sh

WEBHOOK_URL="${1:-https://your-n8n.example.com/webhook/bridge-router}"
SECRET="${2:-}"

echo "🧪 Bridge Kit Smoke Tests"
echo "========================"

# Test 1: Health check
echo -n "1. Webhook reachable... "
if curl -s -o /dev/null -w "%{http_code}" "$WEBHOOK_URL" | grep -q "405\|200"; then
  echo "✓"
else
  echo "✗ FAIL"
  exit 1
fi

# Test 2: Valid request
echo -n "2. Valid context capture... "
RESPONSE=$(curl -s -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"version":"1.0.0","action":"context.capture","source":"api-direct","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}')

if echo "$RESPONSE" | grep -q '"success":true'; then
  echo "✓"
else
  echo "✗ FAIL: $RESPONSE"
  exit 1
fi

# Test 3: Invalid action rejected
echo -n "3. Invalid action rejected... "
RESPONSE=$(curl -s -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"version":"1.0.0","action":"invalid.action","source":"api-direct","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}')

if echo "$RESPONSE" | grep -q 'not allowed\|error'; then
  echo "✓"
else
  echo "✗ FAIL: Should reject invalid action"
  exit 1
fi

echo ""
echo "All smoke tests passed! ✅"
```

### Integration Tests

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Browser → GitHub | Select text → Context menu → Create Issue | Issue created in 5s |
| CLI → GitHub | MCP tool call | Issue created via n8n |
| Desktop → Docs | MCP tool call | Text appended to Doc |
| Offline → Sync | Disconnect → Action → Reconnect | Queued action executes |

### Performance Baselines

| Metric | Target | Acceptable |
|--------|--------|------------|
| Webhook latency (p50) | < 200ms | < 500ms |
| Webhook latency (p99) | < 500ms | < 2s |
| GitHub issue creation | < 3s | < 5s |
| MCP tool round-trip | < 2s | < 5s |

---

## Rollback Plan

### n8n Rollback

```bash
# Stop current deployment
docker-compose down

# Restore from backup
pg_restore -h postgres -U n8n -d n8n backup.dump

# Start previous version
docker-compose up -d --pull never
```

### Chrome Extension Rollback

1. Users: Disable current extension
2. Load previous version from backup directory
3. Publish hotfix to Chrome Web Store (if published)

### MCP Server Rollback

1. Edit Claude Desktop config to point to previous version
2. Restart Claude Desktop
