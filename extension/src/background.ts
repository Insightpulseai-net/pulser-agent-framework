// extension/src/background.ts
import { callBridgeRouter, BridgeEnvelope } from "./router";

const BRIDGE_VERSION = "1.0.0";
const ROUTER_URL = "https://n8n.insightpulseai.net/webhook/bridge-router";

// demo secret storage: chrome.storage.local
// (replace with your real provisioning flow)
async function getHmacSecret(): Promise<string> {
  const { bridgeHmacSecret } = await chrome.storage.local.get(["bridgeHmacSecret"]);
  if (!bridgeHmacSecret) throw new Error("Missing bridgeHmacSecret in chrome.storage.local");
  return bridgeHmacSecret;
}

function nowIso(): string {
  return new Date().toISOString();
}

function makeIdempotencyKey(): string {
  // simple deterministic-ish key (replace with UUID if desired)
  return `bk_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

interface BridgeCaptureRequest {
  type: "BRIDGE_CAPTURE_AND_SEND";
  correlationId?: string;
  payload?: {
    url?: string;
    title?: string;
    selection?: string;
    htmlSnippet?: string;
    instruction?: string;
  };
}

interface BridgeResponse {
  ok: boolean;
  result?: unknown;
  error?: string;
}

chrome.runtime.onMessage.addListener(
  (
    req: BridgeCaptureRequest | { type: string },
    _sender: chrome.runtime.MessageSender,
    sendResponse: (response: BridgeResponse) => void
  ) => {
    (async () => {
      try {
        if (req?.type === "BRIDGE_CAPTURE_AND_SEND") {
          const captureReq = req as BridgeCaptureRequest;
          const secret = await getHmacSecret();

          const env: BridgeEnvelope = {
            version: BRIDGE_VERSION,
            action: "context.capture",
            source: "chrome-extension",
            timestamp: nowIso(),
            idempotencyKey: makeIdempotencyKey(),
            correlationId: captureReq.correlationId || undefined,
            payload: {
              url: captureReq.payload?.url,
              title: captureReq.payload?.title,
              selection: captureReq.payload?.selection,
              htmlSnippet: captureReq.payload?.htmlSnippet,
              instruction: captureReq.payload?.instruction,
            },
          };

          const result = await callBridgeRouter({
            routerUrl: ROUTER_URL,
            hmacSecret: secret,
            envelope: env,
          });

          sendResponse({ ok: true, result });
          return;
        }

        sendResponse({ ok: false, error: "Unknown message type" });
      } catch (e: unknown) {
        const error = e instanceof Error ? e.message : String(e);
        sendResponse({ ok: false, error });
      }
    })();

    return true; // async
  }
);
