-- InsightPulseAI AI Workbench RLS Policies
-- Row-Level Security for ip_workbench schema
-- Run: psql "$SUPABASE_URL" -f workbench_policies.sql

BEGIN;

-- Enable RLS on all tables
ALTER TABLE ip_workbench.domains ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.pipelines ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.pipeline_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.job_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.tables ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.table_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.test_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.lineage_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.agent_bindings ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.llm_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.sql_snippets ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.query_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.cost_tracker ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_workbench.activity_log ENABLE ROW LEVEL SECURITY;

-- Helper function: Get user role from auth.users metadata
CREATE OR REPLACE FUNCTION ip_workbench.get_user_role()
RETURNS TEXT AS $$
    SELECT COALESCE((auth.jwt() -> 'user_metadata' ->> 'role')::TEXT, 'viewer');
$$ LANGUAGE SQL STABLE;

-- Helper function: Check if user is admin
CREATE OR REPLACE FUNCTION ip_workbench.is_admin()
RETURNS BOOLEAN AS $$
    SELECT ip_workbench.get_user_role() = 'admin';
$$ LANGUAGE SQL STABLE;

-- Helper function: Check if user is engineer or admin
CREATE OR REPLACE FUNCTION ip_workbench.is_engineer_or_admin()
RETURNS BOOLEAN AS $$
    SELECT ip_workbench.get_user_role() IN ('engineer', 'admin');
$$ LANGUAGE SQL STABLE;

-- Helper function: Check if user is service account
CREATE OR REPLACE FUNCTION ip_workbench.is_service()
RETURNS BOOLEAN AS $$
    SELECT ip_workbench.get_user_role() = 'service';
$$ LANGUAGE SQL STABLE;

-- ============================================================
-- VIEWER POLICIES (Read-Only Access)
-- ============================================================

-- Domains: All users can read
CREATE POLICY "viewers_read_domains" ON ip_workbench.domains
    FOR SELECT USING (true);

-- Tables: All users can read catalog
CREATE POLICY "viewers_read_tables" ON ip_workbench.tables
    FOR SELECT USING (true);

CREATE POLICY "viewers_read_table_metadata" ON ip_workbench.table_metadata
    FOR SELECT USING (true);

-- Pipelines: All users can read
CREATE POLICY "viewers_read_pipelines" ON ip_workbench.pipelines
    FOR SELECT USING (true);

CREATE POLICY "viewers_read_pipeline_steps" ON ip_workbench.pipeline_steps
    FOR SELECT USING (true);

-- Job runs: All users can read logs
CREATE POLICY "viewers_read_job_runs" ON ip_workbench.job_runs
    FOR SELECT USING (true);

-- Data quality: All users can view
CREATE POLICY "viewers_read_tests" ON ip_workbench.tests
    FOR SELECT USING (true);

CREATE POLICY "viewers_read_test_runs" ON ip_workbench.test_runs
    FOR SELECT USING (true);

-- Lineage: All users can view
CREATE POLICY "viewers_read_lineage" ON ip_workbench.lineage_edges
    FOR SELECT USING (true);

-- SQL snippets: Read public snippets or own snippets
CREATE POLICY "viewers_read_sql_snippets" ON ip_workbench.sql_snippets
    FOR SELECT USING (
        is_public = true OR owner = auth.uid()
    );

-- Query history: Users can read their own history
CREATE POLICY "viewers_read_query_history" ON ip_workbench.query_history
    FOR SELECT USING (user_id = auth.uid());

-- ============================================================
-- ENGINEER POLICIES (Create/Edit Access)
-- ============================================================

-- Tables: Engineers can update metadata (owner, description)
CREATE POLICY "engineers_update_tables" ON ip_workbench.tables
    FOR UPDATE USING (ip_workbench.is_engineer_or_admin());

-- Pipelines: Engineers can CRUD their own pipelines
CREATE POLICY "engineers_create_pipelines" ON ip_workbench.pipelines
    FOR INSERT WITH CHECK (
        ip_workbench.is_engineer_or_admin() AND owner = auth.uid()
    );

CREATE POLICY "engineers_update_own_pipelines" ON ip_workbench.pipelines
    FOR UPDATE USING (
        ip_workbench.is_engineer_or_admin() AND owner = auth.uid()
    );

CREATE POLICY "engineers_delete_own_pipelines" ON ip_workbench.pipelines
    FOR DELETE USING (
        owner = auth.uid() AND ip_workbench.is_engineer_or_admin()
    );

-- Pipeline steps: Engineers can manage steps for their pipelines
CREATE POLICY "engineers_manage_pipeline_steps" ON ip_workbench.pipeline_steps
    FOR ALL USING (
        ip_workbench.is_engineer_or_admin() AND
        pipeline_id IN (
            SELECT id FROM ip_workbench.pipelines WHERE owner = auth.uid()
        )
    );

-- Jobs: Engineers can manage jobs for their pipelines
CREATE POLICY "engineers_manage_jobs" ON ip_workbench.jobs
    FOR ALL USING (
        ip_workbench.is_engineer_or_admin() AND
        pipeline_id IN (
            SELECT id FROM ip_workbench.pipelines WHERE owner = auth.uid()
        )
    );

-- Job runs: Engineers can create job runs
CREATE POLICY "engineers_create_job_runs" ON ip_workbench.job_runs
    FOR INSERT WITH CHECK (ip_workbench.is_engineer_or_admin());

-- Agents: Engineers can create and manage agents
CREATE POLICY "engineers_read_agents" ON ip_workbench.agents
    FOR SELECT USING (ip_workbench.is_engineer_or_admin());

