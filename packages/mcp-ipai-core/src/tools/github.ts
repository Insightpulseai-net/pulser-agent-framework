/**
 * GitHub tools for IPAI MCP Server
 * Namespace: github.*
 */

import { getConfig } from '../config.js';
import {
  GitHubCreatePrSchema,
  GitHubCommentPrSchema,
  GitHubGetFileSchema,
  type GitHubCreatePr,
  type GitHubCommentPr,
  type GitHubGetFile,
  type ToolResult
} from '../types.js';

const GITHUB_API_BASE = 'https://api.github.com';

async function githubFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const config = getConfig();

  const response = await fetch(`${GITHUB_API_BASE}${path}`, {
    ...options,
    headers: {
      'Accept': 'application/vnd.github+json',
      'Authorization': `Bearer ${config.github.token}`,
      'X-GitHub-Api-Version': '2022-11-28',
      ...options.headers
    }
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`GitHub API error (${response.status}): ${error}`);
  }

  return response.json() as Promise<T>;
}

/**
 * github.create_pr - Create a pull request
 */
async function createPr(params: GitHubCreatePr): Promise<ToolResult<{
  number: number;
  html_url: string;
  state: string;
}>> {
  try {
    const pr = await githubFetch<{
      number: number;
      html_url: string;
      state: string;
    }>(`/repos/${params.owner}/${params.repo}/pulls`, {
      method: 'POST',
      body: JSON.stringify({
        title: params.title,
        body: params.body,
        head: params.head,
        base: params.base
      })
    });

    return {
      success: true,
      data: {
        number: pr.number,
        html_url: pr.html_url,
        state: pr.state
      }
    };
  } catch (err) {
    return {
      success: false,
      error: `Failed to create PR: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * github.comment_pr - Add a comment to a PR
 */
async function commentPr(params: GitHubCommentPr): Promise<ToolResult<{
  id: number;
  html_url: string;
}>> {
  try {
    const comment = await githubFetch<{
      id: number;
      html_url: string;
    }>(`/repos/${params.owner}/${params.repo}/issues/${params.pr_number}/comments`, {
      method: 'POST',
      body: JSON.stringify({
        body: params.body
      })
    });

    return {
      success: true,
      data: {
        id: comment.id,
        html_url: comment.html_url
      }
    };
  } catch (err) {
    return {
      success: false,
      error: `Failed to comment on PR: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * github.get_file - Get file content from a repository
 */
async function getFile(params: GitHubGetFile): Promise<ToolResult<{
  name: string;
  path: string;
  sha: string;
  content: string;
  encoding: string;
}>> {
  try {
    const ref = params.ref ? `?ref=${params.ref}` : '';
    const file = await githubFetch<{
      name: string;
      path: string;
      sha: string;
      content: string;
      encoding: string;
    }>(`/repos/${params.owner}/${params.repo}/contents/${params.path}${ref}`);

    // Decode base64 content if present
    let content = file.content;
    if (file.encoding === 'base64' && content) {
      content = Buffer.from(content, 'base64').toString('utf-8');
    }

    return {
      success: true,
      data: {
        name: file.name,
        path: file.path,
        sha: file.sha,
        content,
        encoding: file.encoding
      }
    };
  } catch (err) {
    return {
      success: false,
      error: `Failed to get file: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

/**
 * github.list_repos - List repositories for the authenticated user or org
 */
async function listRepos(params: { org?: string; type?: string; per_page?: number }): Promise<ToolResult<Array<{
  name: string;
  full_name: string;
  private: boolean;
  html_url: string;
  description: string | null;
}>>> {
  try {
    const config = getConfig();
    const org = params.org || config.github.defaultOwner;
    const perPage = params.per_page || 30;
    const type = params.type || 'all';

    const repos = await githubFetch<Array<{
      name: string;
      full_name: string;
      private: boolean;
      html_url: string;
      description: string | null;
    }>>(org
      ? `/orgs/${org}/repos?per_page=${perPage}&type=${type}`
      : `/user/repos?per_page=${perPage}&type=${type}`
    );

    return {
      success: true,
      data: repos.map(r => ({
        name: r.name,
        full_name: r.full_name,
        private: r.private,
        html_url: r.html_url,
        description: r.description
      }))
    };
  } catch (err) {
    return {
      success: false,
      error: `Failed to list repos: ${err instanceof Error ? err.message : String(err)}`
    };
  }
}

// Export tools array for aggregation
export const tools = [
  {
    name: 'github.create_pr',
    description: 'Create a pull request in a GitHub repository.',
    inputSchema: GitHubCreatePrSchema,
    execute: createPr
  },
  {
    name: 'github.comment_pr',
    description: 'Add a comment to a pull request. Useful for agents leaving build notes.',
    inputSchema: GitHubCommentPrSchema,
    execute: commentPr
  },
  {
    name: 'github.get_file',
    description: 'Get file content from a GitHub repository. Useful for reading config, specs, DBML, etc.',
    inputSchema: GitHubGetFileSchema,
    execute: getFile
  },
  {
    name: 'github.list_repos',
    description: 'List repositories for the authenticated user or organization.',
    inputSchema: {
      type: 'object',
      properties: {
        org: { type: 'string', description: 'Organization name (optional)' },
        type: { type: 'string', description: 'Repository type: all, public, private, forks, sources, member' },
        per_page: { type: 'number', description: 'Results per page (default 30)' }
      }
    },
    execute: listRepos
  }
];
