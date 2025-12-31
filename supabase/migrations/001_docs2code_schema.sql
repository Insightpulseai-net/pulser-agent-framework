-- ==============================================================================
-- Docs2Code Automation Pipeline - Database Schema
-- ==============================================================================
--
-- PostgreSQL 16 + pgvector for semantic search
-- Row-Level Security for multi-tenant isolation
-- Medallion Architecture: Bronze → Silver → Gold
--
-- Usage:
--   psql -h $SUPABASE_HOST -U postgres -d postgres -f 001_docs2code_schema.sql
--
-- ==============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas for medallion architecture
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- ==============================================================================
-- BRONZE LAYER: Raw ingested documents
-- ==============================================================================

-- Raw documents as extracted from sources
CREATE TABLE IF NOT EXISTS bronze.docs_raw (
    id BIGSERIAL PRIMARY KEY,

    -- Source identification
    source_type TEXT NOT NULL CHECK (source_type IN (
        'sap_s4hana', 'microsoft_learn', 'odoo_core',
        'oca_modules', 'bir_regulatory', 'databricks_arch', 'figma_design'
    )),
    source_url TEXT NOT NULL,
    source_version TEXT,  -- e.g., 'odoo-18.0', 'bir-2024'

    -- Document content
    document_title TEXT,
    document_content TEXT,
    document_hash TEXT,  -- SHA256 for deduplication

    -- Extraction metadata
    extraction_id TEXT NOT NULL,  -- Groups related extractions
    extracted_at TIMESTAMPTZ DEFAULT NOW(),
    extraction_confidence DECIMAL(3,2) CHECK (extraction_confidence BETWEEN 0 AND 1),
    extraction_method TEXT,  -- 'web_scrape', 'github_api', 'pdf_ocr'

    -- Raw metadata
    raw_metadata JSONB DEFAULT '{}',

    -- Multi-tenant
    tenant_id TEXT DEFAULT 'default',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for bronze.docs_raw
CREATE INDEX IF NOT EXISTS idx_docs_raw_source ON bronze.docs_raw(source_type);
CREATE INDEX IF NOT EXISTS idx_docs_raw_extraction_id ON bronze.docs_raw(extraction_id);
CREATE INDEX IF NOT EXISTS idx_docs_raw_extracted_at ON bronze.docs_raw(extracted_at DESC);
CREATE INDEX IF NOT EXISTS idx_docs_raw_hash ON bronze.docs_raw(document_hash);
CREATE INDEX IF NOT EXISTS idx_docs_raw_tenant ON bronze.docs_raw(tenant_id);

-- ==============================================================================
-- SILVER LAYER: Processed and normalized chunks
-- ==============================================================================

-- Chunked and structured content
CREATE TABLE IF NOT EXISTS silver.docs_chunks (
    id BIGSERIAL PRIMARY KEY,
    docs_raw_id BIGINT NOT NULL REFERENCES bronze.docs_raw(id) ON DELETE CASCADE,

    -- Chunk positioning
    chunk_index INT NOT NULL,
    chunk_content TEXT NOT NULL,
    chunk_length INT GENERATED ALWAYS AS (length(chunk_content)) STORED,

    -- Semantic structure
    entity_type TEXT CHECK (entity_type IN (
        'workflow', 'table', 'rule', 'form', 'api_endpoint',
        'code_example', 'glossary', 'config'
    )),
    entity_name TEXT,
    entity_description TEXT,

    -- Relationships
    relationships JSONB DEFAULT '[]',  -- [{target_entity, relationship_type}]

    -- Code patterns extracted
    code_patterns JSONB DEFAULT '[]',  -- [{language, pseudocode, regulatory_refs}]

    -- Regulatory references
    regulatory_refs TEXT[] DEFAULT '{}',  -- ['BIR_1700', 'PFRS_16', ...]

    -- Quality flags
    is_valid BOOLEAN DEFAULT TRUE,
    validation_errors JSONB DEFAULT '[]',
    confidence DECIMAL(3,2) CHECK (confidence BETWEEN 0 AND 1),

    -- Multi-tenant
    tenant_id TEXT DEFAULT 'default',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(docs_raw_id, chunk_index)
);

-- Indexes for silver.docs_chunks
CREATE INDEX IF NOT EXISTS idx_docs_chunks_raw_id ON silver.docs_chunks(docs_raw_id);
CREATE INDEX IF NOT EXISTS idx_docs_chunks_entity_type ON silver.docs_chunks(entity_type);
CREATE INDEX IF NOT EXISTS idx_docs_chunks_regulatory ON silver.docs_chunks USING GIN(regulatory_refs);
CREATE INDEX IF NOT EXISTS idx_docs_chunks_tenant ON silver.docs_chunks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_docs_chunks_content_trgm ON silver.docs_chunks USING GIN(chunk_content gin_trgm_ops);

-- ==============================================================================
-- GOLD LAYER: Semantic embeddings for AI search
-- ==============================================================================

-- Vector embeddings for semantic search
CREATE TABLE IF NOT EXISTS gold.docs_embeddings (
    id BIGSERIAL PRIMARY KEY,
    docs_chunks_id BIGINT NOT NULL REFERENCES silver.docs_chunks(id) ON DELETE CASCADE,

    -- Embedding content
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536),  -- OpenAI ada-002 / Claude embeddings dimension
    embedding_model TEXT DEFAULT 'text-embedding-ada-002',

    -- Searchable metadata
    search_keywords TEXT[] DEFAULT '{}',
    entity_type TEXT,
    regulatory_tags TEXT[] DEFAULT '{}',

    -- Multi-tenant
    tenant_id TEXT DEFAULT 'default',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for gold.docs_embeddings
CREATE INDEX IF NOT EXISTS idx_docs_embeddings_chunk_id ON gold.docs_embeddings(docs_chunks_id);
CREATE INDEX IF NOT EXISTS idx_docs_embeddings_entity ON gold.docs_embeddings(entity_type);
CREATE INDEX IF NOT EXISTS idx_docs_embeddings_tenant ON gold.docs_embeddings(tenant_id);

-- IVFFlat index for vector similarity search (create after data exists)
-- CREATE INDEX idx_docs_embeddings_vector ON gold.docs_embeddings
--   USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ==============================================================================
-- COMPLIANCE RULES: Regulatory matrix
-- ==============================================================================

-- Philippine regulatory rules (BIR, PFRS, DOLE)
CREATE TABLE IF NOT EXISTS public.compliance_rules (
    id BIGSERIAL PRIMARY KEY,

    -- Regulation identification
    regulation_type TEXT NOT NULL CHECK (regulation_type IN (
        'BIR_FORM', 'PFRS_STANDARD', 'DOLE_RULE', 'SOX_CONTROL', 'CUSTOM'
    )),
    regulation_code TEXT NOT NULL,  -- 'BIR_1700', 'PFRS_16', etc.
    regulation_title TEXT NOT NULL,

    -- Description
    description TEXT,
    requirements JSONB DEFAULT '[]',  -- [{field_name, validation_rule, mandatory}]

    -- Validity period
    effective_date DATE,
    expiry_date DATE,
    version TEXT,

    -- Source reference
    source_url TEXT,
    source_document TEXT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(regulation_type, regulation_code, version)
);

-- Indexes for compliance_rules
CREATE INDEX IF NOT EXISTS idx_compliance_rules_type ON public.compliance_rules(regulation_type);
CREATE INDEX IF NOT EXISTS idx_compliance_rules_code ON public.compliance_rules(regulation_code);
CREATE INDEX IF NOT EXISTS idx_compliance_rules_active ON public.compliance_rules(is_active);

-- ==============================================================================
-- GENERATED ARTIFACTS: Code, migrations, tests
-- ==============================================================================

-- Generated code and artifacts
CREATE TABLE IF NOT EXISTS public.generated_artifacts (
    id BIGSERIAL PRIMARY KEY,

    -- Artifact identification
    artifact_type TEXT NOT NULL CHECK (artifact_type IN (
        'odoo_module', 'fastapi_route', 'sql_migration',
        'test_suite', 'react_component', 'documentation'
    )),
    artifact_name TEXT NOT NULL,
    artifact_version TEXT,

    -- Source traceability
    source_chunks BIGINT[] DEFAULT '{}',  -- References to silver.docs_chunks.id
    validation_id TEXT,  -- From ComplianceValidator
    generation_id TEXT,  -- From CodeGenerator

    -- Content
    code_content TEXT,
    code_language TEXT CHECK (code_language IN (
        'python', 'sql', 'xml', 'javascript', 'typescript', 'yaml', 'json'
    )),
    file_path TEXT,

    -- Quality metrics
    test_coverage DECIMAL(3,2) CHECK (test_coverage BETWEEN 0 AND 1),
    performance_p99_latency_ms INT,
    security_scan_passed BOOLEAN,
    lint_passed BOOLEAN,

    -- 80/15/5 rule tracking
    native_odoo_percent DECIMAL(5,2),
    oca_modules_percent DECIMAL(5,2),
    custom_code_percent DECIMAL(5,2),

    -- Multi-tenant
    tenant_id TEXT DEFAULT 'default',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for generated_artifacts
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON public.generated_artifacts(artifact_type);
CREATE INDEX IF NOT EXISTS idx_artifacts_validation_id ON public.generated_artifacts(validation_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_generation_id ON public.generated_artifacts(generation_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_tenant ON public.generated_artifacts(tenant_id);

-- ==============================================================================
-- PIPELINE LINEAGE: Full traceability
-- ==============================================================================

-- Track what generated what (doc → code → test → deploy)
CREATE TABLE IF NOT EXISTS public.pipeline_lineage (
    id BIGSERIAL PRIMARY KEY,

    -- Source
    source_type TEXT NOT NULL,  -- 'doc_raw', 'doc_chunk', 'compliance_rule', 'artifact'
    source_id TEXT NOT NULL,

    -- Target
    target_type TEXT NOT NULL,  -- 'doc_chunk', 'artifact', 'test', 'deployment'
    target_id TEXT NOT NULL,

    -- Transformation
    agent_name TEXT NOT NULL,  -- 'DocumentationParser', 'CodeGenerator', etc.
    transformation_type TEXT,  -- 'parsed', 'validated', 'generated', 'tested', 'deployed'

    -- Context
    metadata JSONB DEFAULT '{}',  -- Context, decisions, warnings

    -- Multi-tenant
    tenant_id TEXT DEFAULT 'default',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for pipeline_lineage
CREATE INDEX IF NOT EXISTS idx_lineage_source ON public.pipeline_lineage(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_lineage_target ON public.pipeline_lineage(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_lineage_agent ON public.pipeline_lineage(agent_name);
CREATE INDEX IF NOT EXISTS idx_lineage_tenant ON public.pipeline_lineage(tenant_id);

-- ==============================================================================
-- DEPLOYMENT LOG: Blue/green deployments
-- ==============================================================================

-- Deployment history with rollback capability
CREATE TABLE IF NOT EXISTS public.deployment_log (
    id BIGSERIAL PRIMARY KEY,

    -- Deployment identification
    deployment_id UUID NOT NULL DEFAULT uuid_generate_v4(),
    validation_run_id TEXT,  -- From ValidationAgent

    -- Strategy
    deployment_strategy TEXT CHECK (deployment_strategy IN (
        'blue_green', 'canary', 'rolling', 'recreate'
    )),
    platform TEXT CHECK (platform IN (
        'digitalocean', 'kubernetes', 'docker_compose', 'manual'
    )),

    -- Version tracking
    previous_version TEXT,
    new_version TEXT,
    artifact_ids BIGINT[] DEFAULT '{}',

    -- Status
    deployment_status TEXT CHECK (deployment_status IN (
        'pending', 'in_progress', 'success', 'failed', 'rolled_back', 'cancelled'
    )),

    -- Health checks
    health_checks JSONB DEFAULT '[]',  -- [{endpoint, status, response_time}]

    -- Error handling
    error_message TEXT,
    rollback_triggered BOOLEAN DEFAULT FALSE,
    rollback_reason TEXT,

    -- Performance
    duration_seconds INT,
    downtime_seconds INT,

    -- Multi-tenant
    tenant_id TEXT DEFAULT 'default',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Indexes for deployment_log
CREATE UNIQUE INDEX IF NOT EXISTS idx_deployment_id ON public.deployment_log(deployment_id);
CREATE INDEX IF NOT EXISTS idx_deployment_status ON public.deployment_log(deployment_status);
CREATE INDEX IF NOT EXISTS idx_deployment_tenant ON public.deployment_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_deployment_created ON public.deployment_log(created_at DESC);

-- ==============================================================================
-- AGENTBENCH DPO PAIRS: Continuous hardening
-- ==============================================================================

-- Failure → preference pairs for agent retraining
CREATE TABLE IF NOT EXISTS public.agentbench_dpo_pairs (
    id BIGSERIAL PRIMARY KEY,

    -- Agent identification
    agent_name TEXT NOT NULL,  -- Which agent failed?
    agent_version TEXT,

    -- Failure context
    failure_scenario TEXT NOT NULL,
    failure_source TEXT,  -- 'test', 'deployment', 'compliance', etc.

    -- Preference pair
    preferred_output TEXT NOT NULL,  -- Correct/better response
    dispreferred_output TEXT NOT NULL,  -- Wrong/failed response

    -- Ranking
    priority DECIMAL(3,2) CHECK (priority BETWEEN 0 AND 1),  -- 0.0-1.0

    -- Processing status
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    submission_id TEXT,  -- From agentbench API

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Multi-tenant
    tenant_id TEXT DEFAULT 'default',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for agentbench_dpo_pairs
CREATE INDEX IF NOT EXISTS idx_dpo_pairs_agent ON public.agentbench_dpo_pairs(agent_name);
CREATE INDEX IF NOT EXISTS idx_dpo_pairs_priority ON public.agentbench_dpo_pairs(priority DESC);
CREATE INDEX IF NOT EXISTS idx_dpo_pairs_processed ON public.agentbench_dpo_pairs(processed);
CREATE INDEX IF NOT EXISTS idx_dpo_pairs_tenant ON public.agentbench_dpo_pairs(tenant_id);

-- ==============================================================================
-- ROW-LEVEL SECURITY (Multi-tenant isolation)
-- ==============================================================================

-- Enable RLS on all tables
ALTER TABLE bronze.docs_raw ENABLE ROW LEVEL SECURITY;
ALTER TABLE silver.docs_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE gold.docs_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.compliance_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.generated_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pipeline_lineage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.deployment_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agentbench_dpo_pairs ENABLE ROW LEVEL SECURITY;

-- Tenant isolation policies
CREATE POLICY tenant_isolation_docs_raw ON bronze.docs_raw
    USING (tenant_id = current_setting('app.current_tenant', TRUE) OR tenant_id = 'default');

CREATE POLICY tenant_isolation_docs_chunks ON silver.docs_chunks
    USING (tenant_id = current_setting('app.current_tenant', TRUE) OR tenant_id = 'default');

CREATE POLICY tenant_isolation_docs_embeddings ON gold.docs_embeddings
    USING (tenant_id = current_setting('app.current_tenant', TRUE) OR tenant_id = 'default');

CREATE POLICY tenant_isolation_compliance ON public.compliance_rules
    USING (TRUE);  -- Compliance rules are shared across tenants

CREATE POLICY tenant_isolation_artifacts ON public.generated_artifacts
    USING (tenant_id = current_setting('app.current_tenant', TRUE) OR tenant_id = 'default');

CREATE POLICY tenant_isolation_lineage ON public.pipeline_lineage
    USING (tenant_id = current_setting('app.current_tenant', TRUE) OR tenant_id = 'default');

CREATE POLICY tenant_isolation_deployment ON public.deployment_log
    USING (tenant_id = current_setting('app.current_tenant', TRUE) OR tenant_id = 'default');

CREATE POLICY tenant_isolation_dpo ON public.agentbench_dpo_pairs
    USING (tenant_id = current_setting('app.current_tenant', TRUE) OR tenant_id = 'default');

-- ==============================================================================
-- MATERIALIZED VIEWS: Gold layer analytics
-- ==============================================================================

-- Compliance coverage matrix
CREATE MATERIALIZED VIEW IF NOT EXISTS gold.compliance_matrix AS
SELECT
    cr.regulation_code,
    cr.regulation_title,
    cr.regulation_type,
    COUNT(DISTINCT dc.id) AS covered_chunks,
    ARRAY_AGG(DISTINCT dc.entity_type) FILTER (WHERE dc.entity_type IS NOT NULL) AS entity_types,
    cr.is_active,
    cr.effective_date,
    cr.updated_at
FROM public.compliance_rules cr
LEFT JOIN silver.docs_chunks dc
    ON cr.regulation_code = ANY(dc.regulatory_refs)
WHERE cr.is_active = TRUE
GROUP BY cr.id, cr.regulation_code, cr.regulation_title, cr.regulation_type,
         cr.is_active, cr.effective_date, cr.updated_at
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_compliance_matrix_code
    ON gold.compliance_matrix(regulation_code);

-- Extraction summary
CREATE MATERIALIZED VIEW IF NOT EXISTS gold.extraction_summary AS
SELECT
    dr.extraction_id,
    dr.source_type,
    COUNT(DISTINCT dr.id) AS documents_count,
    COUNT(DISTINCT dc.id) AS chunks_count,
    COUNT(DISTINCT de.id) AS embeddings_count,
    AVG(dr.extraction_confidence) AS avg_confidence,
    MIN(dr.extracted_at) AS started_at,
    MAX(dr.extracted_at) AS completed_at,
    dr.tenant_id
FROM bronze.docs_raw dr
LEFT JOIN silver.docs_chunks dc ON dc.docs_raw_id = dr.id
LEFT JOIN gold.docs_embeddings de ON de.docs_chunks_id = dc.id
GROUP BY dr.extraction_id, dr.source_type, dr.tenant_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_extraction_summary_id
    ON gold.extraction_summary(extraction_id, source_type);

-- ==============================================================================
-- FUNCTIONS: Semantic search
-- ==============================================================================

-- Semantic search function using pgvector
CREATE OR REPLACE FUNCTION search_docs_semantic(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.75,
    match_count INT DEFAULT 10,
    p_tenant_id TEXT DEFAULT 'default'
)
RETURNS TABLE (
    chunk_id BIGINT,
    chunk_text TEXT,
    entity_type TEXT,
    regulatory_tags TEXT[],
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        de.docs_chunks_id,
        de.chunk_text,
        de.entity_type,
        de.regulatory_tags,
        1 - (de.embedding <=> query_embedding) AS similarity
    FROM gold.docs_embeddings de
    WHERE de.tenant_id = p_tenant_id OR de.tenant_id = 'default'
    AND 1 - (de.embedding <=> query_embedding) > match_threshold
    ORDER BY de.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ==============================================================================
-- FUNCTIONS: Update timestamps
-- ==============================================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add update triggers
CREATE TRIGGER trg_docs_raw_updated
    BEFORE UPDATE ON bronze.docs_raw
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_docs_chunks_updated
    BEFORE UPDATE ON silver.docs_chunks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_compliance_rules_updated
    BEFORE UPDATE ON public.compliance_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ==============================================================================
-- SEED DATA: BIR 2024 Tax Brackets
-- ==============================================================================

INSERT INTO public.compliance_rules (regulation_type, regulation_code, regulation_title, description, requirements, effective_date, version)
VALUES
    ('BIR_FORM', 'BIR_TAX_BRACKET_2024_1', 'Tax Bracket 0-250K', 'Annual income 0 to 250,000 PHP',
     '[{"min": 0, "max": 250000, "rate": 0, "fixed": 0}]'::jsonb, '2024-01-01', '2024'),
    ('BIR_FORM', 'BIR_TAX_BRACKET_2024_2', 'Tax Bracket 250K-400K', 'Annual income 250,001 to 400,000 PHP',
     '[{"min": 250001, "max": 400000, "rate": 0.15, "fixed": 0, "excess_over": 250000}]'::jsonb, '2024-01-01', '2024'),
    ('BIR_FORM', 'BIR_TAX_BRACKET_2024_3', 'Tax Bracket 400K-800K', 'Annual income 400,001 to 800,000 PHP',
     '[{"min": 400001, "max": 800000, "rate": 0.20, "fixed": 22500, "excess_over": 400000}]'::jsonb, '2024-01-01', '2024'),
    ('BIR_FORM', 'BIR_TAX_BRACKET_2024_4', 'Tax Bracket 800K-2M', 'Annual income 800,001 to 2,000,000 PHP',
     '[{"min": 800001, "max": 2000000, "rate": 0.25, "fixed": 102500, "excess_over": 800000}]'::jsonb, '2024-01-01', '2024'),
    ('BIR_FORM', 'BIR_TAX_BRACKET_2024_5', 'Tax Bracket 2M-8M', 'Annual income 2,000,001 to 8,000,000 PHP',
     '[{"min": 2000001, "max": 8000000, "rate": 0.30, "fixed": 402500, "excess_over": 2000000}]'::jsonb, '2024-01-01', '2024'),
    ('BIR_FORM', 'BIR_TAX_BRACKET_2024_6', 'Tax Bracket Over 8M', 'Annual income over 8,000,000 PHP',
     '[{"min": 8000001, "max": null, "rate": 0.35, "fixed": 2202500, "excess_over": 8000000}]'::jsonb, '2024-01-01', '2024')
ON CONFLICT (regulation_type, regulation_code, version) DO NOTHING;

-- Common BIR Forms
INSERT INTO public.compliance_rules (regulation_type, regulation_code, regulation_title, description, effective_date, version, source_url)
VALUES
    ('BIR_FORM', 'BIR_1700', 'Annual Income Tax Return', 'For individuals earning purely compensation income', '2024-01-01', '2024', 'https://www.bir.gov.ph/ebirforms'),
    ('BIR_FORM', 'BIR_1701', 'Annual Income Tax Return', 'For self-employed and mixed income earners', '2024-01-01', '2024', 'https://www.bir.gov.ph/ebirforms'),
    ('BIR_FORM', 'BIR_1601_C', 'Monthly Remittance Return', 'Creditable income taxes withheld', '2024-01-01', '2024', 'https://www.bir.gov.ph/ebirforms'),
    ('BIR_FORM', 'BIR_2550_Q', 'Quarterly VAT Return', 'Quarterly VAT declaration', '2024-01-01', '2024', 'https://www.bir.gov.ph/ebirforms'),
    ('BIR_FORM', 'BIR_2306', 'Certificate of Final Tax', 'Creditable withholding tax certificate', '2024-01-01', '2024', 'https://www.bir.gov.ph/ebirforms')
ON CONFLICT (regulation_type, regulation_code, version) DO NOTHING;

-- PFRS Standards
INSERT INTO public.compliance_rules (regulation_type, regulation_code, regulation_title, description, effective_date, version)
VALUES
    ('PFRS_STANDARD', 'PFRS_16', 'Leases', 'Right-of-use assets and lease liabilities recognition', '2019-01-01', '2019'),
    ('PFRS_STANDARD', 'PFRS_15', 'Revenue from Contracts', 'Five-step revenue recognition model', '2018-01-01', '2018'),
    ('PFRS_STANDARD', 'PAS_1', 'Financial Statement Presentation', 'General requirements for financial statements', '2005-01-01', '2005'),
    ('PFRS_STANDARD', 'PAS_12', 'Income Taxes', 'Deferred tax accounting requirements', '1996-01-01', '1996')
ON CONFLICT (regulation_type, regulation_code, version) DO NOTHING;

-- ==============================================================================
-- GRANTS: Application roles
-- ==============================================================================

-- Create application roles if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_readonly') THEN
        CREATE ROLE app_readonly;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_readwrite') THEN
        CREATE ROLE app_readwrite;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_admin') THEN
        CREATE ROLE app_admin;
    END IF;
END
$$;

-- Grant schema usage
GRANT USAGE ON SCHEMA bronze TO app_readonly, app_readwrite, app_admin;
GRANT USAGE ON SCHEMA silver TO app_readonly, app_readwrite, app_admin;
GRANT USAGE ON SCHEMA gold TO app_readonly, app_readwrite, app_admin;

-- Grant table permissions
GRANT SELECT ON ALL TABLES IN SCHEMA bronze TO app_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA silver TO app_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO app_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;

GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA bronze TO app_readwrite;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA silver TO app_readwrite;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA gold TO app_readwrite;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_readwrite;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA bronze TO app_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA silver TO app_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA gold TO app_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_admin;

-- Grant sequence usage
GRANT USAGE ON ALL SEQUENCES IN SCHEMA bronze TO app_readwrite, app_admin;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA silver TO app_readwrite, app_admin;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA gold TO app_readwrite, app_admin;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_readwrite, app_admin;

-- ==============================================================================
-- COMMENTS: Documentation
-- ==============================================================================

COMMENT ON SCHEMA bronze IS 'Docs2Code: Raw ingested data (immutable after write)';
COMMENT ON SCHEMA silver IS 'Docs2Code: Cleansed and normalized data';
COMMENT ON SCHEMA gold IS 'Docs2Code: Business-ready views and embeddings';

COMMENT ON TABLE bronze.docs_raw IS 'Raw documents extracted from SAP, Microsoft, Odoo, BIR, etc.';
COMMENT ON TABLE silver.docs_chunks IS 'Chunked and structured content with semantic metadata';
COMMENT ON TABLE gold.docs_embeddings IS 'Vector embeddings for semantic search (pgvector)';
COMMENT ON TABLE public.compliance_rules IS 'BIR, PFRS, DOLE regulatory rules matrix';
COMMENT ON TABLE public.generated_artifacts IS 'Generated Odoo modules, migrations, tests';
COMMENT ON TABLE public.pipeline_lineage IS 'Full traceability: doc → code → test → deploy';
COMMENT ON TABLE public.deployment_log IS 'Blue/green deployment history with rollback';
COMMENT ON TABLE public.agentbench_dpo_pairs IS 'Failure preference pairs for agent hardening';
