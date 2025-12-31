# Google Credentials Setup - Docs2Code Pipeline

**Definitive guide for Google API authentication in the InsightPulseAI stack**

## Overview

Your stack requires **2 credential types**:
1. **OAuth 2.0 Web Application** - For n8n workflows (user-consent flows)
2. **Service Account** - For headless automation (cron, CI/CD, scheduled ingestion)

**Never use API keys** except for truly public APIs (Maps, etc.).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Google Cloud Project: insightpulseai                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ OAuth 2.0 Credentials (User Consent):                      │
│   ├─ n8n_prod (Web App)                                    │
│   │  └─ Redirect: https://n8n.insightpulseai.net/rest/...  │
│   ├─ odoo_web (Web App)                                    │
│   │  └─ For Odoo Google Sign-In SSO                        │
│   └─ Desktop client 2 (Desktop)                            │
│      └─ For local dev/CLI tools                            │
│                                                             │
│ Service Accounts (Headless):                               │
│   ├─ docs2code-svc@...iam.gserviceaccount.com              │
│   │  ├─ Docs/Drive ingestion (scheduled)                   │
│   │  ├─ OCR/Vision API calls                               │
│   │  └─ GitHub sync workflows                              │
│   └─ ocr-service@...iam.gserviceaccount.com (if separate)  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Service Account Setup (Headless Automation)

### Create Service Account

```bash
# Set project
gcloud config set project insightpulseai

# Create service account
gcloud iam service-accounts create docs2code-svc \
  --display-name="Docs2Code Pipeline Service Account" \
  --description="Headless automation for Docs→GitHub sync, OCR, scheduled ingestion"

# Get service account email
SA_EMAIL="docs2code-svc@$(gcloud config get-value project).iam.gserviceaccount.com"
echo "Service Account Email: $SA_EMAIL"
```

### Generate Key File

```bash
# Create secrets directory (gitignored)
mkdir -p secrets

# Generate JSON key
gcloud iam service-accounts keys create secrets/docs2code-svc.json \
  --iam-account="$SA_EMAIL"

echo "✅ Key file created: secrets/docs2code-svc.json"
echo "⚠️  NEVER commit this file to git!"
```

### Grant Required Roles

```bash
# Project-level roles (adjust as needed)
gcloud projects add-iam-policy-binding insightpulseai \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/cloudfunctions.invoker"

# For Vision API (OCR)
gcloud projects add-iam-policy-binding insightpulseai \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/cloudvision.user"
```

### Share Google Drive Files

**Service accounts don't automatically see Drive files.** You must share:

**Option A: Share specific folders/files**
```
1. Open Google Drive
2. Right-click folder → Share
3. Add: docs2code-svc@insightpulseai.iam.gserviceaccount.com
4. Set permissions: "Viewer" or "Editor"
```

**Option B: Domain-wide delegation (Workspace admins only)**
```bash
# 1. Enable domain-wide delegation in Console
# 2. Add OAuth scopes:
#    - https://www.googleapis.com/auth/drive.readonly
#    - https://www.googleapis.com/auth/documents.readonly
#    - https://www.googleapis.com/auth/spreadsheets.readonly
```

### Required API Scopes (for service account)

Add to your code when initializing credentials:

```python
SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/cloud-vision",  # For OCR
]

from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    'secrets/docs2code-svc.json',
    scopes=SCOPES
)
```

### Store in GitHub Secrets

```bash
# Copy JSON content
cat secrets/docs2code-svc.json | pbcopy  # macOS
# Or: cat secrets/docs2code-svc.json | xclip -selection clipboard  # Linux

# Add to GitHub:
# 1. Go to: https://github.com/Insightpulseai-net/pulser-agent-framework/settings/secrets/actions
# 2. Click "New repository secret"
# 3. Name: GOOGLE_CREDENTIALS
# 4. Value: <paste JSON>
```

---

## 2. OAuth 2.0 Setup (n8n Workflows)

### Create OAuth Client for n8n

**In Google Cloud Console:**

1. **Navigate to**: [APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)
2. **Click**: "Create Credentials" → "OAuth 2.0 Client ID"
3. **Application type**: "Web application"
4. **Name**: `n8n_prod`
5. **Authorized redirect URIs**:
   ```
   https://n8n.insightpulseai.net/rest/oauth2-credential/callback
   ```
6. **Click**: "Create"
7. **Copy**: Client ID and Client Secret

### Configure in n8n

**In n8n UI:**

