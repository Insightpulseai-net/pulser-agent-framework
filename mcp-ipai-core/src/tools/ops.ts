/**
 * Ops tools (ops.*)
 * Cross-stack health / self-healing
 */

import { z } from "zod";
import { createClient } from "@supabase/supabase-js";
import type { McpTool, ToolContext, HealthCheckResult } from "../types.js";

// Import other tool modules for aggregate health check
import { tools as supabaseTools } from "./supabase.js";
import { tools as figmaTools } from "./figma.js";
import { tools as odooTools } from "./odoo.js";

// 8.1 ops.stack_health
const stackHealthSchema = z.object({
  include: z.array(z.enum(["supabase", "figma", "odoo", "n8n"])).optional()
    .describe("Services to check (default: all)"),
});

async function executeStackHealth(
  args: z.infer<typeof stackHealthSchema>,
  ctx: ToolContext
): Promise<{
  overall_status: HealthCheckResult["status"];
  services: Record<string, HealthCheckResult>;
  timestamp: string;
}> {
  const include = args.include || ["supabase", "figma", "odoo", "n8n"];
  const services: Record<string, HealthCheckResult> = {};
  let overallStatus: HealthCheckResult["status"] = "healthy";

  // Run health checks in parallel
  const healthChecks = [];

  if (include.includes("supabase")) {
    const supabaseHealthTool = supabaseTools.find(t => t.name === "supabase.health_check");
    if (supabaseHealthTool) {
      healthChecks.push(
        supabaseHealthTool.execute({}, ctx)
          .then(result => ({ service: "supabase", result: result as HealthCheckResult }))
          .catch(e => ({
            service: "supabase",
            result: {
              status: "broken" as const,
              checks: [{ name: "error", passed: false, message: String(e) }],
              timestamp: new Date().toISOString(),
            },
          }))
      );
    }
  }

  if (include.includes("figma")) {
    const figmaHealthTool = figmaTools.find(t => t.name === "figma.health_check");
    if (figmaHealthTool) {
      healthChecks.push(
        figmaHealthTool.execute({}, ctx)
          .then(result => ({ service: "figma", result: result as HealthCheckResult }))
          .catch(e => ({
            service: "figma",
            result: {
              status: "broken" as const,
              checks: [{ name: "error", passed: false, message: String(e) }],
              timestamp: new Date().toISOString(),
            },
          }))
      );
    }
  }

  if (include.includes("odoo")) {
    const odooHealthTool = odooTools.find(t => t.name === "odoo.nav_health");
    if (odooHealthTool) {
      healthChecks.push(
        odooHealthTool.execute({}, ctx)
          .then(result => ({ service: "odoo", result: result as HealthCheckResult }))
          .catch(e => ({
            service: "odoo",
            result: {
              status: "broken" as const,
              checks: [{ name: "error", passed: false, message: String(e) }],
              timestamp: new Date().toISOString(),
            },
          }))
      );
    }
  }

  if (include.includes("n8n") && ctx.n8nUrl) {
    healthChecks.push(
      (async () => {
        try {
          const response = await fetch(`${ctx.n8nUrl}/healthz`, {
            headers: ctx.n8nApiKey ? { "X-N8N-API-KEY": ctx.n8nApiKey } : {},
          });
          return {
            service: "n8n",
            result: {
              status: response.ok ? "healthy" : "broken",
              checks: [{
                name: "n8n_health_endpoint",
                passed: response.ok,
                message: response.ok ? "n8n is healthy" : `n8n returned ${response.status}`,
              }],
              timestamp: new Date().toISOString(),
            } as HealthCheckResult,
          };
        } catch (e) {
          return {
            service: "n8n",
            result: {
              status: "broken" as const,
              checks: [{ name: "n8n_reachable", passed: false, message: String(e) }],
              timestamp: new Date().toISOString(),
            },
          };
        }
      })()
    );
  }

  // Wait for all checks
  const results = await Promise.all(healthChecks);

  for (const { service, result } of results) {
    services[service] = result;
    if (result.status === "broken") {
      overallStatus = "broken";
    } else if (result.status === "degraded" && overallStatus === "healthy") {
      overallStatus = "degraded";
    }
  }

  return {
    overall_status: overallStatus,
    services,
    timestamp: new Date().toISOString(),
  };
}

// 8.2 ops.db_lint_summary
const dbLintSummarySchema = z.object({
  severity: z.enum(["critical", "warning", "info", "all"]).default("all")
    .describe("Filter by severity level"),
  limit: z.number().default(100).describe("Maximum findings to return"),
});

async function executeDbLintSummary(
  args: z.infer<typeof dbLintSummarySchema>,
  ctx: ToolContext
): Promise<unknown> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  let query = supabase
    .from("ops.db_lint_findings")
    .select(`
      id,
      name,
      level,
      detail,
      metadata,
      created_at
    `)
    .order("level", { ascending: true })
    .order("created_at", { ascending: false })
    .limit(args.limit);

  if (args.severity !== "all") {
    query = query.eq("level", args.severity);
  }

  const { data, error } = await query;

  if (error) {
    // Try alternative table name
    const { data: altData, error: altError } = await supabase
      .from("db_lint_results")
      .select("*")
      .limit(args.limit);

    if (altError) {
      throw new Error(`Failed to fetch lint findings: ${error.message}`);
    }

    return {
      findings: altData || [],
      summary: {
        total: (altData || []).length,
        by_level: groupByLevel(altData || []),
      },
    };
  }

  return {
    findings: data || [],
    summary: {
      total: (data || []).length,
      by_level: groupByLevel(data || []),
    },
  };
}

