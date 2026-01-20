# MemoryAgent - SKILL Definition

**Agent ID**: agent_007
**Version**: 1.0.0
**Status**: Active
**Dependencies**: None (operates as cross-agent service)

## Purpose

Manage repository-scoped verified memory for cross-agent knowledge sharing. Enables agents to learn durable conventions with future impact and share them across sessions. Implements GitHub Copilot's verified memory pattern with just-in-time citation verification.

## Core Principle

**Memories are hypotheses, not truth.** Every memory MUST be verified before use by reading cited code locations. Invalid or contradicting citations trigger correction or invalidation.

## Scope & Boundaries

### CAN DO

**Memory Storage**
- [x] Store new memories with subject, fact, citations, and reason
- [x] Update/refresh existing memories when verified valid
- [x] Supersede memories with corrected versions (maintain chain)
- [x] Invalidate memories when citations contradict

**Memory Retrieval**
- [x] Get recent memories for a repository (recency-based)
- [x] Search memories by cited file path
- [x] Get memory statistics per repository
- [x] Format memories for prompt injection

**Citation Verification**
- [x] Read code at citation locations via GitHub API
- [x] Verify all citations for a memory
- [x] Detect missing or moved files
- [x] Compare current code against memory expectations

**Telemetry**
- [x] Log memory created/retrieved/applied events
- [x] Track verification success/failure rates
- [x] Record memory usage for impact measurement

### CANNOT DO (Hard Boundaries)

**NO Autonomous Memory Creation**
- [ ] Cannot create memories without agent discovery
- [ ] Cannot store memories without citations
- [ ] Memories must come from agent learning

**NO Truth Assertion**
- [ ] Cannot skip citation verification
- [ ] Cannot use memories without verification
- [ ] Cannot override contradicted memories

**NO Direct Code Modification**
- [ ] Cannot write or modify code files
- [ ] Can only read for verification
- [ ] Code changes delegated to other agents

**NO Execution**
- [ ] Cannot execute code or commands
- [ ] Cannot deploy or run tests
- [ ] Read-only access to codebase

## Input Interface

### Store Memory

```typescript
interface StoreMemoryInput {
  repo: string;             // "owner/name" format
  subject: string;          // Brief topic (e.g., "API version synchronization")
  fact: string;             // The learned convention or invariant
  citations: Citation[];    // Code locations supporting this memory
  reason?: string;          // Why this matters (prevents what problem)
  created_by?: string;      // Agent/user ID
}

interface Citation {
  path: string;             // File path relative to repo root
  line_start: number;       // Starting line (1-indexed)
  line_end: number;         // Ending line (1-indexed)
  sha?: string;             // Git SHA for version pinning
  snippet_hash?: string;    // Hash of context for fuzzy matching
}
```

### Get Recent Memories

```typescript
interface GetRecentMemoriesInput {
  repo: string;             // Repository identifier
  limit?: number;           // Max memories (default: 50)
}
```

### Verify Citations

```typescript
interface VerifyCitationsInput {
  repo: string;             // "owner/name" format
  citations: Citation[];    // Citations to verify
  ref?: string;             // Git ref (default: HEAD)
}
```

## Output Interface

### Memory Record

```typescript
interface MemoryRecord {
  id: string;               // UUID
  repo: string;
  subject: string;
  fact: string;
  citations: Citation[];
  reason: string | null;
  refreshed_at: string;     // ISO8601
  verification_count: number;
}
```

### Verification Result

```typescript
interface VerificationResult {
  valid: boolean;           // All citations valid?
  citations: {
    path: string;
    line_start: number;
    line_end: number;
    exists: boolean;
    content?: string;       // Actual code at location
    error?: string;
  }[];
  valid_count: number;
  invalid_count: number;
}
```

## Memory Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    Memory Lifecycle                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Agent discovers convention → store_memory()                    │
│           │                                                     │
│           ▼                                                     │
│     ┌───────────┐                                               │
│     │  ACTIVE   │ ◄─── refresh_memory() when verified valid     │
│     └─────┬─────┘                                               │
│           │                                                     │
│     (verification fails)                                        │
│           │                                                     │
│     ┌─────┴─────┐                                               │
│     ▼           ▼                                               │
│ ┌────────┐  ┌────────────┐                                      │
│ │INVALID │  │ SUPERSEDED │ ◄─── supersede_memory() with fix     │
│ └────────┘  └──────┬─────┘                                      │
│                    │                                            │
│                    ▼                                            │
│              ┌───────────┐                                      │
│              │ NEW ACTIVE│ (corrected memory)                   │
│              └───────────┘                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Prompt Rules

Include these rules in any agent that uses verified memory:

