/**
 * Core types for IPAI MCP Server
 */

import { z } from 'zod';

// Tool result types
export interface ToolResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}

// Health check types
export type HealthStatus = 'healthy' | 'degraded' | 'broken';

export interface HealthCheckResult {
  status: HealthStatus;
  checks: Array<{
    name: string;
    status: HealthStatus;
    message?: string;
    latencyMs?: number;
  }>;
  timestamp: string;
}

// Supabase types
export const SqlQuerySchema = z.object({
  sql: z.string().describe('Read-only SQL query (SELECT only)'),
  params: z.record(z.union([z.string(), z.number(), z.boolean()])).optional()
    .describe('Query parameters for prepared statements')
});

export const RpcCallSchema = z.object({
  schema: z.string().describe('Database schema (e.g., "public", "scout", "ces")'),
  function: z.string().describe('Function name to call'),
  args: z.record(z.unknown()).optional().describe('Function arguments')
});

export const TableSelectSchema = z.object({
  schema: z.string().describe('Database schema (e.g., "odoo_mirror", "scout", "ces", "saas")'),
  table: z.string().describe('Table name'),
  filters: z.array(z.object({
    column: z.string(),
    op: z.enum(['eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'like', 'ilike', 'in', 'is']),
    value: z.unknown()
  })).optional().describe('Filter conditions'),
  limit: z.number().default(100).describe('Maximum rows to return'),
  order_by: z.object({
    column: z.string(),
    direction: z.enum(['asc', 'desc'])
  }).optional().describe('Sort order')
});

// Odoo types
export const OdooSearchSchema = z.object({
  model: z.string().describe('Odoo model name (e.g., "res.partner", "account.move")'),
  domain: z.array(z.unknown()).describe('Odoo domain filter as JSON array'),
  fields: z.array(z.string()).describe('Fields to fetch'),
  limit: z.number().default(100).describe('Maximum records to return')
});

export const OdooMirrorSyncSchema = z.object({
  mode: z.enum(['full', 'delta']).describe('Sync mode: full rebuild or incremental'),
  entities: z.array(z.string()).describe('Entity names to sync (e.g., ["res_partner", "account_move"])')
});

// n8n types
export const N8nRunWorkflowSchema = z.object({
  workflow_id: z.union([z.string(), z.number()]).describe('Workflow ID or name'),
  payload: z.record(z.unknown()).optional().describe('Payload to pass to workflow')
});

export const N8nGetExecutionSchema = z.object({
  execution_id: z.string().describe('Execution ID to poll')
});

// Figma types
export const FigmaSyncProjectSchema = z.object({
  project_key: z.string().describe('Figma project key'),
  mode: z.enum(['full', 'delta']).describe('Sync mode'),
  include_tokens: z.boolean().default(true).describe('Include design tokens')
});

// GitHub types
export const GitHubCreatePrSchema = z.object({
  owner: z.string().describe('Repository owner'),
  repo: z.string().describe('Repository name'),
  title: z.string().describe('PR title'),
  body: z.string().describe('PR description'),
  head: z.string().describe('Feature branch name'),
  base: z.string().default('main').describe('Base branch')
});

export const GitHubCommentPrSchema = z.object({
  owner: z.string(),
  repo: z.string(),
  pr_number: z.number().describe('Pull request number'),
  body: z.string().describe('Comment content')
});

export const GitHubGetFileSchema = z.object({
  owner: z.string(),
  repo: z.string(),
  path: z.string().describe('File path in repository'),
  ref: z.string().optional().describe('Git ref (branch, tag, commit)')
});

// Scout types
export const ScoutTxInsightSchema = z.object({
  question: z.string().describe('Plain-language question about Scout transaction data')
});

export const ScoutSeedDemoSchema = z.object({
  tenant_code: z.string().describe('Tenant identifier'),
  mode: z.enum(['reset', 'append']).describe('Seed mode: reset existing or append')
});

// CES types
export const CesCampaignOverviewSchema = z.object({
  campaign_code: z.string().optional().describe('Campaign code'),
  campaign_id: z.string().optional().describe('Campaign ID (UUID)')
}).refine(data => data.campaign_code || data.campaign_id, {
  message: 'Either campaign_code or campaign_id must be provided'
});

export const CesLinkFigmaSchema = z.object({
  campaign_code: z.string().describe('Campaign code'),
  figma_file_key: z.string().describe('Figma file key'),
  node_id: z.string().optional().describe('Specific node ID in Figma file')
});

// Ops types
export const DbLintSummarySchema = z.object({
  limit: z.number().default(20).describe('Maximum issues to return'),
  severity: z.enum(['error', 'warning', 'info']).optional().describe('Filter by severity')
});

// Type exports
export type SqlQuery = z.infer<typeof SqlQuerySchema>;
export type RpcCall = z.infer<typeof RpcCallSchema>;
export type TableSelect = z.infer<typeof TableSelectSchema>;
export type OdooSearch = z.infer<typeof OdooSearchSchema>;
export type OdooMirrorSync = z.infer<typeof OdooMirrorSyncSchema>;
export type N8nRunWorkflow = z.infer<typeof N8nRunWorkflowSchema>;
export type N8nGetExecution = z.infer<typeof N8nGetExecutionSchema>;
export type FigmaSyncProject = z.infer<typeof FigmaSyncProjectSchema>;
export type GitHubCreatePr = z.infer<typeof GitHubCreatePrSchema>;
export type GitHubCommentPr = z.infer<typeof GitHubCommentPrSchema>;
export type GitHubGetFile = z.infer<typeof GitHubGetFileSchema>;
export type ScoutTxInsight = z.infer<typeof ScoutTxInsightSchema>;
export type ScoutSeedDemo = z.infer<typeof ScoutSeedDemoSchema>;
export type CesCampaignOverview = z.infer<typeof CesCampaignOverviewSchema>;
export type CesLinkFigma = z.infer<typeof CesLinkFigmaSchema>;
export type DbLintSummary = z.infer<typeof DbLintSummarySchema>;
