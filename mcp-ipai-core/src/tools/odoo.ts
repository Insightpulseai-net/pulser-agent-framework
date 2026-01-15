/**
 * Odoo tools (odoo.*)
 * Live Odoo 18 CE/OCA interactions
 */

import { z } from "zod";
import type { McpTool, ToolContext, HealthCheckResult } from "../types.js";

// Helper: Make XML-RPC call to Odoo
async function odooRpc(
  ctx: ToolContext,
  service: string,
  method: string,
  params: unknown[]
): Promise<unknown> {
  if (!ctx.odooUrl || !ctx.odooDb || !ctx.odooUser || !ctx.odooPassword) {
    throw new Error("Odoo credentials not configured");
  }

  const url = `${ctx.odooUrl}/xmlrpc/2/${service}`;

  // Build XML-RPC request
  const xmlBody = buildXmlRpcRequest(method, params);

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "text/xml" },
    body: xmlBody,
  });

  if (!response.ok) {
    throw new Error(`Odoo RPC failed: ${response.status} ${response.statusText}`);
  }

  const text = await response.text();
  return parseXmlRpcResponse(text);
}

function buildXmlRpcRequest(method: string, params: unknown[]): string {
  const paramsXml = params.map((p) => `<param>${valueToXml(p)}</param>`).join("");
  return `<?xml version="1.0"?>
<methodCall>
  <methodName>${method}</methodName>
  <params>${paramsXml}</params>
</methodCall>`;
}

function valueToXml(value: unknown): string {
  if (value === null || value === undefined) {
    return "<value><boolean>0</boolean></value>";
  }
  if (typeof value === "boolean") {
    return `<value><boolean>${value ? 1 : 0}</boolean></value>`;
  }
  if (typeof value === "number") {
    if (Number.isInteger(value)) {
      return `<value><int>${value}</int></value>`;
    }
    return `<value><double>${value}</double></value>`;
  }
  if (typeof value === "string") {
    return `<value><string>${escapeXml(value)}</string></value>`;
  }
  if (Array.isArray(value)) {
    const items = value.map((v) => valueToXml(v)).join("");
    return `<value><array><data>${items}</data></array></value>`;
  }
  if (typeof value === "object") {
    const members = Object.entries(value as Record<string, unknown>)
      .map(([k, v]) => `<member><name>${k}</name>${valueToXml(v)}</member>`)
      .join("");
    return `<value><struct>${members}</struct></value>`;
  }
  return `<value><string>${String(value)}</string></value>`;
}

function escapeXml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function parseXmlRpcResponse(xml: string): unknown {
  // Simple XML-RPC response parser
  const valueMatch = xml.match(/<value>([\s\S]*?)<\/value>/);
  if (!valueMatch) {
    if (xml.includes("<fault>")) {
      const faultMatch = xml.match(/<string>([\s\S]*?)<\/string>/);
      throw new Error(`Odoo fault: ${faultMatch?.[1] || "Unknown error"}`);
    }
    return null;
  }
  return parseXmlValue(valueMatch[1]);
}

function parseXmlValue(xml: string): unknown {
  if (xml.includes("<int>") || xml.includes("<i4>")) {
    const match = xml.match(/<(?:int|i4)>(-?\d+)<\/(?:int|i4)>/);
    return match ? parseInt(match[1], 10) : 0;
  }
  if (xml.includes("<boolean>")) {
    const match = xml.match(/<boolean>(\d)<\/boolean>/);
    return match?.[1] === "1";
  }
  if (xml.includes("<double>")) {
    const match = xml.match(/<double>(-?[\d.]+)<\/double>/);
    return match ? parseFloat(match[1]) : 0;
  }
  if (xml.includes("<string>")) {
    const match = xml.match(/<string>([\s\S]*?)<\/string>/);
    return match?.[1] || "";
  }
  if (xml.includes("<array>")) {
    const dataMatch = xml.match(/<data>([\s\S]*?)<\/data>/);
    if (!dataMatch) return [];
    const values = dataMatch[1].match(/<value>([\s\S]*?)<\/value>/g) || [];
    return values.map((v) => parseXmlValue(v.replace(/<\/?value>/g, "")));
  }
  if (xml.includes("<struct>")) {
    const result: Record<string, unknown> = {};
    const memberMatches = xml.matchAll(/<member>\s*<name>(\w+)<\/name>\s*<value>([\s\S]*?)<\/value>\s*<\/member>/g);
    for (const match of memberMatches) {
      result[match[1]] = parseXmlValue(match[2]);
    }
    return result;
  }
  return xml.trim();
}

