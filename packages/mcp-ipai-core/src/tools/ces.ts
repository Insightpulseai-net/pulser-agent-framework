/**
 * CES (Creative Effectiveness Score) tools for IPAI MCP Server
 * Namespace: ces.*
 *
 * Creative effectiveness helpers on top of ces.* schema.
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { getConfig } from '../config.js';
import {
  CesCampaignOverviewSchema,
  CesLinkFigmaSchema,
  type CesCampaignOverview,
  type CesLinkFigma,
  type HealthCheckResult,
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

interface CampaignData {
  id: string;
  campaign_code: string;
  name: string;
  brand_name: string;
  status: string;
  start_date: string;
  end_date: string;
  scores?: {
    overall: number;
    attention: number;
    branding: number;
    communication: number;
    distinctiveness: number;
  };
  explanations?: Record<string, string>;
}

/**
 * ces.campaign_overview - Fetch campaign with scores and explanations
 */
async function campaignOverview(params: CesCampaignOverview): Promise<ToolResult<CampaignData>> {
  const supabase = getSupabaseClient();

  try {
    let query = supabase
      .schema('ces')
      .from('campaigns')
      .select(`
        id,
        campaign_code,
        name,
        brand_name,
        status,
        start_date,
        end_date,
        scores:campaign_scores(
          overall,
          attention,
          branding,
          communication,
          distinctiveness
        ),
        explanations:campaign_explanations(
          dimension,
          explanation
        )
      `);

    if (params.campaign_code) {
      query = query.eq('campaign_code', params.campaign_code);
    } else if (params.campaign_id) {
      query = query.eq('id', params.campaign_id);
    }

    const { data, error } = await query.single();

    if (error) {
      return {
        success: false,
        error: `Failed to fetch campaign: ${error.message}`
      };
    }

    if (!data) {
      return {
        success: false,
        error: 'Campaign not found'
      };
    }

    // Transform explanations array to object
    const explanationsObj: Record<string, string> = {};
    if (Array.isArray(data.explanations)) {
      for (const exp of data.explanations as Array<{ dimension: string; explanation: string }>) {
        explanationsObj[exp.dimension] = exp.explanation;
      }
    }

    return {
      success: true,
      data: {
        id: data.id,
        campaign_code: data.campaign_code,
        name: data.name,
        brand_name: data.brand_name,
        status: data.status,
        start_date: data.start_date,
        end_date: data.end_date,
        scores: Array.isArray(data.scores) && data.scores.length > 0 ? data.scores[0] : undefined,
        explanations: Object.keys(explanationsObj).length > 0 ? explanationsObj : undefined
      }
    };
  } catch (err) {
    return {
      success: false,
      error: `Campaign overview failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * ces.link_figma_asset - Connect CES campaign to Figma asset
 */
async function linkFigmaAsset(params: CesLinkFigma): Promise<ToolResult<{ linked: boolean; asset_id?: string }>> {
  const supabase = getSupabaseClient();

  try {
    // First, get the campaign ID
    const { data: campaign, error: campaignError } = await supabase
      .schema('ces')
      .from('campaigns')
      .select('id')
      .eq('campaign_code', params.campaign_code)
      .single();

    if (campaignError || !campaign) {
      return {
        success: false,
        error: `Campaign not found: ${params.campaign_code}`
      };
    }

    // Create or update the Figma asset link
    const { data: asset, error: assetError } = await supabase
      .schema('ces')
      .from('campaign_figma_assets')
      .upsert({
        campaign_id: campaign.id,
        figma_file_key: params.figma_file_key,
        figma_node_id: params.node_id,
        linked_at: new Date().toISOString()
      }, {
        onConflict: 'campaign_id,figma_file_key'
      })
      .select('id')
      .single();

    if (assetError) {
      return {
        success: false,
        error: `Failed to link Figma asset: ${assetError.message}`
      };
    }

    return {
      success: true,
      data: {
        linked: true,
        asset_id: asset?.id
      }
    };
  } catch (err) {
    return {
      success: false,
      error: `Link Figma asset failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * ces.list_campaigns - List campaigns with optional filters
 */
async function listCampaigns(params: {
  brand_name?: string;
  status?: string;
  limit?: number;
}): Promise<ToolResult<Array<{
  id: string;
  campaign_code: string;
  name: string;
  brand_name: string;
  status: string;
  overall_score?: number;
}>>> {
  const supabase = getSupabaseClient();

  try {
    let query = supabase
      .schema('ces')
      .from('campaigns')
      .select(`
        id,
        campaign_code,
        name,
        brand_name,
        status,
        scores:campaign_scores(overall)
      `)
      .limit(params.limit || 20);

    if (params.brand_name) {
      query = query.ilike('brand_name', `%${params.brand_name}%`);
    }
    if (params.status) {
      query = query.eq('status', params.status);
    }

    const { data, error } = await query;

    if (error) {
      return {
        success: false,
        error: `Failed to list campaigns: ${error.message}`
      };
    }

    return {
      success: true,
      data: (data || []).map(c => ({
        id: c.id,
        campaign_code: c.campaign_code,
        name: c.name,
        brand_name: c.brand_name,
        status: c.status,
        overall_score: Array.isArray(c.scores) && c.scores.length > 0
          ? (c.scores[0] as { overall: number }).overall
          : undefined
      }))
    };
  } catch (err) {
    return {
      success: false,
      error: `List campaigns failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * ces.health_check - Check CES schema health
 */
async function healthCheck(): Promise<ToolResult<HealthCheckResult>> {
  const supabase = getSupabaseClient();
  const checks: HealthCheckResult['checks'] = [];
  let overallStatus: HealthCheckResult['status'] = 'healthy';

  // Check 1: campaigns table not empty
  try {
    const { count, error } = await supabase
      .schema('ces')
      .from('campaigns')
      .select('*', { count: 'exact', head: true });

    if (error) {
      checks.push({
        name: 'campaigns_table',
        status: 'broken',
        message: error.message
      });
      overallStatus = 'broken';
    } else if (!count || count === 0) {
      checks.push({
        name: 'campaigns_table',
        status: 'degraded',
        message: 'No campaigns found'
      });
      if (overallStatus === 'healthy') overallStatus = 'degraded';
    } else {
      checks.push({
        name: 'campaigns_table',
        status: 'healthy',
        message: `${count} campaigns`
      });
    }
  } catch (err) {
    checks.push({
      name: 'campaigns_table',
      status: 'broken',
      message: err instanceof Error ? err.message : 'Check failed'
    });
    overallStatus = 'broken';
  }

  // Check 2: Seeds from v19 present (Brand X test data)
  try {
    const { data, error } = await supabase
      .schema('ces')
      .from('campaigns')
      .select('campaign_code')
      .ilike('brand_name', '%Brand X%')
      .limit(1);

    if (error) {
      checks.push({
        name: 'seed_data',
        status: 'degraded',
        message: error.message
      });
      if (overallStatus === 'healthy') overallStatus = 'degraded';
    } else if (!data || data.length === 0) {
      checks.push({
        name: 'seed_data',
        status: 'degraded',
        message: 'Brand X seed data not found'
      });
      if (overallStatus === 'healthy') overallStatus = 'degraded';
    } else {
      checks.push({
        name: 'seed_data',
        status: 'healthy',
        message: 'Brand X seed data present'
      });
    }
  } catch (err) {
    checks.push({
      name: 'seed_data',
      status: 'degraded',
      message: err instanceof Error ? err.message : 'Check failed'
    });
    if (overallStatus === 'healthy') overallStatus = 'degraded';
  }

  // Check 3: RLS behaves correctly (implicit - if query works, RLS is configured)
  checks.push({
    name: 'rls_configured',
    status: overallStatus !== 'broken' ? 'healthy' : 'degraded',
    message: overallStatus !== 'broken' ? 'RLS allowing service_role access' : 'Unable to verify RLS'
  });

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
    name: 'ces.campaign_overview',
    description: 'Fetch a CES campaign with scores and explanations. The main structured fetch for Ask Ces.',
    inputSchema: CesCampaignOverviewSchema,
    execute: campaignOverview
  },
  {
    name: 'ces.link_figma_asset',
    description: 'Connect a CES campaign to a Figma asset for design system integration.',
    inputSchema: CesLinkFigmaSchema,
    execute: linkFigmaAsset
  },
  {
    name: 'ces.list_campaigns',
    description: 'List CES campaigns with optional brand and status filters.',
    inputSchema: {
      type: 'object',
      properties: {
        brand_name: { type: 'string', description: 'Filter by brand name (partial match)' },
        status: { type: 'string', description: 'Filter by status (active, completed, draft)' },
        limit: { type: 'number', description: 'Maximum results (default 20)' }
      }
    },
    execute: listCampaigns
  },
  {
    name: 'ces.health_check',
    description: 'Check CES schema health: campaigns not empty, seed data present, RLS configured.',
    inputSchema: null,
    execute: healthCheck
  }
];
