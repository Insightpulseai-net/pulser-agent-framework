/**
 * Ops / health tools for IPAI MCP Server
 * Namespace: ops.*
 *
 * Cross-stack health checks and self-healing recommendations.
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { getConfig } from '../config.js';
import {
  DbLintSummarySchema,
  type DbLintSummary,
  type HealthCheckResult,
  type HealthStatus,
  type ToolResult
} from '../types.js';

let supabaseClient: SupabaseClient | null = null;

function getSupabaseClient(): SupabaseClient {
  if (!supabaseClient) {
    const config = getConfig();
    supabaseClient = createClient(config.supabase.url, config.supabase.serviceRoleKey, {
      auth: { persistSession: false }
    });
  }
  return supabaseClient;
}

interface StackHealthResult {
  overall_status: HealthStatus;
  components: {
    supabase: HealthCheckResult | null;
    odoo: HealthCheckResult | null;
    figma: HealthCheckResult | null;
    n8n: { status: string } | null;
  };
  timestamp: string;
}

/**
 * Simple health check for Supabase connectivity
 */
async function checkSupabaseHealth(): Promise<HealthCheckResult> {
  const supabase = getSupabaseClient();
  const checks: HealthCheckResult['checks'] = [];
  let overallStatus: HealthStatus = 'healthy';

  const dbStart = Date.now();
  try {
    await supabase.from('_dummy_check_').select('count').limit(0);
    checks.push({
      name: 'db_connection',
      status: 'healthy',
      latencyMs: Date.now() - dbStart
    });
  } catch (err) {
    checks.push({
      name: 'db_connection',
      status: 'broken',
      message: err instanceof Error ? err.message : 'Connection failed',
      latencyMs: Date.now() - dbStart
    });
    overallStatus = 'broken';
  }

  return {
    status: overallStatus,
    checks,
    timestamp: new Date().toISOString()
  };
}

/**
 * Simple health check for n8n connectivity
 */
async function checkN8nHealth(): Promise<{ status: string }> {
  const config = getConfig();

  try {
    const response = await fetch(`${config.n8n.baseUrl}/healthz`, {
      method: 'GET',
      headers: {
        'X-N8N-API-KEY': config.n8n.apiKey
      }
    });

    return { status: response.ok ? 'healthy' : 'degraded' };
  } catch {
    return { status: 'broken' };
  }
}

/**
 * ops.stack_health - Single "tell me if everything is ok" tool
 */
async function stackHealth(): Promise<ToolResult<StackHealthResult>> {
  const results: StackHealthResult = {
    overall_status: 'healthy',
    components: {
      supabase: null,
      odoo: null,
      figma: null,
      n8n: null
    },
    timestamp: new Date().toISOString()
  };

  // Run health checks in parallel
  const [supabaseResult, n8nResult] = await Promise.allSettled([
    checkSupabaseHealth(),
    checkN8nHealth()
  ]);

  // Process Supabase result
  if (supabaseResult.status === 'fulfilled') {
    results.components.supabase = supabaseResult.value;
    if (supabaseResult.value.status === 'broken') {
      results.overall_status = 'broken';
    } else if (supabaseResult.value.status === 'degraded' && results.overall_status === 'healthy') {
      results.overall_status = 'degraded';
    }
  } else {
    results.overall_status = 'broken';
  }

  // Process n8n result
  if (n8nResult.status === 'fulfilled') {
    results.components.n8n = n8nResult.value;
    if (n8nResult.value.status !== 'healthy' && results.overall_status === 'healthy') {
      results.overall_status = 'degraded';
    }
  }

  // Note: Odoo and Figma health checks are optional and can be called separately
  // to avoid circular dependencies

  return {
    success: true,
    data: results
  };
}

interface DbLintIssue {
  id: string;
  severity: 'error' | 'warning' | 'info';
  category: string;
  message: string;
  object_name?: string;
  recommendation?: string;
}

/**
 * ops.db_lint_summary - Surface Supabase db-linter results
 */
