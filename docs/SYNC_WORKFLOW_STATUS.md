# Google Docs Sync Workflow - Status & Next Steps

**Date**: 2025-12-31
**Status**: Ready to Execute (Pending Drive Sharing)

---

## ✅ Completed Setup

### 1. Service Account Configuration
- **Service Account**: `ipai-docs2code-runner@gen-lang-client-0909706188.iam.gserviceaccount.com`
- **Key File**: `secrets/ipai-docs2code-runner.json` ✅
- **GitHub Secret**: `GOOGLE_CREDENTIALS` added (2025-12-31T20:38:20Z) ✅
- **IAM Roles**: secretmanager, storage, aiplatform ✅
- **APIs Enabled**: drive, docs, sheets, vision ✅

### 2. Workflow Configuration
- **Workflow File**: `.github/workflows/sync-google-docs.yml` ✅
- **Fetch Script**: `scripts/docs-sync/fetch_google_doc.py` ✅
- **Default Document**: `1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4`
- **Target Path**: `docs/testing/COMPREHENSIVE_TESTING_STRATEGY.md`

### 3. CLI Tools
- **Share Script**: `scripts/docs-sync/share_drive.py` ✅
- **Verify Script**: `scripts/docs-sync/verify_sa_access.py` ✅
- **Python Dependencies**: Installed in `.venv` ✅

---

## 📋 Remaining Steps (CLI-Only)

### Step 1: Share Google Doc with Service Account

**Option A: Via Drive API (Recommended - Pure CLI)**

Requires OAuth Desktop Client JSON (one-time download):

1. **Create OAuth Desktop Client** (if not exists):
   ```bash
   # Go to: https://console.cloud.google.com/apis/credentials?project=gen-lang-client-0909706188
   # Click: "+ CREATE CREDENTIALS" → "OAuth client ID"
   # Application type: "Desktop app"
   # Name: "docs-sync-cli"
   # Click: "CREATE"
   # Download JSON → save as "client_oauth.json" in repo root
   ```

2. **Run Sharing Script**:
   ```bash
   source .venv/bin/activate

   export SA_EMAIL="ipai-docs2code-runner@gen-lang-client-0909706188.iam.gserviceaccount.com"
   export DRIVE_IDS="1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4"

   python scripts/docs-sync/share_drive.py
   # This will open browser once for OAuth consent
   # Then share the doc with the service account
   ```

3. **Verify Access**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="secrets/ipai-docs2code-runner.json"
   export DRIVE_IDS="1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4"

   python scripts/docs-sync/verify_sa_access.py
   # Expected output: ✅ OK 1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4 ...
   ```

**Option B: Manual UI (Fallback)**

If OAuth client creation is blocked:

1. Open: https://docs.google.com/document/d/1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4/edit
2. Click: "Share" button
3. Add email: `ipai-docs2code-runner@gen-lang-client-0909706188.iam.gserviceaccount.com`
4. Set permission: "Viewer"
5. Click: "Send"

---

### Step 2: Trigger Sync Workflow (CLI)

Once the document is shared and verified:

```bash
export GITHUB_TOKEN="YOUR_GITHUB_TOKEN_HERE"  # Use your GitHub PAT
REPO="Insightpulseai-net/pulser-agent-framework"
WF="sync-google-docs.yml"
BRANCH="claude/data-engineering-workbench-01Pk6KXASta9H4oeCMY8EBAE"

# Trigger workflow
gh workflow run "$WF" -R "$REPO" --ref "$BRANCH"

# Get run ID (wait a few seconds for it to start)
sleep 5
RUN_ID=$(gh run list -R "$REPO" --workflow "$WF" --limit 1 --json databaseId --jq '.[0].databaseId')

# Watch logs in real-time
gh run view -R "$REPO" "$RUN_ID" --log
```

---

### Step 3: Verify Results (CLI)

After workflow completes:

```bash
# Fetch latest changes
git fetch origin

# Check for new commits from doc-sync-bot
git log --oneline --author="doc-sync-bot" -n 5

# View the synced file
git show origin/"$BRANCH":docs/testing/COMPREHENSIVE_TESTING_STRATEGY.md | head -50
```

**Success Criteria**:
- ✅ Workflow status: "completed" (green check)
- ✅ New commit by "doc-sync-bot" with message "docs: sync testing strategy from Google Docs"
- ✅ File `docs/testing/COMPREHENSIVE_TESTING_STRATEGY.md` updated with latest content
- ✅ Frontmatter contains: `document_id`, `revision_id`, `synced_at`

---

## 🔍 Current Status Check

### Service Account Access Test (Just Ran)

```bash
$ python scripts/docs-sync/verify_sa_access.py
❌ FAIL 1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4 File not found: 1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4
```

**Interpretation**: Document is NOT yet shared with service account (expected)

**Next Action**: Complete Step 1 (Share Google Doc)

---

## 📊 Workflow Details

### Default Configuration

```yaml
Document ID: 1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4
Target File: docs/testing/COMPREHENSIVE_TESTING_STRATEGY.md
Create PR: true (creates PR for review instead of direct commit)
Schedule: Hourly at minute 15 (cron: '15 * * * *')
```

### Manual Trigger Options

The workflow supports manual dispatch with custom inputs:

```bash
# Sync specific document to custom path
gh workflow run sync-google-docs.yml \
  -R "$REPO" \
  --ref "$BRANCH" \
  -f document_id="CUSTOM_DOC_ID" \
  -f target_path="docs/custom/path.md" \
  -f create_pr=false  # Direct commit instead of PR
```

### Workflow Jobs

1. **sync-docs**:
   - Checkout repository
   - Setup Python 3.11 + install dependencies
   - Fetch Google Doc using service account
   - Export as HTML, convert to Markdown
   - Check for changes
   - Create PR or direct commit

2. **validate-docs** (runs after sync-docs):
   - Validate Markdown syntax
   - Check for TODOs/FIXMEs
   - Report any warnings

---

## 🎯 Zero-UI Execution Path

**Complete CLI-only workflow**:

```bash
#!/bin/bash
set -e

# 1. Share document (one-time OAuth consent)
SA_EMAIL="ipai-docs2code-runner@gen-lang-client-0909706188.iam.gserviceaccount.com"
DRIVE_IDS="1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4"
python scripts/docs-sync/share_drive.py

# 2. Verify access
GOOGLE_APPLICATION_CREDENTIALS="secrets/ipai-docs2code-runner.json"
python scripts/docs-sync/verify_sa_access.py

# 3. Trigger workflow
REPO="Insightpulseai-net/pulser-agent-framework"
gh workflow run sync-google-docs.yml -R "$REPO" --ref "$BRANCH"

# 4. Wait for completion and view logs
sleep 10
RUN_ID=$(gh run list -R "$REPO" --workflow sync-google-docs.yml --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch -R "$REPO" "$RUN_ID"

# 5. View synced content
git fetch origin
git show origin/"$BRANCH":docs/testing/COMPREHENSIVE_TESTING_STRATEGY.md
```

---

## 🔐 Security Notes

- ✅ Service account key stored in GitHub Secrets (never in code)
- ✅ OAuth Desktop client JSON gitignored (never committed)
- ✅ Workflow uses DOCS_SYNC_PAT or GITHUB_TOKEN (repo scope)
- ✅ Service account has read-only access to Drive/Docs
- ✅ PR workflow ensures human review before merge

---

**Next Immediate Action**: Create OAuth Desktop Client JSON and run Step 1 (Share Google Doc)