// 2.1 odoo.nav_health
const navHealthSchema = z.object({}).optional();

async function executeNavHealth(
  _args: unknown,
  ctx: ToolContext
): Promise<HealthCheckResult> {
  const checks: HealthCheckResult["checks"] = [];
  let overallStatus: HealthCheckResult["status"] = "healthy";

  // Check 1: Login works
  const loginStart = Date.now();
  try {
    const uid = await odooRpc(ctx, "common", "authenticate", [
      ctx.odooDb,
      ctx.odooUser,
      ctx.odooPassword,
      {},
    ]);

    if (!uid) {
      throw new Error("Authentication returned false/null");
    }

    checks.push({
      name: "login",
      passed: true,
      message: `Login successful, uid: ${uid}`,
      duration_ms: Date.now() - loginStart,
    });
  } catch (e) {
    checks.push({
      name: "login",
      passed: false,
      message: `Login failed: ${e instanceof Error ? e.message : String(e)}`,
      duration_ms: Date.now() - loginStart,
    });
    overallStatus = "broken";
    return { status: overallStatus, checks, timestamp: new Date().toISOString() };
  }

  // Get UID for subsequent calls
  const uid = await odooRpc(ctx, "common", "authenticate", [
    ctx.odooDb,
    ctx.odooUser,
    ctx.odooPassword,
    {},
  ]);

  // Check 2: Key menus exist
  const keyMenus = ["Accounting", "Sales", "Projects", "Inventory", "Contacts"];
  const menuStart = Date.now();
  try {
    const menuIds = await odooRpc(ctx, "object", "execute_kw", [
      ctx.odooDb,
      uid,
      ctx.odooPassword,
      "ir.ui.menu",
      "search_read",
      [[["name", "in", keyMenus]]],
      { fields: ["name"] },
    ]) as Array<{ name: string }>;

    const foundMenus = menuIds.map((m) => m.name);
    const missingMenus = keyMenus.filter((m) => !foundMenus.includes(m));

    checks.push({
      name: "key_menus",
      passed: missingMenus.length === 0,
      message: missingMenus.length === 0
        ? `All key menus found: ${foundMenus.join(", ")}`
        : `Missing menus: ${missingMenus.join(", ")}`,
      duration_ms: Date.now() - menuStart,
    });

    if (missingMenus.length > 0 && overallStatus === "healthy") {
      overallStatus = "degraded";
    }
  } catch (e) {
    checks.push({
      name: "key_menus",
      passed: false,
      message: `Menu check failed: ${e instanceof Error ? e.message : String(e)}`,
      duration_ms: Date.now() - menuStart,
    });
    overallStatus = "degraded";
  }

  // Check 3: Minimal record presence
  const modelsToCheck = [
    { model: "res.partner", name: "partners" },
    { model: "res.company", name: "companies" },
    { model: "res.users", name: "users" },
  ];

  for (const { model, name } of modelsToCheck) {
    const recordStart = Date.now();
    try {
      const count = await odooRpc(ctx, "object", "execute_kw", [
        ctx.odooDb,
        uid,
        ctx.odooPassword,
        model,
        "search_count",
        [[]],
      ]) as number;

      checks.push({
        name: `records_${name}`,
        passed: count > 0,
        message: `${name}: ${count} records`,
        duration_ms: Date.now() - recordStart,
      });
    } catch (e) {
      checks.push({
        name: `records_${name}`,
        passed: false,
        message: `Record check failed: ${e instanceof Error ? e.message : String(e)}`,
        duration_ms: Date.now() - recordStart,
      });
    }
  }

  return {
    status: overallStatus,
    checks,
    timestamp: new Date().toISOString(),
  };
}

