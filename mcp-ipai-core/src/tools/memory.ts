/**
 * Memory tools (memory.*)
 *
 * Repository-scoped cross-agent memory with citation verification.
 * Inspired by GitHub Copilot's verified memory system (Jan 2026).
 *
 * Key behaviors:
 * - Memories are hypotheses, not truth - must be verified before use
 * - Citations link to specific code locations
 * - Verification detects contradictions and triggers correction/refresh
 * - Recency-based retrieval with status tracking
 */

import { z } from "zod";
import { createClient } from "@supabase/supabase-js";
import type { McpTool, ToolContext } from "../types.js";

// Citation schema matching Copilot's structure
const CitationSchema = z.object({
  path: z.string().describe("File path relative to repo root"),
  line_start: z.number().describe("Starting line number (1-indexed)"),
  line_end: z.number().describe("Ending line number (1-indexed)"),
  sha: z.string().optional().describe("Git SHA for version pinning"),
  snippet_hash: z.string().optional().describe("Hash of surrounding context for fuzzy matching"),
});

export type Citation = z.infer<typeof CitationSchema>;

// Memory record schema
const MemoryRecordSchema = z.object({
  id: z.string().uuid(),
  subject: z.string(),
  fact: z.string(),
  citations: z.array(CitationSchema),
  reason: z.string().nullable(),
  refreshed_at: z.string(),
  verification_count: z.number(),
});

export type MemoryRecord = z.infer<typeof MemoryRecordSchema>;

// =============================================================================
// memory.store - Store a new memory with citations
// =============================================================================

const storeMemorySchema = z.object({
  repo: z.string().describe("Repository identifier (e.g., 'owner/name')"),
  subject: z.string().describe("Brief topic/category (e.g., 'API version synchronization')"),
  fact: z.string().describe("The learned convention, invariant, or rule"),
  citations: z.array(CitationSchema).describe("Code locations that support this memory"),
  reason: z.string().optional().describe("Why this matters (what problem it prevents)"),
  created_by: z.string().optional().describe("Agent or user ID creating this memory"),
});

async function executeStoreMemory(
  args: z.infer<typeof storeMemorySchema>,
  ctx: ToolContext
): Promise<{ id: string; status: "created" | "refreshed" }> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  const { data, error } = await supabase.rpc("store_memory", {
    p_repo: args.repo,
    p_subject: args.subject,
    p_fact: args.fact,
    p_citations: args.citations,
    p_reason: args.reason || null,
    p_created_by: args.created_by || null,
  });

  if (error) {
    throw new Error(`Failed to store memory: ${error.message}`);
  }

  return {
    id: data,
    status: "created",
  };
}

// =============================================================================
// memory.get_recent - Get recent memories for a repo
// =============================================================================

const getRecentMemoriesSchema = z.object({
  repo: z.string().describe("Repository identifier (e.g., 'owner/name')"),
  limit: z.number().default(50).describe("Maximum number of memories to return"),
});

async function executeGetRecentMemories(
  args: z.infer<typeof getRecentMemoriesSchema>,
  ctx: ToolContext
): Promise<MemoryRecord[]> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  const { data, error } = await supabase.rpc("get_recent_memories", {
    p_repo: args.repo,
    p_limit: args.limit,
  });

  if (error) {
    throw new Error(`Failed to get memories: ${error.message}`);
  }

  return (data || []) as MemoryRecord[];
}

// =============================================================================
// memory.search_by_path - Find memories citing a specific file
// =============================================================================

const searchByPathSchema = z.object({
  repo: z.string().describe("Repository identifier"),
  path: z.string().describe("File path to search for in citations"),
});

async function executeSearchByPath(
  args: z.infer<typeof searchByPathSchema>,
  ctx: ToolContext
): Promise<MemoryRecord[]> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  const { data, error } = await supabase.rpc("search_memories_by_path", {
    p_repo: args.repo,
    p_path: args.path,
  });

  if (error) {
    throw new Error(`Failed to search memories: ${error.message}`);
  }

  return (data || []) as MemoryRecord[];
}

// =============================================================================
// memory.refresh - Refresh a memory after successful verification
// =============================================================================

const refreshMemorySchema = z.object({
  memory_id: z.string().uuid().describe("ID of the memory to refresh"),
  verified_by: z.string().optional().describe("Agent or user ID verifying this memory"),
});

async function executeRefreshMemory(
  args: z.infer<typeof refreshMemorySchema>,
  ctx: ToolContext
): Promise<{ success: boolean }> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  const { data, error } = await supabase.rpc("refresh_memory", {
    p_memory_id: args.memory_id,
    p_verified_by: args.verified_by || null,
  });

  if (error) {
    throw new Error(`Failed to refresh memory: ${error.message}`);
  }

  return { success: data };
}

// =============================================================================
// memory.invalidate - Mark a memory as invalid
// =============================================================================