1. **Go to**: Credentials → Add Credential
2. **Select**: "Google OAuth2 API"
3. **Name**: "Google Docs/Drive (Production)"
4. **Paste**:
   - **Client ID**: `<YOUR_CLIENT_ID>.apps.googleusercontent.com`
   - **Client Secret**: `<YOUR_CLIENT_SECRET>`
5. **Scopes**: (n8n auto-adds these, but verify)
   ```
   https://www.googleapis.com/auth/drive
   https://www.googleapis.com/auth/documents
   https://www.googleapis.com/auth/spreadsheets
   ```
6. **Click**: "Connect my account" → Complete OAuth flow
7. **Save**

### Use in n8n Workflows

**Example: Google Docs node**

```json
{
  "nodes": [
    {
      "name": "Fetch Google Doc",
      "type": "n8n-nodes-base.googleDocs",
      "credentials": {
        "googleDocsOAuth2Api": {
          "id": "1",
          "name": "Google Docs/Drive (Production)"
        }
      },
      "parameters": {
        "operation": "get",
        "documentId": "1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4"
      }
    }
  ]
}
```

---

## 3. OCR/Vision API Setup

### Enable APIs

```bash
gcloud services enable vision.googleapis.com
gcloud services enable documentai.googleapis.com  # Optional: Document AI
```

### Use Service Account (Recommended)

**Python example:**

```python
from google.cloud import vision
from google.oauth2 import service_account

# Initialize with service account
credentials = service_account.Credentials.from_service_account_file(
    'secrets/docs2code-svc.json'
)

client = vision.ImageAnnotatorClient(credentials=credentials)

# Perform OCR
with open('receipt.jpg', 'rb') as image_file:
    content = image_file.read()

image = vision.Image(content=content)
response = client.text_detection(image=image)

print(response.full_text_annotation.text)
```

### Alternative: API Key (Less Secure)

**Only use if service account doesn't work:**

```bash
gcloud alpha services api-keys create \
  --display-name="OCR API Key (Legacy)" \
  --api-target=service=vision.googleapis.com

# Get key value
gcloud alpha services api-keys list --filter="displayName:OCR"
```

**Not recommended** because:
- No fine-grained permissions
- Can't be rotated easily
- Less secure audit trail

---

## 4. GitHub Workflows Integration

### Workflow Environment Variables

**In `.github/workflows/sync-google-docs.yml`:**

```yaml
env:
  GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
  DOCUMENT_ID: '1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4'
```

### Python Script Usage

**`scripts/docs-sync/fetch_google_doc.py`:**

```python
import os
import json
from google.oauth2 import service_account

# Load from environment (GitHub Actions)
creds_json = os.environ.get("GOOGLE_CREDENTIALS")
creds_dict = json.loads(creds_json)

credentials = service_account.Credentials.from_service_account_info(
    creds_dict,
    scopes=[
        "https://www.googleapis.com/auth/documents.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
)
```

---

## 5. Odoo Google Sign-In (Optional)

### Use Existing OAuth Client

**If you already have `odoo_web` OAuth client:**

1. **Verify redirect URI**:
   ```
   https://odoo.insightpulseai.net/auth_oauth/signin
   ```
2. **In Odoo**: Settings → Users & Companies → OAuth Providers
3. **Add Google provider**:
   - **Client ID**: From `odoo_web` OAuth client
   - **Client Secret**: From `odoo_web` OAuth client
   - **Allowed**: `true`
   - **Scope**: `openid email profile`

---

## 6. Local Development (Desktop Client)

### Use Existing Desktop Client

**For CLI tools that open browser:**

```python
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

flow = InstalledAppFlow.from_client_secrets_file(
    'secrets/desktop_client_2.json',  # Download from Console
    SCOPES
)

credentials = flow.run_local_server(port=8080)
```

---

## 7. Security Best Practices

### Secret Storage

**✅ DO:**
- Store service account JSON in GitHub Secrets
- Use environment variables in production
- Rotate keys quarterly
- Limit scopes to minimum required

**❌ DON'T:**
- Commit JSON keys to git
- Share service account emails in public docs
- Use API keys for Drive/Docs
- Grant `roles/owner` to service accounts

### Key Rotation

```bash
# 1. Create new key
gcloud iam service-accounts keys create secrets/docs2code-svc-new.json \
  --iam-account="$SA_EMAIL"

# 2. Update GitHub Secret: GOOGLE_CREDENTIALS

# 3. Test workflows

# 4. Delete old key
gcloud iam service-accounts keys list --iam-account="$SA_EMAIL"
gcloud iam service-accounts keys delete <KEY_ID> \
  --iam-account="$SA_EMAIL"
```

