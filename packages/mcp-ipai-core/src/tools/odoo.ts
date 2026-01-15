/**
 * Odoo tools for IPAI MCP Server
 * Namespace: odoo.*
 */

import { getConfig } from '../config.js';
import {
  OdooSearchSchema,
  OdooMirrorSyncSchema,
  type OdooSearch,
  type OdooMirrorSync,
  type HealthCheckResult,
  type ToolResult
} from '../types.js';

// Dynamic import for xmlrpc (CommonJS module)
import * as xmlrpcModule from 'xmlrpc';

interface OdooClient {
  uid: number;
  call: (model: string, method: string, args: unknown[]) => Promise<unknown>;
}

let odooClient: OdooClient | null = null;

async function getOdooClient(): Promise<OdooClient> {
  if (odooClient) return odooClient;

  const config = getConfig();

  const url = new URL(config.odoo.url);
  const isSecure = url.protocol === 'https:';
  const port = url.port ? parseInt(url.port) : (isSecure ? 443 : 80);

  const commonClient = isSecure
    ? xmlrpcModule.createSecureClient({ host: url.hostname, port, path: '/xmlrpc/2/common' })
    : xmlrpcModule.createClient({ host: url.hostname, port, path: '/xmlrpc/2/common' });

  const objectClient = isSecure
    ? xmlrpcModule.createSecureClient({ host: url.hostname, port, path: '/xmlrpc/2/object' })
    : xmlrpcModule.createClient({ host: url.hostname, port, path: '/xmlrpc/2/object' });

  // Authenticate
  const uid = await new Promise<number>((resolve, reject) => {
    commonClient.methodCall('authenticate', [
      config.odoo.db,
      config.odoo.username,
      config.odoo.password,
      {}
    ], (err: unknown, value: unknown) => {
      if (err) reject(err);
      else resolve(value as number);
    });
  });

  if (!uid) {
    throw new Error('Odoo authentication failed');
  }

  odooClient = {
    uid,
    call: async (model: string, method: string, args: unknown[]): Promise<unknown> => {
      return new Promise((resolve, reject) => {
        objectClient.methodCall('execute_kw', [
          config.odoo.db,
          uid,
          config.odoo.password,
          model,
          method,
          args
        ], (err: unknown, value: unknown) => {
          if (err) reject(err);
          else resolve(value);
        });
      });
    }
  };

  return odooClient;
}

/**
 * odoo.nav_health - Check Odoo navigation and basic functionality
 */
