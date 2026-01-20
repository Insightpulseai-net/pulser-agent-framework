-- =============================================================================
-- Verified Memory Schema for Cross-Agent Knowledge Sharing
-- =============================================================================
-- Inspired by GitHub Copilot's repository-scoped cross-agent memory system.
-- Stores memories with citations (code locations), verified just-in-time at use-time
-- instead of expensive offline memory curation pipelines.
--
-- Key behaviors:
-- - Memories are hypotheses, not truth - must be verified before use
-- - Citations link to specific code locations (path, line_start, line_end, sha)
-- - Verification detects contradictions and triggers correction/refresh
-- - Recency-based retrieval with status tracking (active/superseded/invalid)
-- =============================================================================

-- =============================================================================
-- Agent Memory Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Repository scope (e.g., "owner/name" or internal repo id)
    repo TEXT NOT NULL,

    -- Memory content (matching Copilot's structure)
    subject TEXT NOT NULL,              -- Brief topic/category (e.g., "API version synchronization")
    fact TEXT NOT NULL,                 -- The learned convention or invariant
    reason TEXT,                        -- Why this matters (prevents what problem)

    -- Citations: code locations that support this memory
    -- Structure: [{path, line_start, line_end, sha?, snippet_hash?}...]
    citations JSONB NOT NULL DEFAULT '[]'::JSONB,

    -- Provenance
    created_by TEXT,                    -- User/agent ID that created this memory
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- Updated when memory is verified and useful

    -- Memory lifecycle status
    -- active: Memory is current and can be used
    -- superseded: Memory has been replaced by a newer/corrected version
    -- invalid: Memory was verified and found to be incorrect
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'superseded', 'invalid')),

    -- Chain for correction tracking
    supersedes_id UUID REFERENCES public.agent_memory(id),
    superseded_by_id UUID REFERENCES public.agent_memory(id),

    -- Verification telemetry
    verification_count INT NOT NULL DEFAULT 0,
    last_verified_at TIMESTAMPTZ,
    last_verified_by TEXT,

    -- Multi-tenant isolation
    tenant_id TEXT NOT NULL DEFAULT 'default'
);

-- Prevent exact duplicate memories per repo
CREATE UNIQUE INDEX IF NOT EXISTS uq_agent_memory_repo_subject_fact
    ON public.agent_memory (repo, subject, fact)
    WHERE status = 'active';

-- Primary query pattern: most recent active memories for a repo
CREATE INDEX IF NOT EXISTS idx_agent_memory_repo_refreshed
    ON public.agent_memory (repo, refreshed_at DESC)
    WHERE status = 'active';

-- Citation search: find memories referencing specific paths
CREATE INDEX IF NOT EXISTS idx_agent_memory_citations_gin
    ON public.agent_memory USING GIN (citations jsonb_path_ops);

-- Status filtering
CREATE INDEX IF NOT EXISTS idx_agent_memory_status
    ON public.agent_memory (status);

-- Tenant isolation
CREATE INDEX IF NOT EXISTS idx_agent_memory_tenant
    ON public.agent_memory (tenant_id);

-- Supersession chain navigation
CREATE INDEX IF NOT EXISTS idx_agent_memory_supersedes
    ON public.agent_memory (supersedes_id)
    WHERE supersedes_id IS NOT NULL;

-- =============================================================================
-- Memory Telemetry Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.agent_memory_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL REFERENCES public.agent_memory(id) ON DELETE CASCADE,

    -- Event type
    event TEXT NOT NULL CHECK (event IN (
        'created',           -- Memory was created
        'retrieved',         -- Memory was fetched for potential use
        'verified_valid',    -- Memory was verified and found correct
        'verified_invalid',  -- Memory was verified and found incorrect
        'corrected',         -- Memory was corrected (new version created)
        'refreshed',         -- Memory timestamp was refreshed (still useful)
        'superseded',        -- Memory was replaced by a better version
        'applied'            -- Memory was actually used in a task
    )),

    -- Context
    agent_id TEXT,                      -- Which agent triggered this event
    session_id TEXT,                    -- Session/conversation context

    -- Verification details (for verification events)
    verification_result JSONB,          -- {valid_citations: [], invalid_citations: [], reason: ""}

    -- Timing
    duration_ms INT,                    -- How long the operation took

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Multi-tenant
    tenant_id TEXT NOT NULL DEFAULT 'default'
);

CREATE INDEX IF NOT EXISTS idx_memory_telemetry_memory_id
    ON public.agent_memory_telemetry (memory_id);

CREATE INDEX IF NOT EXISTS idx_memory_telemetry_event
    ON public.agent_memory_telemetry (event);

CREATE INDEX IF NOT EXISTS idx_memory_telemetry_created
    ON public.agent_memory_telemetry (created_at DESC);

-- =============================================================================
-- Row Level Security
-- =============================================================================

ALTER TABLE public.agent_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_memory_telemetry ENABLE ROW LEVEL SECURITY;

