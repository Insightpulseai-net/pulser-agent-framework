-- migrations/0001_init.sql
-- ============================================================================
-- InsightPulseAI - Multi-Tenant Agent Platform Schema
-- ============================================================================
--
-- COMMIT: Combined from:
--   - claude/create-engine-map-01Uf44ZeXKUg93ypUgB1ZHxD
--   - claude/data-engineering-workbench-01Pk6KXASta9H4oeCMY8EBAE
--
-- NOTE: This is just a STARTING POINT.
-- Adjust fields/types to fit your platform's exact requirements.
--
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- SCHEMA MIGRATIONS TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     TEXT PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- TENANTS (Organizations/Companies)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL UNIQUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tenants_slug ON tenants(slug);

-- ============================================================================
-- WORKSPACES (Projects within Tenants)
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL,
    config          JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, slug)
);

CREATE INDEX idx_workspaces_tenant ON workspaces(tenant_id);

-- ============================================================================
-- 0001_init.sql - Main Multi-Tenant Base Schema
-- InsightPulseAI Platform
-- ============================================================================
--
-- This migration creates the foundational tables for:
--   - Multi-tenant tenants (tenants, users, subscriptions)
--   - Workspace organization
--   - Agent registry
--
-- ============================================================================

-- SCHEMA
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- TENANTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.tenants (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT NOT NULL UNIQUE,
    plan_id             TEXT NOT NULL DEFAULT 'free',
    max_storage_per_user_kb BIGINT DEFAULT 104857600,
    max_users           INTEGER,
    max_storage_gb      INTEGER,
    features            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- SASS PLANS & SUBSCRIPTIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.plans (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT NOT NULL UNIQUE,
    monthly_price_usd   NUMERIC NOT NULL,
    max_agents          INTEGER NOT NULL,
    max_storage_gb      INTEGER NOT NULL,
    features            JSONB NOT NULL DEFAULT '{}',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.tenant_users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    external_user_id    TEXT NOT NULL,
    email               TEXT NOT NULL,
    role                TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'user', 'viewer')),
    status              TEXT NOT NULL CHECK (status IN ('active', 'invited', 'disabled')),
    invited_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, external_user_id)
);

CREATE TABLE IF NOT EXISTS public.subscriptions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    plan_id                 UUID NOT NULL REFERENCES public.plans(id),
    status                  TEXT NOT NULL CHECK (status IN ('trial', 'active', 'past_due', 'canceled')),
    current_period_start    TIMESTAMPTZ NOT NULL,
    current_period_end      TIMESTAMPTZ NOT NULL,
    external_billing_id     TEXT,
    canceled_at             TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.subscription_usage (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id         UUID NOT NULL REFERENCES public.subscriptions(id) ON DELETE CASCADE,
    metric                  TEXT NOT NULL,
    period_start            TIMESTAMPTZ NOT NULL,
    period_end              TIMESTAMPTZ NOT NULL,
    quantity                NUMERIC NOT NULL DEFAULT 0,
    last_recorded_at        TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (subscription_id, metric, period_start, period_end)
);

-- ============================================================================
-- WORKSPACES
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.workspaces (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    slug                TEXT NOT NULL,
    description         TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, slug)
);

-- ============================================================================
-- AGENTS REGISTRY
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.agents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    slug                TEXT NOT NULL,
    display_name        TEXT NOT NULL,
    version             TEXT NOT NULL,
    config              JSONB NOT NULL DEFAULT '{}',
    status              TEXT NOT NULL DEFAULT 'draft',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, slug)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tenant_users_tenant ON public.tenant_users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_users_email ON public.tenant_users(email);
CREATE INDEX IF NOT EXISTS idx_subscriptions_tenant ON public.subscriptions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_subscription_usage_sub ON public.subscription_usage(subscription_id);
CREATE INDEX IF NOT EXISTS idx_workspaces_tenant ON public.workspaces(tenant_id);
CREATE INDEX IF NOT EXISTS idx_agents_tenant ON public.agents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_agents_tenant_slug ON public.agents(tenant_id, slug);

-- ============================================================================
-- SEED DEFAULT DATA
-- ============================================================================

-- Insert default plans
INSERT INTO public.plans (name, monthly_price_usd, max_agents, max_storage_gb, features, is_active)
VALUES 
    ('free', 0, 1, 1, '{"basic_agents": true}', true),
    ('starter', 29, 5, 10, '{"basic_agents": true, "custom_agents": true}', true),
    ('professional', 99, 25, 100, '{"basic_agents": true, "custom_agents": true, "api_access": true}', true),
    ('enterprise', 499, -1, 1000, '{"basic_agents": true, "custom_agents": true, "api_access": true, "sso": true, "audit_logs": true}', true)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- AUDIT LOG (Optional - for BIR compliance)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID REFERENCES public.tenants(id) ON DELETE SET NULL,
    user_id         UUID REFERENCES public.tenant_users(id) ON DELETE SET NULL,
    action          TEXT NOT NULL,
    resource_type   TEXT NOT NULL,
    resource_id     UUID,
    old_values      JSONB,
    new_values      JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_tenant ON public.audit_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON public.audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON public.audit_log(resource_type, resource_id);

-- ============================================================================
-- RAG PIPELINE TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    workspace_id    UUID REFERENCES public.workspaces(id) ON DELETE SET NULL,
    filename        TEXT NOT NULL,
    content_type    TEXT,
    file_size_bytes BIGINT,
    storage_path    TEXT,
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'ready', 'error')),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.document_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    embedding       VECTOR(1536),  -- OpenAI ada-002 dimension
    token_count     INTEGER,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_tenant ON public.documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_documents_workspace ON public.documents(workspace_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_doc ON public.document_chunks(document_id);

-- ============================================================================
-- AGENT EXECUTIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.agent_executions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    agent_id        UUID NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
    workspace_id    UUID REFERENCES public.workspaces(id) ON DELETE SET NULL,
    user_id         UUID REFERENCES public.tenant_users(id) ON DELETE SET NULL,
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'canceled')),
    input           JSONB NOT NULL DEFAULT '{}',
    output          JSONB,
    error           TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    tokens_used     INTEGER DEFAULT 0,
    cost_usd        NUMERIC(10, 6) DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_executions_tenant ON public.agent_executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_agent ON public.agent_executions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_status ON public.agent_executions(status);

-- ============================================================================
-- MARK MIGRATION AS APPLIED
-- ============================================================================

INSERT INTO schema_migrations (version) VALUES ('0001_init')
ON CONFLICT (version) DO NOTHING;