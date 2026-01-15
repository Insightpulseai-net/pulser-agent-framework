#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
  McpError,
  ErrorCode,
} from "@modelcontextprotocol/sdk/types.js";
import * as crypto from "crypto";

// Configuration from environment
const N8N_WEBHOOK_URL = process.env.N8N_WEBHOOK_URL || "https://n8n.insightpulseai.net/webhook/bridge-router";
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || "";

// Initialize MCP server
const server = new Server(
  { name: "bridge-kit-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// Tool definitions matching the router contract
const TOOLS = [
  {
    name: "github_create_issue",
    description: "Create a GitHub issue via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        repo: { type: "string", description: "Repository in owner/repo format" },
        title: { type: "string", description: "Issue title" },
        body: { type: "string", description: "Issue body (markdown)" },
        labels: { type: "array", items: { type: "string" }, description: "Labels to apply" }
      },
      required: ["repo", "title"]
    }
  },
  {
    name: "github_create_pr",
    description: "Create a GitHub pull request via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        repo: { type: "string", description: "Repository in owner/repo format" },
        title: { type: "string", description: "PR title" },
        body: { type: "string", description: "PR description" },
        head: { type: "string", description: "Source branch" },
        base: { type: "string", description: "Target branch (default: main)" }
      },
      required: ["repo", "title", "head"]
    }
  },
  {
    name: "docs_append_text",
    description: "Append text to a Google Doc via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        documentId: { type: "string", description: "Google Doc ID" },
        text: { type: "string", description: "Text to append" }
      },
      required: ["documentId", "text"]
    }
  },
  {
    name: "sheets_append_row",
    description: "Append a row to a Google Sheet via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        spreadsheetId: { type: "string", description: "Google Sheet ID" },
        sheetName: { type: "string", description: "Sheet name (default: Sheet1)" },
        values: { type: "array", items: { type: "string" }, description: "Row values" }
      },
      required: ["spreadsheetId", "values"]
    }
  },
  {
    name: "slack_send_message",
    description: "Send a Slack message via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        channel: { type: "string", description: "Channel name or ID" },
        message: { type: "string", description: "Message text" }
      },
      required: ["channel", "message"]
    }
  },
  {
    name: "ai_summarize",
    description: "Summarize content using Claude via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        content: { type: "string", description: "Content to summarize" }
      },
      required: ["content"]
    }
  },
  {
    name: "drive_search",
    description: "Search Google Drive via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        query: { type: "string", description: "Search query" }
      },
      required: ["query"]
    }
  },
  {
    name: "context_capture",
    description: "Capture and log context via Bridge Kit router",
    inputSchema: {
      type: "object" as const,
      properties: {
        context: { type: "object", description: "Context data to capture" }
      },
      required: ["context"]
    }
  }
];

// Tool name → action mapping
const ACTION_MAP: Record<string, string> = {
  github_create_issue: "github.issue_create",
  github_create_pr: "github.pr_create",
  docs_append_text: "docs.text_append",
  sheets_append_row: "sheets.row_append",
  slack_send_message: "slack.message_send",
  ai_summarize: "ai.summarize",
  drive_search: "drive.file_list",
  context_capture: "context.capture"
};

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  const action = ACTION_MAP[name];
  if (!action) {
    throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
  }

  // Build envelope
  const envelope = {
    version: "1.0.0",
    action,
    source: "claude-desktop-mcp",
    timestamp: new Date().toISOString(),
    idempotencyKey: crypto.randomUUID(),
    correlationId: crypto.randomUUID(),
    context: {},
    payload: buildPayload(name, args),
    target: buildTarget(name, args)
  };

  // Dispatch to n8n
  const result = await dispatchToRouter(envelope);

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(result, null, 2)
      }
    ]
  };
});

function buildPayload(toolName: string, args: Record<string, unknown> | undefined): Record<string, unknown> {
  if (!args) return {};

  switch (toolName) {
    case "github_create_issue":
      return { title: args.title, body: args.body, labels: args.labels };
    case "github_create_pr":
      return { title: args.title, body: args.body, head: args.head, base: args.base || "main" };
    case "docs_append_text":
      return { text: args.text };
    case "sheets_append_row":
      return { values: args.values };
    case "slack_send_message":
      return { message: args.message };
    case "ai_summarize":
      return { content: args.content };
    case "drive_search":
      return { query: args.query };
    case "context_capture":
      return { data: args.context };
    default:
      return args;
  }
}

function buildTarget(toolName: string, args: Record<string, unknown> | undefined): Record<string, unknown> {
  if (!args) return {};

  switch (toolName) {
    case "github_create_issue":
    case "github_create_pr":
      return { repo: args.repo };
    case "docs_append_text":
      return { documentId: args.documentId };
    case "sheets_append_row":
      return { spreadsheetId: args.spreadsheetId, sheetName: args.sheetName || "Sheet1" };
    case "slack_send_message":
      return { channel: args.channel };
    default:
      return {};
  }
}

async function dispatchToRouter(envelope: Record<string, unknown>): Promise<Record<string, unknown>> {
  const body = JSON.stringify(envelope);

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Source": "claude-desktop-mcp",
    "X-Request-ID": envelope.correlationId as string
  };

  // Add HMAC signature if secret configured
  if (WEBHOOK_SECRET) {
    const signature = crypto
      .createHmac("sha256", WEBHOOK_SECRET)
      .update(body)
      .digest("hex");
    headers["X-Signature"] = `sha256=${signature}`;
  }

  const response = await fetch(N8N_WEBHOOK_URL, {
    method: "POST",
    headers,
    body
  });

  if (!response.ok) {
    throw new McpError(
      ErrorCode.InternalError,
      `Router returned ${response.status}: ${response.statusText}`
    );
  }

  return response.json();
}

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Bridge Kit MCP server running on stdio");
}

main().catch(console.error);
