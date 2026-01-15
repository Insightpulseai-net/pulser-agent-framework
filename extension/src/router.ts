// extension/src/router.ts
// HMAC signer + POST wrapper for Bridge Kit router

const DEFAULT_ROUTER_URL = "https://n8n.insightpulseai.net/webhook/bridge-router";

// NOTE: In production, DO NOT hardcode secrets in the extension.
// Use a short-lived session token from your backend or use per-user secrets provisioned securely.
// This is a functional reference implementation.

export type BridgeAction =
  | "context.capture"
  | "ai.summarize"
  | "github.issue_create"
  | "github.branch_create"
  | "github.file_upsert"
  | "github.commit_create"
  | "github.pr_open"
  | "drive.file_list"
  | "drive.file_read"
  | "docs.text_append"
  | "docs.create"
  | "sheets.row_append"
  | "sheets.update"
  | "slack.message_send";

export type BridgeSource =
  | "chrome-extension"
  | "claude-code-cli"
  | "claude-desktop-mcp"
  | "apps-script"
  | "n8n-internal"
  | "api-direct";

export type BridgeEnvelope = {
  version: string; // must match BRIDGE_VERSION on n8n
  action: BridgeAction;
  source: BridgeSource;
  timestamp: string; // ISO
  idempotencyKey?: string;
  correlationId?: string;
  payload: Record<string, unknown>;
};

function toHex(buffer: ArrayBuffer): string {
  return Array.from(new Uint8Array(buffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function hmacSha256Hex(secret: string, message: string): Promise<string> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(message));
  return toHex(sig);
}

export async function callBridgeRouter(params: {
  routerUrl?: string;
  hmacSecret: string;
  envelope: BridgeEnvelope;
}): Promise<unknown> {
  const routerUrl = params.routerUrl || DEFAULT_ROUTER_URL;

  // IMPORTANT: signature must be computed on the EXACT raw JSON string sent
  const body = JSON.stringify(params.envelope);

  const hex = await hmacSha256Hex(params.hmacSecret, body);
  const signature = `sha256=${hex}`;

  const res = await fetch(routerUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-bridge-signature": signature,
    },
    body,
  });

  const text = await res.text();
  let json: unknown = null;
  try {
    json = JSON.parse(text);
  } catch {
    // keep as text
  }

  if (!res.ok) {
    const msg = typeof json === "object" ? JSON.stringify(json) : text;
    throw new Error(`Bridge router error ${res.status}: ${msg}`);
  }

  return json ?? text;
}
