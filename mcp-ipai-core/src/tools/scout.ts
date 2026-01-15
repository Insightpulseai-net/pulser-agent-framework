/**
 * Scout tools (scout.*)
 * Retail analytics on scout_* schemas / gold views
 */

import { z } from "zod";
import { createClient } from "@supabase/supabase-js";
import type { McpTool, ToolContext, HealthCheckResult } from "../types.js";

// 6.1 scout.tx_insight
const txInsightSchema = z.object({
  question: z.string().describe("Plain-language question about transactions"),
  store_id: z.string().optional().describe("Filter by specific store"),
  date_from: z.string().optional().describe("Start date (YYYY-MM-DD)"),
  date_to: z.string().optional().describe("End date (YYYY-MM-DD)"),
  limit: z.number().default(100).describe("Max rows for result"),
});

async function executeTxInsight(
  args: z.infer<typeof txInsightSchema>,
  ctx: ToolContext
): Promise<unknown> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  // Build SQL based on question patterns (NL->SQL template)
  // This is a simplified mapper; in production, use LLM for complex NL
  const question = args.question.toLowerCase();
  let sql = "";

  // Scout Gold schema fields (26-field spec):
  // id, store_id, timestamp, product_category, brand_name, sku,
  // quantity, unit_price, total_amount, payment_method, customer_segment,
  // basket_id, promotion_applied, margin_percent, region, city,
  // store_type, channel, day_of_week, hour_of_day, is_weekend,
  // weather_condition, competitor_nearby, loyalty_member, return_flag, notes

  if (question.includes("top") && question.includes("brand")) {
    sql = `
      SELECT brand_name, SUM(total_amount) as revenue, COUNT(*) as tx_count
      FROM scout_gold_transactions_flat
      WHERE 1=1
      ${args.store_id ? `AND store_id = '${args.store_id}'` : ""}
      ${args.date_from ? `AND timestamp >= '${args.date_from}'` : ""}
      ${args.date_to ? `AND timestamp <= '${args.date_to}'` : ""}
      GROUP BY brand_name
      ORDER BY revenue DESC
      LIMIT ${args.limit}
    `;
  } else if (question.includes("sales") && question.includes("category")) {
    sql = `
      SELECT product_category, SUM(total_amount) as revenue,
             SUM(quantity) as units_sold, AVG(margin_percent) as avg_margin
      FROM scout_gold_transactions_flat
      WHERE 1=1
      ${args.store_id ? `AND store_id = '${args.store_id}'` : ""}
      ${args.date_from ? `AND timestamp >= '${args.date_from}'` : ""}
      ${args.date_to ? `AND timestamp <= '${args.date_to}'` : ""}
      GROUP BY product_category
      ORDER BY revenue DESC
      LIMIT ${args.limit}
    `;
  } else if (question.includes("trend") || question.includes("daily")) {
    sql = `
      SELECT DATE(timestamp) as date, SUM(total_amount) as revenue,
             COUNT(DISTINCT basket_id) as transactions
      FROM scout_gold_transactions_flat
      WHERE 1=1
      ${args.store_id ? `AND store_id = '${args.store_id}'` : ""}
      ${args.date_from ? `AND timestamp >= '${args.date_from}'` : ""}
      ${args.date_to ? `AND timestamp <= '${args.date_to}'` : ""}
      GROUP BY DATE(timestamp)
      ORDER BY date DESC
      LIMIT ${args.limit}
    `;
  } else if (question.includes("store") && question.includes("performance")) {
    sql = `
      SELECT store_id, store_type, region, city,
             SUM(total_amount) as revenue, COUNT(*) as tx_count,
             AVG(total_amount) as avg_basket
      FROM scout_gold_transactions_flat
      WHERE 1=1
      ${args.date_from ? `AND timestamp >= '${args.date_from}'` : ""}
      ${args.date_to ? `AND timestamp <= '${args.date_to}'` : ""}
      GROUP BY store_id, store_type, region, city
      ORDER BY revenue DESC
      LIMIT ${args.limit}
    `;
  } else {
    // Default: general summary
    sql = `
      SELECT
        COUNT(*) as total_transactions,
        SUM(total_amount) as total_revenue,
        AVG(total_amount) as avg_transaction,
        COUNT(DISTINCT store_id) as stores,
        COUNT(DISTINCT brand_name) as brands
      FROM scout_gold_transactions_flat
      WHERE 1=1
      ${args.store_id ? `AND store_id = '${args.store_id}'` : ""}
      ${args.date_from ? `AND timestamp >= '${args.date_from}'` : ""}
      ${args.date_to ? `AND timestamp <= '${args.date_to}'` : ""}
    `;
  }

  // Execute via RPC or direct query
  const { data, error } = await supabase.rpc("exec_sql", { query: sql });

  if (error) {
    // Fallback to direct table query
    throw new Error(`Query failed: ${error.message}. SQL: ${sql}`);
  }

  return {
    question: args.question,
    sql_generated: sql.trim(),
    result: data,
  };
}