-- Tenant isolation policies
CREATE POLICY tenant_isolation_agent_memory ON public.agent_memory
    USING (tenant_id = current_setting('app.current_tenant', TRUE) OR tenant_id = 'default');

CREATE POLICY tenant_isolation_agent_memory_telemetry ON public.agent_memory_telemetry
    USING (tenant_id = current_setting('app.current_tenant', TRUE) OR tenant_id = 'default');

-- Service role policies for full access
CREATE POLICY service_role_agent_memory ON public.agent_memory
    FOR ALL TO service_role USING (true);

CREATE POLICY service_role_agent_memory_telemetry ON public.agent_memory_telemetry
    FOR ALL TO service_role USING (true);

-- =============================================================================
-- Functions: Store Memory
-- =============================================================================

CREATE OR REPLACE FUNCTION public.store_memory(
    p_repo TEXT,
    p_subject TEXT,
    p_fact TEXT,
    p_citations JSONB DEFAULT '[]'::JSONB,
    p_reason TEXT DEFAULT NULL,
    p_created_by TEXT DEFAULT NULL,
    p_tenant_id TEXT DEFAULT 'default'
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO public.agent_memory (
        repo, subject, fact, citations, reason, created_by, tenant_id
    )
    VALUES (
        p_repo, p_subject, p_fact, p_citations, p_reason, p_created_by, p_tenant_id
    )
    ON CONFLICT (repo, subject, fact) WHERE status = 'active'
    DO UPDATE SET
        refreshed_at = NOW(),
        citations = EXCLUDED.citations,
        reason = COALESCE(EXCLUDED.reason, public.agent_memory.reason)
    RETURNING id INTO v_id;

    -- Log telemetry
    INSERT INTO public.agent_memory_telemetry (memory_id, event, agent_id, tenant_id)
    VALUES (v_id, 'created', p_created_by, p_tenant_id);

    RETURN v_id;
END;
$$;

COMMENT ON FUNCTION public.store_memory IS 'Store or refresh a memory with citations. Returns memory ID.';

-- =============================================================================
-- Functions: Get Recent Memories
-- =============================================================================

CREATE OR REPLACE FUNCTION public.get_recent_memories(
    p_repo TEXT,
    p_limit INT DEFAULT 50,
    p_tenant_id TEXT DEFAULT 'default'
)
RETURNS TABLE (
    id UUID,
    subject TEXT,
    fact TEXT,
    citations JSONB,
    reason TEXT,
    refreshed_at TIMESTAMPTZ,
    verification_count INT
)
LANGUAGE sql STABLE
AS $$
    SELECT
        am.id,
        am.subject,
        am.fact,
        am.citations,
        am.reason,
        am.refreshed_at,
        am.verification_count
    FROM public.agent_memory am
    WHERE am.repo = p_repo
      AND am.status = 'active'
      AND (am.tenant_id = p_tenant_id OR am.tenant_id = 'default')
    ORDER BY am.refreshed_at DESC
    LIMIT p_limit;
$$;

COMMENT ON FUNCTION public.get_recent_memories IS 'Get most recent active memories for a repo, ordered by recency.';

-- =============================================================================
-- Functions: Search Memories by Citation Path
-- =============================================================================

CREATE OR REPLACE FUNCTION public.search_memories_by_path(
    p_repo TEXT,
    p_path TEXT,
    p_tenant_id TEXT DEFAULT 'default'
)
RETURNS TABLE (
    id UUID,
    subject TEXT,
    fact TEXT,
    citations JSONB,
    reason TEXT,
    refreshed_at TIMESTAMPTZ
)
LANGUAGE sql STABLE
AS $$
    SELECT
        am.id,
        am.subject,
        am.fact,
        am.citations,
        am.reason,
        am.refreshed_at
    FROM public.agent_memory am
    WHERE am.repo = p_repo
      AND am.status = 'active'
      AND (am.tenant_id = p_tenant_id OR am.tenant_id = 'default')
      AND am.citations @> jsonb_build_array(jsonb_build_object('path', p_path))
    ORDER BY am.refreshed_at DESC;
$$;

COMMENT ON FUNCTION public.search_memories_by_path IS 'Find memories that cite a specific file path.';

-- =============================================================================
-- Functions: Refresh Memory
-- =============================================================================

CREATE OR REPLACE FUNCTION public.refresh_memory(
    p_memory_id UUID,
    p_verified_by TEXT DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.agent_memory
    SET
        refreshed_at = NOW(),
        verification_count = verification_count + 1,
        last_verified_at = NOW(),
        last_verified_by = p_verified_by
    WHERE id = p_memory_id AND status = 'active';

    IF FOUND THEN
        -- Log telemetry
        INSERT INTO public.agent_memory_telemetry (memory_id, event, agent_id)
        VALUES (p_memory_id, 'refreshed', p_verified_by);
        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$;

COMMENT ON FUNCTION public.refresh_memory IS 'Refresh a memory timestamp after successful verification.';

-- =============================================================================
-- Functions: Invalidate Memory
-- =============================================================================

CREATE OR REPLACE FUNCTION public.invalidate_memory(
    p_memory_id UUID,
    p_reason TEXT DEFAULT NULL,
    p_invalidated_by TEXT DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.agent_memory
    SET
        status = 'invalid',
        last_verified_at = NOW(),
        last_verified_by = p_invalidated_by
    WHERE id = p_memory_id AND status = 'active';

    IF FOUND THEN
        -- Log telemetry
        INSERT INTO public.agent_memory_telemetry (
            memory_id, event, agent_id, verification_result
        )
        VALUES (
            p_memory_id,
            'verified_invalid',
            p_invalidated_by,
            jsonb_build_object('reason', p_reason)
        );
        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$;

COMMENT ON FUNCTION public.invalidate_memory IS 'Mark a memory as invalid after verification finds contradictions.';

-- =============================================================================
-- Functions: Supersede Memory (Correct with new version)
-- =============================================================================

CREATE OR REPLACE FUNCTION public.supersede_memory(
    p_old_memory_id UUID,
    p_new_fact TEXT,
    p_new_citations JSONB DEFAULT NULL,
    p_new_reason TEXT DEFAULT NULL,
    p_created_by TEXT DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_old_memory RECORD;
    v_new_id UUID;
BEGIN
    -- Get old memory details
    SELECT repo, subject, citations, reason, tenant_id
    INTO v_old_memory
    FROM public.agent_memory
    WHERE id = p_old_memory_id AND status = 'active';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Memory % not found or not active', p_old_memory_id;
    END IF;

    -- Create new corrected memory
    INSERT INTO public.agent_memory (
        repo, subject, fact, citations, reason, created_by, tenant_id, supersedes_id
    )
    VALUES (
        v_old_memory.repo,
        v_old_memory.subject,
        p_new_fact,
        COALESCE(p_new_citations, v_old_memory.citations),
        COALESCE(p_new_reason, v_old_memory.reason),
        p_created_by,
        v_old_memory.tenant_id,
        p_old_memory_id
    )
    RETURNING id INTO v_new_id;

    -- Mark old memory as superseded
    UPDATE public.agent_memory
    SET
        status = 'superseded',
        superseded_by_id = v_new_id
    WHERE id = p_old_memory_id;

    -- Log telemetry for both
    INSERT INTO public.agent_memory_telemetry (memory_id, event, agent_id)
    VALUES
        (p_old_memory_id, 'superseded', p_created_by),
        (v_new_id, 'corrected', p_created_by);

    RETURN v_new_id;
END;
$$;

COMMENT ON FUNCTION public.supersede_memory IS 'Replace an incorrect memory with a corrected version, maintaining chain.';

-- =============================================================================
-- Functions: Log Memory Applied
-- =============================================================================

CREATE OR REPLACE FUNCTION public.log_memory_applied(
    p_memory_id UUID,
    p_agent_id TEXT DEFAULT NULL,
    p_session_id TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO public.agent_memory_telemetry (memory_id, event, agent_id, session_id)
    VALUES (p_memory_id, 'applied', p_agent_id, p_session_id);
END;
$$;

COMMENT ON FUNCTION public.log_memory_applied IS 'Log when a memory is actually applied in a task.';

-- =============================================================================
-- View: Memory Stats
-- =============================================================================

CREATE OR REPLACE VIEW public.agent_memory_stats AS
SELECT
    repo,
    tenant_id,
    COUNT(*) FILTER (WHERE status = 'active') AS active_count,
    COUNT(*) FILTER (WHERE status = 'superseded') AS superseded_count,
    COUNT(*) FILTER (WHERE status = 'invalid') AS invalid_count,
    AVG(verification_count) FILTER (WHERE status = 'active') AS avg_verifications,
    MAX(refreshed_at) FILTER (WHERE status = 'active') AS last_refresh,
    MIN(created_at) AS first_memory,
    MAX(created_at) AS latest_memory
FROM public.agent_memory
GROUP BY repo, tenant_id;

COMMENT ON VIEW public.agent_memory_stats IS 'Aggregate statistics for agent memories per repo.';

-- =============================================================================
-- Comments
-- =============================================================================

COMMENT ON TABLE public.agent_memory IS 'Repository-scoped cross-agent memory with citation verification (Copilot-inspired)';
COMMENT ON TABLE public.agent_memory_telemetry IS 'Telemetry events for memory lifecycle tracking';

COMMENT ON COLUMN public.agent_memory.subject IS 'Brief topic/category of the memory';
COMMENT ON COLUMN public.agent_memory.fact IS 'The learned convention, invariant, or rule';
COMMENT ON COLUMN public.agent_memory.citations IS 'Code locations supporting this memory: [{path, line_start, line_end, sha?}]';
COMMENT ON COLUMN public.agent_memory.reason IS 'Why this memory matters (what problem it prevents)';
COMMENT ON COLUMN public.agent_memory.refreshed_at IS 'Updated when memory is verified and found useful';
COMMENT ON COLUMN public.agent_memory.status IS 'active=current, superseded=replaced, invalid=incorrect';
