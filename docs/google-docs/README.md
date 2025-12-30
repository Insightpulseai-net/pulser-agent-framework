# Google Docs Sync Directory

This directory contains markdown files automatically synced from Google Docs.

## How It Works

1. **n8n Workflow** monitors a Google Drive folder for changes
2. When a Google Doc is updated, it's exported as Markdown
3. The Markdown file is committed to this directory
4. Mattermost notification (optional) alerts the team

## Sync Trigger Methods

| Method | How to Trigger |
|--------|----------------|
| **Automatic** | Edit any doc in the watched Google Drive folder |
| **Webhook** | `POST https://n8n.insightpulseai.net/webhook/docs-sync` |
| **Claude** | `/sync` command |

## File Naming Convention

Google Doc titles are converted to uppercase snake_case:
- "Comprehensive Testing Strategy" → `COMPREHENSIVE_TESTING_STRATEGY.md`
- "BIR Tax Automation Spec" → `BIR_TAX_AUTOMATION_SPEC.md`

## YAML Frontmatter

Each synced file includes metadata:

```yaml
---
title: "Original Document Title"
source: google-docs
sync_date: "2024-12-30T12:00:00.000Z"
doc_id: "1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4"
---
```

## Configuration

Set these in n8n:
- `GOOGLE_DRIVE_FOLDER_ID` - The folder to watch
- `GITHUB_TOKEN` - Token with repo write access
- `MATTERMOST_WEBHOOK_URL` - (Optional) For notifications
- `SUPABASE_URL` - (Optional) For audit logging

## Verification

```bash
# Check latest synced files
ls -la docs/google-docs/

# View recent sync commits
git log --oneline -n 10 -- docs/google-docs/
```
