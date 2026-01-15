/**
 * Scout tools for IPAI MCP Server
 * Namespace: scout.*
 *
 * Retail analytics helpers on top of scout_* schemas and gold views.
 * Based on the 26-field Scout Gold schema.
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { getConfig } from '../config.js';
import {
  ScoutTxInsightSchema,
  ScoutSeedDemoSchema,
  type ScoutTxInsight,
  type ScoutSeedDemo,
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

// Scout Gold schema field definitions for NL→SQL mapping
const SCOUT_GOLD_FIELDS = {
  id: 'Transaction unique identifier (UUID)',
  store_id: 'Store identifier',
  store_name: 'Store name',
  timestamp: 'Transaction timestamp',
  transaction_date: 'Date of transaction',
  product_id: 'Product identifier',
  product_name: 'Product name',
  product_category: 'Product category (e.g., beverages, snacks)',
  brand_id: 'Brand identifier',
  brand_name: 'Brand name',
  sku: 'Stock keeping unit',
  quantity: 'Quantity sold',
  unit_price: 'Price per unit',
  total_amount: 'Total transaction amount',
  payment_method: 'Payment method (cash, gcash, etc.)',
  customer_id: 'Customer identifier (if available)',
  customer_type: 'Customer segment',
  region: 'Geographic region',
  city: 'City name',
  barangay: 'Barangay (neighborhood)',
  latitude: 'Store latitude',
  longitude: 'Store longitude',
  promo_code: 'Promotion code applied',
  discount_amount: 'Discount amount',
  created_at: 'Record creation timestamp',
  updated_at: 'Record update timestamp'
};

// NL→SQL template patterns
const QUERY_TEMPLATES: Record<string, string> = {
  top_brands: `
    SELECT brand_name, COUNT(*) as transactions, SUM(total_amount) as revenue
    FROM scout.gold_transactions_flat
    WHERE timestamp >= NOW() - INTERVAL '{{period}}'
    GROUP BY brand_name
    ORDER BY revenue DESC
    LIMIT {{limit}}
  `,
  top_products: `
    SELECT product_name, product_category, SUM(quantity) as units_sold, SUM(total_amount) as revenue
    FROM scout.gold_transactions_flat
    WHERE timestamp >= NOW() - INTERVAL '{{period}}'
    GROUP BY product_name, product_category
    ORDER BY units_sold DESC
    LIMIT {{limit}}
  `,
  store_performance: `
    SELECT store_name, region, COUNT(*) as transactions, SUM(total_amount) as revenue
    FROM scout.gold_transactions_flat
    WHERE timestamp >= NOW() - INTERVAL '{{period}}'
    GROUP BY store_name, region
    ORDER BY revenue DESC
    LIMIT {{limit}}
  `,
  category_breakdown: `
    SELECT product_category, COUNT(*) as transactions, SUM(quantity) as units, SUM(total_amount) as revenue
    FROM scout.gold_transactions_flat
    WHERE timestamp >= NOW() - INTERVAL '{{period}}'
    GROUP BY product_category
    ORDER BY revenue DESC
  `,
  payment_methods: `
    SELECT payment_method, COUNT(*) as transactions, SUM(total_amount) as revenue
    FROM scout.gold_transactions_flat
    WHERE timestamp >= NOW() - INTERVAL '{{period}}'
    GROUP BY payment_method
    ORDER BY transactions DESC
  `
};

function detectQueryTemplate(question: string): { template: string; params: Record<string, string> } | null {
  const q = question.toLowerCase();
  const params: Record<string, string> = {
    period: '30 days',
    limit: '10'
  };

  // Detect time period
  if (q.includes('today')) params.period = '1 day';
  else if (q.includes('week')) params.period = '7 days';
  else if (q.includes('month')) params.period = '30 days';
  else if (q.includes('quarter')) params.period = '90 days';
  else if (q.includes('year')) params.period = '365 days';

  // Detect limit
  const limitMatch = q.match(/top\s+(\d+)/);
  if (limitMatch) params.limit = limitMatch[1];

  // Detect query type
  if (q.includes('brand') || q.includes('brands')) return { template: 'top_brands', params };
  if (q.includes('product') || q.includes('products')) return { template: 'top_products', params };
  if (q.includes('store') || q.includes('stores')) return { template: 'store_performance', params };
  if (q.includes('category') || q.includes('categories')) return { template: 'category_breakdown', params };
  if (q.includes('payment') || q.includes('gcash') || q.includes('cash')) return { template: 'payment_methods', params };

  return null;
}

/**
 * scout.tx_insight - Natural language query helper for Scout transactions
 */