const invalidateMemorySchema = z.object({
  memory_id: z.string().uuid().describe("ID of the memory to invalidate"),
  reason: z.string().optional().describe("Why the memory is invalid"),
  invalidated_by: z.string().optional().describe("Agent or user ID invalidating this memory"),
});

async function executeInvalidateMemory(
  args: z.infer<typeof invalidateMemorySchema>,
  ctx: ToolContext
): Promise<{ success: boolean }> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  const { data, error } = await supabase.rpc("invalidate_memory", {
    p_memory_id: args.memory_id,
    p_reason: args.reason || null,
    p_invalidated_by: args.invalidated_by || null,
  });

  if (error) {
    throw new Error(`Failed to invalidate memory: ${error.message}`);
  }

  return { success: data };
}

// =============================================================================
// memory.supersede - Replace a memory with a corrected version
// =============================================================================

const supersedeMemorySchema = z.object({
  old_memory_id: z.string().uuid().describe("ID of the memory to supersede"),
  new_fact: z.string().describe("The corrected fact"),
  new_citations: z.array(CitationSchema).optional().describe("Updated citations (optional)"),
  new_reason: z.string().optional().describe("Updated reason (optional)"),
  created_by: z.string().optional().describe("Agent or user ID creating the correction"),
});

async function executeSupersedeMemory(
  args: z.infer<typeof supersedeMemorySchema>,
  ctx: ToolContext
): Promise<{ new_memory_id: string }> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  const { data, error } = await supabase.rpc("supersede_memory", {
    p_old_memory_id: args.old_memory_id,
    p_new_fact: args.new_fact,
    p_new_citations: args.new_citations || null,
    p_new_reason: args.new_reason || null,
    p_created_by: args.created_by || null,
  });

  if (error) {
    throw new Error(`Failed to supersede memory: ${error.message}`);
  }

  return { new_memory_id: data };
}

// =============================================================================
// memory.log_applied - Log when a memory is used
// =============================================================================

const logAppliedSchema = z.object({
  memory_id: z.string().uuid().describe("ID of the memory that was applied"),
  agent_id: z.string().optional().describe("Agent that applied the memory"),
  session_id: z.string().optional().describe("Session/conversation context"),
});

async function executeLogApplied(
  args: z.infer<typeof logAppliedSchema>,
  ctx: ToolContext
): Promise<{ logged: boolean }> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  const { error } = await supabase.rpc("log_memory_applied", {
    p_memory_id: args.memory_id,
    p_agent_id: args.agent_id || null,
    p_session_id: args.session_id || null,
  });

  if (error) {
    throw new Error(`Failed to log memory application: ${error.message}`);
  }

  return { logged: true };
}

// =============================================================================
// memory.read_citation - Read code at a citation location
// =============================================================================

const readCitationSchema = z.object({
  repo: z.string().describe("Repository in 'owner/name' format"),
  path: z.string().describe("File path relative to repo root"),
  line_start: z.number().describe("Starting line number (1-indexed)"),
  line_end: z.number().describe("Ending line number (1-indexed)"),
  ref: z.string().default("HEAD").describe("Git ref (branch, tag, or commit SHA)"),
});

interface CitationContent {
  path: string;
  line_start: number;
  line_end: number;
  content: string;
  sha: string;
  exists: boolean;
  error?: string;
}