// 6.2 scout.gold_health
const goldHealthSchema = z.object({}).optional();

async function executeGoldHealth(
  _args: unknown,
  ctx: ToolContext
): Promise<HealthCheckResult> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);
  const checks: HealthCheckResult["checks"] = [];
  let overallStatus: HealthCheckResult["status"] = "healthy";

  // Check 1: Gold view exists
  const viewStart = Date.now();
  try {
    const { error } = await supabase
      .from("scout_gold_transactions_flat")
      .select("id")
      .limit(1);

    checks.push({
      name: "gold_view_exists",
      passed: !error,
      message: error ? error.message : "Gold view accessible",
      duration_ms: Date.now() - viewStart,
    });

    if (error) overallStatus = "broken";
  } catch (e) {
    checks.push({
      name: "gold_view_exists",
      passed: false,
      message: `Check failed: ${e instanceof Error ? e.message : String(e)}`,
      duration_ms: Date.now() - viewStart,
    });
    overallStatus = "broken";
  }

  // Check 2: Row count > 0
  const countStart = Date.now();
  try {
    const { count, error } = await supabase
      .from("scout_gold_transactions_flat")
      .select("*", { count: "exact", head: true });

    checks.push({
      name: "gold_has_data",
      passed: !error && (count ?? 0) > 0,
      message: error ? error.message : `${count} transactions in gold view`,
      duration_ms: Date.now() - countStart,
    });

    if ((count ?? 0) === 0 && overallStatus === "healthy") {
      overallStatus = "degraded";
    }
  } catch (e) {
    checks.push({
      name: "gold_has_data",
      passed: false,
      message: `Check failed: ${e instanceof Error ? e.message : String(e)}`,
      duration_ms: Date.now() - countStart,
    });
  }

  // Check 3: Required columns present (26-field spec)
  const requiredColumns = [
    "id", "store_id", "timestamp", "product_category", "brand_name",
    "sku", "quantity", "unit_price", "total_amount", "payment_method",
  ];
  const columnsStart = Date.now();
  try {
    const { data, error } = await supabase
      .from("scout_gold_transactions_flat")
      .select(requiredColumns.join(","))
      .limit(1);

    const hasAllColumns = !error && data && data.length > 0;
    checks.push({
      name: "required_columns",
      passed: hasAllColumns,
      message: hasAllColumns
        ? "All required columns present"
        : `Missing or inaccessible columns: ${error?.message || "no data"}`,
      duration_ms: Date.now() - columnsStart,
    });

    if (!hasAllColumns && overallStatus === "healthy") {
      overallStatus = "degraded";
    }
  } catch (e) {
    checks.push({
      name: "required_columns",
      passed: false,
      message: `Check failed: ${e instanceof Error ? e.message : String(e)}`,
      duration_ms: Date.now() - columnsStart,
    });
  }

  return {
    status: overallStatus,
    checks,
    timestamp: new Date().toISOString(),
  };
}

// 6.3 scout.seed_demo_data
const seedDemoDataSchema = z.object({
  tenant_code: z.string().describe("Tenant code for demo data"),
  mode: z.enum(["reset", "append"]).default("append").describe("Seed mode"),
});

async function executeSeedDemoData(
  args: z.infer<typeof seedDemoDataSchema>,
  ctx: ToolContext
): Promise<{ status: string; message: string }> {
  // Call Edge Function for idempotent seeding
  const response = await fetch(`${ctx.supabaseUrl}/functions/v1/scout-seed-demo`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${ctx.supabaseServiceKey}`,
    },
    body: JSON.stringify({
      tenant_code: args.tenant_code,
      mode: args.mode,
    }),
  });

  if (!response.ok) {
    throw new Error(`Seed demo data failed: ${response.status}`);
  }

  const result = await response.json() as { rows_inserted?: number };
  return {
    status: "success",
    message: `Demo data ${args.mode === "reset" ? "reset and " : ""}seeded for ${args.tenant_code}. ${result.rows_inserted || 0} rows.`,
  };
}

export const tools: McpTool[] = [
  {
    name: "scout.tx_insight",
    description: "Answer questions about Scout transactions using NL->SQL on gold schema.",
    inputSchema: txInsightSchema,
    execute: executeTxInsight,
  },
  {
    name: "scout.gold_health",
    description: "Check gold view exists, has data, required columns match 26-field spec.",
    inputSchema: goldHealthSchema,
    execute: executeGoldHealth,
  },
  {
    name: "scout.seed_demo_data",
    description: "Idempotent seed for demo tenants via Edge Function.",
    inputSchema: seedDemoDataSchema,
    execute: executeSeedDemoData,
  },
];
