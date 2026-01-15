// extension/src/content.ts

interface BridgeContextRequest {
  type: "BRIDGE_GET_CONTEXT";
}

interface BridgeContextResponse {
  ok: boolean;
  payload?: {
    url: string;
    title: string;
    selection: string;
    htmlSnippet: string;
  };
}

function getSelectionText(): string {
  return window.getSelection()?.toString() || "";
}

chrome.runtime.onMessage.addListener(
  (
    req: BridgeContextRequest | { type: string },
    _sender: chrome.runtime.MessageSender,
    sendResponse: (response: BridgeContextResponse) => void
  ) => {
    if (req?.type === "BRIDGE_GET_CONTEXT") {
      sendResponse({
        ok: true,
        payload: {
          url: location.href,
          title: document.title,
          selection: getSelectionText(),
          // Keep small to avoid huge payloads
          htmlSnippet: document.body?.innerText?.slice(0, 4000) || "",
        },
      });
      return;
    }
  }
);
