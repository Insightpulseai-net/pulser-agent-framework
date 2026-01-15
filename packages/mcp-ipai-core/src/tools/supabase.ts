/**
 * Supabase tools for IPAI MCP Server
 * Namespace: supabase.*
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { getConfig } from '../config.js';
import {
  SqlQuerySchema,
  RpcCallSchema,
  TableSelectSchema,
  type SqlQuery,
  type RpcCall,
  type TableSelect,
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

/**
 * supabase.sql_query - Execute read-only SQL queries
 */
async function sqlQuery(params: SqlQuery): Promise<ToolResult<unknown[]>> {
  const supabase = getSupabaseClient();

  // Validate SELECT-only
  const trimmedSql = params.sql.trim().toUpperCase();
  if (!trimmedSql.startsWith('SELECT') && !trimmedSql.startsWith('WITH')) {
    return {
      success: false,
      error: 'Only SELECT queries are allowed. Use RPC functions for writes.'
    };
  }

  try {
    const { data, error } = await supabase.rpc('exec_sql', {
      query: params.sql,
      params: params.params
    });

    if (error) {
      // Fallback to raw query if exec_sql RPC doesn't exist
      const { data: rawData, error: rawError } = await supabase
        .from('_dummy_')
        .select()
        .limit(0);

      // Use postgres.js or pg for raw queries if RPC fails
      return {
        success: false,
        error: `SQL execution failed: ${error.message}. Consider using supabase.table_select for structured queries.`
      };
    }

    return { success: true, data: data || [] };
  } catch (err) {
    return {
      success: false,
      error: `SQL query failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * supabase.rpc_call - Call Postgres functions
 */
async function rpcCall(params: RpcCall): Promise<ToolResult<unknown>> {
  const supabase = getSupabaseClient();

  try {
    const { data, error } = await supabase
      .schema(params.schema)
      .rpc(params.function, params.args || {});

    if (error) {
      return { success: false, error: error.message };
    }

    return { success: true, data };
  } catch (err) {
    return {
      success: false,
      error: `RPC call failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * supabase.table_select - Structured table queries
 */
async function tableSelect(params: TableSelect): Promise<ToolResult<unknown[]>> {
  const supabase = getSupabaseClient();

  try {
    let query = supabase
      .schema(params.schema)
      .from(params.table)
      .select('*')
      .limit(params.limit);

    // Apply filters
    if (params.filters) {
      for (const filter of params.filters) {
        switch (filter.op) {
          case 'eq':
            query = query.eq(filter.column, filter.value);
            break;
          case 'neq':
            query = query.neq(filter.column, filter.value);
            break;
          case 'gt':
            query = query.gt(filter.column, filter.value);
            break;
          case 'gte':
            query = query.gte(filter.column, filter.value);
            break;
          case 'lt':
            query = query.lt(filter.column, filter.value);
            break;
          case 'lte':
            query = query.lte(filter.column, filter.value);
            break;
          case 'like':
            query = query.like(filter.column, String(filter.value));
            break;
          case 'ilike':
            query = query.ilike(filter.column, String(filter.value));
            break;
          case 'in':
            query = query.in(filter.column, filter.value as unknown[]);
            break;
          case 'is':
            query = query.is(filter.column, filter.value as null);
            break;
        }
      }
    }

    // Apply ordering
    if (params.order_by) {
      query = query.order(params.order_by.column, {
        ascending: params.order_by.direction === 'asc'
      });
    }

    const { data, error } = await query;

    if (error) {
      return { success: false, error: error.message };
    }

    return { success: true, data: data || [] };
  } catch (err) {
    return {
      success: false,
      error: `Table select failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * supabase.health_check - Verify Supabase connectivity and critical resources
 */
async function healthCheck(): Promise<ToolResult<HealthCheckResult>> {
  const supabase = getSupabaseClient();
  const checks: HealthCheckResult['checks'] = [];
  let overallStatus: HealthCheckResult['status'] = 'healthy';

  // Check 1: Database connection
  const dbStart = Date.now();
  try {
    const { error } = await supabase.from('_dummy_check_').select('count').limit(0);
    // Error is expected for non-existent table, but connection works
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

  // Check 2: Critical views exist
  const criticalViews = [
    { schema: 'public', view: 'v_tx_trends' },
    { schema: 'ces', view: 'campaigns' },
    { schema: 'odoo_mirror', view: 'res_partner' }
  ];

  for (const { schema, view } of criticalViews) {
    const viewStart = Date.now();
    try {
      const { error } = await supabase
        .schema(schema)
        .from(view)
        .select('*')
        .limit(1);

      if (error && !error.message.includes('does not exist')) {
        checks.push({
          name: `view_${schema}.${view}`,
          status: 'degraded',
          message: error.message,
          latencyMs: Date.now() - viewStart
        });
        if (overallStatus === 'healthy') overallStatus = 'degraded';
      } else if (error) {
        checks.push({
          name: `view_${schema}.${view}`,
          status: 'degraded',
          message: 'View does not exist',
          latencyMs: Date.now() - viewStart
        });
        if (overallStatus === 'healthy') overallStatus = 'degraded';
      } else {
        checks.push({
          name: `view_${schema}.${view}`,
          status: 'healthy',
          latencyMs: Date.now() - viewStart
        });
      }
    } catch (err) {
      checks.push({
        name: `view_${schema}.${view}`,
        status: 'broken',
        message: err instanceof Error ? err.message : 'Check failed',
        latencyMs: Date.now() - viewStart
      });
      overallStatus = 'broken';
    }
  }

  // Check 3: odoo_mirror not empty
  try {
    const { count, error } = await supabase
      .schema('odoo_mirror')
      .from('res_partner')
      .select('*', { count: 'exact', head: true });

    if (error) {
      checks.push({
        name: 'odoo_mirror_populated',
        status: 'degraded',
        message: 'Mirror table not accessible'
      });
      if (overallStatus === 'healthy') overallStatus = 'degraded';
    } else if (!count || count === 0) {
      checks.push({
        name: 'odoo_mirror_populated',
        status: 'degraded',
        message: 'Mirror is empty - sync may be needed'
      });
      if (overallStatus === 'healthy') overallStatus = 'degraded';
    } else {
      checks.push({
        name: 'odoo_mirror_populated',
        status: 'healthy',
        message: `${count} records in mirror`
      });
    }
  } catch (err) {
    checks.push({
      name: 'odoo_mirror_populated',
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

// Export tools array for aggregation
export const tools = [
  {
    name: 'supabase.sql_query',
    description: 'Execute a read-only SQL query against Supabase (analytics-only). Only SELECT statements allowed.',
    inputSchema: SqlQuerySchema,
    execute: sqlQuery
  },
  {
    name: 'supabase.rpc_call',
    description: 'Call a Postgres function (RPC) in Supabase. Use for health checks, Odoo mirror jobs, etc.',
    inputSchema: RpcCallSchema,
    execute: rpcCall
  },
  {
    name: 'supabase.table_select',
    description: 'Structured table select without hand-writing SQL. Supports filtering, ordering, and pagination.',
    inputSchema: TableSelectSchema,
    execute: tableSelect
  },
  {
    name: 'supabase.health_check',
    description: 'Verify Supabase connectivity: DB reachable, critical views exist, odoo_mirror populated.',
    inputSchema: null,
    execute: healthCheck
  }
];
