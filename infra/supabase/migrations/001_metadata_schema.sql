-- InsightPulseAI AI Workbench Metadata Schema
-- Migration 001: Core metadata tables for Workbench
-- Run: psql "$SUPABASE_URL" -f 001_metadata_schema.sql

BEGIN;

-- Create schema
CREATE SCHEMA IF NOT EXISTS ip_workbench;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for secure token generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- CORE ENTITIES
-- ============================================================

-- Domains (Finance, Retail, Creative, HR)
CREATE TABLE ip_workbench.domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    color TEXT, -- Hex color for UI
    icon TEXT, -- Material icon name
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_domains_name ON ip_workbench.domains(name);

-- Pipelines (logical ETL/ELT workflows)
CREATE TABLE ip_workbench.pipelines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    definition JSONB NOT NULL, -- React Flow nodes/edges
    schedule TEXT, -- Cron expression
    owner UUID REFERENCES auth.users(id),
    domain_id UUID REFERENCES ip_workbench.domains(id),
    enabled BOOLEAN DEFAULT TRUE,
    n8n_webhook_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_pipelines_name ON ip_workbench.pipelines(name);
CREATE INDEX idx_pipelines_owner ON ip_workbench.pipelines(owner);
CREATE INDEX idx_pipelines_domain ON ip_workbench.pipelines(domain_id);
CREATE INDEX idx_pipelines_enabled ON ip_workbench.pipelines(enabled);

-- Pipeline Steps (ordered transformation steps)
CREATE TABLE ip_workbench.pipeline_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_id UUID NOT NULL REFERENCES ip_workbench.pipelines(id) ON DELETE CASCADE,
    step_order INT NOT NULL,
    step_type TEXT NOT NULL, -- 'bronze', 'silver', 'gold', 'custom'
    step_name TEXT NOT NULL,
    sql TEXT, -- Transformation SQL
    config JSONB, -- Additional config (schedule, owner, etc.)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(pipeline_id, step_order)
);

CREATE INDEX idx_pipeline_steps_pipeline ON ip_workbench.pipeline_steps(pipeline_id);
CREATE INDEX idx_pipeline_steps_order ON ip_workbench.pipeline_steps(pipeline_id, step_order);

-- Jobs (scheduled executions)
CREATE TABLE ip_workbench.jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_id UUID NOT NULL REFERENCES ip_workbench.pipelines(id) ON DELETE CASCADE,
    schedule TEXT, -- Cron expression
    enabled BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_jobs_pipeline ON ip_workbench.jobs(pipeline_id);
CREATE INDEX idx_jobs_enabled ON ip_workbench.jobs(enabled);
CREATE INDEX idx_jobs_next_run ON ip_workbench.jobs(next_run_at);

-- Job Runs (execution history with logs)
CREATE TABLE ip_workbench.job_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES ip_workbench.jobs(id) ON DELETE CASCADE,
    pipeline_id UUID NOT NULL REFERENCES ip_workbench.pipelines(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    logs TEXT,
    rows_processed BIGINT,
    error_message TEXT,
    triggered_by UUID REFERENCES auth.users(id)
);

CREATE INDEX idx_job_runs_job ON ip_workbench.job_runs(job_id);
CREATE INDEX idx_job_runs_pipeline ON ip_workbench.job_runs(pipeline_id);
CREATE INDEX idx_job_runs_status ON ip_workbench.job_runs(status);
CREATE INDEX idx_job_runs_started ON ip_workbench.job_runs(started_at DESC);

-- ============================================================
-- CATALOG METADATA
-- ============================================================

-- Tables (catalog metadata)
CREATE TABLE ip_workbench.tables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_name TEXT NOT NULL, -- bronze, silver, gold, platinum
    table_name TEXT NOT NULL,
    description TEXT,
    owner UUID REFERENCES auth.users(id),
    domain_id UUID REFERENCES ip_workbench.domains(id),
    row_count BIGINT,
    size_bytes BIGINT,
    last_updated TIMESTAMP,
    dq_score NUMERIC(5, 2), -- 0-100
    slo_freshness_hours INT,
    slo_completeness_pct NUMERIC(5, 2),
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(schema_name, table_name)
);

CREATE INDEX idx_tables_schema ON ip_workbench.tables(schema_name);
CREATE INDEX idx_tables_name ON ip_workbench.tables(table_name);
CREATE INDEX idx_tables_owner ON ip_workbench.tables(owner);
CREATE INDEX idx_tables_domain ON ip_workbench.tables(domain_id);
CREATE INDEX idx_tables_dq_score ON ip_workbench.tables(dq_score);
CREATE INDEX idx_tables_tags ON ip_workbench.tables USING GIN(tags);

