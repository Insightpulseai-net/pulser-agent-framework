-- =============================================================================
-- 0002_rag_core.sql - RAG + OCR Foundry Core Schema
-- InsightPulseAI Platform
-- =============================================================================
--
-- This migration creates the multi-tenant RAG infrastructure:
-- - Document sources and extraction
-- - Chunked content with embeddings (pgvector)
-- - Query logging for evaluation
-- - RAGAS/human evaluation metrics
--

-- Ensure pgvector extension is available
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- RAG SOURCES (what & where)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.rag_sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    workspace_id    UUID REFERENCES public.workspaces(id) ON DELETE SET NULL,

    -- Source identification
    kind            TEXT NOT NULL,          -- 'upload', 'gdrive', 'web', 'email', 'odoo', 's3', 'notion'
    uri             TEXT NOT NULL,          -- original path / URL / object key
    display_name    TEXT,

    -- Content details
    content_type    TEXT,                   -- 'pdf', 'docx', 'html', 'ocr-image', 'markdown'
    file_size_bytes BIGINT,

    -- OCR configuration
    ocr_engine      TEXT,                   -- 'tesseract', 'paddle', 'azure', 'gvision', 'llamaparse'
    ocr_config      JSONB DEFAULT '{}'::jsonb,

    -- Processing status
    status          TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'processing', 'processed', 'error'
    error_message   TEXT,
    retry_count     INTEGER DEFAULT 0,

    -- Metadata
    meta            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- RAG DOCUMENTS (post-OCR, normalized)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.rag_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    source_id       UUID REFERENCES public.rag_sources(id) ON DELETE SET NULL,

    -- Document metadata
    title           TEXT,
    language        TEXT,
    page_count      INTEGER,
    word_count      INTEGER,

    -- De-duplication
    hash_sha256     TEXT,

    -- Full text (for full-text search fallback)
    full_text       TEXT,

    -- Processing metadata
    extraction_model TEXT,                  -- model used for extraction
    extraction_confidence FLOAT,

    -- Metadata
    meta            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- RAG CHUNKS (ready for embeddings)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.rag_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    document_id     UUID NOT NULL REFERENCES public.rag_documents(id) ON DELETE CASCADE,

    -- Chunk positioning
    chunk_index     INTEGER NOT NULL,
    section_path    TEXT,                   -- e.g. '1.Intro > 1.2.Scope'
    page_number     INTEGER,

    -- Content
    text            TEXT NOT NULL,
    token_count     INTEGER,

    -- Chunking metadata
    chunking_strategy TEXT,                 -- 'recursive', 'semantic', 'sentence', 'fixed'
    overlap_tokens  INTEGER,

    -- Metadata
    meta            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (document_id, chunk_index)
);

-- =============================================================================
-- RAG EMBEDDINGS (pgvector)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.rag_embeddings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    chunk_id        UUID NOT NULL REFERENCES public.rag_chunks(id) ON DELETE CASCADE,

    -- Embedding details
    model           TEXT NOT NULL,          -- 'text-embedding-3-large', 'nomic-embed-text', etc.
    dimensions      INTEGER NOT NULL,

    -- The embedding vector (1536 for OpenAI, 768 for many others)
    -- Using 1536 as default, can be changed per deployment
    embedding       VECTOR(1536),

    -- Metadata
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (chunk_id, model)
);