async function dbLintSummary(params: DbLintSummary): Promise<ToolResult<{
  issues: DbLintIssue[];
  summary: {
    errors: number;
    warnings: number;
    info: number;
  };
}>> {
  const supabase = getSupabaseClient();

  try {
    // Try to read from db_lint_results table if it exists
    let query = supabase
      .from('db_lint_results')
      .select('*')
      .limit(params.limit);

    if (params.severity) {
      query = query.eq('severity', params.severity);
    }

    query = query.order('severity', { ascending: true });

    const { data, error } = await query;

    if (error && error.message.includes('does not exist')) {
      // Table doesn't exist, run live lint via RPC
      const { data: lintData, error: lintError } = await supabase.rpc('run_db_lint');

      if (lintError) {
        return {
          success: false,
          error: `DB lint failed: ${lintError.message}`
        };
      }

      const issues = (lintData || []) as DbLintIssue[];
      return {
        success: true,
        data: {
          issues: issues.slice(0, params.limit),
          summary: {
            errors: issues.filter(i => i.severity === 'error').length,
            warnings: issues.filter(i => i.severity === 'warning').length,
            info: issues.filter(i => i.severity === 'info').length
          }
        }
      };
    }

    if (error) {
      return {
        success: false,
        error: `DB lint query failed: ${error.message}`
      };
    }

    const issues = (data || []) as DbLintIssue[];
    return {
      success: true,
      data: {
        issues,
        summary: {
          errors: issues.filter(i => i.severity === 'error').length,
          warnings: issues.filter(i => i.severity === 'warning').length,
          info: issues.filter(i => i.severity === 'info').length
        }
      }
    };
  } catch (err) {
    return {
      success: false,
      error: `DB lint summary failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

interface HealRecommendation {
  id: string;
  priority: 'high' | 'medium' | 'low';
  category: string;
  issue: string;
  fix_type: 'sql' | 'config' | 'code';
  fix_description: string;
  sql_patch?: string;
  pr_template?: {
    title: string;
    body: string;
    files: Array<{ path: string; content: string }>;
  };
}

/**
 * ops.self_heal_recommendations - Read db-lint + schema state and suggest patches
 */
async function selfHealRecommendations(): Promise<ToolResult<{
  recommendations: HealRecommendation[];
  auto_fixable: number;
  manual_review: number;
}>> {
  // First get lint results
  const lintResult = await dbLintSummary({ limit: 50 });

  if (!lintResult.success || !lintResult.data) {
    return {
      success: false,
      error: 'Could not fetch lint results for recommendations'
    };
  }

  const recommendations: HealRecommendation[] = [];

  // Generate recommendations based on lint issues
  for (const issue of lintResult.data.issues) {
    const recommendation: HealRecommendation = {
      id: issue.id,
      priority: issue.severity === 'error' ? 'high' : issue.severity === 'warning' ? 'medium' : 'low',
      category: issue.category,
      issue: issue.message,
      fix_type: 'sql',
      fix_description: issue.recommendation || 'Manual review required'
    };

    // Generate SQL patches for common issues
    if (issue.category === 'security' && issue.message.includes('SECURITY DEFINER')) {
      recommendation.sql_patch = `
-- Fix SECURITY DEFINER without search_path
ALTER FUNCTION ${issue.object_name} SET search_path = public;
      `.trim();
    } else if (issue.category === 'security' && issue.message.includes('RLS')) {
      recommendation.sql_patch = `
-- Enable RLS on table
ALTER TABLE ${issue.object_name} ENABLE ROW LEVEL SECURITY;

-- Create default policy (adjust as needed)
CREATE POLICY "Default access policy" ON ${issue.object_name}
  FOR ALL
  USING (auth.role() = 'authenticated');
      `.trim();
    } else if (issue.category === 'performance' && issue.message.includes('index')) {
      recommendation.sql_patch = `
-- Consider adding index (review column selection)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_${issue.object_name?.replace('.', '_')}_suggested
  ON ${issue.object_name} (/* add columns here */);
      `.trim();
    }

    // Generate PR template for code fixes
    if (recommendation.sql_patch) {
      recommendation.pr_template = {
        title: `fix(db): ${issue.category} - ${issue.message.substring(0, 50)}`,
        body: `## Summary
Fixes ${issue.category} issue detected by db-linter.

## Issue
${issue.message}

## Solution
${recommendation.fix_description}

## SQL Changes
\`\`\`sql
${recommendation.sql_patch}
\`\`\`

## Testing
- [ ] Migration tested locally
- [ ] RLS policies verified
- [ ] Performance impact assessed
`,
        files: [{
          path: `migrations/${Date.now()}_fix_${issue.id}.sql`,
          content: recommendation.sql_patch
        }]
      };
    }

    recommendations.push(recommendation);
  }

  return {
    success: true,
    data: {
      recommendations,
      auto_fixable: recommendations.filter(r => r.sql_patch).length,
      manual_review: recommendations.filter(r => !r.sql_patch).length
    }
  };
}

// Export tools array for aggregation
export const tools = [
  {
    name: 'ops.stack_health',
    description: 'Single "tell me if everything is ok" tool. Checks Supabase and n8n.',
    inputSchema: null,
    execute: stackHealth
  },
  {
    name: 'ops.db_lint_summary',
    description: 'Surface Supabase db-linter results: SECURITY DEFINER issues, RLS findings, etc.',
    inputSchema: DbLintSummarySchema,
    execute: dbLintSummary
  },
  {
    name: 'ops.self_heal_recommendations',
    description: 'Read db-lint + schema state and suggest patches. Generates SQL and PR templates.',
    inputSchema: null,
    execute: selfHealRecommendations
  }
];
