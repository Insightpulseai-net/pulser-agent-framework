#!/usr/bin/env node
/**
 * bridge.js
 * Emits BridgeEnvelope and POSTs to n8n router with x-bridge-signature.
 *
 * Usage:
 *   node bridge.js context.capture --payload '{"text":"hello"}'
 *   node bridge.js github.issue_create --payload-file payload.json
 *   node bridge.js ai.summarize --payload '{"text":"summarize this"}'
 *
 * Env:
 *   BRIDGE_ROUTER_URL (default: https://n8n.insightpulseai.net/webhook/bridge-router)
 *   BRIDGE_HMAC_SECRET (required)
 *   BRIDGE_VERSION (default: 1.0.0)
 *
 * Supported actions:
 *   context.capture, ai.summarize, github.issue_create, github.branch_create,
 *   github.file_upsert, github.commit_create, github.pr_open, drive.file_list,
 *   drive.file_read, docs.text_append, docs.create, sheets.row_append,
 *   sheets.update, slack.message_send
 */

import crypto from "crypto";
import fs from "fs";

const ROUTER_URL =
  process.env.BRIDGE_ROUTER_URL ||
  "https://n8n.insightpulseai.net/webhook/bridge-router";
const HMAC_SECRET = process.env.BRIDGE_HMAC_SECRET;
const VERSION = process.env.BRIDGE_VERSION || "1.0.0";

if (!HMAC_SECRET) {
  console.error("Error: Missing env BRIDGE_HMAC_SECRET");
  console.error("");
  console.error("Set it with:");
  console.error("  export BRIDGE_HMAC_SECRET='your-secret-here'");
  process.exit(2);
}

function sign(body) {
  const hex = crypto
    .createHmac("sha256", HMAC_SECRET)
    .update(body, "utf8")
    .digest("hex");
  return `sha256=${hex}`;
}

function nowIso() {
  return new Date().toISOString();
}

function idem() {
  return `bk_${Date.now()}_${crypto.randomBytes(6).toString("hex")}`;
}

function printUsage() {
  console.error(`Usage: node bridge.js <action> [options]

Actions:
  context.capture      Capture and process context
  ai.summarize         Summarize content with AI
  github.issue_create  Create a GitHub issue
  github.branch_create Create a GitHub branch
  github.file_upsert   Create or update a file in GitHub
  github.commit_create Create a commit
  github.pr_open       Open a pull request
  drive.file_list      List Google Drive files
  drive.file_read      Read a Google Drive file
  docs.text_append     Append text to Google Doc
  docs.create          Create a new Google Doc
  sheets.row_append    Append row to Google Sheet
  sheets.update        Update Google Sheet
  slack.message_send   Send a Slack message

Options:
  --payload '{...}'       JSON payload string
  --payload-file file.json  Read payload from file
  --correlation-id ID     Optional correlation ID for tracing

Examples:
  node bridge.js context.capture --payload '{"text":"hello world"}'
  node bridge.js github.issue_create --payload-file issue.json
  node bridge.js ai.summarize --payload '{"text":"long text to summarize"}'
`);
}

function parseArgs() {
  const [, , action, ...rest] = process.argv;

  if (!action || action === "--help" || action === "-h") {
    printUsage();
    process.exit(action ? 0 : 2);
  }

  let payloadStr = null;
  let payloadFile = null;
  let correlationId = null;

  for (let i = 0; i < rest.length; i++) {
    if (rest[i] === "--payload") payloadStr = rest[++i];
    if (rest[i] === "--payload-file") payloadFile = rest[++i];
    if (rest[i] === "--correlation-id") correlationId = rest[++i];
  }

  let payload = {};
  if (payloadFile) {
    try {
      payload = JSON.parse(fs.readFileSync(payloadFile, "utf8"));
    } catch (e) {
      console.error(`Error reading payload file: ${e.message}`);
      process.exit(2);
    }
  } else if (payloadStr) {
    try {
      payload = JSON.parse(payloadStr);
    } catch (e) {
      console.error(`Error parsing payload JSON: ${e.message}`);
      process.exit(2);
    }
  }

  return { action, payload, correlationId };
}

async function main() {
  const { action, payload, correlationId } = parseArgs();

  const envelope = {
    version: VERSION,
    action,
    source: "claude-code-cli",
    timestamp: nowIso(),
    idempotencyKey: idem(),
    ...(correlationId && { correlationId }),
    payload,
  };

  const body = JSON.stringify(envelope);
  const sig = sign(body);

  if (process.env.BRIDGE_DEBUG) {
    console.error("DEBUG: Envelope:", JSON.stringify(envelope, null, 2));
    console.error("DEBUG: Signature:", sig);
    console.error("DEBUG: Router URL:", ROUTER_URL);
  }

  const res = await fetch(ROUTER_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-bridge-signature": sig,
    },
    body,
  });

  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {
    // keep as text
  }

  if (!res.ok) {
    console.error(`Router error ${res.status}:`, json ?? text);
    process.exit(1);
  }

  console.log(JSON.stringify(json ?? { raw: text }, null, 2));
}

main().catch((e) => {
  console.error(e?.stack || e?.message || String(e));
  process.exit(1);
});
