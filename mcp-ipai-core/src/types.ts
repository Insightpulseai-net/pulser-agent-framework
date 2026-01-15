/**
 * Common types for MCP IPAI Core tools
 */

import { z } from "zod";

// Tool context passed to all tool executions
export interface ToolContext {
  supabaseUrl: string;
  supabaseServiceKey: string;
  odooUrl?: string;
  odooDb?: string;
  odooUser?: string;
  odooPassword?: string;
  n8nUrl?: string;
  n8nApiKey?: string;
  figmaToken?: string;
  githubToken?: string;
}

// Generic MCP tool definition
export interface McpTool<T = unknown> {
  name: string;
  description: string;
  inputSchema: z.ZodType<T>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  execute: (args: any, ctx: ToolContext) => Promise<unknown>;
}

// Helper to create typed tools
export function createTool<T>(
  name: string,
  description: string,
  inputSchema: z.ZodType<T>,
  execute: (args: T, ctx: ToolContext) => Promise<unknown>
): McpTool<T> {
  return { name, description, inputSchema, execute };
}

// Health check result
export const HealthCheckResultSchema = z.object({
  status: z.enum(["healthy", "degraded", "broken"]),
  checks: z.array(z.object({
    name: z.string(),
    passed: z.boolean(),
    message: z.string().optional(),
    duration_ms: z.number().optional(),
  })),
  timestamp: z.string(),
});

export type HealthCheckResult = z.infer<typeof HealthCheckResultSchema>;

// SQL query result
export interface SqlQueryResult {
  rows: Record<string, unknown>[];
  rowCount: number;
  fields: string[];
}

// Table filter for structured queries
export const TableFilterSchema = z.object({
  column: z.string(),
  op: z.enum(["eq", "neq", "gt", "gte", "lt", "lte", "like", "ilike", "in", "is"]),
  value: z.union([z.string(), z.number(), z.boolean(), z.null(), z.array(z.string())]),
});

export type TableFilter = z.infer<typeof TableFilterSchema>;

// Order by specification
export const OrderBySchema = z.object({
  column: z.string(),
  direction: z.enum(["asc", "desc"]).default("asc"),
});

export type OrderBy = z.infer<typeof OrderBySchema>;