// 2.2 odoo.search_records
const searchRecordsSchema = z.object({
  model: z.string().describe("Odoo model (e.g., res.partner, account.move)"),
  domain: z.array(z.unknown()).describe("Odoo domain as JSON array"),
  fields: z.array(z.string()).describe("Fields to fetch"),
  limit: z.number().default(100).describe("Maximum records to return"),
  offset: z.number().default(0).describe("Offset for pagination"),
});

async function executeSearchRecords(
  args: z.infer<typeof searchRecordsSchema>,
  ctx: ToolContext
): Promise<unknown[]> {
  const uid = await odooRpc(ctx, "common", "authenticate", [
    ctx.odooDb,
    ctx.odooUser,
    ctx.odooPassword,
    {},
  ]);

  const records = await odooRpc(ctx, "object", "execute_kw", [
    ctx.odooDb,
    uid,
    ctx.odooPassword,
    args.model,
    "search_read",
    [args.domain],
    {
      fields: args.fields,
      limit: args.limit,
      offset: args.offset,
    },
  ]);

  return records as unknown[];
}

// 2.3 odoo.trigger_mirror_sync
const triggerMirrorSyncSchema = z.object({
  mode: z.enum(["full", "delta"]).describe("Sync mode"),
  entities: z.array(z.string()).describe("Entities to sync (e.g., res_partner, account_move)"),
});

async function executeTriggerMirrorSync(
  args: z.infer<typeof triggerMirrorSyncSchema>,
  ctx: ToolContext
): Promise<{ status: string; message: string }> {
  // Trigger via n8n workflow (preferred) or Edge Function
  if (ctx.n8nUrl && ctx.n8nApiKey) {
    const response = await fetch(`${ctx.n8nUrl}/webhook/odoo-mirror-sync`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-N8N-API-KEY": ctx.n8nApiKey,
      },
      body: JSON.stringify({
        mode: args.mode,
        entities: args.entities,
      }),
    });

    if (!response.ok) {
      throw new Error(`n8n webhook failed: ${response.status}`);
    }

    return {
      status: "triggered",
      message: `Mirror sync ${args.mode} triggered for: ${args.entities.join(", ")}`,
    };
  }

  // Fallback: Call Supabase Edge Function
  const response = await fetch(`${ctx.supabaseUrl}/functions/v1/odoo-mirror-import`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${ctx.supabaseServiceKey}`,
    },
    body: JSON.stringify({
      mode: args.mode,
      tables: args.entities,
    }),
  });

  if (!response.ok) {
    throw new Error(`Edge function failed: ${response.status}`);
  }

  return {
    status: "triggered",
    message: `Mirror sync ${args.mode} triggered via Edge Function`,
  };
}

// Export all odoo tools
export const tools: McpTool[] = [
  {
    name: "odoo.nav_health",
    description: "Check Odoo health: login, key menus, minimal record presence.",
    inputSchema: navHealthSchema,
    execute: executeNavHealth,
  },
  {
    name: "odoo.search_records",
    description: "Generic XML-RPC search for any Odoo model. Use sparingly; prefer odoo_mirror via supabase.*",
    inputSchema: searchRecordsSchema,
    execute: executeSearchRecords,
  },
  {
    name: "odoo.trigger_mirror_sync",
    description: "Kick off Odoo -> Supabase mirror flow via n8n or Edge Function.",
    inputSchema: triggerMirrorSyncSchema,
    execute: executeTriggerMirrorSync,
  },
];
