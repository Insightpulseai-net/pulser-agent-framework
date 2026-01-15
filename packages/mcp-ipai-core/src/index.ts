#!/usr/bin/env node
/**
 * IPAI MCP Core Server
 *
 * Canonical MCP tool surface for InsightPulse AI agents:
 * - Bolt Agent (backend/infra)
 * - Figma Agent (design/system)
 * - Ask Ces Agent (creative effectiveness)
 * - Scout / Sari-Sari Expert (retail analytics)
 * - FeedMe Agent (content/data)
 *
 * Namespaces:
 * - supabase.* – DB / SaaS core / Odoo mirror / Scout / CES
 * - odoo.* – live Odoo 18 CE/OCA interactions
 * - n8n.* – workflow orchestration
 * - figma.* – design system + Code Connect
 * - github.* – PRs, files, comments
 * - scout.* – retail analytics helpers
 * - ces.* – creative effectiveness helpers
 * - ops.* – cross-stack health / self-healing
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  type Tool
} from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';

// Import tool modules
import { tools as supabaseTools } from './tools/supabase.js';
import { tools as odooTools } from './tools/odoo.js';
import { tools as n8nTools } from './tools/n8n.js';
import { tools as figmaTools } from './tools/figma.js';
import { tools as githubTools } from './tools/github.js';
import { tools as scoutTools } from './tools/scout.js';
import { tools as cesTools } from './tools/ces.js';
import { tools as opsTools } from './tools/ops.js';

// Define tool interface
interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: z.ZodType<unknown> | { type: string; properties: Record<string, unknown>; required?: string[] } | null;
  execute: (params: unknown) => Promise<{ success: boolean; data?: unknown; error?: string }>;
}

// Aggregate all tools
const allTools: ToolDefinition[] = [
  ...supabaseTools,
  ...odooTools,
  ...n8nTools,
  ...figmaTools,
  ...githubTools,
  ...scoutTools,
  ...cesTools,
  ...opsTools
] as ToolDefinition[];

// Create tool lookup map
const toolMap = new Map(allTools.map(tool => [tool.name, tool]));

// Convert Zod schema to JSON Schema format for MCP
function zodToJsonSchema(schema: z.ZodType<unknown> | { type: string; properties: Record<string, unknown>; required?: string[] } | null): Tool['inputSchema'] {
  if (!schema) {
    return { type: 'object', properties: {} };
  }

  // If it's already a JSON schema object
  if ('type' in schema && typeof schema.type === 'string') {
    return schema as Tool['inputSchema'];
  }

  // Try to extract shape from Zod schema
  try {
    const zodSchema = schema as z.ZodObject<z.ZodRawShape>;
    if (zodSchema._def?.typeName === 'ZodObject' && zodSchema.shape) {
      const properties: Record<string, object> = {};
      const required: string[] = [];

      for (const [key, value] of Object.entries(zodSchema.shape)) {
        const field = value as z.ZodTypeAny;
        const fieldDef = field._def;

        let fieldType = 'string';
        let description = fieldDef?.description || key;

        // Determine field type
        if (fieldDef?.typeName === 'ZodNumber') {
          fieldType = 'number';
        } else if (fieldDef?.typeName === 'ZodBoolean') {
          fieldType = 'boolean';
        } else if (fieldDef?.typeName === 'ZodArray') {
          fieldType = 'array';
        } else if (fieldDef?.typeName === 'ZodObject' || fieldDef?.typeName === 'ZodRecord') {
          fieldType = 'object';
        }

        // Handle optional fields
        if (fieldDef?.typeName === 'ZodOptional') {
          const innerDef = fieldDef.innerType?._def;
          description = innerDef?.description || description;
        } else if (fieldDef?.typeName === 'ZodDefault') {
          // Fields with defaults are not required
        } else {
          required.push(key);
        }

        properties[key] = { type: fieldType, description };
      }

      return { type: 'object', properties, required };
    }

    // Handle ZodEffects (refined schemas)
    const typeName = zodSchema._def?.typeName as string;
    if (typeName === 'ZodEffects') {
      const innerSchema = (zodSchema._def as { schema?: z.ZodType<unknown> }).schema;
      if (innerSchema) {
        return zodToJsonSchema(innerSchema);
      }
    }
  } catch {
    // Fall back to empty schema
  }

  return { type: 'object', properties: {} };
}

// Convert internal tool format to MCP Tool format
function toMcpTool(tool: ToolDefinition): Tool {
  return {
    name: tool.name,
    description: tool.description,
    inputSchema: zodToJsonSchema(tool.inputSchema)
  };
}

// Initialize MCP Server
const server = new Server(
  {
    name: 'ipai-core',
    version: '1.0.0'
  },
  {
    capabilities: {
      tools: {}
    }
  }
);

// Handle tools/list request
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: allTools.map(toMcpTool)
  };
});

// Handle tools/call request
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  const tool = toolMap.get(name);
  if (!tool) {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: `Tool not found: ${name}`
          })
        }
      ],
      isError: true
    };
  }

  try {
    // Validate input if schema exists and has parse method
    let validatedArgs: unknown = args || {};
    if (tool.inputSchema && 'parse' in tool.inputSchema && typeof tool.inputSchema.parse === 'function') {
      validatedArgs = tool.inputSchema.parse(args);
    }

    // Execute tool
    const result = await tool.execute(validatedArgs);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ],
      isError: !result.success
    };
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : String(err);
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: `Tool execution failed: ${errorMessage}`
          })
        }
      ],
      isError: true
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Log startup info to stderr (stdout is for JSON-RPC)
  console.error(`IPAI MCP Core Server started`);
  console.error(`Loaded ${allTools.length} tools across ${8} namespaces`);
  console.error(`Namespaces: supabase, odoo, n8n, figma, github, scout, ces, ops`);
}

main().catch((err) => {
  console.error('Server failed to start:', err);
  process.exit(1);
});

// Export for programmatic use
export { allTools, toolMap, server };