async function txInsight(params: ScoutTxInsight): Promise<ToolResult<{
  query: string;
  results: unknown[];
  explanation: string;
}>> {
  const supabase = getSupabaseClient();

  const detected = detectQueryTemplate(params.question);

  if (!detected) {
    return {
      success: false,
      error: `Could not understand question. Try asking about: top brands, top products, store performance, category breakdown, or payment methods.`
    };
  }

  // Build SQL from template
  let sql = QUERY_TEMPLATES[detected.template];
  for (const [key, value] of Object.entries(detected.params)) {
    sql = sql.replace(new RegExp(`{{${key}}}`, 'g'), value);
  }

  try {
    const { data, error } = await supabase.rpc('exec_sql', { query: sql.trim() });

    if (error) {
      return {
        success: false,
        error: `Query failed: ${error.message}`
      };
    }

    return {
      success: true,
      data: {
        query: sql.trim(),
        results: data || [],
        explanation: `Analyzed ${detected.template.replace('_', ' ')} for the last ${detected.params.period}`
      }
    };
  } catch (err) {
    return {
      success: false,
      error: `Scout insight failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * scout.gold_health - Check Scout Gold schema health
 */
async function goldHealth(): Promise<ToolResult<HealthCheckResult>> {
  const supabase = getSupabaseClient();
  const checks: HealthCheckResult['checks'] = [];
  let overallStatus: HealthCheckResult['status'] = 'healthy';

  // Check 1: Gold view exists
  try {
    const { error } = await supabase
      .schema('scout')
      .from('gold_transactions_flat')
      .select('*')
      .limit(1);

    if (error && error.message.includes('does not exist')) {
      checks.push({
        name: 'gold_view_exists',
        status: 'broken',
        message: 'View scout.gold_transactions_flat does not exist'
      });
      overallStatus = 'broken';
    } else if (error) {
      checks.push({
        name: 'gold_view_exists',
        status: 'degraded',
        message: error.message
      });
      if (overallStatus === 'healthy') overallStatus = 'degraded';
    } else {
      checks.push({
        name: 'gold_view_exists',
        status: 'healthy'
      });
    }
  } catch (err) {
    checks.push({
      name: 'gold_view_exists',
      status: 'broken',
      message: err instanceof Error ? err.message : 'Check failed'
    });
    overallStatus = 'broken';
  }

  // Check 2: Row count > 0
  try {
    const { count, error } = await supabase
      .schema('scout')
      .from('gold_transactions_flat')
      .select('*', { count: 'exact', head: true });

    if (error) {
      checks.push({
        name: 'gold_row_count',
        status: 'degraded',
        message: error.message
      });
      if (overallStatus === 'healthy') overallStatus = 'degraded';
    } else if (!count || count === 0) {
      checks.push({
        name: 'gold_row_count',
        status: 'degraded',
        message: 'Gold view is empty'
      });
      if (overallStatus === 'healthy') overallStatus = 'degraded';
    } else {
      checks.push({
        name: 'gold_row_count',
        status: 'healthy',
        message: `${count.toLocaleString()} records`
      });
    }
  } catch (err) {
    checks.push({
      name: 'gold_row_count',
      status: 'degraded',
      message: err instanceof Error ? err.message : 'Check failed'
    });
    if (overallStatus === 'healthy') overallStatus = 'degraded';
  }

  // Check 3: Required columns match 26-field spec
  const requiredColumns = ['id', 'store_id', 'timestamp', 'product_category', 'brand_name', 'sku', 'total_amount'];
  try {
    const { data, error } = await supabase
      .schema('scout')
      .from('gold_transactions_flat')
      .select(requiredColumns.join(','))
      .limit(1);

    if (error) {
      checks.push({
        name: 'gold_schema_match',
        status: 'degraded',
        message: `Missing columns: ${error.message}`
      });
      if (overallStatus === 'healthy') overallStatus = 'degraded';
    } else {
      checks.push({
        name: 'gold_schema_match',
        status: 'healthy',
        message: `All ${requiredColumns.length} required columns present`
      });
    }
  } catch (err) {
    checks.push({
      name: 'gold_schema_match',
      status: 'degraded',
      message: err instanceof Error ? err.message : 'Check failed'
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

/**
 * scout.seed_demo_data - Idempotent seed for demo tenants
 */
async function seedDemoData(params: ScoutSeedDemo): Promise<ToolResult<{ status: string; records_affected?: number }>> {
  const config = getConfig();

  try {
    const response = await fetch(`${config.supabase.url}/functions/v1/scout-seed-demo`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.supabase.serviceRoleKey}`
      },
      body: JSON.stringify({
        tenant_code: params.tenant_code,
        mode: params.mode
      })
    });

    if (!response.ok) {
      throw new Error(`Seed failed: ${response.statusText}`);
    }

    const result = await response.json() as { status: string; records_affected?: number };
    return { success: true, data: result };
  } catch (err) {
    return {
      success: false,
      error: `Demo seed failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

// Export tools array for aggregation
export const tools = [
  {
    name: 'scout.tx_insight',
    description: 'Natural language query helper for Scout transaction data. Uses the 26-field Gold schema.',
    inputSchema: ScoutTxInsightSchema,
    execute: txInsight
  },
  {
    name: 'scout.gold_health',
    description: 'Check Scout Gold schema health: view exists, row count > 0, required columns match 26-field spec.',
    inputSchema: null,
    execute: goldHealth
  },
  {
    name: 'scout.seed_demo_data',
    description: 'Idempotent seed for demo tenants. Can reset or append demo data.',
    inputSchema: ScoutSeedDemoSchema,
    execute: seedDemoData
  }
];
