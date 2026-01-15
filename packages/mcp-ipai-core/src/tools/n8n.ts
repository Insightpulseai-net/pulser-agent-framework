/**
 * n8n tools for IPAI MCP Server
 * Namespace: n8n.*
 */

import { getConfig } from '../config.js';
import {
  N8nRunWorkflowSchema,
  N8nGetExecutionSchema,
  type N8nRunWorkflow,
  type N8nGetExecution,
  type ToolResult
} from '../types.js';

interface N8nWorkflow {
  id: number | string;
  name: string;
  active: boolean;
  createdAt: string;
  updatedAt: string;
}

interface N8nExecution {
  id: string;
  finished: boolean;
  mode: string;
  startedAt: string;
  stoppedAt?: string;
  status: 'waiting' | 'running' | 'success' | 'error';
  data?: {
    resultData?: {
      runData?: Record<string, unknown>;
    };
  };
}

async function n8nFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const config = getConfig();

  const response = await fetch(`${config.n8n.baseUrl}/api/v1${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-N8N-API-KEY': config.n8n.apiKey,
      ...options.headers
    }
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`n8n API error (${response.status}): ${error}`);
  }

  return response.json() as Promise<T>;
}

/**
 * n8n.run_workflow - Execute a workflow by ID or name
 */
async function runWorkflow(params: N8nRunWorkflow): Promise<ToolResult<{ execution_id: string; status: string }>> {
  try {
    // If workflow_id is a string name, resolve it first
    let workflowId = params.workflow_id;

    if (typeof workflowId === 'string' && isNaN(Number(workflowId))) {
      // Search for workflow by name
      const workflows = await n8nFetch<{ data: N8nWorkflow[] }>('/workflows');
      const found = workflows.data.find(w => w.name === workflowId);
      if (!found) {
        return {
          success: false,
          error: `Workflow not found: ${workflowId}`
        };
      }
      workflowId = found.id;
    }

    // Execute the workflow
    const result = await n8nFetch<{ data: { executionId: string } }>(`/workflows/${workflowId}/execute`, {
      method: 'POST',
      body: JSON.stringify(params.payload || {})
    });

    return {
      success: true,
      data: {
        execution_id: result.data.executionId,
        status: 'running'
      }
    };
  } catch (err) {
    return {
      success: false,
      error: `Workflow execution failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * n8n.get_execution - Get execution status and result
 */
async function getExecution(params: N8nGetExecution): Promise<ToolResult<N8nExecution>> {
  try {
    const execution = await n8nFetch<{ data: N8nExecution }>(`/executions/${params.execution_id}`);
    return { success: true, data: execution.data };
  } catch (err) {
    return {
      success: false,
      error: `Failed to get execution: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * n8n.list_workflows - List available workflows
 */
async function listWorkflows(): Promise<ToolResult<N8nWorkflow[]>> {
  try {
    const result = await n8nFetch<{ data: N8nWorkflow[] }>('/workflows');
    return {
      success: true,
      data: result.data.map(w => ({
        id: w.id,
        name: w.name,
        active: w.active,
        createdAt: w.createdAt,
        updatedAt: w.updatedAt
      }))
    };
  } catch (err) {
    return {
      success: false,
      error: `Failed to list workflows: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * n8n.health_check - Check n8n instance health
 */
async function healthCheck(): Promise<ToolResult<{ status: string; version?: string }>> {
  const config = getConfig();

  try {
    const response = await fetch(`${config.n8n.baseUrl}/healthz`, {
      method: 'GET',
      headers: {
        'X-N8N-API-KEY': config.n8n.apiKey
      }
    });

    if (response.ok) {
      return {
        success: true,
        data: { status: 'healthy' }
      };
    } else {
      return {
        success: true,
        data: { status: 'degraded' }
      };
    }
  } catch (err) {
    return {
      success: false,
      error: `n8n health check failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

// Export tools array for aggregation
export const tools = [
  {
    name: 'n8n.run_workflow',
    description: 'Execute an n8n workflow by ID or name. Returns execution ID for polling.',
    inputSchema: N8nRunWorkflowSchema,
    execute: runWorkflow
  },
  {
    name: 'n8n.get_execution',
    description: 'Poll execution status and result for a running/completed workflow.',
    inputSchema: N8nGetExecutionSchema,
    execute: getExecution
  },
  {
    name: 'n8n.list_workflows',
    description: 'List all available n8n workflows for discovery.',
    inputSchema: null,
    execute: listWorkflows
  },
  {
    name: 'n8n.health_check',
    description: 'Check n8n instance health and availability.',
    inputSchema: null,
    execute: healthCheck
  }
];
