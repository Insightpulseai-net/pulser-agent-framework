-- GENERATED FILE - DO NOT EDIT MANUALLY
-- Source: docs-to-code-pipeline
-- Generated: 2026-01-01T00:00:00Z
-- Regenerate: Managed by repository template

-- Workbench Artifact Tables
-- Tracks artifact ingestion, routing, and processing

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS workbench;

-- Artifacts table - main registry
CREATE TABLE IF NOT EXISTS workbench.artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_type VARCHAR(50) NOT NULL,
    schema_version VARCHAR(10) NOT NULL DEFAULT 'v1',
    source VARCHAR(50) NOT NULL,
    content_sha256 VARCHAR(64) NOT NULL UNIQUE,
    intent VARCHAR(50) NOT NULL,
    target VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    routed_to VARCHAR(255),
    uri TEXT,
    metadata JSONB DEFAULT '{}',
    constraints JSONB DEFAULT '{}',
    files JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Index for idempotency check
CREATE INDEX IF NOT EXISTS idx_artifacts_content_sha256
    ON workbench.artifacts(content_sha256);

-- Index for filtering
CREATE INDEX IF NOT EXISTS idx_artifacts_type_intent
    ON workbench.artifacts(artifact_type, intent);

CREATE INDEX IF NOT EXISTS idx_artifacts_status
    ON workbench.artifacts(status);

CREATE INDEX IF NOT EXISTS idx_artifacts_created_at
    ON workbench.artifacts(created_at DESC);

-- Runs table - tracks pipeline executions
CREATE TABLE IF NOT EXISTS workbench.runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_type VARCHAR(50) NOT NULL,
    intent VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    config JSONB DEFAULT '{}',
    config_hash VARCHAR(64),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Index for run queries
CREATE INDEX IF NOT EXISTS idx_runs_type_status
    ON workbench.runs(run_type, status);

CREATE INDEX IF NOT EXISTS idx_runs_started_at
    ON workbench.runs(started_at DESC);

-- Artifact-Run link table
CREATE TABLE IF NOT EXISTS workbench.artifact_run_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID NOT NULL REFERENCES workbench.artifacts(id) ON DELETE CASCADE,
    run_id UUID NOT NULL REFERENCES workbench.runs(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'input', -- input, output, reference
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(artifact_id, run_id, role)
);

-- Index for link queries
CREATE INDEX IF NOT EXISTS idx_artifact_run_links_artifact
    ON workbench.artifact_run_links(artifact_id);

CREATE INDEX IF NOT EXISTS idx_artifact_run_links_run
    ON workbench.artifact_run_links(run_id);

-- Labels table (for triage and categorization)
CREATE TABLE IF NOT EXISTS workbench.labels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID NOT NULL REFERENCES workbench.artifacts(id) ON DELETE CASCADE,
    label_key VARCHAR(100) NOT NULL,
    label_value VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(artifact_id, label_key)
);

-- Index for label queries
CREATE INDEX IF NOT EXISTS idx_labels_artifact
    ON workbench.labels(artifact_id);

CREATE INDEX IF NOT EXISTS idx_labels_key_value
    ON workbench.labels(label_key, label_value);

-- Events table (audit log)
CREATE TABLE IF NOT EXISTS workbench.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    actor VARCHAR(100),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for event queries
CREATE INDEX IF NOT EXISTS idx_events_entity
    ON workbench.events(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_events_type
    ON workbench.events(event_type);

CREATE INDEX IF NOT EXISTS idx_events_created_at
    ON workbench.events(created_at DESC);

-- Update trigger for artifacts
CREATE OR REPLACE FUNCTION workbench.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_artifacts_updated_at ON workbench.artifacts;
CREATE TRIGGER trigger_artifacts_updated_at
    BEFORE UPDATE ON workbench.artifacts
    FOR EACH ROW
    EXECUTE FUNCTION workbench.update_updated_at();

-- Comments
COMMENT ON TABLE workbench.artifacts IS 'Registry of ingested artifacts with envelope metadata';
COMMENT ON TABLE workbench.runs IS 'Pipeline execution runs';
COMMENT ON TABLE workbench.artifact_run_links IS 'Links between artifacts and runs';
COMMENT ON TABLE workbench.labels IS 'Artifact labels for categorization';
COMMENT ON TABLE workbench.events IS 'Audit log of system events';
