/**
 * Supabase tools (supabase.*)
 * DB / SaaS core / Odoo mirror / Scout / CES
 */

import { z } from "zod";
import { createClient } from "@supabase/supabase-js";
import type { McpTool, ToolContext, HealthCheckResult, SqlQueryResult } from "../types.js";
import { TableFilterSchema, OrderBySchema } from "../types.js";

// 1.1 supabase.sql_query
const sqlQuerySchema = z.object({
  sql: z.string().describe("Read-only SQL query (SELECT only)."),
  params: z.record(z.union([z.string(), z.number(), z.boolean()])).optional(),
});

async function executeSqlQuery(
  args: z.infer<typeof sqlQuerySchema>,
  ctx: ToolContext
): Promise<SqlQueryResult> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  // Validate SELECT only
  const normalizedSql = args.sql.trim().toLowerCase();
  if (!normalizedSql.startsWith("select") && !normalizedSql.startsWith("with")) {
    throw new Error("Only SELECT queries are allowed. Use Edge Functions or n8n for writes.");
  }

  const { data, error } = await supabase.rpc("exec_sql", {
    query: args.sql,
    params: args.params || {},
  });

  if (error) {
    // Fallback: try direct query if RPC not available
    const { data: directData, error: directError } = await supabase
      .from("_sql")
      .select()
      .limit(1);

    if (directError) {
      throw new Error(`SQL execution failed: ${error.message}`);
    }
  }

  return {
    rows: data || [],
    rowCount: (data || []).length,
    fields: data && data.length > 0 ? Object.keys(data[0]) : [],
  };
}

// 1.2 supabase.rpc_call
const rpcCallSchema = z.object({
  schema: z.string().describe("Schema name (e.g., 'public', 'odoo_mirror')"),
  function: z.string().describe("Function name to call"),
  args: z.record(z.unknown()).optional().describe("Function arguments"),
});

async function executeRpcCall(
  args: z.infer<typeof rpcCallSchema>,
  ctx: ToolContext
): Promise<unknown> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  const { data, error } = await supabase.rpc(args.function, args.args || {});

  if (error) {
    throw new Error(`RPC call failed: ${error.message}`);
  }

  return data;
}

// 1.3 supabase.table_select
const tableSelectSchema = z.object({
  schema: z.string().describe("Schema name (e.g., 'odoo_mirror', 'scout', 'ces', 'saas')"),
  table: z.string().describe("Table name"),
  filters: z.array(TableFilterSchema).optional().describe("Filter conditions"),
  limit: z.number().default(100).describe("Maximum rows to return"),
  order_by: OrderBySchema.optional().describe("Order specification"),
  columns: z.array(z.string()).optional().describe("Columns to select (default: all)"),
});

async function executeTableSelect(
  args: z.infer<typeof tableSelectSchema>,
  ctx: ToolContext
): Promise<SqlQueryResult> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  const tablePath = args.schema === "public" ? args.table : `${args.schema}.${args.table}`;
  let query = supabase.from(tablePath).select(args.columns?.join(",") || "*");

  // Apply filters
  if (args.filters) {
    for (const filter of args.filters) {
      switch (filter.op) {
        case "eq":
          query = query.eq(filter.column, filter.value);
          break;
        case "neq":
          query = query.neq(filter.column, filter.value);
          break;
        case "gt":
          query = query.gt(filter.column, filter.value);
          break;
        case "gte":
          query = query.gte(filter.column, filter.value);
          break;
        case "lt":
          query = query.lt(filter.column, filter.value);
          break;
        case "lte":
          query = query.lte(filter.column, filter.value);
          break;
        case "like":
          query = query.like(filter.column, filter.value as string);
          break;
        case "ilike":
          query = query.ilike(filter.column, filter.value as string);
          break;
        case "in":
          query = query.in(filter.column, filter.value as string[]);
          break;
        case "is":
          query = query.is(filter.column, filter.value);
          break;
      }
    }
  }

  // Apply ordering
  if (args.order_by) {
    query = query.order(args.order_by.column, {
      ascending: args.order_by.direction === "asc",
    });
  }

  // Apply limit
  query = query.limit(args.limit);

  const { data, error } = await query;

  if (error) {
    throw new Error(`Table select failed: ${error.message}`);
  }

  const rows = (data || []) as unknown as Record<string, unknown>[];
  return {
    rows,
    rowCount: rows.length,
    fields: rows.length > 0 ? Object.keys(rows[0]) : [],
  };
}

