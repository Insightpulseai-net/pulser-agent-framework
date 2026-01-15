// extension/src/popup.ts

interface TabContext {
  ok: boolean;
  payload?: {
    url: string;
    title: string;
    selection: string;
    htmlSnippet: string;
  };
}

interface BridgeResponse {
  ok: boolean;
  result?: unknown;
  error?: string;
}

async function getActiveTab(): Promise<chrome.tabs.Tab> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) throw new Error("No active tab");
  return tab;
}

document.addEventListener("DOMContentLoaded", async () => {
  const instructionEl = document.getElementById("instruction") as HTMLTextAreaElement;
  const statusEl = document.getElementById("status") as HTMLDivElement;
  const sendBtn = document.getElementById("send") as HTMLButtonElement;

  sendBtn.onclick = async () => {
    try {
      statusEl.textContent = "Capturing…";
      sendBtn.disabled = true;

      const tab = await getActiveTab();
      const ctx: TabContext = await chrome.tabs.sendMessage(tab.id!, { type: "BRIDGE_GET_CONTEXT" });
      if (!ctx?.ok) throw new Error("Failed to capture context");

      statusEl.textContent = "Sending…";
      const resp: BridgeResponse = await chrome.runtime.sendMessage({
        type: "BRIDGE_CAPTURE_AND_SEND",
        payload: { ...ctx.payload, instruction: instructionEl.value },
      });

      if (!resp?.ok) throw new Error(resp?.error || "Router call failed");

      statusEl.textContent = "OK ✅";
    } catch (e: unknown) {
      const error = e instanceof Error ? e.message : String(e);
      statusEl.textContent = `Error: ${error}`;
    } finally {
      sendBtn.disabled = false;
    }
  };
});