-- Table Metadata (column definitions)
CREATE TABLE ip_workbench.table_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_id UUID NOT NULL REFERENCES ip_workbench.tables(id) ON DELETE CASCADE,
    column_name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    is_nullable BOOLEAN NOT NULL DEFAULT TRUE,
    is_primary_key BOOLEAN DEFAULT FALSE,
    description TEXT,
    sample_values TEXT[], -- Up to 10 sample values
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(table_id, column_name)
);

CREATE INDEX idx_table_metadata_table ON ip_workbench.table_metadata(table_id);
CREATE INDEX idx_table_metadata_column ON ip_workbench.table_metadata(column_name);

-- ============================================================
-- DATA QUALITY
-- ============================================================

-- Tests (data quality test definitions)
CREATE TABLE ip_workbench.tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_id UUID NOT NULL REFERENCES ip_workbench.tables(id) ON DELETE CASCADE,
    test_name TEXT NOT NULL,
    test_type TEXT NOT NULL CHECK (test_type IN ('uniqueness', 'completeness', 'consistency', 'accuracy', 'timeliness', 'validity')),
    test_sql TEXT NOT NULL,
    threshold NUMERIC,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(table_id, test_name)
);

CREATE INDEX idx_tests_table ON ip_workbench.tests(table_id);
CREATE INDEX idx_tests_type ON ip_workbench.tests(test_type);
CREATE INDEX idx_tests_enabled ON ip_workbench.tests(enabled);

-- Test Runs (validation results)
CREATE TABLE ip_workbench.test_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_id UUID NOT NULL REFERENCES ip_workbench.tests(id) ON DELETE CASCADE,
    table_id UUID NOT NULL REFERENCES ip_workbench.tables(id) ON DELETE CASCADE,
    passed BOOLEAN NOT NULL,
    result_value NUMERIC,
    details JSONB,
    executed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_test_runs_test ON ip_workbench.test_runs(test_id);
CREATE INDEX idx_test_runs_table ON ip_workbench.test_runs(table_id);
CREATE INDEX idx_test_runs_passed ON ip_workbench.test_runs(passed);
CREATE INDEX idx_test_runs_executed ON ip_workbench.test_runs(executed_at DESC);

-- ============================================================
-- LINEAGE
-- ============================================================

-- Lineage Edges (source→target relationships)
CREATE TABLE ip_workbench.lineage_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_table_id UUID NOT NULL REFERENCES ip_workbench.tables(id) ON DELETE CASCADE,
    target_table_id UUID NOT NULL REFERENCES ip_workbench.tables(id) ON DELETE CASCADE,
    transformation_sql TEXT,
    pipeline_id UUID REFERENCES ip_workbench.pipelines(id) ON DELETE SET NULL,
    column_mappings JSONB, -- {source_col: target_col}
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_table_id, target_table_id)
);

CREATE INDEX idx_lineage_source ON ip_workbench.lineage_edges(source_table_id);
CREATE INDEX idx_lineage_target ON ip_workbench.lineage_edges(target_table_id);
CREATE INDEX idx_lineage_pipeline ON ip_workbench.lineage_edges(pipeline_id);

-- ============================================================
-- AI ASSIST
-- ============================================================

-- Agents (AI agent definitions)
CREATE TABLE ip_workbench.agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    tools JSONB NOT NULL, -- Array of tool names
    model TEXT NOT NULL DEFAULT 'claude-sonnet-4.5',
    system_prompt TEXT,
    temperature NUMERIC(3, 2) DEFAULT 0.7,
    max_tokens INT DEFAULT 4000,
    budget_usd NUMERIC(10, 2) DEFAULT 1.0,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agents_name ON ip_workbench.agents(name);
CREATE INDEX idx_agents_created_by ON ip_workbench.agents(created_by);

-- Agent Bindings (agents→gold tables)
CREATE TABLE ip_workbench.agent_bindings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES ip_workbench.agents(id) ON DELETE CASCADE,
    table_id UUID NOT NULL REFERENCES ip_workbench.tables(id) ON DELETE CASCADE,
    context JSONB, -- Additional context for agent
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(agent_id, table_id)
);