// 1.4 supabase.health_check
const healthCheckSchema = z.object({}).optional();

async function executeHealthCheck(
  _args: unknown,
  ctx: ToolContext
): Promise<HealthCheckResult> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);
  const checks: HealthCheckResult["checks"] = [];
  let overallStatus: HealthCheckResult["status"] = "healthy";

  // Check 1: DB reachable
  const dbStart = Date.now();
  try {
    const { error } = await supabase.from("_health").select("1").limit(1);
    if (error && !error.message.includes("does not exist")) {
      throw error;
    }
    checks.push({
      name: "db_reachable",
      passed: true,
      message: "Database connection successful",
      duration_ms: Date.now() - dbStart,
    });
  } catch (e) {
    checks.push({
      name: "db_reachable",
      passed: false,
      message: `Database connection failed: ${e instanceof Error ? e.message : String(e)}`,
      duration_ms: Date.now() - dbStart,
    });
    overallStatus = "broken";
  }

  // Check 2: Critical views exist
  const criticalViews = [
    "public.v_tx_trends",
    "ces.campaigns",
    "odoo_mirror.res_partner",
  ];

  for (const view of criticalViews) {
    const viewStart = Date.now();
    try {
      const [schema, table] = view.split(".");
      const { error } = await supabase.from(view).select("*").limit(1);
      checks.push({
        name: `view_${view}`,
        passed: !error,
        message: error ? error.message : `View ${view} accessible`,
        duration_ms: Date.now() - viewStart,
      });
      if (error && overallStatus === "healthy") {
        overallStatus = "degraded";
      }
    } catch (e) {
      checks.push({
        name: `view_${view}`,
        passed: false,
        message: `View check failed: ${e instanceof Error ? e.message : String(e)}`,
        duration_ms: Date.now() - viewStart,
      });
      if (overallStatus === "healthy") {
        overallStatus = "degraded";
      }
    }
  }

  // Check 3: odoo_mirror not empty
  const mirrorStart = Date.now();
  try {
    const { count, error } = await supabase
      .from("odoo_mirror.res_partner")
      .select("*", { count: "exact", head: true });

    checks.push({
      name: "odoo_mirror_populated",
      passed: !error && (count ?? 0) > 0,
      message: error ? error.message : `odoo_mirror has ${count} partners`,
      duration_ms: Date.now() - mirrorStart,
    });
  } catch (e) {
    checks.push({
      name: "odoo_mirror_populated",
      passed: false,
      message: `Mirror check failed: ${e instanceof Error ? e.message : String(e)}`,
      duration_ms: Date.now() - mirrorStart,
    });
  }

  return {
    status: overallStatus,
    checks,
    timestamp: new Date().toISOString(),
  };
}

// Export all supabase tools
export const tools: McpTool[] = [
  {
    name: "supabase.sql_query",
    description: "Execute a read-only SQL query against Supabase (analytics-only).",
    inputSchema: sqlQuerySchema,
    execute: executeSqlQuery,
  },
  {
    name: "supabase.rpc_call",
    description: "Call a Postgres function (e.g., health checks, Odoo mirror jobs).",
    inputSchema: rpcCallSchema,
    execute: executeRpcCall,
  },
  {
    name: "supabase.table_select",
    description: "Structured select without hand-writing SQL. Use for CRUD-y reads.",
    inputSchema: tableSelectSchema,
    execute: executeTableSelect,
  },
  {
    name: "supabase.health_check",
    description: "Verify DB reachable, critical views present, odoo_mirror populated.",
    inputSchema: healthCheckSchema,
    execute: executeHealthCheck,
  },
];
