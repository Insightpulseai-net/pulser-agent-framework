#!/usr/bin/env node
/**
 * MCP IPAI Core Server
 *
 * Canonical tool surface for all IPAI agents:
 * - Bolt Agent (backend/infra)
 * - FeedMe Agent (data pipelines)
 * - Ask Ces Agent (creative effectiveness)
 * - Scout Agent (retail analytics)
 * - Figma Agent (design system)
 *
 * Namespaces:
 * - supabase.* – DB / SaaS core / Odoo mirror
 * - odoo.* – Live Odoo 18 CE/OCA
 * - n8n.* – Workflow orchestration
 * - figma.* – Design system + Code Connect
 * - github.* – PRs, files, comments
 * - scout.* – Retail analytics
 * - ces.* – Creative effectiveness
 * - ops.* – Cross-stack health / self-healing
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
  McpError,
  ErrorCode,
} from "@modelcontextprotocol/sdk/types.js";

import { z } from "zod";
import type { ToolContext, McpTool } from "./types.js";

// Import all tool modules
import { tools as supabaseTools } from "./tools/supabase.js";
import { tools as odooTools } from "./tools/odoo.js";
import { tools as n8nTools } from "./tools/n8n.js";
import { tools as figmaTools } from "./tools/figma.js";
import { tools as githubTools } from "./tools/github.js";
import { tools as scoutTools } from "./tools/scout.js";
import { tools as cesTools } from "./tools/ces.js";
import { tools as opsTools } from "./tools/ops.js";

// Aggregate all tools
const allTools: McpTool[] = [
  ...supabaseTools,
  ...odooTools,
  ...n8nTools,
  ...figmaTools,
  ...githubTools,
  ...scoutTools,
  ...cesTools,
  ...opsTools,
];

// Create tool lookup map
const toolMap = new Map<string, McpTool>();
for (const tool of allTools) {
  toolMap.set(tool.name, tool);
}

// Build context from environment variables
function buildContext(): ToolContext {
  const ctx: ToolContext = {
    supabaseUrl: process.env.SUPABASE_URL || "",
    supabaseServiceKey: process.env.SUPABASE_SERVICE_ROLE_KEY || "",
  };

  // Optional Odoo config
  if (process.env.ODOO_URL) {
    ctx.odooUrl = process.env.ODOO_URL;
    ctx.odooDb = process.env.ODOO_DB;
    ctx.odooUser = process.env.ODOO_USER;
    ctx.odooPassword = process.env.ODOO_PASSWORD;
  }

  // Optional n8n config
  if (process.env.N8N_URL) {
    ctx.n8nUrl = process.env.N8N_URL;
    ctx.n8nApiKey = process.env.N8N_API_KEY;
  }

  // Optional Figma config
  if (process.env.FIGMA_TOKEN) {
    ctx.figmaToken = process.env.FIGMA_TOKEN;
  }

  // Optional GitHub config
  if (process.env.GITHUB_TOKEN) {
    ctx.githubToken = process.env.GITHUB_TOKEN;
  }

  return ctx;
}

// Initialize MCP server
const server = new Server(
  {
    name: "mcp-ipai-core",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: allTools.map((tool) => ({
      name: tool.name,
      description: tool.description,
      inputSchema: zodToJsonSchema(tool.inputSchema),
    })),
  };
});

// Helper: Convert Zod schema to JSON Schema (simplified)
function zodToJsonSchema(schema: z.ZodType<unknown>): Record<string, unknown> {
  // Use zod's built-in JSON schema conversion if available
  // For now, return a basic object schema
  try {
    const def = (schema as z.ZodObject<z.ZodRawShape>)._def;
    if (def && "shape" in def && typeof def.shape === "function") {
      const shape = def.shape();
      const properties: Record<string, unknown> = {};
      const required: string[] = [];

      for (const [key, value] of Object.entries(shape)) {
        const zodValue = value as z.ZodTypeAny;
        properties[key] = {
          type: getZodPrimitiveType(zodValue),
          description: zodValue.description || "",
        };
        if (!zodValue.isOptional()) {
          required.push(key);
        }
      }

      return {
        type: "object",
        properties,
        required: required.length > 0 ? required : undefined,
      };
    }
  } catch {
    // Fallback for non-object schemas
  }

  return { type: "object", properties: {} };
}

// Helper: Get primitive type from Zod schema
function getZodPrimitiveType(schema: z.ZodTypeAny): string {
  const typeName = schema._def?.typeName;
  switch (typeName) {
    case "ZodString":
      return "string";
    case "ZodNumber":
      return "number";
    case "ZodBoolean":
      return "boolean";
    case "ZodArray":
      return "array";
    case "ZodObject":
    case "ZodRecord":
      return "object";
    case "ZodOptional":
    case "ZodDefault":
      return getZodPrimitiveType(schema._def.innerType);
    case "ZodEnum":
      return "string";
    case "ZodUnion":
      return "string"; // Simplified
    default:
      return "string";
  }
}

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  const tool = toolMap.get(name);
  if (!tool) {
    throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
  }

  const ctx = buildContext();

  try {
    // Validate input
    const validatedArgs = tool.inputSchema.parse(args || {});

    // Execute tool
    const result = await tool.execute(validatedArgs, ctx);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  } catch (error) {
    if (error instanceof Error) {
      throw new McpError(ErrorCode.InternalError, error.message);
    }
    throw new McpError(ErrorCode.InternalError, String(error));
  }
});

// Start server
async function main() {
  // Validate required config
  if (!process.env.SUPABASE_URL || !process.env.SUPABASE_SERVICE_ROLE_KEY) {
    console.error("Warning: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY not set");
    console.error("Some tools may not function correctly.");
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error(`MCP IPAI Core server running on stdio`);
  console.error(`Loaded ${allTools.length} tools across ${8} namespaces:`);
  console.error(`  - supabase.* (${supabaseTools.length} tools)`);
  console.error(`  - odoo.* (${odooTools.length} tools)`);
  console.error(`  - n8n.* (${n8nTools.length} tools)`);
  console.error(`  - figma.* (${figmaTools.length} tools)`);
  console.error(`  - github.* (${githubTools.length} tools)`);
  console.error(`  - scout.* (${scoutTools.length} tools)`);
  console.error(`  - ces.* (${cesTools.length} tools)`);
  console.error(`  - ops.* (${opsTools.length} tools)`);
}

main().catch((error) => {
  console.error("MCP server failed:", error);
  process.exit(1);
});