function groupByLevel(findings: Array<{ level?: string }>): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const f of findings) {
    const level = f.level || "unknown";
    counts[level] = (counts[level] || 0) + 1;
  }
  return counts;
}

// 8.3 ops.self_heal_recommendations
const selfHealRecommendationsSchema = z.object({
  scope: z.enum(["security", "performance", "schema", "all"]).default("all")
    .describe("Category of recommendations"),
  auto_create_pr: z.boolean().default(false)
    .describe("Automatically create PR for fixes (requires GitHub token)"),
});

async function executeSelfHealRecommendations(
  args: z.infer<typeof selfHealRecommendationsSchema>,
  ctx: ToolContext
): Promise<unknown> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  // Fetch lint findings
  const { data: findings } = await supabase
    .from("ops.db_lint_findings")
    .select("name, level, detail, metadata")
    .in("level", ["critical", "warning"])
    .limit(50);

  const recommendations: Array<{
    finding: string;
    severity: string;
    recommendation: string;
    sql_fix?: string;
    migration_file?: string;
  }> = [];

  for (const finding of findings || []) {
    const rec = generateRecommendation(finding);
    if (rec && (args.scope === "all" || rec.category === args.scope)) {
      recommendations.push({
        finding: finding.name,
        severity: finding.level,
        recommendation: rec.recommendation,
        sql_fix: rec.sql_fix,
        migration_file: rec.migration_file,
      });
    }
  }

  // If auto_create_pr is true and we have recommendations, we would create a PR
  // For now, just return recommendations for human review
  if (args.auto_create_pr && recommendations.length > 0 && ctx.githubToken) {
    return {
      recommendations,
      action: "pr_creation_available",
      message: "Use github.create_pr with the SQL fixes to apply recommendations.",
    };
  }

  return {
    recommendations,
    total: recommendations.length,
    scope: args.scope,
    message: recommendations.length > 0
      ? "Review recommendations and apply via migration pipeline."
      : "No actionable recommendations found.",
  };
}

function generateRecommendation(finding: {
  name: string;
  level: string;
  detail?: string;
  metadata?: Record<string, unknown>;
}): {
  category: string;
  recommendation: string;
  sql_fix?: string;
  migration_file?: string;
} | null {
  const name = finding.name.toLowerCase();

  // Security recommendations
  if (name.includes("security_definer") && name.includes("rls")) {
    return {
      category: "security",
      recommendation: "Function uses SECURITY DEFINER without search_path. Add explicit search_path to prevent privilege escalation.",
      sql_fix: `ALTER FUNCTION ${finding.metadata?.function_name || 'unknown'} SET search_path = public;`,
      migration_file: `migrations/${Date.now()}_fix_security_definer.sql`,
    };
  }

  if (name.includes("rls") && name.includes("disabled")) {
    return {
      category: "security",
      recommendation: "Table has RLS disabled. Enable RLS and add appropriate policies.",
      sql_fix: `ALTER TABLE ${finding.metadata?.table_name || 'unknown'} ENABLE ROW LEVEL SECURITY;`,
      migration_file: `migrations/${Date.now()}_enable_rls.sql`,
    };
  }

  // Performance recommendations
  if (name.includes("index") && name.includes("missing")) {
    return {
      category: "performance",
      recommendation: "Missing index on frequently queried column.",
      sql_fix: `CREATE INDEX CONCURRENTLY idx_${finding.metadata?.table_name || 'table'}_${finding.metadata?.column_name || 'column'} ON ${finding.metadata?.table_name || 'table'}(${finding.metadata?.column_name || 'column'});`,
      migration_file: `migrations/${Date.now()}_add_index.sql`,
    };
  }

  // Schema recommendations
  if (name.includes("nullable") && name.includes("required")) {
    return {
      category: "schema",
      recommendation: "Column should be NOT NULL but allows nulls.",
      sql_fix: `ALTER TABLE ${finding.metadata?.table_name || 'unknown'} ALTER COLUMN ${finding.metadata?.column_name || 'unknown'} SET NOT NULL;`,
      migration_file: `migrations/${Date.now()}_fix_nullable.sql`,
    };
  }

  return null;
}

export const tools: McpTool[] = [
  {
    name: "ops.stack_health",
    description: "Single 'tell me if everything is ok' tool. Checks Supabase, Figma, Odoo, n8n.",
    inputSchema: stackHealthSchema,
    execute: executeStackHealth,
  },
  {
    name: "ops.db_lint_summary",
    description: "Surface Supabase db-linter results (SECURITY DEFINER, RLS findings).",
    inputSchema: dbLintSummarySchema,
    execute: executeDbLintSummary,
  },
  {
    name: "ops.self_heal_recommendations",
    description: "Read db-lint + schema state and suggest patches. Fixes go through migration pipeline via PRs.",
    inputSchema: selfHealRecommendationsSchema,
    execute: executeSelfHealRecommendations,
  },
];