### Scope Minimization

**Only grant what you need:**

| Use Case | Required Scopes |
|----------|----------------|
| Read docs only | `documents.readonly`, `drive.readonly` |
| Edit docs | `documents`, `drive.file` |
| OCR/Vision | `cloud-vision` |
| Sheets read | `spreadsheets.readonly` |
| Full Drive access | `drive` (⚠️ avoid if possible) |

---

## 8. Troubleshooting

### "Insufficient permissions"

**Cause**: Service account not shared on Drive files

**Fix**:
```
1. Find service account email: docs2code-svc@insightpulseai.iam.gserviceaccount.com
2. Share Drive folder/file with this email
3. Grant "Viewer" or "Editor" access
```

### "Invalid credentials"

**Cause**: JSON key not loaded correctly

**Fix**:
```python
# Verify JSON structure
import json
with open('secrets/docs2code-svc.json') as f:
    creds = json.load(f)
    print(creds.get('type'))  # Should be "service_account"
    print(creds.get('client_email'))  # Should be your SA email
```

### "Redirect URI mismatch"

**Cause**: OAuth redirect URI not whitelisted

**Fix**:
```
1. Check n8n callback URL: https://n8n.insightpulseai.net/rest/oauth2-credential/callback
2. Add exact URL to OAuth client in Console
3. No trailing slashes, exact match required
```

### "API not enabled"

```bash
# Enable required APIs
gcloud services enable drive.googleapis.com
gcloud services enable docs.googleapis.com
gcloud services enable sheets.googleapis.com
gcloud services enable vision.googleapis.com
```

---

## 9. Quick Reference

### Service Account Locations

| Environment | Storage Location |
|-------------|-----------------|
| **Local Dev** | `secrets/docs2code-svc.json` (gitignored) |
| **GitHub Actions** | `secrets.GOOGLE_CREDENTIALS` |
| **n8n** | Not used (use OAuth instead) |
| **Odoo** | Not used (use OAuth for SSO) |
| **Supabase Vault** | Store as `google_service_account_json` |

### OAuth Client Locations

| Client | Purpose | Redirect URI |
|--------|---------|-------------|
| `n8n_prod` | n8n workflows | `https://n8n.insightpulseai.net/rest/oauth2-credential/callback` |
| `odoo_web` | Odoo SSO | `https://odoo.insightpulseai.net/auth_oauth/signin` |
| `Desktop client 2` | Local CLI tools | `http://localhost:8080` |

### Enabled APIs (Verify)

```bash
gcloud services list --enabled | grep -E "drive|docs|sheets|vision"
```

**Expected output:**
```
drive.googleapis.com
docs.googleapis.com
sheets.googleapis.com
vision.googleapis.com
```

---

## 10. Next Steps

**After creating credentials:**

1. ✅ **Test GitHub workflow**:
   ```bash
   # Trigger manual workflow
   gh workflow run sync-google-docs.yml
   ```

2. ✅ **Test n8n integration**:
   - Create simple workflow with Google Docs node
   - Verify OAuth connection works
   - Test document fetch

3. ✅ **Test OCR pipeline**:
   ```bash
   python scripts/ocr/test_vision_api.py
   ```

4. ✅ **Update `.env`**:
   ```bash
   echo "GOOGLE_SERVICE_ACCOUNT_FILE=secrets/docs2code-svc.json" >> .env
   ```

5. ✅ **Share Drive folders**:
   - Share all Docs2Code source folders with service account email
   - Verify access by running a test fetch

---

## Summary

**Minimum Required Credentials:**

1. ✅ **Service Account** (`docs2code-svc`)
   - For: GitHub workflows, scheduled ingestion, OCR
   - Key file: `secrets/docs2code-svc.json`
   - GitHub secret: `GOOGLE_CREDENTIALS`

2. ✅ **OAuth Client** (`n8n_prod`)
   - For: n8n Google Docs/Drive/Sheets nodes
   - Configure in: n8n UI → Credentials
   - Redirect: `https://n8n.insightpulseai.net/rest/oauth2-credential/callback`

**Optional:**
- `odoo_web` OAuth client (if using Google SSO in Odoo)
- `Desktop client 2` (for local dev tools)
- API keys (⚠️ only for public APIs, not Drive/Docs)

---

**Repository**: https://github.com/Insightpulseai-net/pulser-agent-framework
**Last Updated**: 2026-01-01
**Maintainer**: InsightPulseAI Team