-- =============================================================================
-- RAG QUERIES (for logging and evaluation)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.rag_queries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    workspace_id    UUID REFERENCES public.workspaces(id) ON DELETE SET NULL,
    agent_id        UUID REFERENCES public.agents(id) ON DELETE SET NULL,

    -- User context
    user_id         TEXT,
    session_id      TEXT,

    -- Query
    query_text      TEXT NOT NULL,
    query_embedding VECTOR(1536),

    -- Retrieval configuration
    retrieval_config JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {k: 5, filter: {...}, rerank: true}

    -- Retrieved chunks (for evaluation)
    retrieved_chunks JSONB DEFAULT '[]'::jsonb,  -- [{chunk_id, score, text}]

    -- Response
    model           TEXT NOT NULL,
    response_text   TEXT,
    citations       JSONB DEFAULT '[]'::jsonb,  -- [{chunk_id, text, score}]

    -- Performance metrics
    latency_ms      INTEGER,
    retrieval_ms    INTEGER,
    generation_ms   INTEGER,

    -- Token usage
    token_usage     JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {prompt, completion, total}

    -- Status
    success         BOOLEAN,
    error_message   TEXT,

    -- Metadata
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- RAG EVALUATIONS (RAGAS / human labels)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.rag_evaluations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rag_query_id    UUID NOT NULL REFERENCES public.rag_queries(id) ON DELETE CASCADE,

    -- Evaluator
    evaluator       TEXT NOT NULL,          -- 'ragas', 'human', 'trulens', 'custom'
    evaluator_version TEXT,

    -- RAGAS-style metrics
    metrics         JSONB NOT NULL,         -- {faithfulness: 0.92, answer_relevance: 0.88, context_relevance: 0.85, ...}

    -- Human feedback
    human_rating    INTEGER,                -- 1-5 scale
    human_feedback  TEXT,

    -- Metadata
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- LLM REQUEST LOG (for cost tracking and debugging)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.llm_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,

    -- Request context
    agent_id        UUID REFERENCES public.agents(id) ON DELETE SET NULL,
    rag_query_id    UUID REFERENCES public.rag_queries(id) ON DELETE SET NULL,

    -- Provider and model
    provider        TEXT NOT NULL,          -- 'anthropic', 'openai', 'ollama', 'azure'
    model           TEXT NOT NULL,

    -- Request
    request_type    TEXT NOT NULL,          -- 'chat', 'completion', 'embedding', 'tool_call'
    messages        JSONB,
    prompt          TEXT,

    -- Response
    response        JSONB,
    response_text   TEXT,

    -- Tokens and cost
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    total_tokens    INTEGER,
    cost_usd        NUMERIC(10, 6),

    -- Performance
    latency_ms      INTEGER,

    -- Status
    success         BOOLEAN,
    error_message   TEXT,

    -- Metadata
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR RAG PERFORMANCE
-- =============================================================================

-- Source indexes
CREATE INDEX IF NOT EXISTS idx_rag_sources_tenant_status
    ON public.rag_sources(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_rag_sources_tenant_kind
    ON public.rag_sources(tenant_id, kind);

-- Document indexes
CREATE INDEX IF NOT EXISTS idx_rag_documents_tenant
    ON public.rag_documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_rag_documents_source
    ON public.rag_documents(source_id);
CREATE INDEX IF NOT EXISTS idx_rag_documents_hash
    ON public.rag_documents(hash_sha256);

-- Chunk indexes
CREATE INDEX IF NOT EXISTS idx_rag_chunks_tenant_doc
    ON public.rag_chunks(tenant_id, document_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_document
    ON public.rag_chunks(document_id);

-- Embedding indexes
CREATE INDEX IF NOT EXISTS idx_rag_embeddings_chunk
    ON public.rag_embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_rag_embeddings_model
    ON public.rag_embeddings(model);

-- Vector similarity search index (IVFFlat for large scale)
CREATE INDEX IF NOT EXISTS idx_rag_embeddings_vector
    ON public.rag_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Query indexes
CREATE INDEX IF NOT EXISTS idx_rag_queries_tenant_created
    ON public.rag_queries(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rag_queries_session
    ON public.rag_queries(session_id);

-- LLM request indexes
CREATE INDEX IF NOT EXISTS idx_llm_requests_tenant_created
    ON public.llm_requests(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_requests_provider_model
    ON public.llm_requests(provider, model);

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Function to search similar chunks by embedding
CREATE OR REPLACE FUNCTION search_similar_chunks(
    p_tenant_id UUID,
    p_query_embedding VECTOR(1536),
    p_model TEXT DEFAULT 'text-embedding-3-large',
    p_limit INTEGER DEFAULT 5,
    p_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    text TEXT,
    similarity FLOAT,
    meta JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id AS chunk_id,
        c.document_id,
        c.text,
        1 - (e.embedding <=> p_query_embedding) AS similarity,
        c.meta
    FROM public.rag_embeddings e
    JOIN public.rag_chunks c ON e.chunk_id = c.id
    WHERE e.tenant_id = p_tenant_id
      AND e.model = p_model
      AND 1 - (e.embedding <=> p_query_embedding) >= p_threshold
    ORDER BY e.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
