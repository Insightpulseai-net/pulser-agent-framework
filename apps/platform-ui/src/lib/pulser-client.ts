/**
 * Pulser Agent Client
 *
 * Calls Pulser agents which in turn use the MCP IPAI Core tools.
 */

export interface ToolCall {
  server: string;
  tool: string;
  input: Record<string, unknown>;
}

export interface AgentRequest {
  task: string;
  tool_call?: ToolCall;
  context?: Record<string, unknown>;
}

export interface AgentResponse {
  success: boolean;
  result?: unknown;
  error?: string;
}

const PULSER_API_URL = process.env.NEXT_PUBLIC_PULSER_API_URL || "https://mcp.insightpulseai.net";

export async function callPulserAgent(
  agentName: string,
  request: AgentRequest
): Promise<AgentResponse> {
  try {
    const response = await fetch(`${PULSER_API_URL}/agents/${agentName}/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Agent call failed: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      result: data,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

// Convenience function to call MCP tools directly via Bolt agent
export async function callMcpTool(
  server: string,
  tool: string,
  input: Record<string, unknown>
): Promise<AgentResponse> {
  return callPulserAgent("bolt", {
    task: `Execute MCP tool: ${tool}`,
    tool_call: { server, tool, input },
  });
}

// Pre-configured tool callers
export const mcpTools = {
  supabase: {
    healthCheck: () => callMcpTool("mcp-ipai-core", "supabase.health_check", {}),
    tableSelect: (schema: string, table: string, filters?: unknown[], limit?: number) =>
      callMcpTool("mcp-ipai-core", "supabase.table_select", { schema, table, filters, limit }),
    sqlQuery: (sql: string, params?: Record<string, unknown>) =>
      callMcpTool("mcp-ipai-core", "supabase.sql_query", { sql, params }),
  },
  ops: {
    stackHealth: (include?: string[]) =>
      callMcpTool("mcp-ipai-core", "ops.stack_health", { include }),
    dbLintSummary: (severity?: string, limit?: number) =>
      callMcpTool("mcp-ipai-core", "ops.db_lint_summary", { severity, limit }),
  },
  scout: {
    txInsight: (question: string, options?: Record<string, unknown>) =>
      callMcpTool("mcp-ipai-core", "scout.tx_insight", { question, ...options }),
    goldHealth: () => callMcpTool("mcp-ipai-core", "scout.gold_health", {}),
  },
  ces: {
    campaignOverview: (campaignCode?: string, campaignId?: string) =>
      callMcpTool("mcp-ipai-core", "ces.campaign_overview", { campaign_code: campaignCode, campaign_id: campaignId }),
    healthCheck: () => callMcpTool("mcp-ipai-core", "ces.health_check", {}),
  },
  figma: {
    healthCheck: () => callMcpTool("mcp-ipai-core", "figma.health_check", {}),
    auditDesignSystem: (projectKey?: string) =>
      callMcpTool("mcp-ipai-core", "figma.audit_design_system", { project_key: projectKey }),
  },
};