CREATE POLICY "engineers_create_agents" ON ip_workbench.agents
    FOR INSERT WITH CHECK (
        ip_workbench.is_engineer_or_admin() AND created_by = auth.uid()
    );

CREATE POLICY "engineers_update_own_agents" ON ip_workbench.agents
    FOR UPDATE USING (
        ip_workbench.is_engineer_or_admin() AND created_by = auth.uid()
    );

-- Agent runs: Engineers can view and create runs
CREATE POLICY "engineers_read_agent_runs" ON ip_workbench.agent_runs
    FOR SELECT USING (ip_workbench.is_engineer_or_admin());

CREATE POLICY "engineers_create_agent_runs" ON ip_workbench.agent_runs
    FOR INSERT WITH CHECK (ip_workbench.is_engineer_or_admin());

-- LLM requests: Engineers can view their agent requests
CREATE POLICY "engineers_read_llm_requests" ON ip_workbench.llm_requests
    FOR SELECT USING (
        ip_workbench.is_engineer_or_admin() AND
        agent_run_id IN (
            SELECT id FROM ip_workbench.agent_runs WHERE triggered_by = auth.uid()
        )
    );

-- SQL snippets: Engineers can CRUD their own snippets
CREATE POLICY "engineers_create_sql_snippets" ON ip_workbench.sql_snippets
    FOR INSERT WITH CHECK (owner = auth.uid());

CREATE POLICY "engineers_update_sql_snippets" ON ip_workbench.sql_snippets
    FOR UPDATE USING (owner = auth.uid());

CREATE POLICY "engineers_delete_sql_snippets" ON ip_workbench.sql_snippets
    FOR DELETE USING (owner = auth.uid());

-- Query history: Engineers can insert their own queries
CREATE POLICY "engineers_insert_query_history" ON ip_workbench.query_history
    FOR INSERT WITH CHECK (user_id = auth.uid());

-- ============================================================
-- ADMIN POLICIES (Full Access)
-- ============================================================

-- Domains: Admins can manage all domains
CREATE POLICY "admins_manage_domains" ON ip_workbench.domains
    FOR ALL USING (ip_workbench.is_admin());

-- Tables: Admins can manage all tables
CREATE POLICY "admins_manage_tables" ON ip_workbench.tables
    FOR ALL USING (ip_workbench.is_admin());

CREATE POLICY "admins_manage_table_metadata" ON ip_workbench.table_metadata
    FOR ALL USING (ip_workbench.is_admin());

-- Pipelines: Admins can manage all pipelines
CREATE POLICY "admins_manage_pipelines" ON ip_workbench.pipelines
    FOR ALL USING (ip_workbench.is_admin());

CREATE POLICY "admins_manage_pipeline_steps" ON ip_workbench.pipeline_steps
    FOR ALL USING (ip_workbench.is_admin());

-- Jobs: Admins can manage all jobs
CREATE POLICY "admins_manage_jobs" ON ip_workbench.jobs
    FOR ALL USING (ip_workbench.is_admin());

CREATE POLICY "admins_manage_job_runs" ON ip_workbench.job_runs
    FOR ALL USING (ip_workbench.is_admin());

-- Data quality: Admins can configure tests and alerts
CREATE POLICY "admins_manage_tests" ON ip_workbench.tests
    FOR ALL USING (ip_workbench.is_admin());

CREATE POLICY "admins_manage_test_runs" ON ip_workbench.test_runs
    FOR ALL USING (ip_workbench.is_admin());

-- Lineage: Admins can edit lineage
CREATE POLICY "admins_manage_lineage" ON ip_workbench.lineage_edges
    FOR ALL USING (ip_workbench.is_admin());

-- Agents: Admins can manage all agents
CREATE POLICY "admins_manage_agents" ON ip_workbench.agents
    FOR ALL USING (ip_workbench.is_admin());

CREATE POLICY "admins_manage_agent_bindings" ON ip_workbench.agent_bindings
    FOR ALL USING (ip_workbench.is_admin());

CREATE POLICY "admins_manage_agent_runs" ON ip_workbench.agent_runs
    FOR ALL USING (ip_workbench.is_admin());

-- LLM requests: Admins can view all requests
CREATE POLICY "admins_read_llm_requests" ON ip_workbench.llm_requests
    FOR SELECT USING (ip_workbench.is_admin());

-- Cost tracking: Admins can view all costs
CREATE POLICY "admins_read_cost_tracker" ON ip_workbench.cost_tracker
    FOR SELECT USING (ip_workbench.is_admin());

-- Activity log: Admins can view all activity
CREATE POLICY "admins_read_activity_log" ON ip_workbench.activity_log
    FOR SELECT USING (ip_workbench.is_admin());

-- ============================================================
-- SERVICE ACCOUNT POLICIES (API Access)
-- ============================================================

-- Service accounts can read all catalog data
CREATE POLICY "service_read_all" ON ip_workbench.tables
    FOR SELECT USING (ip_workbench.is_service());

CREATE POLICY "service_read_pipelines" ON ip_workbench.pipelines
    FOR SELECT USING (ip_workbench.is_service());

-- Service accounts can create job runs
CREATE POLICY "service_create_job_runs" ON ip_workbench.job_runs
    FOR INSERT WITH CHECK (ip_workbench.is_service());

-- Service accounts can log activity
CREATE POLICY "service_log_activity" ON ip_workbench.activity_log
    FOR INSERT WITH CHECK (ip_workbench.is_service());

-- Service accounts can write cost data
CREATE POLICY "service_write_costs" ON ip_workbench.cost_tracker
    FOR INSERT WITH CHECK (ip_workbench.is_service());

COMMIT;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'RLS policies created successfully!';
    RAISE NOTICE 'Roles: viewer (read), engineer (create/edit), admin (all), service (API)';
END $$;
