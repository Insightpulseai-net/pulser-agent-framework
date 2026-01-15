/**
 * n8n tools (n8n.*)
 * Workflow orchestration
 */

import { z } from "zod";
import type { McpTool, ToolContext } from "../types.js";

// 3.1 n8n.run_workflow
const runWorkflowSchema = z.object({
  workflow_id: z.union([z.string(), z.number()]).describe("Workflow ID or name"),
  payload: z.record(z.unknown()).optional().describe("Payload to pass to workflow"),
});

async function executeRunWorkflow(
  args: z.infer<typeof runWorkflowSchema>,
  ctx: ToolContext
): Promise<{ execution_id: string; status: string }> {
  if (!ctx.n8nUrl || !ctx.n8nApiKey) {
    throw new Error("n8n not configured");
  }

  const response = await fetch(`${ctx.n8nUrl}/api/v1/workflows/${args.workflow_id}/execute`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-N8N-API-KEY": ctx.n8nApiKey,
    },
    body: JSON.stringify({ data: args.payload || {} }),
  });

  if (!response.ok) {
    throw new Error(`n8n workflow execution failed: ${response.status}`);
  }

  const result = await response.json() as { id: string };
  return {
    execution_id: result.id,
    status: "triggered",
  };
}

// 3.2 n8n.get_execution
const getExecutionSchema = z.object({
  execution_id: z.string().describe("Execution ID to check"),
});

async function executeGetExecution(
  args: z.infer<typeof getExecutionSchema>,
  ctx: ToolContext
): Promise<unknown> {
  if (!ctx.n8nUrl || !ctx.n8nApiKey) {
    throw new Error("n8n not configured");
  }

  const response = await fetch(`${ctx.n8nUrl}/api/v1/executions/${args.execution_id}`, {
    headers: {
      "X-N8N-API-KEY": ctx.n8nApiKey,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to get execution: ${response.status}`);
  }

  return response.json();
}

// 3.3 n8n.list_workflows
const listWorkflowsSchema = z.object({
  active_only: z.boolean().default(false).describe("Only list active workflows"),
  limit: z.number().default(50).describe("Maximum workflows to return"),
});

async function executeListWorkflows(
  args: z.infer<typeof listWorkflowsSchema>,
  ctx: ToolContext
): Promise<unknown[]> {
  if (!ctx.n8nUrl || !ctx.n8nApiKey) {
    throw new Error("n8n not configured");
  }

  const params = new URLSearchParams({
    limit: String(args.limit),
    ...(args.active_only && { active: "true" }),
  });

  const response = await fetch(`${ctx.n8nUrl}/api/v1/workflows?${params}`, {
    headers: {
      "X-N8N-API-KEY": ctx.n8nApiKey,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to list workflows: ${response.status}`);
  }

  const data = await response.json() as { data: unknown[] };
  return data.data || [];
}

export const tools: McpTool[] = [
  {
    name: "n8n.run_workflow",
    description: "Execute an n8n workflow. Main orchestration tool.",
    inputSchema: runWorkflowSchema,
    execute: executeRunWorkflow,
  },
  {
    name: "n8n.get_execution",
    description: "Poll execution result for long-running workflows.",
    inputSchema: getExecutionSchema,
    execute: executeGetExecution,
  },
  {
    name: "n8n.list_workflows",
    description: "List available n8n workflows for discovery.",
    inputSchema: listWorkflowsSchema,
    execute: executeListWorkflows,
  },
];