async function executeReadCitation(
  args: z.infer<typeof readCitationSchema>,
  ctx: ToolContext
): Promise<CitationContent> {
  if (!ctx.githubToken) {
    throw new Error("GitHub token not configured. Set GITHUB_TOKEN environment variable.");
  }

  const [owner, repo] = args.repo.split("/");
  if (!owner || !repo) {
    throw new Error("Invalid repo format. Expected 'owner/name'");
  }

  try {
    // Fetch file content from GitHub API
    const response = await fetch(
      `https://api.github.com/repos/${owner}/${repo}/contents/${args.path}?ref=${args.ref}`,
      {
        headers: {
          Authorization: `Bearer ${ctx.githubToken}`,
          Accept: "application/vnd.github.v3+json",
          "X-GitHub-Api-Version": "2022-11-28",
        },
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return {
          path: args.path,
          line_start: args.line_start,
          line_end: args.line_end,
          content: "",
          sha: "",
          exists: false,
          error: "File not found",
        };
      }
      throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json() as { content: string; sha: string; encoding: string };

    // Decode base64 content
    const fullContent = Buffer.from(data.content, "base64").toString("utf-8");
    const lines = fullContent.split("\n");

    // Extract the specified line range (1-indexed)
    const startIdx = Math.max(0, args.line_start - 1);
    const endIdx = Math.min(lines.length, args.line_end);
    const selectedLines = lines.slice(startIdx, endIdx);

    return {
      path: args.path,
      line_start: args.line_start,
      line_end: args.line_end,
      content: selectedLines.join("\n"),
      sha: data.sha,
      exists: true,
    };
  } catch (error) {
    return {
      path: args.path,
      line_start: args.line_start,
      line_end: args.line_end,
      content: "",
      sha: "",
      exists: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

// =============================================================================
// memory.verify_citations - Verify all citations for a memory
// =============================================================================

const verifyCitationsSchema = z.object({
  repo: z.string().describe("Repository in 'owner/name' format"),
  citations: z.array(CitationSchema).describe("Citations to verify"),
  ref: z.string().default("HEAD").describe("Git ref to verify against"),
});

interface VerificationResult {
  valid: boolean;
  citations: Array<{
    path: string;
    line_start: number;
    line_end: number;
    exists: boolean;
    content?: string;
    error?: string;
  }>;
  valid_count: number;
  invalid_count: number;
}

async function executeVerifyCitations(
  args: z.infer<typeof verifyCitationsSchema>,
  ctx: ToolContext
): Promise<VerificationResult> {
  const results = await Promise.all(
    args.citations.map((citation) =>
      executeReadCitation(
        {
          repo: args.repo,
          path: citation.path,
          line_start: citation.line_start,
          line_end: citation.line_end,
          ref: args.ref,
        },
        ctx
      )
    )
  );

  const validCount = results.filter((r) => r.exists).length;
  const invalidCount = results.filter((r) => !r.exists).length;

  return {
    valid: invalidCount === 0,
    citations: results.map((r) => ({
      path: r.path,
      line_start: r.line_start,
      line_end: r.line_end,
      exists: r.exists,
      content: r.content || undefined,
      error: r.error,
    })),
    valid_count: validCount,
    invalid_count: invalidCount,
  };
}

// =============================================================================
// memory.stats - Get memory statistics for a repo
// =============================================================================

const getStatsSchema = z.object({
  repo: z.string().describe("Repository identifier"),
});

interface MemoryStats {
  repo: string;
  active_count: number;
  superseded_count: number;
  invalid_count: number;
  avg_verifications: number;
  last_refresh: string | null;
  first_memory: string | null;
  latest_memory: string | null;
}

async function executeGetStats(
  args: z.infer<typeof getStatsSchema>,
  ctx: ToolContext
): Promise<MemoryStats | null> {
  const supabase = createClient(ctx.supabaseUrl, ctx.supabaseServiceKey);

  const { data, error } = await supabase
    .from("agent_memory_stats")
    .select("*")
    .eq("repo", args.repo)
    .single();

  if (error) {
    if (error.code === "PGRST116") {
      // No rows found
      return null;
    }
    throw new Error(`Failed to get stats: ${error.message}`);
  }

  return data as MemoryStats;
}

// =============================================================================
// Export all memory tools
// =============================================================================

export const tools: McpTool[] = [
  {
    name: "memory.store",
    description:
      "Store a memory (learned convention/invariant) with citations. Use when discovering durable patterns with future impact.",
    inputSchema: storeMemorySchema,
    execute: executeStoreMemory,
  },
  {
    name: "memory.get_recent",
    description:
      "Get recent active memories for a repository, ordered by recency. Inject into agent context at session start.",
    inputSchema: getRecentMemoriesSchema,
    execute: executeGetRecentMemories,
  },
  {
    name: "memory.search_by_path",
    description:
      "Find memories that cite a specific file path. Useful when modifying a file to check for relevant conventions.",
    inputSchema: searchByPathSchema,
    execute: executeSearchByPath,
  },
  {
    name: "memory.refresh",
    description:
      "Refresh a memory timestamp after successful verification. Keeps useful memories at the top of recency ranking.",
    inputSchema: refreshMemorySchema,
    execute: executeRefreshMemory,
  },
  {
    name: "memory.invalidate",
    description:
      "Mark a memory as invalid after verification finds contradictions. Memory will no longer be returned in queries.",
    inputSchema: invalidateMemorySchema,
    execute: executeInvalidateMemory,
  },
  {
    name: "memory.supersede",
    description:
      "Replace an incorrect memory with a corrected version. Maintains chain for traceability.",
    inputSchema: supersedeMemorySchema,
    execute: executeSupersedeMemory,
  },
  {
    name: "memory.log_applied",
    description: "Log when a memory is actually used in a task. Used for telemetry and impact measurement.",
    inputSchema: logAppliedSchema,
    execute: executeLogApplied,
  },
  {
    name: "memory.read_citation",
    description:
      "Read code at a specific citation location (file + line range) from GitHub. Essential for just-in-time verification.",
    inputSchema: readCitationSchema,
    execute: executeReadCitation,
  },
  {
    name: "memory.verify_citations",
    description:
      "Verify all citations for a memory at once. Returns validity status and content for each citation.",
    inputSchema: verifyCitationsSchema,
    execute: executeVerifyCitations,
  },
  {
    name: "memory.stats",
    description: "Get aggregate statistics for memories in a repository (counts, verifications, etc.).",
    inputSchema: getStatsSchema,
    execute: executeGetStats,
  },
];
