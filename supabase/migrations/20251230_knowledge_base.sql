-- =============================================================================
-- Knowledge Base Schema for Docs2Code RAG + Skills Pipeline
-- =============================================================================
-- Enable pgvector extension
-- Run this in Supabase SQL Editor or via migration
-- =============================================================================

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- Source documents (1 row per file version)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.knowledge_docs (
  id BIGSERIAL PRIMARY KEY,
  repo TEXT NOT NULL,
  ref TEXT NOT NULL DEFAULT 'main',
  path TEXT NOT NULL,
  sha TEXT NOT NULL,
  url TEXT,
  license TEXT,
  lang TEXT,
  bytes INT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (repo, ref, path, sha)
);

COMMENT ON TABLE public.knowledge_docs IS 'Source documents from GitHub repos for RAG knowledge base';
COMMENT ON COLUMN public.knowledge_docs.repo IS 'Repository in owner/name format';
COMMENT ON COLUMN public.knowledge_docs.ref IS 'Git ref (branch/tag/commit)';
COMMENT ON COLUMN public.knowledge_docs.path IS 'File path relative to repo root';
COMMENT ON COLUMN public.knowledge_docs.sha IS 'SHA256 hash of file content';
COMMENT ON COLUMN public.knowledge_docs.lang IS 'Detected language (python, typescript, markdown, etc.)';

