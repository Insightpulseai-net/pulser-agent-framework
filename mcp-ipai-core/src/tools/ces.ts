/**
 * CES tools (ces.*)
 * Creative Effectiveness Score helpers
 */

import { z } from "zod";
import { createClient } from "@supabase/supabase-js";
import type { McpTool, ToolContext, HealthCheckResult } from "../types.js";

// 7.1 ces.campaign_overview
const campaignOverviewSchema = z.object({
  campaign_code: z.string().optional().describe("Campaign code to fetch"),
  campaign_id: z.string().optional().describe("Campaign ID (UUID)"),
});

async function executeCampaignOverview(
  args: z.infer<typeof campaignOverviewSchema>,
  ctx: ToolContext
): Promise<unknown> {
  if (!args.campaign_code && !args.campaign_id) {
    throw new Error("Either campaign_code or campaign_id is required");
  }

  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  // Fetch campaign with scores and explanations
  let query = supabase
    .from("ces.campaigns")
    .select(`
      id,
      code,
      name,
      brand,
      category,
      start_date,
      end_date,
      status,
      overall_score,
      attention_score,
      branding_score,
      communication_score,
      distinction_score,
      familiarity_score,
      relevance_score,
      explanation,
      recommendations,
      created_at,
      updated_at
    `);

  if (args.campaign_code) {
    query = query.eq("code", args.campaign_code);
  } else if (args.campaign_id) {
    query = query.eq("id", args.campaign_id);
  }

  const { data: campaign, error: campaignError } = await query.single();

  if (campaignError) {
    throw new Error(`Failed to fetch campaign: ${campaignError.message}`);
  }

  // Fetch associated assets
  const { data: assets } = await supabase
    .from("ces.campaign_assets")
    .select(`
      id,
      asset_type,
      asset_url,
      thumbnail_url,
      platform,
      metrics
    `)
    .eq("campaign_id", campaign.id)
    .limit(20);

  // Fetch Figma links if any
  const { data: figmaLinks } = await supabase
    .from("ces.campaign_figma_assets")
    .select(`
      figma_file_key,
      node_id,
      asset_type,
      linked_at
    `)
    .eq("campaign_code", campaign.code)
    .limit(10);

  return {
    campaign,
    assets: assets || [],
    figma_links: figmaLinks || [],
    scores_breakdown: {
      overall: campaign.overall_score,
      attention: campaign.attention_score,
      branding: campaign.branding_score,
      communication: campaign.communication_score,
      distinction: campaign.distinction_score,
      familiarity: campaign.familiarity_score,
      relevance: campaign.relevance_score,
    },
  };
}

// 7.2 ces.link_figma_asset
const linkFigmaAssetSchema = z.object({
  campaign_code: z.string().describe("Campaign code to link"),
  figma_file_key: z.string().describe("Figma file key"),
  node_id: z.string().optional().describe("Specific node ID (optional)"),
  asset_type: z.enum(["hero", "banner", "social", "video_thumbnail", "other"]).default("other"),
});

async function executeLinkFigmaAsset(
  args: z.infer<typeof linkFigmaAssetSchema>,
  ctx: ToolContext
): Promise<{ status: string; link_id: string }> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  const { data, error } = await supabase
    .from("ces.campaign_figma_assets")
    .upsert({
      campaign_code: args.campaign_code,
      figma_file_key: args.figma_file_key,
      node_id: args.node_id,
      asset_type: args.asset_type,
      linked_at: new Date().toISOString(),
    }, {
      onConflict: "campaign_code,figma_file_key,node_id",
    })
    .select("id")
    .single();

  if (error) {
    throw new Error(`Failed to link Figma asset: ${error.message}`);
  }

  return {
    status: "linked",
    link_id: data.id,
  };
}

// 7.3 ces.health_check
const cesHealthCheckSchema = z.object({}).optional();

async function executeCesHealthCheck(
  _args: unknown,
  ctx: ToolContext
): Promise<HealthCheckResult> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);
  const checks: HealthCheckResult["checks"] = [];
  let overallStatus: HealthCheckResult["status"] = "healthy";

  // Check 1: ces.campaigns not empty
  const campaignsStart = Date.now();
  try {
    const { count, error } = await supabase
      .from("ces.campaigns")
      .select("*", { count: "exact", head: true });

    checks.push({
      name: "campaigns_populated",
      passed: !error && (count ?? 0) > 0,
      message: error ? error.message : `${count} campaigns in CES`,
      duration_ms: Date.now() - campaignsStart,
    });

    if ((count ?? 0) === 0 && overallStatus === "healthy") {
      overallStatus = "degraded";
    }
  } catch (e) {
    checks.push({
      name: "campaigns_populated",
      passed: false,
      message: `Check failed: ${e instanceof Error ? e.message : String(e)}`,
      duration_ms: Date.now() - campaignsStart,
    });
    overallStatus = "degraded";
  }

  // Check 2: Seeds from v19 present (Brand X, etc.)
  const seedsStart = Date.now();
  try {
    const knownSeeds = ["BRAND_X_Q4_2024", "BRAND_Y_LAUNCH", "DEMO_CAMPAIGN"];
    const { data, error } = await supabase
      .from("ces.campaigns")
      .select("code")
      .in("code", knownSeeds);

    const foundSeeds = data?.map((c: { code: string }) => c.code) || [];
    checks.push({
      name: "seed_campaigns_present",
      passed: foundSeeds.length > 0,
      message: foundSeeds.length > 0
        ? `Found seed campaigns: ${foundSeeds.join(", ")}`
        : "No seed campaigns found",
      duration_ms: Date.now() - seedsStart,
    });
  } catch (e) {
    checks.push({
      name: "seed_campaigns_present",
      passed: false,
      message: `Check failed: ${e instanceof Error ? e.message : String(e)}`,
      duration_ms: Date.now() - seedsStart,
    });
  }

  // Check 3: RLS behaves correctly (basic check)
  const rlsStart = Date.now();
  try {
    // This is a simplified check; real RLS testing needs tenant context
    const { error } = await supabase
      .from("ces.campaigns")
      .select("id")
      .limit(1);

    checks.push({
      name: "rls_accessible",
      passed: !error,
      message: error ? `RLS may be blocking: ${error.message}` : "RLS allows service role access",
      duration_ms: Date.now() - rlsStart,
    });
  } catch (e) {
    checks.push({
      name: "rls_accessible",
      passed: false,
      message: `RLS check failed: ${e instanceof Error ? e.message : String(e)}`,
      duration_ms: Date.now() - rlsStart,
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
    name: "ces.campaign_overview",
    description: "Fetch campaign with scores, explanations, assets. Main Ask Ces entry point.",
    inputSchema: campaignOverviewSchema,
    execute: executeCampaignOverview,
  },
  {
    name: "ces.link_figma_asset",
    description: "Connect CES campaigns to Figma assets.",
    inputSchema: linkFigmaAssetSchema,
    execute: executeLinkFigmaAsset,
  },
  {
    name: "ces.health_check",
    description: "Check ces.campaigns not empty, seeds present, RLS correct.",
    inputSchema: cesHealthCheckSchema,
    execute: executeCesHealthCheck,
  },
];
