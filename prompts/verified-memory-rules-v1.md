# Verified Memory System - Agent Prompt Rules v1

## Overview

This document defines the behavioral rules for agents using the verified memory system. These rules should be included in any agent system prompt that has access to repository memories.

Copy the relevant sections into your agent's system prompt based on which capabilities it needs.

## Core Principle

> **Memories are hypotheses, not truth.**
>
> Every memory MUST be verified before use. Citations are the evidence - if the evidence doesn't match, the memory is invalid.

## Session Start: Memory Injection

At the start of each session, inject recent memories into the agent context:

```markdown
## Repository Memories

The following are learned conventions for this repository. You MUST verify each memory before using it.

### Memory 1: {subject}
**Fact:** {fact}
**Why:** {reason}
**Citations:**
  - `{path}` (lines {line_start}-{line_end})
**ID:** `{memory_id}`

[... more memories ...]
```

## Verification-Before-Use Protocol

**MANDATORY RULE: Before applying ANY memory to your work, you MUST:**

1. **Read every cited location** using `memory.read_citation` tool
2. **Compare the code** against the memory's fact
3. **Decide action** based on verification result:

| Verification Result | Action |
|---------------------|--------|
| All citations valid, fact matches | `memory.refresh` then use it |
| Some citations missing/moved | `memory.supersede` with updated citations |
| Code contradicts the fact | `memory.invalidate` with reason |
| File deleted entirely | `memory.invalidate` with "file removed" |

## Full Memory Rules Block

Copy this entire block into agent system prompts:

```markdown
## MEMORY RULES

You have access to repository memories - learned conventions from previous sessions.

### Rule 1: Verify Before Use
For each memory you might use:
1. Read EVERY cited code location with `memory.read_citation`
2. Check if the code still supports the memory's fact
3. Do NOT use unverified memories

### Rule 2: Handle Invalid Memories
If ANY citation is missing, outdated, or contradicts:
- Do NOT apply the memory
- Call `memory.invalidate` with explanation
- OR call `memory.supersede` with corrected fact/citations

### Rule 3: Refresh Valid Memories
If memory is verified and useful:
- Call `memory.refresh` to update timestamp
- Then apply the memory to your work
- Call `memory.log_applied` for telemetry

### Rule 4: Store New Memories Sparingly
Only store memories that are:
- **Durable**: Will remain true across many changes
- **Convention**: Represents a pattern or rule, not a fact about a single file
- **Impactful**: Violating it would cause problems

Good memory examples:
- "API version must match in client, server, and docs"
- "All database migrations must have a rollback script"
- "Test files must use the _test.py suffix"

Bad memory examples (don't store):
- "The login function is on line 42" (too specific, will drift)
- "Fixed bug in payment module" (one-time fix, not convention)
- "User requested dark mode" (preference, not code convention)

### Rule 5: Include Citations
Every stored memory MUST have at least one citation:
- Cite the specific file and line range
- Multiple citations strengthen the memory
- Citations enable verification
```

## MCP Tool Reference

Include this reference section for agents that need tool usage examples:

```markdown
## Memory Tools

### Reading Memories
```typescript
// Get recent memories at session start
memory.get_recent({ repo: "owner/name", limit: 20 })

// Search for memories about a file you're modifying
memory.search_by_path({ repo: "owner/name", path: "src/api/routes.ts" })
```

### Verification
```typescript
// Read code at a citation to verify
memory.read_citation({
  repo: "owner/name",
  path: "src/config.ts",
  line_start: 10,
  line_end: 15,
  ref: "HEAD"
})

// Verify all citations at once
memory.verify_citations({
  repo: "owner/name",
  citations: [...],
  ref: "HEAD"
})
```

### Memory Lifecycle
```typescript
// Refresh valid memory (updates timestamp)
memory.refresh({ memory_id: "uuid" })

// Invalidate incorrect memory
memory.invalidate({
  memory_id: "uuid",
  reason: "File was deleted"
})

// Correct a memory
memory.supersede({
  old_memory_id: "uuid",
  new_fact: "Updated convention...",
  new_citations: [...]
})

// Log when you use a memory
memory.log_applied({ memory_id: "uuid" })
```

### Storing New Memories
```typescript
memory.store({
  repo: "owner/name",
  subject: "API versioning",
  fact: "Version constant must be updated in 3 files simultaneously",
  citations: [
    { path: "src/version.ts", line_start: 1, line_end: 1 },
    { path: "server/config.go", line_start: 8, line_end: 8 },
    { path: "docs/README.md", line_start: 3, line_end: 3 }
  ],
  reason: "Prevents client-server version mismatch"
})
```
```

## Failure Modes and Recovery

Include this for agents that need to handle edge cases:

```markdown
## Memory Failure Handling

### Network Failures
If citation verification fails due to network issues:
- Retry once with backoff
- If still failing, skip the memory (don't use unverified)
- Log the skip for debugging

### High Memory Volume
If repo has >100 memories:
- Process top 20 by recency
- Filter by relevance to current task
- Don't try to verify everything

### Conflicting Memories
If two memories contradict:
- The more recently refreshed memory wins
- Invalidate the older one
- Report the conflict in output
```

## Integration Examples

### Coding Agent Integration

```markdown
You are a coding agent with access to repository memories.

Before making any code changes:
1. Check `memory.search_by_path` for the files you'll modify
2. Verify any returned memories
3. Apply valid conventions to your changes
4. If you discover a new convention, store it

After completing a task:
1. If you learned a durable convention, call `memory.store`
2. Log any applied memories with `memory.log_applied`
```

### Code Review Agent Integration

```markdown
You are a code review agent with access to repository memories.

When reviewing a PR:
1. Get recent memories with `memory.get_recent`
2. Verify memories relevant to changed files
3. Check if PR violates any valid conventions
4. Flag convention violations in review comments
5. If PR establishes a new convention, suggest storing it
```

### CLI Agent Integration

```markdown
You are a CLI agent with access to repository memories.

At session start:
1. Fetch and verify top 10 memories
2. Keep verified memories in context
3. Reference them when giving suggestions

When user asks about conventions:
1. Check memory search results
2. Verify before quoting
3. Acknowledge if memory was stale
```

## Telemetry Guidelines

For accurate impact measurement, ensure agents log these events:

| Event | When to Log | Tool |
|-------|-------------|------|
| `retrieved` | Memory fetched from DB | Automatic |
| `verified_valid` | Citations checked, all valid | After verification |
| `verified_invalid` | Citations checked, some invalid | After verification |
| `refreshed` | Valid memory timestamp updated | `memory.refresh` |
| `invalidated` | Memory marked invalid | `memory.invalidate` |
| `superseded` | Memory replaced with correction | `memory.supersede` |
| `applied` | Memory used in actual work | `memory.log_applied` |
| `created` | New memory stored | `memory.store` |

## Anti-Patterns to Avoid

1. **Blind Trust**: Using memories without verification
2. **Over-Storage**: Storing every observation as a memory
3. **Stale Citations**: Not updating citations when code moves
4. **Missing Reasons**: Storing facts without explaining why they matter
5. **Single Citations**: Only citing one location when multiple exist
6. **Skip Logging**: Not calling `log_applied` after using a memory

## Related Documents

- `agents/MemoryAgent.SKILL.md` - Full agent skill definition
- `supabase/migrations/20260116_verified_memory.sql` - Database schema
- `mcp-ipai-core/src/tools/memory.ts` - MCP tool implementations
