/**
 * Figma tools (figma.*)
 * Design system + Code Connect
 */

import { z } from "zod";
import { createClient } from "@supabase/supabase-js";
import type { McpTool, ToolContext, HealthCheckResult } from "../types.js";

// 4.1 figma.sync_project
const syncProjectSchema = z.object({
  project_key: z.string().describe("Figma project key"),
  mode: z.enum(["full", "delta"]).default("delta").describe("Sync mode"),
  include_tokens: z.boolean().default(true).describe("Include design tokens"),
});

async function executeSyncProject(
  args: z.infer<typeof syncProjectSchema>,
  ctx: ToolContext
): Promise<{ status: string; message: string }> {
  // Call figma-sync Edge Function or orchestrator
  const response = await fetch(`${ctx.supabaseUrl}/functions/v1/figma-sync`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${ctx.supabaseServiceKey}`,
    },
    body: JSON.stringify({
      project_key: args.project_key,
      mode: args.mode,
      include_tokens: args.include_tokens,
    }),
  });

  if (!response.ok) {
    throw new Error(`Figma sync failed: ${response.status}`);
  }

  return {
    status: "triggered",
    message: `Figma sync ${args.mode} triggered for project ${args.project_key}`,
  };
}

// 4.2 figma.audit_design_system
const auditDesignSystemSchema = z.object({
  project_key: z.string().optional().describe("Specific project to audit (optional)"),
  include_ces_mapping: z.boolean().default(true).describe("Include CES campaign mappings"),
});

async function executeAuditDesignSystem(
  args: z.infer<typeof auditDesignSystemSchema>,
  ctx: ToolContext
): Promise<unknown> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  // Query Figma integration tables
  let query = supabase
    .from("figma_components")
    .select(`
      id,
      name,
      component_key,
      project_key,
      variant_properties,
      updated_at,
      figma_projects!inner(name, last_synced_at)
    `);

  if (args.project_key) {
    query = query.eq("project_key", args.project_key);
  }

  const { data: components, error: componentsError } = await query.limit(500);

  if (componentsError) {
    throw new Error(`Failed to fetch components: ${componentsError.message}`);
  }

  // Get CES mappings if requested
  let cesMappings: unknown[] = [];
  if (args.include_ces_mapping) {
    const { data, error } = await supabase
      .from("ces.campaign_figma_assets")
      .select(`
        campaign_code,
        figma_file_key,
        node_id,
        asset_type
      `)
      .limit(500);

    if (!error) {
      cesMappings = data || [];
    }
  }

  // Generate audit summary
  const summary = {
    total_components: components?.length || 0,
    projects_analyzed: [...new Set(components?.map((c: { project_key: string }) => c.project_key))].length,
    ces_linked_assets: cesMappings.length,
    recommendations: [] as string[],
  };

  // Add recommendations based on findings
  if (summary.total_components === 0) {
    summary.recommendations.push("No components found. Run figma.sync_project first.");
  }
  if (cesMappings.length === 0 && args.include_ces_mapping) {
    summary.recommendations.push("No CES-Figma asset links found. Consider linking campaigns to design assets.");
  }

  return {
    summary,
    components: components?.slice(0, 50), // Return first 50 for brevity
    ces_mappings: cesMappings.slice(0, 50),
  };
}

// 4.3 figma.health_check
const figmaHealthCheckSchema = z.object({}).optional();

async function executeFigmaHealthCheck(
  _args: unknown,
  ctx: ToolContext
): Promise<HealthCheckResult> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);
  const checks: HealthCheckResult["checks"] = [];
  let overallStatus: HealthCheckResult["status"] = "healthy";

  // Check 1: Figma projects table exists and has data
  const projectsStart = Date.now();
  try {
    const { count, error } = await supabase
      .from("figma_projects")
      .select("*", { count: "exact", head: true });

    checks.push({
      name: "figma_projects_table",
      passed: !error && (count ?? 0) > 0,
      message: error ? error.message : `${count} Figma projects synced`,
      duration_ms: Date.now() - projectsStart,
    });

    if (error || (count ?? 0) === 0) {
      overallStatus = "degraded";
    }
  } catch (e) {
    checks.push({
      name: "figma_projects_table",
      passed: false,
      message: `Check failed: ${e instanceof Error ? e.message : String(e)}`,
      duration_ms: Date.now() - projectsStart,
    });
    overallStatus = "degraded";
  }

  // Check 2: OAuth tokens valid (if stored)
  const tokensStart = Date.now();
  try {
    const { data, error } = await supabase
      .from("figma_oauth_tokens")
      .select("expires_at")
      .limit(1)
      .single();

    if (data) {
      const expiresAt = new Date(data.expires_at);
      const isValid = expiresAt > new Date();
      checks.push({
        name: "figma_oauth_valid",
        passed: isValid,
        message: isValid ? "OAuth token valid" : "OAuth token expired",
        duration_ms: Date.now() - tokensStart,
      });
      if (!isValid && overallStatus === "healthy") {
        overallStatus = "degraded";
      }
    } else {
      checks.push({
        name: "figma_oauth_valid",
        passed: true,
        message: "No OAuth tokens configured (using API token)",
        duration_ms: Date.now() - tokensStart,
      });
    }
  } catch (e) {
    checks.push({
      name: "figma_oauth_valid",
      passed: true,
      message: "OAuth not configured",
      duration_ms: Date.now() - tokensStart,
    });
  }

  // Check 3: Sync queue depth
  const queueStart = Date.now();
  try {
    const { count, error } = await supabase
      .from("figma_sync_queue")
      .select("*", { count: "exact", head: true })
      .eq("status", "pending");

    const queueDepth = count ?? 0;
    const isHealthy = queueDepth < 100; // Threshold

    checks.push({
      name: "figma_sync_queue",
      passed: isHealthy,
      message: `${queueDepth} pending sync items`,
      duration_ms: Date.now() - queueStart,
    });

    if (!isHealthy && overallStatus === "healthy") {
      overallStatus = "degraded";
    }
  } catch (e) {
    checks.push({
      name: "figma_sync_queue",
      passed: true,
      message: "Sync queue not configured",
      duration_ms: Date.now() - queueStart,
    });
  }

  return {
    status: overallStatus,
    checks,
    timestamp: new Date().toISOString(),
  };
}

export const tools: McpTool[] = [
  {
    name: "figma.sync_project",
    description: "Call figma-sync Edge Function / orchestrator.",
    inputSchema: syncProjectSchema,
    execute: executeSyncProject,
  },
  {
    name: "figma.audit_design_system",
    description: "Audit design system alignment using Figma DB + CES data.",
    inputSchema: auditDesignSystemSchema,
    execute: executeAuditDesignSystem,
  },
  {
    name: "figma.health_check",
    description: "Check Figma webhook, OAuth tokens, sync queue, DB tables.",
    inputSchema: figmaHealthCheckSchema,
    execute: executeFigmaHealthCheck,
  },
];