async function navHealth(): Promise<ToolResult<HealthCheckResult>> {
  const checks: HealthCheckResult['checks'] = [];
  let overallStatus: HealthCheckResult['status'] = 'healthy';

  // Check 1: Login works
  const loginStart = Date.now();
  try {
    const client = await getOdooClient();
    checks.push({
      name: 'login',
      status: 'healthy',
      message: `Authenticated as UID ${client.uid}`,
      latencyMs: Date.now() - loginStart
    });
  } catch (err) {
    checks.push({
      name: 'login',
      status: 'broken',
      message: err instanceof Error ? err.message : 'Login failed',
      latencyMs: Date.now() - loginStart
    });
    return {
      success: true,
      data: {
        status: 'broken',
        checks,
        timestamp: new Date().toISOString()
      }
    };
  }

  // Check 2: Key menus exist
  const keyMenus = [
    'Accounting',
    'Sales',
    'Projects',
    'Inventory',
    'Contacts'
  ];

  try {
    const client = await getOdooClient();
    const menus = await client.call('ir.ui.menu', 'search_read', [
      [['name', 'in', keyMenus]],
      ['name']
    ]) as Array<{ name: string }>;

    const foundMenus = menus.map(m => m.name);
    const missingMenus = keyMenus.filter(m => !foundMenus.includes(m));

    if (missingMenus.length === 0) {
      checks.push({
        name: 'key_menus',
        status: 'healthy',
        message: `All ${keyMenus.length} key menus present`
      });
    } else if (missingMenus.length < keyMenus.length / 2) {
      checks.push({
        name: 'key_menus',
        status: 'degraded',
        message: `Missing menus: ${missingMenus.join(', ')}`
      });
      if (overallStatus === 'healthy') overallStatus = 'degraded';
    } else {
      checks.push({
        name: 'key_menus',
        status: 'broken',
        message: `Most menus missing: ${missingMenus.join(', ')}`
      });
      overallStatus = 'broken';
    }
  } catch (err) {
    checks.push({
      name: 'key_menus',
      status: 'degraded',
      message: err instanceof Error ? err.message : 'Menu check failed'
    });
    if (overallStatus === 'healthy') overallStatus = 'degraded';
  }

  // Check 3: Minimal record presence
  const criticalModels = [
    { model: 'res.company', min: 1 },
    { model: 'res.users', min: 1 },
    { model: 'res.partner', min: 1 }
  ];

  for (const { model, min } of criticalModels) {
    try {
      const client = await getOdooClient();
      const count = await client.call(model, 'search_count', [[]]) as number;

      if (count >= min) {
        checks.push({
          name: `records_${model}`,
          status: 'healthy',
          message: `${count} records`
        });
      } else {
        checks.push({
          name: `records_${model}`,
          status: 'degraded',
          message: `Only ${count} records (min: ${min})`
        });
        if (overallStatus === 'healthy') overallStatus = 'degraded';
      }
    } catch (err) {
      checks.push({
        name: `records_${model}`,
        status: 'degraded',
        message: err instanceof Error ? err.message : 'Check failed'
      });
      if (overallStatus === 'healthy') overallStatus = 'degraded';
    }
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
 * odoo.search_records - Generic XML-RPC search for any model
 */
async function searchRecords(params: OdooSearch): Promise<ToolResult<unknown[]>> {
  try {
    const client = await getOdooClient();
    const records = await client.call(params.model, 'search_read', [
      params.domain,
      params.fields,
      0, // offset
      params.limit
    ]);

    return { success: true, data: records as unknown[] };
  } catch (err) {
    return {
      success: false,
      error: `Odoo search failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * odoo.trigger_mirror_sync - Kick off Odoo → Supabase mirror flow
 */
async function triggerMirrorSync(params: OdooMirrorSync): Promise<ToolResult<{ execution_id?: string; status: string }>> {
  const config = getConfig();

  // Prefer n8n workflow for orchestration
  if (config.n8n.apiKey) {
    try {
      const response = await fetch(`${config.n8n.baseUrl}/api/v1/workflows/odoo-mirror-sync/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${config.n8n.apiKey}`
        },
        body: JSON.stringify({
          mode: params.mode,
          entities: params.entities
        })
      });

      if (!response.ok) {
        throw new Error(`n8n workflow trigger failed: ${response.statusText}`);
      }

      const result = await response.json() as { executionId?: string };
      return {
        success: true,
        data: {
          execution_id: result.executionId,
          status: 'triggered'
        }
      };
    } catch (err) {
      // Fallback to direct Edge Function call
      console.warn('n8n trigger failed, falling back to Edge Function:', err);
    }
  }

  // Fallback: Call Supabase Edge Function directly
  try {
    const response = await fetch(`${config.supabase.url}/functions/v1/odoo-mirror-import`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.supabase.serviceRoleKey}`
      },
      body: JSON.stringify({
        mode: params.mode,
        entities: params.entities
      })
    });

    if (!response.ok) {
      throw new Error(`Edge Function call failed: ${response.statusText}`);
    }

    const result = await response.json() as { status: string };
    return {
      success: true,
      data: {
        status: result.status || 'triggered'
      }
    };
  } catch (err) {
    return {
      success: false,
      error: `Mirror sync trigger failed: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

// Export tools array for aggregation
export const tools = [
  {
    name: 'odoo.nav_health',
    description: 'Check Odoo navigation health: login works, key menus exist, minimal records present.',
    inputSchema: null,
    execute: navHealth
  },
  {
    name: 'odoo.search_records',
    description: 'Generic XML-RPC search for any Odoo model. Returns matching records with specified fields.',
    inputSchema: OdooSearchSchema,
    execute: searchRecords
  },
  {
    name: 'odoo.trigger_mirror_sync',
    description: 'Kick off Odoo → Supabase mirror sync. Uses n8n workflow or Edge Function.',
    inputSchema: OdooMirrorSyncSchema,
    execute: triggerMirrorSync
  }
];