CREATE INDEX idx_agent_bindings_agent ON ip_workbench.agent_bindings(agent_id);
CREATE INDEX idx_agent_bindings_table ON ip_workbench.agent_bindings(table_id);

-- Agent Runs (execution history)
CREATE TABLE ip_workbench.agent_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES ip_workbench.agents(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    input_prompt TEXT NOT NULL,
    output TEXT,
    tokens_used INT,
    cost_usd NUMERIC(10, 4),
    model TEXT,
    trace_url TEXT, -- Langfuse trace link
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT,
    triggered_by UUID REFERENCES auth.users(id)
);

CREATE INDEX idx_agent_runs_agent ON ip_workbench.agent_runs(agent_id);
CREATE INDEX idx_agent_runs_status ON ip_workbench.agent_runs(status);
CREATE INDEX idx_agent_runs_started ON ip_workbench.agent_runs(started_at DESC);

-- LLM Requests (detailed token tracking)
CREATE TABLE ip_workbench.llm_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_run_id UUID REFERENCES ip_workbench.agent_runs(id) ON DELETE CASCADE,
    model TEXT NOT NULL,
    prompt_tokens INT NOT NULL,
    completion_tokens INT NOT NULL,
    cost_usd NUMERIC(10, 6) NOT NULL,
    latency_ms INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_llm_requests_agent_run ON ip_workbench.llm_requests(agent_run_id);
CREATE INDEX idx_llm_requests_model ON ip_workbench.llm_requests(model);
CREATE INDEX idx_llm_requests_created ON ip_workbench.llm_requests(created_at DESC);

-- ============================================================
-- SQL EDITOR
-- ============================================================

-- SQL Snippets (saved queries)
CREATE TABLE ip_workbench.sql_snippets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    sql TEXT NOT NULL,
    owner UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    tags TEXT[],
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sql_snippets_owner ON ip_workbench.sql_snippets(owner);
CREATE INDEX idx_sql_snippets_tags ON ip_workbench.sql_snippets USING GIN(tags);
CREATE INDEX idx_sql_snippets_public ON ip_workbench.sql_snippets(is_public);

-- Query History (execution log)
CREATE TABLE ip_workbench.query_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    sql TEXT NOT NULL,
    rows_returned INT,
    execution_time_ms INT,
    executed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_query_history_user ON ip_workbench.query_history(user_id);
CREATE INDEX idx_query_history_executed ON ip_workbench.query_history(executed_at DESC);

-- ============================================================
-- COST TRACKING
-- ============================================================

-- Cost Tracker (service-level costs)
CREATE TABLE ip_workbench.cost_tracker (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service TEXT NOT NULL CHECK (service IN ('llm', 'pipeline', 'storage', 'compute', 'network')),
    resource_id UUID, -- Foreign key to related entity
    cost_usd NUMERIC(10, 4) NOT NULL,
    metadata JSONB, -- Additional cost details
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cost_tracker_service ON ip_workbench.cost_tracker(service);
CREATE INDEX idx_cost_tracker_resource ON ip_workbench.cost_tracker(resource_id);
CREATE INDEX idx_cost_tracker_recorded ON ip_workbench.cost_tracker(recorded_at DESC);

-- ============================================================
-- AUDIT LOG
-- ============================================================

-- Activity Log (user actions)
CREATE TABLE ip_workbench.activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL, -- 'create_pipeline', 'run_query', 'deploy_agent', etc.
    resource_type TEXT NOT NULL,
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_activity_log_user ON ip_workbench.activity_log(user_id);
CREATE INDEX idx_activity_log_action ON ip_workbench.activity_log(action);
CREATE INDEX idx_activity_log_created ON ip_workbench.activity_log(created_at DESC);

COMMIT;

-- Seed initial data
INSERT INTO ip_workbench.domains (name, description, color, icon) VALUES
    ('Finance', 'Financial data and BIR compliance', '#10B981', 'account_balance'),
    ('Retail', 'Sales, inventory, and customer data', '#3B82F6', 'shopping_cart'),
    ('Creative', 'Marketing campaigns and content', '#8B5CF6', 'palette'),
    ('HR', 'Employee data and payroll', '#F59E0B', 'people')
ON CONFLICT (name) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Schema ip_workbench created successfully!';
    RAISE NOTICE 'Tables created: domains, pipelines, pipeline_steps, jobs, job_runs, tables, table_metadata, tests, test_runs, lineage_edges, agents, agent_bindings, agent_runs, llm_requests, sql_snippets, query_history, cost_tracker, activity_log';
END $$;