-- =============================================================================
-- Chunks (many rows per file)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.knowledge_chunks (
  id BIGSERIAL PRIMARY KEY,
  doc_id BIGINT NOT NULL REFERENCES public.knowledge_docs(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  content TEXT NOT NULL,
  content_tokens INT,
  embedding VECTOR(1536),  -- OpenAI text-embedding-3-small dimension
  meta JSONB NOT NULL DEFAULT '{}'::JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (doc_id, chunk_index)
);

COMMENT ON TABLE public.knowledge_chunks IS 'Token-chunked content with embeddings for semantic search';
COMMENT ON COLUMN public.knowledge_chunks.embedding IS 'Vector embedding (1536 dim for text-embedding-3-small)';
COMMENT ON COLUMN public.knowledge_chunks.meta IS 'Metadata: repo, ref, path, lang, url, etc.';

-- =============================================================================
-- Skills (generated from chunks)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.skills (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  category TEXT,
  tags TEXT[],
  content TEXT NOT NULL,  -- Full skill.md content
  source_chunks BIGINT[],  -- References to knowledge_chunks.id
  version TEXT NOT NULL DEFAULT '1.0.0',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.skills IS 'Generated skills from knowledge base chunks';

-- =============================================================================
-- Skill examples
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.skill_examples (
  id BIGSERIAL PRIMARY KEY,
  skill_id BIGINT NOT NULL REFERENCES public.skills(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  source_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- Docs2Code tracking (from earlier)
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS docs2code;

CREATE TABLE IF NOT EXISTS docs2code.sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  google_doc_id TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  last_synced_at TIMESTAMPTZ,
  revision_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS docs2code.generated_modules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id UUID REFERENCES docs2code.sources(id),
  module_name TEXT NOT NULL,
  framework TEXT NOT NULL,  -- 'odoo', 'fastapi', 'react'
  version TEXT NOT NULL,
  file_count INTEGER,
  github_path TEXT,
  github_commit_sha TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS docs2code.generation_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  module_id UUID REFERENCES docs2code.generated_modules(id),
  status TEXT NOT NULL,  -- 'started', 'completed', 'failed'
  message TEXT,
  duration_ms INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Indexes
-- =============================================================================

-- IVFFlat index for approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS knowledge_chunks_embedding_idx
  ON public.knowledge_chunks USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- B-tree indexes for filtering
CREATE INDEX IF NOT EXISTS knowledge_docs_repo_idx ON public.knowledge_docs(repo);
CREATE INDEX IF NOT EXISTS knowledge_docs_path_idx ON public.knowledge_docs(path);
CREATE INDEX IF NOT EXISTS knowledge_docs_lang_idx ON public.knowledge_docs(lang);
CREATE INDEX IF NOT EXISTS knowledge_chunks_doc_id_idx ON public.knowledge_chunks(doc_id);
CREATE INDEX IF NOT EXISTS skills_category_idx ON public.skills(category);
CREATE INDEX IF NOT EXISTS skills_tags_idx ON public.skills USING gin(tags);

-- =============================================================================
-- Row Level Security
-- =============================================================================

ALTER TABLE public.knowledge_docs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.skill_examples ENABLE ROW LEVEL SECURITY;
ALTER TABLE docs2code.sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE docs2code.generated_modules ENABLE ROW LEVEL SECURITY;
ALTER TABLE docs2code.generation_logs ENABLE ROW LEVEL SECURITY;

-- Policies: Allow authenticated read, service_role write
CREATE POLICY "Allow authenticated read knowledge_docs" ON public.knowledge_docs
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow service role all knowledge_docs" ON public.knowledge_docs
  FOR ALL TO service_role USING (true);

CREATE POLICY "Allow authenticated read knowledge_chunks" ON public.knowledge_chunks
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow service role all knowledge_chunks" ON public.knowledge_chunks
  FOR ALL TO service_role USING (true);

CREATE POLICY "Allow authenticated read skills" ON public.skills
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow service role all skills" ON public.skills
  FOR ALL TO service_role USING (true);

CREATE POLICY "Allow authenticated read skill_examples" ON public.skill_examples
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow service role all skill_examples" ON public.skill_examples
  FOR ALL TO service_role USING (true);

CREATE POLICY "Allow authenticated read docs2code.sources" ON docs2code.sources
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow service role all docs2code.sources" ON docs2code.sources
  FOR ALL TO service_role USING (true);

CREATE POLICY "Allow authenticated read docs2code.generated_modules" ON docs2code.generated_modules
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow service role all docs2code.generated_modules" ON docs2code.generated_modules
  FOR ALL TO service_role USING (true);

CREATE POLICY "Allow authenticated read docs2code.generation_logs" ON docs2code.generation_logs
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow service role all docs2code.generation_logs" ON docs2code.generation_logs
  FOR ALL TO service_role USING (true);

-- =============================================================================
-- Functions: Semantic Search
-- =============================================================================

-- Semantic search with optional repo filter
CREATE OR REPLACE FUNCTION public.knowledge_search(
  query_embedding VECTOR(1536),
  match_count INT DEFAULT 20,
  repo_filter TEXT DEFAULT NULL,
  lang_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
  score FLOAT,
  repo TEXT,
  ref TEXT,
  path TEXT,
  sha TEXT,
  chunk_index INT,
  content TEXT,
  meta JSONB
)
LANGUAGE sql STABLE
AS $$
  SELECT
    1 - (kc.embedding <=> query_embedding) AS score,
    kd.repo, kd.ref, kd.path, kd.sha,
    kc.chunk_index, kc.content, kc.meta
  FROM public.knowledge_chunks kc
  JOIN public.knowledge_docs kd ON kd.id = kc.doc_id
  WHERE (repo_filter IS NULL OR kd.repo = repo_filter)
    AND (lang_filter IS NULL OR kd.lang = lang_filter)
  ORDER BY kc.embedding <=> query_embedding
  LIMIT match_count;
$$;

COMMENT ON FUNCTION public.knowledge_search IS 'Semantic search over knowledge chunks with optional filters';

-- Hybrid search (semantic + keyword)
CREATE OR REPLACE FUNCTION public.knowledge_hybrid_search(
  query_embedding VECTOR(1536),
  query_text TEXT,
  match_count INT DEFAULT 20,
  repo_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
  score FLOAT,
  repo TEXT,
  ref TEXT,
  path TEXT,
  chunk_index INT,
  content TEXT,
  meta JSONB
)
LANGUAGE sql STABLE
AS $$
  WITH semantic AS (
    SELECT
      kc.id,
      1 - (kc.embedding <=> query_embedding) AS semantic_score
    FROM public.knowledge_chunks kc
    JOIN public.knowledge_docs kd ON kd.id = kc.doc_id
    WHERE (repo_filter IS NULL OR kd.repo = repo_filter)
    ORDER BY kc.embedding <=> query_embedding
    LIMIT match_count * 2
  ),
  keyword AS (
    SELECT
      kc.id,
      ts_rank(to_tsvector('english', kc.content), plainto_tsquery('english', query_text)) AS keyword_score
    FROM public.knowledge_chunks kc
    WHERE to_tsvector('english', kc.content) @@ plainto_tsquery('english', query_text)
    LIMIT match_count * 2
  ),
  combined AS (
    SELECT
      COALESCE(s.id, k.id) AS id,
      COALESCE(s.semantic_score, 0) * 0.7 + COALESCE(k.keyword_score, 0) * 0.3 AS combined_score
    FROM semantic s
    FULL OUTER JOIN keyword k ON s.id = k.id
  )
  SELECT
    c.combined_score AS score,
    kd.repo, kd.ref, kd.path,
    kc.chunk_index, kc.content, kc.meta
  FROM combined c
  JOIN public.knowledge_chunks kc ON kc.id = c.id
  JOIN public.knowledge_docs kd ON kd.id = kc.doc_id
  ORDER BY c.combined_score DESC
  LIMIT match_count;
$$;

-- Get similar chunks to a specific chunk (for skill building)
CREATE OR REPLACE FUNCTION public.similar_chunks(
  source_chunk_id BIGINT,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  score FLOAT,
  chunk_id BIGINT,
  repo TEXT,
  path TEXT,
  content TEXT
)
LANGUAGE sql STABLE
AS $$
  SELECT
    1 - (kc.embedding <=> source.embedding) AS score,
    kc.id AS chunk_id,
    kd.repo, kd.path, kc.content
  FROM public.knowledge_chunks kc
  JOIN public.knowledge_docs kd ON kd.id = kc.doc_id
  CROSS JOIN (
    SELECT embedding FROM public.knowledge_chunks WHERE id = source_chunk_id
  ) source
  WHERE kc.id != source_chunk_id
  ORDER BY kc.embedding <=> source.embedding
  LIMIT match_count;
$$;

-- =============================================================================
-- Trigger: Update timestamps
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER knowledge_docs_updated_at
  BEFORE UPDATE ON public.knowledge_docs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER skills_updated_at
  BEFORE UPDATE ON public.skills
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER docs2code_sources_updated_at
  BEFORE UPDATE ON docs2code.sources
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- =============================================================================
-- Enable Realtime (optional)
-- =============================================================================

-- Uncomment to enable realtime on these tables
-- ALTER PUBLICATION supabase_realtime ADD TABLE public.knowledge_docs;
-- ALTER PUBLICATION supabase_realtime ADD TABLE public.knowledge_chunks;
-- ALTER PUBLICATION supabase_realtime ADD TABLE public.skills;
-- ALTER PUBLICATION supabase_realtime ADD TABLE docs2code.generation_logs;

-- =============================================================================
-- Stats view
-- =============================================================================

CREATE OR REPLACE VIEW public.knowledge_stats AS
SELECT
  (SELECT COUNT(*) FROM public.knowledge_docs) AS total_docs,
  (SELECT COUNT(*) FROM public.knowledge_chunks) AS total_chunks,
  (SELECT COUNT(DISTINCT repo) FROM public.knowledge_docs) AS unique_repos,
  (SELECT COUNT(*) FROM public.skills) AS total_skills,
  (SELECT SUM(content_tokens) FROM public.knowledge_chunks) AS total_tokens,
  (SELECT array_agg(DISTINCT lang) FROM public.knowledge_docs) AS languages;

COMMENT ON VIEW public.knowledge_stats IS 'Quick stats for the knowledge base';
