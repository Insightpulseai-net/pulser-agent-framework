# Bridge Kit Chrome Extension

Chrome MV3 extension for capturing page context and routing to the n8n Bridge Kit workflow with HMAC authentication.

## Features

- Captures page URL, title, text selection, and content
- Routes context to n8n webhook with HMAC-SHA256 signature
- Supports custom instructions for AI processing
- MV3 compliant (service worker, no persistent background)

## Setup

### 1. Install dependencies

```bash
cd extension
npm install
```

### 2. Build

```bash
npm run build
```

### 3. Configure HMAC secret

Before using the extension, you need to provision the HMAC secret in Chrome storage.

**Option A: Via DevTools console (dev only)**

1. Load the extension in Chrome
2. Go to `chrome://extensions`
3. Click "Service Worker" under Bridge Kit extension
4. In the console, run:

```js
chrome.storage.local.set({ bridgeHmacSecret: 'YOUR_SECRET_HERE' });
```

**Option B: Via options page (production)**

Implement an options page that securely provisions the secret (recommended for real deployments).

### 4. Load in Chrome

1. Go to `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension` folder

## Usage

1. Navigate to any webpage
2. Optionally select text
3. Click the Bridge Kit extension icon
4. Enter an instruction (e.g., "summarize this page")
5. Click "Send to Router"

## Development

```bash
# Watch mode for development
npm run watch

# Type check
npm run typecheck
```

## Architecture

```
extension/
├── src/
│   ├── router.ts      # HMAC signer + fetch wrapper
│   ├── background.ts  # Service worker (message handler)
│   ├── content.ts     # Content script (DOM context capture)
│   └── popup.ts       # Popup UI logic
├── dist/              # Built files (generated)
├── manifest.json      # MV3 manifest
├── popup.html         # Popup UI
├── package.json
└── tsconfig.json
```

## Security Notes

- **Never hardcode secrets** in the extension source for production
- Use a backend service to provision short-lived tokens
- The HMAC secret should be unique per user/installation
- Consider using a secure provisioning flow via your auth system

## Supported Router Actions

The extension currently sends `context.capture` action by default. The router handles:

- `context.capture` - Capture page context
- `ai.summarize` - Summarize with AI
- `github.issue_create` - Create GitHub issue
- `docs.text_append` - Append to Google Doc
- `sheets.row_append` - Append to Google Sheet
- `slack.message_send` - Send Slack message

See the full list in `router.ts`.
