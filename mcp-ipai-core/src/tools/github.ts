/**
 * GitHub tools (github.*)
 * PRs, files, comments
 */

import { z } from "zod";
import type { McpTool, ToolContext } from "../types.js";

// Helper: Make GitHub API call
async function githubApi(
  ctx: ToolContext,
  method: string,
  endpoint: string,
  body?: unknown
): Promise<unknown> {
  if (!ctx.githubToken) {
    throw new Error("GitHub token not configured");
  }

  const response = await fetch(`https://api.github.com${endpoint}`, {
    method,
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${ctx.githubToken}`,
      "X-GitHub-Api-Version": "2022-11-28",
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`GitHub API error ${response.status}: ${errorText}`);
  }

  return response.json();
}

// 5.1 github.create_pr
const createPrSchema = z.object({
  owner: z.string().describe("Repository owner"),
  repo: z.string().describe("Repository name"),
  title: z.string().describe("PR title"),
  body: z.string().optional().describe("PR description"),
  head: z.string().describe("Feature branch"),
  base: z.string().default("main").describe("Target branch"),
  draft: z.boolean().default(false).describe("Create as draft PR"),
});

async function executeCreatePr(
  args: z.infer<typeof createPrSchema>,
  ctx: ToolContext
): Promise<unknown> {
  return githubApi(ctx, "POST", `/repos/${args.owner}/${args.repo}/pulls`, {
    title: args.title,
    body: args.body || "",
    head: args.head,
    base: args.base,
    draft: args.draft,
  });
}

// 5.2 github.comment_pr
const commentPrSchema = z.object({
  owner: z.string().describe("Repository owner"),
  repo: z.string().describe("Repository name"),
  pull_number: z.number().describe("PR number"),
  body: z.string().describe("Comment body (markdown)"),
});

async function executeCommentPr(
  args: z.infer<typeof commentPrSchema>,
  ctx: ToolContext
): Promise<unknown> {
  return githubApi(
    ctx,
    "POST",
    `/repos/${args.owner}/${args.repo}/issues/${args.pull_number}/comments`,
    { body: args.body }
  );
}

// 5.3 github.get_file
const getFileSchema = z.object({
  owner: z.string().describe("Repository owner"),
  repo: z.string().describe("Repository name"),
  path: z.string().describe("File path"),
  ref: z.string().optional().describe("Git ref (branch/tag/sha)"),
});

async function executeGetFile(
  args: z.infer<typeof getFileSchema>,
  ctx: ToolContext
): Promise<{ content: string; sha: string; size: number }> {
  const params = args.ref ? `?ref=${encodeURIComponent(args.ref)}` : "";
  const data = await githubApi(
    ctx,
    "GET",
    `/repos/${args.owner}/${args.repo}/contents/${args.path}${params}`
  ) as { content: string; sha: string; size: number; encoding: string };

  // Decode base64 content
  const content = data.encoding === "base64"
    ? Buffer.from(data.content, "base64").toString("utf-8")
    : data.content;

  return {
    content,
    sha: data.sha,
    size: data.size,
  };
}

// Additional: github.create_issue (useful for many agents)
const createIssueSchema = z.object({
  owner: z.string().describe("Repository owner"),
  repo: z.string().describe("Repository name"),
  title: z.string().describe("Issue title"),
  body: z.string().optional().describe("Issue body (markdown)"),
  labels: z.array(z.string()).optional().describe("Labels to apply"),
  assignees: z.array(z.string()).optional().describe("Assignees"),
});

async function executeCreateIssue(
  args: z.infer<typeof createIssueSchema>,
  ctx: ToolContext
): Promise<unknown> {
  return githubApi(ctx, "POST", `/repos/${args.owner}/${args.repo}/issues`, {
    title: args.title,
    body: args.body || "",
    labels: args.labels || [],
    assignees: args.assignees || [],
  });
}

export const tools: McpTool[] = [
  {
    name: "github.create_pr",
    description: "Create a GitHub pull request.",
    inputSchema: createPrSchema,
    execute: executeCreatePr,
  },
  {
    name: "github.comment_pr",
    description: "Add a comment to a GitHub PR (agents leave build notes).",
    inputSchema: commentPrSchema,
    execute: executeCommentPr,
  },
  {
    name: "github.get_file",
    description: "Read config/spec file from repo (DBML, YAML, Spec Kit).",
    inputSchema: getFileSchema,
    execute: executeGetFile,
  },
  {
    name: "github.create_issue",
    description: "Create a GitHub issue.",
    inputSchema: createIssueSchema,
    execute: executeCreateIssue,
  },
];