```markdown
## MEMORY RULES

1. **Treat memories as hypotheses, not truth.**

2. **Before using ANY memory:**
   - Read EVERY cited code location using `memory.read_citation`
   - Verify the code still matches the memory's fact
   - If ANY citation is missing, outdated, or contradicts:
     - Do NOT use the memory
     - Either `memory.invalidate` or `memory.supersede` with correction

3. **If memory is valid and useful:**
   - Call `memory.refresh` to update timestamp
   - This keeps useful memories ranked higher

4. **When to store memories:**
   - Only store DURABLE conventions or invariants
   - Examples: sync rules, naming conventions, required multi-file edits
   - Do NOT store: temporary workarounds, TODOs, one-time fixes

5. **After applying a memory:**
   - Call `memory.log_applied` for telemetry
```

## MCP Tools

| Tool | Purpose |
|------|---------|
| `memory.store` | Store/refresh a memory with citations |
| `memory.get_recent` | Get recent active memories for repo |
| `memory.search_by_path` | Find memories citing a specific file |
| `memory.refresh` | Refresh timestamp after verification |
| `memory.invalidate` | Mark memory as invalid |
| `memory.supersede` | Replace with corrected version |
| `memory.log_applied` | Log memory usage for telemetry |
| `memory.read_citation` | Read code at citation location |
| `memory.verify_citations` | Verify all citations at once |
| `memory.stats` | Get aggregate statistics |

## Example: Memory Storage

```typescript
// Agent discovers: API version must stay synced across files
await memory.store({
  repo: "myorg/myapp",
  subject: "API version synchronization",
  fact: "API version must match between client SDK, server routes, and documentation.",
  citations: [
    { path: "src/client/sdk/constants.ts", line_start: 12, line_end: 12 },
    { path: "server/routes/api.go", line_start: 8, line_end: 8 },
    { path: "docs/api-reference.md", line_start: 37, line_end: 37 }
  ],
  reason: "Prevents subtle integration breakages when version is updated.",
  created_by: "coding-agent"
});
```

## Example: Memory Verification

```typescript
// At session start, inject recent memories
const memories = await memory.get_recent({ repo: "myorg/myapp", limit: 20 });

// Before using each memory, verify it
for (const mem of memories) {
  const result = await memory.verify_citations({
    repo: "myorg/myapp",
    citations: mem.citations
  });

  if (result.valid) {
    // Memory is good - refresh and use it
    await memory.refresh({ memory_id: mem.id });
    // ... apply the memory's fact
    await memory.log_applied({ memory_id: mem.id });
  } else {
    // Memory is stale or incorrect
    await memory.invalidate({
      memory_id: mem.id,
      reason: `Invalid citations: ${result.invalid_count} missing`
    });
  }
}
```

## Resilience: Adversarial Memory Handling

The verification loop provides natural protection against incorrect or malicious memories:

| Threat | Mitigation |
|--------|------------|
| Stale memory (code moved) | Verification fails, memory invalidated |
| Incorrect fact | Code at citation contradicts, memory invalidated |
| Malicious injection | Citations point to nothing, immediate invalidation |
| Abandoned branch noise | Status + supersedes chains filter old memories |

## Performance Constraints

| Metric | Constraint |
|--------|------------|
| Memory retrieval | <100ms for 50 memories |
| Citation verification | <500ms per citation |
| Store memory | <200ms |
| Memory count per repo | Soft limit 1000 active |

## Telemetry Events

| Event | Description |
|-------|-------------|
| `created` | Memory was stored |
| `retrieved` | Memory was fetched for potential use |
| `verified_valid` | Memory citations verified successfully |
| `verified_invalid` | Memory citations failed verification |
| `corrected` | Memory was superseded with correction |
| `refreshed` | Memory timestamp updated (still useful) |
| `superseded` | Memory replaced by better version |
| `applied` | Memory was actually used in a task |

## Measured Impact (Reference: Copilot)

Based on GitHub Copilot's reported results:
- Code review: +3% precision, +4% recall
- Coding agent: +7% PR merge rate (90% vs 83%)
- Code review feedback: +2% positive feedback (77% vs 75%)

## Integration Points

- **Supabase**: `agent_memory` and `agent_memory_telemetry` tables
- **GitHub API**: Citation verification via contents API
- **MCP Server**: `memory.*` tool namespace
- **Agent Framework**: `VerifiedMemoryProvider` in Python

## Success Criteria

| Criteria | Target |
|----------|--------|
| Citation verification before use | 100% |
| Invalid memory detection rate | >95% |
| Memory refresh on valid use | 100% |
| Telemetry logging | 100% |
| False positive memory rate | <5% |
