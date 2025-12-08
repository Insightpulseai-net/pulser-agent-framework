# n8n Workflow Automation

Workflow automation for AI Workbench pipelines and agent triggers.

## Features

- **Expense approval workflows**: Auto-approve or escalate based on thresholds
- **Pipeline triggers**: Execute ETL pipelines on schedule or webhook
- **Mattermost notifications**: Real-time alerts for approvals and failures
- **Odoo integration**: Sync data between Odoo and Supabase

## Quick Start

### 1. Access n8n UI

```bash
# Open in browser
open https://n8n.insightpulseai.net

# Login with credentials (set in Helm values)
# Username: admin
# Password: <from secrets.yaml>
```

### 2. Import Workflows

```bash
# Via n8n UI: Workflows → Import → Select JSON file

# Or via CLI
curl -X POST https://n8n.insightpulseai.net/rest/workflows \
  -H "Authorization: Bearer <api-key>" \
  -H "Content-Type: application/json" \
  -d @workflows/expense-approval.json
```

### 3. Configure Credentials

#### Supabase PostgreSQL

1. Go to: Credentials → Add Credential → Postgres
2. Name: `Supabase PostgreSQL`
3. Host: `aws-1-us-east-1.pooler.supabase.com`
4. Database: `postgres`
5. User: `postgres`
6. Password: `<from SUPABASE_SERVICE_ROLE_KEY>`
7. Port: `6543`
8. SSL: `require`

#### Mattermost Webhook

1. Go to: Credentials → Add Credential → HTTP Request
2. Name: `Mattermost Webhook`
3. URL: `https://mattermost.insightpulseai.net/hooks/...`
4. Method: `POST`
5. Headers: `Content-Type: application/json`

### 4. Activate Workflows

```bash
# Via UI: Workflows → Select workflow → Toggle "Active"

# Or via API
curl -X PATCH https://n8n.insightpulseai.net/rest/workflows/<workflow-id> \
  -H "Authorization: Bearer <api-key>" \
  -d '{"active": true}'
```

## Available Workflows

### 1. Expense Approval Workflow

**File**: `workflows/expense-approval.json`

**Trigger**: Webhook POST to `/expense-approval`

**Logic**:
1. Receive expense data via webhook
2. Fetch expense details from Supabase
3. Check approval threshold ($5000)
4. Auto-approve if <$5000
5. Send Mattermost notification if >=$5000
6. Return status

**Test**:
```bash
curl -X POST https://n8n.insightpulseai.net/webhook/expense-approval \
  -H "Content-Type: application/json" \
  -d '{"expense_id": "123e4567-e89b-12d3-a456-426614174000"}'
```

### 2. Pipeline Trigger Workflow

**File**: `workflows/pipeline-trigger.json`

**Trigger**: Webhook POST to `/pipeline-trigger`

**Logic**:
1. Receive pipeline ID via webhook
2. Fetch pipeline definition from Supabase
3. Create job run record
4. Extract and execute SQL steps in order
5. Update job run status (completed/failed)
6. Return job run ID

**Test**:
```bash
curl -X POST https://n8n.insightpulseai.net/webhook/pipeline-trigger \
  -H "Content-Type: application/json" \
  -d '{"pipeline_id": "123e4567-e89b-12d3-a456-426614174000"}'
```

## Creating Custom Workflows

### 1. Basic Structure

```json
{
  "name": "My Workflow",
  "nodes": [
    {
      "parameters": {...},
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook"
    },
    {
      "parameters": {...},
      "name": "Process Data",
      "type": "n8n-nodes-base.code"
    }
  ],
  "connections": {...}
}
```

### 2. Common Node Types

#### Webhook Trigger
```json
{
  "type": "n8n-nodes-base.webhook",
  "parameters": {
    "httpMethod": "POST",
    "path": "my-webhook",
    "responseMode": "responseNode"
  }
}
```

#### PostgreSQL Query
```json
{
  "type": "n8n-nodes-base.postgres",
  "parameters": {
    "operation": "executeQuery",
    "query": "SELECT * FROM table WHERE id = '{{ $json.id }}'"
  }
}
```

#### HTTP Request
```json
{
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "https://api.example.com",
    "method": "POST",
    "sendBody": true
  }
}
```

#### JavaScript Code
```json
{
  "type": "n8n-nodes-base.code",
  "parameters": {
    "jsCode": "const data = $input.first().json; return {json: {result: data.value * 2}};"
  }
}
```

## Scheduled Workflows

### Cron Syntax

n8n supports standard cron syntax:

```
* * * * *
│ │ │ │ │
│ │ │ │ └─ Day of week (0-7, Sunday = 0 or 7)
│ │ │ └─── Month (1-12)
│ │ └───── Day of month (1-31)
│ └─────── Hour (0-23)
└───────── Minute (0-59)
```

**Examples**:
- `0 2 * * *` - Daily at 2 AM
- `0 */4 * * *` - Every 4 hours
- `0 0 * * 1` - Every Monday at midnight
- `*/15 * * * *` - Every 15 minutes

### Create Scheduled Workflow

1. Add "Schedule" trigger node
2. Set cron expression
3. Add processing nodes
4. Activate workflow

## Monitoring

### View Executions

```bash
# Via UI: Executions → Select workflow

# Via API
curl https://n8n.insightpulseai.net/rest/executions \
  -H "Authorization: Bearer <api-key>"
```

### Error Handling

n8n automatically logs failed executions. Configure alerts:

1. Go to: Settings → Error Workflow
2. Select workflow to run on errors
3. Add Mattermost notification node

## Performance

### Optimization Tips

1. **Use pagination**: For large datasets, process in batches
2. **Enable caching**: Reduce duplicate API calls
3. **Parallel execution**: Use "Split In Batches" node
4. **Queue mode**: Enable for long-running workflows

### Resource Limits

- **Execution timeout**: 300s (default), 3600s (max)
- **Memory limit**: 512Mi per execution
- **Concurrent executions**: 100 (configurable)

## Security

### API Keys

Generate API keys in n8n UI:
1. Settings → API → Add API Key
2. Copy key (only shown once)
3. Use in Authorization header

### Webhook Security

Add authentication to webhooks:
1. Edit webhook node
2. Enable "Header Auth" or "Query Auth"
3. Set secret token
4. Validate in subsequent nodes

## Troubleshooting

### Workflow Not Triggering

```bash
# Check webhook URL
curl https://n8n.insightpulseai.net/webhook/<path>

# Verify workflow is active
# UI: Workflows → Check "Active" toggle

# Check logs
kubectl logs -f deployment/n8n -n n8n
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql "$POSTGRES_URL" -c "SELECT 1;"

# Verify credentials in n8n
# Credentials → Supabase PostgreSQL → Test Connection
```

### Execution Timeout

```bash
# Increase timeout in workflow settings
# Settings → Execution Timeout → 600 (seconds)

# Or split into smaller workflows
```

## Backup

### Export Workflows

```bash
# Via UI: Workflows → Select → Download

# Via API
curl https://n8n.insightpulseai.net/rest/workflows/<workflow-id> \
  -H "Authorization: Bearer <api-key>" \
  > workflow-backup.json
```

### Database Backup

n8n stores data in PostgreSQL. Backup handled by Supabase.

## Next Steps

1. Import sample workflows
2. Configure credentials (Supabase, Mattermost)
3. Create custom workflows for your use cases
4. Setup monitoring and alerts

## Resources

- **n8n Docs**: https://docs.n8n.io/
- **Community**: https://community.n8n.io/
- **Templates**: https://n8n.io/workflows
