/**
 * Figma tools for IPAI MCP Server
 * Namespace: figma.*
 */

import { getConfig } from '../config.js';
import {
  FigmaSyncProjectSchema,
  type FigmaSyncProject,
  type HealthCheckResult,
  type ToolResult
} from '../types.js';

const FIGMA_API_BASE = 'https://api.figma.com/v1';

async function figmaFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const config = getConfig();

  const response = await fetch(`${FIGMA_API_BASE}${path}`, {
    ...options,
    headers: {
      'X-Figma-Token': config.figma.accessToken,
      ...options.headers
    }
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Figma API error (${response.status}): ${error}`);
  }

  return response.json() as Promise<T>;
}

/**
 * figma.sync_project - Trigger Figma project sync
 */
async function syncProject(params: FigmaSyncProject): Promise<ToolResult<{ status: string; synced_items?: number }>> {
  const config = getConfig();

  try {
    // Call Supabase Edge Function for sync orchestration
    const response = await fetch(`${config.supabase.url}/functions/v1/figma-sync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.supabase.serviceRoleKey}`
      },
      body: JSON.stringify({
        project_key: params.project_key,
        mode: params.mode,
        include_tokens: params.include_tokens
      })
    });

    if (!response.ok) {
      throw new Error(`Figma sync failed: ${response.statusText}`);
    }

    const result = await response.json() as { status: string; synced_items?: number };
    return { success: true, data: result };
  } catch (err) {
    return {
      success: false,
      error: `Figma sync failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * figma.audit_design_system - Audit design system alignment
 */
async function auditDesignSystem(params: { file_key: string }): Promise<ToolResult<{
  summary: string;
  components: number;
  variables: number;
  recommendations: string[];
}>> {
  try {
    // Get file info from Figma API
    const fileInfo = await figmaFetch<{
      name: string;
      lastModified: string;
      components: Record<string, unknown>;
    }>(`/files/${params.file_key}?depth=1`);

    // Get variables/styles
    const styles = await figmaFetch<{
      meta: { styles: unknown[] };
    }>(`/files/${params.file_key}/styles`);

    const componentCount = Object.keys(fileInfo.components || {}).length;
    const variableCount = styles.meta?.styles?.length || 0;

    const recommendations: string[] = [];

    if (componentCount < 10) {
      recommendations.push('Consider extracting more reusable components');
    }
    if (variableCount < 5) {
      recommendations.push('Add design tokens for colors, typography, and spacing');
    }

    return {
      success: true,
      data: {
        summary: `File "${fileInfo.name}" last modified ${fileInfo.lastModified}`,
        components: componentCount,
        variables: variableCount,
        recommendations
      }
    };
  } catch (err) {
    return {
      success: false,
      error: `Figma audit failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * figma.health_check - Check Figma integration health
 */
async function healthCheck(): Promise<ToolResult<HealthCheckResult>> {
  const config = getConfig();
  const checks: HealthCheckResult['checks'] = [];
  let overallStatus: HealthCheckResult['status'] = 'healthy';

  // Check 1: Figma API reachable
  const apiStart = Date.now();
  try {
    await figmaFetch<{ id: string }>('/me');
    checks.push({
      name: 'figma_api',
      status: 'healthy',
      latencyMs: Date.now() - apiStart
    });
  } catch (err) {
    checks.push({
      name: 'figma_api',
      status: 'broken',
      message: err instanceof Error ? err.message : 'API unreachable',
      latencyMs: Date.now() - apiStart
    });
    overallStatus = 'broken';
  }

  // Check 2: OAuth tokens valid (if stored in DB)
  try {
    const response = await fetch(`${config.supabase.url}/rest/v1/figma_tokens?select=expires_at&limit=1`, {
      headers: {
        'Authorization': `Bearer ${config.supabase.serviceRoleKey}`,
        'apikey': config.supabase.anonKey
      }
    });

    if (response.ok) {
      const tokens = await response.json() as Array<{ expires_at: string }>;
      if (tokens.length > 0) {
        const expiresAt = new Date(tokens[0].expires_at);
        if (expiresAt > new Date()) {
          checks.push({
            name: 'oauth_tokens',
            status: 'healthy',
            message: `Token valid until ${expiresAt.toISOString()}`
          });
        } else {
          checks.push({
            name: 'oauth_tokens',
            status: 'degraded',
            message: 'Token expired - refresh needed'
          });
          if (overallStatus === 'healthy') overallStatus = 'degraded';
        }
      } else {
        checks.push({
          name: 'oauth_tokens',
          status: 'degraded',
          message: 'No OAuth tokens stored'
        });
        if (overallStatus === 'healthy') overallStatus = 'degraded';
      }
    }
  } catch {
    checks.push({
      name: 'oauth_tokens',
      status: 'degraded',
      message: 'Could not check OAuth status'
    });
    if (overallStatus === 'healthy') overallStatus = 'degraded';
  }

  // Check 3: Webhook receiver (if configured)
  if (config.figma.webhookSecret) {
    checks.push({
      name: 'webhook_receiver',
      status: 'healthy',
      message: 'Webhook secret configured'
    });
  } else {
    checks.push({
      name: 'webhook_receiver',
      status: 'degraded',
      message: 'Webhook secret not configured'
    });
    if (overallStatus === 'healthy') overallStatus = 'degraded';
  }

  return {
    success: true,
    data: {
      status: overallStatus,
      checks,
      timestamp: new Date().toISOString()
    }
  };
}

// Export tools array for aggregation
export const tools = [
  {
    name: 'figma.sync_project',
    description: 'Sync a Figma project to Supabase. Extracts components, styles, and optionally design tokens.',
    inputSchema: FigmaSyncProjectSchema,
    execute: syncProject
  },
  {
    name: 'figma.audit_design_system',
    description: 'Audit a Figma file for design system alignment. Returns component/variable counts and recommendations.',
    inputSchema: {
      type: 'object',
      properties: {
        file_key: { type: 'string', description: 'Figma file key' }
      },
      required: ['file_key']
    },
    execute: auditDesignSystem
  },
  {
    name: 'figma.health_check',
    description: 'Check Figma integration health: API reachable, OAuth valid, webhook configured.',
    inputSchema: null,
    execute: healthCheck
  }
];
