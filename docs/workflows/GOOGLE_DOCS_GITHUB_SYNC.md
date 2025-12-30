# Google Docs to GitHub Sync Workflow

Automated synchronization between Google Docs and GitHub repository for documentation version control.

## Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Google Docs   │ ───► │   n8n / GitHub  │ ───► │    GitHub Repo  │
│   (Source)      │      │   Actions       │      │   (Target)      │
└─────────────────┘      └─────────────────┘      └─────────────────┘
         │                       │                        │
         │                       ▼                        │
         │              ┌─────────────────┐               │
         │              │   Mattermost    │               │
         │              │   Notification  │               │
         │              └─────────────────┘               │
         │                       │                        │
         └───────────────────────┼────────────────────────┘
                                 ▼
                        ┌─────────────────┐
                        │    Supabase     │
                        │   Audit Log     │
                        └─────────────────┘
```

## Implementation Options

| Option | Platform | Best For |
|--------|----------|----------|
| **A. n8n Workflow** | Self-hosted | Full control, custom logic |
| **B. GitHub Actions** | Cloud | Native GitHub integration |
| **C. Zapier/Make** | SaaS | Quick setup, limited customization |

## Quick Start

### Option A: n8n Workflow

1. **Import workflow**:
   ```bash
   # In n8n UI: Settings → Import → Upload file
   workflows/n8n/google-docs-github-sync.json
   ```

2. **Configure credentials**:
   - Google Docs OAuth2
   - GitHub Personal Access Token
   - Mattermost Webhook (optional)
   - Supabase API (optional)

3. **Set environment variables**:
   ```
   GOOGLE_DOC_ID=1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4
   GITHUB_OWNER=Insightpulseai-net
   GITHUB_REPO=pulser-agent-framework
   GITHUB_BRANCH=main
   ```

4. **Activate workflow**

### Option B: GitHub Actions

1. **Add secrets to repository**:

   Go to: Settings → Secrets and variables → Actions

   | Secret | Description |
   |--------|-------------|
   | `GOOGLE_CREDENTIALS` | Service account JSON key |
   | `DOCS_SYNC_PAT` | Personal Access Token (optional) |

2. **Create Google Service Account**:
   ```
   1. Go to https://console.cloud.google.com
   2. Create project "odoo-doc-sync"
   3. Enable Google Docs API and Google Drive API
   4. Create Service Account with Editor role
   5. Generate JSON key and download
   6. Add JSON content to GOOGLE_CREDENTIALS secret
   ```

3. **Share document with service account**:
   - Open your Google Doc
   - Click Share
   - Add service account email (from JSON key)
   - Grant Editor access

4. **Trigger workflow**:
   - Automatic: Runs hourly
   - Manual: Actions → Sync Google Docs → Run workflow

## Configuration

### Document Mapping

| Google Doc | Target File |
|------------|-------------|
| COMPREHENSIVE TESTING STRATEGY | `docs/testing/COMPREHENSIVE_TESTING_STRATEGY.md` |

### Sync Schedule

| Method | Frequency | Trigger |
|--------|-----------|---------|
| n8n | Every 5 minutes | Document modified |
| GitHub Actions | Hourly | Scheduled (cron) |
| Manual | On-demand | Workflow dispatch |

## File Structure

```
pulser-agent-framework/
├── .github/
│   └── workflows/
│       └── sync-google-docs.yml    # GitHub Actions workflow
├── scripts/
│   └── docs-sync/
│       └── fetch_google_doc.py     # Python script for fetching docs
├── workflows/
│   └── n8n/
│       └── google-docs-github-sync.json  # n8n workflow export
└── docs/
    └── workflows/
        └── GOOGLE_DOCS_GITHUB_SYNC.md    # This documentation
```

## Security Considerations

### Credentials Management

| Credential | Storage | Rotation |
|------------|---------|----------|
| Google Service Account | n8n Vault / GitHub Secrets | Never expires |
| GitHub PAT | n8n Vault / GitHub Secrets | Every 90 days |
| Mattermost Webhook | n8n Vault | As needed |

### Access Control

- Service account has **read-only** access to Google Docs
- GitHub token limited to **repo** scope
- No PII in commit messages
- Audit trail in Supabase

### Best Practices

1. **Never commit credentials** to the repository
2. **Rotate GitHub PAT** every 90 days
3. **Use branch protection** on main branch
4. **Review PRs** before merging synced docs

## Workflow Details

### n8n Nodes

| Node | Purpose |
|------|---------|
| Google Docs Trigger | Watch for document changes |
| Get Document Content | Fetch full document |
| Extract Content | Parse document structure |
| Convert to Markdown | Transform to GitHub-compatible format |
| GitHub: Create/Update | Push changes to repo |
| GitHub: Create PR | Open pull request for review |
| Mattermost: Notify | Alert team of updates |
| Supabase: Log | Store audit trail |

### GitHub Actions Jobs

| Job | Purpose |
|-----|---------|
| `sync-docs` | Fetch and commit document |
| `validate-docs` | Lint and validate Markdown |

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Document not shared | Share with service account email |
| 401 Unauthorized | Expired token | Regenerate GitHub PAT |
| No changes detected | Content identical | Check file comparison logic |
| Markdown formatting | HTML conversion | Use pandoc for better conversion |

### Debug Commands

```bash
# Test Python script locally
export GOOGLE_CREDENTIALS='{"type":"service_account",...}'
export DOCUMENT_ID='1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4'
python scripts/docs-sync/fetch_google_doc.py

# Check workflow status
gh run list --workflow=sync-google-docs.yml

# View workflow logs
gh run view <run-id> --log
```

## Monitoring

### Metrics

- Sync success rate
- Time since last sync
- Error count (last 24h)

### Alerts

| Condition | Action |
|-----------|--------|
| Sync failed | Mattermost alert to #alerts |
| No sync > 2 hours | Warning notification |
| Repeated failures | Escalate to DevOps |

## Changelog

### v1.0.0 (2025-12-30)

- Initial implementation
- n8n workflow with full sync pipeline
- GitHub Actions alternative
- Mattermost notifications
- Supabase audit logging

## References

- [Google Docs API](https://developers.google.com/docs/api)
- [GitHub REST API](https://docs.github.com/en/rest)
- [n8n Documentation](https://docs.n8n.io/)
- [peter-evans/create-pull-request](https://github.com/peter-evans/create-pull-request)
