# /sync - Trigger Google Docs → GitHub Sync

Triggers the n8n workflow to sync Google Docs to GitHub and verifies the result.

## Steps

1. **Trigger the sync webhook**:
   ```bash
   curl -X POST "https://n8n.insightpulseai.net/webhook/docs-sync" \
     -H "Content-Type: application/json" \
     -d '{"source":"claude-shortcut","mode":"sync_all"}'
   ```

2. **Pull latest changes**:
   ```bash
   git fetch origin main
   git log --oneline -n 5 -- docs/google-docs/
   ```

3. **Verify new files landed**:
   ```bash
   ls -la docs/google-docs/
   ```

4. **Report results**:
   - If new commits exist → Report success with file names
   - If no commits → Check n8n execution logs for errors

## Troubleshooting

If sync fails, check:
- n8n execution logs at https://n8n.insightpulseai.net/
- GitHub API token permissions (needs repo write access)
- Google Drive OAuth2 credentials (needs read access to folder)
