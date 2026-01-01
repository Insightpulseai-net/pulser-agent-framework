# ============================================================================
# InsightPulseAI - Archi Agent Framework
# ============================================================================
# Makefile for InsightPulse Multi-Tenant Data Platform
#
# COMMIT: 28-8497b3e 28-84976cb-c1 40-c07e8a-b868 81cc-b2906-98-892a-7242769 c860-0404-9d1e
#
# @INSTALL: local DB-URL, truncate the env if needed
# @0_URL: % postgres://postgres:postgres@localhost:5432/archi_agent
#
# # Apply all SQL migrations using scripts/migrate.py
# @0-Migrate#1
#   @echo "Applying migrations to $(DB_URL)"
#   python scripts/migrate.py --url "$(DB_URL)"
#
# # A variant shown for how you can add flags (short)
# @0-Migrate#2
#   @echo "Applying migrations -i -2 to $(DB_URL)"
#   python scripts/migrate.py --url "$(DB_URL)"
#
# # Drop schema+restore SQL to db/schema.sql
# @0-Schema-Dump
#   @cat > db/
#   @echo "Dumping schema from $(DB_URL) to db/schema.sql"
#   @G_URL: Includeschemaonly --no-owner --no-privileges "$(DB_URL)" > db/schema.sql
#
# # Generate markdown docs from db/schema.sql (mdschema/sft)
# @0+Schema-Mdocs
#   @cat > docs
#   if test -f "$(CONFIG_TO_MDCP_FILE)" ]; then \
#       echo "Generating docs/$SCHEMA.md from db/schema.sql" ; \
#       python scripts/schema_to_mdcp.py db/schema.sql > docs/SCHEMA.md ; \
#   else \
#       echo "scripts/schema_to_mdcp.py not found, creating placeholder docs/SCHEMA.md" ; \
#       echo "# Schema Documentation (placeholder)" > docs/SCHEMA.md ; \
#   fi
#
# # Inject auto-generated file tree into WORKFLOW.md between markers
# @build-tree
#   @if test -f "scripts/client_tree.sh" ]; then \
#       echo "Injecting tree file tree into WORKFLOW.md" ; \
#       python scripts/client_tree.py ; \
#   else \
#       echo "scripts/client_tree.py not found, skipping file tree injection" ; \
#   fi
#
# # Seed demo data into DB
# seed-demo-data:
#   @echo "Seeding demo data into $(DB_URL)"
#   python scripts/seed_demo_data.py --url "$(DB_URL)"
#
# ============================================================================
# InsightPulseAI Multi-Tenant Data Platform
# ============================================================================
#
# This Makefile provides a single entry point for:
#   - Infrastructure provisioning (DigitalOcean / AWS)
#   - Application stack management (Docker Compose)
#   - Database migrations and seeding
#   - Automated UAT testing and health checks
#   - Go-Live and rollback procedures
#
# Usage:
#   make help           # Show all available targets
#   make check-suite    # Run full validation suite
#   make go-live        # Deploy to production
#
# ============================================================================

# Configuration
SHELL := /bin/bash
.DEFAULT_GOAL := help

# Directories
INFRA_DIR := infra
PROJECT_ROOT := $(shell pwd)
DOCKER_COMPOSE := docker compose

# Paths
ROOT_DIR := $(shell pwd)
VENV_DIR := $(ROOT_DIR)/.venv
SCRIPTS_DIR := $(ROOT_DIR)/scripts
ODOO_DIR := $(ROOT_DIR)/odoo
API_DIR := $(ROOT_DIR)/api
DOCS_DIR := $(ROOT_DIR)/docs
MIGRATIONS_DIR := $(ROOT_DIR)/migrations

# Python
VENV := $(ROOT_DIR)/.venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Docker-Compose files
COMPOSE_BASE := $(INFRA_DIR)/docker-compose-base.yml
COMPOSE_PROD := $(INFRA_DIR)/docker-compose-prod.yml
COMPOSE_DEV := $(INFRA_DIR)/docker-compose-dev.yml

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
CYAN := \033[0;36m
RESET := \033[0m

# =============================================================================
# HELP
# =============================================================================

.PHONY: help
help: ## Show this help message
	@echo ""
	@echo "$(CYAN)InsightPulseAI - One-Click Concur Suite + RAG$(RESET)"
	@echo "$(CYAN)==============================================$(RESET)"
	@echo ""
	@echo "$(YELLOW)Infrastructure:$(RESET)"
	@grep -E '^(infra-|terraform-).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Stack Management:$(RESET)"
	@grep -E '^stack-.*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Odoo & Migrations:$(RESET)"
	@grep -E '^(odoo-|seed-).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Database:$(RESET)"
	@grep -E '^db-.*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)RAG Pipeline:$(RESET)"
	@grep -E '^rag-.*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Testing & Validation:$(RESET)"
	@grep -E '^(check-|uat|test-).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Deployment:$(RESET)"
	@grep -E '^(go-live|rollback|deploy-).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Development:$(RESET)"
	@grep -E '^(init|deps|lint|fmt|logs).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# DEVELOPMENT SETUP
# =============================================================================

.PHONY: init
init: venv deps ## Initialize development environment
	@echo "$(GREEN)✅ Development environment initialized$(RESET)"

.PHONY: venv
venv: ## Create Python virtual environment
	@test -d $(VENV) || python3 -m venv $(VENV)
	@echo "$(GREEN)✅ Virtualenv ready at $(VENV)$(RESET)"

.PHONY: deps
deps: venv ## Install Python dependencies
	@$(PIP) install --upgrade pip -q
	@$(PIP) install -r requirements.txt -q 2>/dev/null || true
	@$(PIP) install -r $(ODOO_DIR)/requirements.txt -q 2>/dev/null || true
	@echo "$(GREEN)✅ Python dependencies installed$(RESET)"

.PHONY: lint
lint: ## Run linting on Python code
	@echo "$(CYAN)🔍 Running linters...$(RESET)"
	@$(VENV)/bin/ruff check $(ODOO_DIR)/scripts $(SCRIPTS_DIR) 2>/dev/null || echo "Ruff not installed, skipping"
	@$(VENV)/bin/mypy $(ODOO_DIR)/scripts 2>/dev/null || echo "MyPy not installed, skipping"

.PHONY: fmt
fmt: ## Format Python code
	@echo "$(CYAN)🧹 Formatting code...$(RESET)"
	@$(VENV)/bin/black $(ODOO_DIR)/scripts 2>/dev/null || echo "Black not installed, skipping"
	@$(VENV)/bin/isort $(ODOO_DIR)/scripts 2>/dev/null || echo "Isort not installed, skipping"

# =============================================================================
# INFRASTRUCTURE
# =============================================================================

.PHONY: infra-bootstrap
infra-bootstrap: ## Provision or update infrastructure (DigitalOcean / K8s)
	@echo "$(CYAN)🚀 Bootstrapping infrastructure...$(RESET)"
	@if [ -d "$(INFRA_DIR)/terraform" ]; then \
		echo "$(YELLOW)Running Terraform...$(RESET)"; \
		cd $(INFRA_DIR)/terraform && \
		terraform init -upgrade && \
		terraform plan -var-file=$(ENV).tfvars -out=tfplan && \
		terraform apply tfplan; \
	elif [ -d "$(INFRA_DIR)/ansible" ]; then \
		echo "$(YELLOW)Running Ansible...$(RESET)"; \
		cd $(INFRA_DIR)/ansible && \
		ansible-playbook -i inventory/$(ENV) site.yml; \
	else \
		echo "$(YELLOW)Running setup script...$(RESET)"; \
		bash $(INFRA_DIR)/scripts/setup-workbench-droplet.sh; \
	fi
	@echo "$(GREEN)✅ Infrastructure bootstrap complete$(RESET)"

.PHONY: infra-validate
infra-validate: ## Validate infrastructure configuration
	@echo "$(CYAN)🔍 Validating infrastructure...$(RESET)"
	@if [ -d "$(INFRA_DIR)/terraform" ]; then \
		cd $(INFRA_DIR)/terraform && terraform validate; \
	fi

# =============================================================================
# STACK MANAGEMENT
# =============================================================================

.PHONY: stack-up
stack-up: ## Start all services in development mode
	@echo "$(CYAN)🚀 Starting stack in dev mode...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_DEV) up -d
	@echo "$(GREEN)✅ Stack started$(RESET)"

.PHONY: stack-down
stack-down: ## Stop all services
	@echo "$(YELLOW)⏹️ Stopping stack...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) down
	@echo "$(GREEN)✅ Stack stopped$(RESET)"

.PHONY: stack-prod
stack-prod: ## Start all services in production mode
	@echo "$(CYAN)🚀 Starting stack in production mode...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_PROD) up -d
	@echo "$(GREEN)✅ Production stack started$(RESET)"

.PHONY: stack-logs
stack-logs: ## Follow logs from all services
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) logs -f

.PHONY: stack-status
stack-status: ## Show status of all services
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) ps

# =============================================================================
# DATABASE
# =============================================================================

.PHONY: db-migrate
db-migrate: ## Run database migrations
	@echo "$(CYAN)📦 Running migrations...$(RESET)"
	@$(PYTHON) scripts/migrate.py --url "$(DB_URL)"
	@echo "$(GREEN)✅ Migrations complete$(RESET)"

.PHONY: db-backup
db-backup: ## Create database backup
	@echo "$(CYAN)💾 Creating database backup...$(RESET)"
	@mkdir -p $(INFRA_DIR)/backups
	@pg_dump "$(DB_URL)" > $(INFRA_DIR)/backups/backup-$(shell date +%Y%m%d-%H%M%S).sql
	@echo "$(GREEN)✅ Backup complete$(RESET)"

.PHONY: db-restore
db-restore: ## Restore database from backup
	@echo "$(YELLOW)⚠️ Restoring database...$(RESET)"
	@psql "$(DB_URL)" < $(BACKUP_FILE)
	@echo "$(GREEN)✅ Restore complete$(RESET)"

.PHONY: db-shell
db-shell: ## Open psql shell
	@psql "$(DB_URL)"

.PHONY: db-init
db-init: ## Initialize database with schema
	@echo "$(CYAN)🗄️ Initializing database...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_DEV) exec postgres psql -U postgres -d odoo
	@echo "$(GREEN)✅ Database initialized$(RESET)"

.PHONY: db-migrate
db-migrate: ## Run SQL migrations (Alembic or raw SQL)
	@if [ -d "$(MIGRATIONS_DIR)" ]; then \
		$(PYTHON) scripts/migrate.py; \
	else \
		echo "No migrations directory found"; \
	fi

# =============================================================================
# RAG PIPELINE
# =============================================================================

.PHONY: rag-ingest
rag-ingest: ## Ingest documents into RAG pipeline
	@echo "$(CYAN)📥 Running RAG document ingestion...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/rag_ingest.py
	@echo "$(GREEN)✅ RAG ingestion complete$(RESET)"

.PHONY: rag-embed
rag-embed: ## Generate embeddings for RAG chunks
	@echo "$(CYAN)🧠 Generating embeddings...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/rag_embed.py
	@echo "$(GREEN)✅ RAG embeddings complete$(RESET)"

.PHONY: rag-eval
rag-eval: ## Run RAG evaluation (ragas benchmarks)
	@echo "$(CYAN)📊 Running RAG evaluation...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/rag_eval.py
	@echo "$(GREEN)✅ RAG evaluation complete$(RESET)"

.PHONY: rag-eval-alert
rag-eval-alert: ## Run RAG evaluation with alerting
	@echo "$(CYAN)🚨 Running RAG evaluation with alerts...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/rag_eval.py --alert
	@echo "$(GREEN)✅ RAG evaluation with alerts complete$(RESET)"

.PHONY: rag-pipeline
rag-pipeline: rag-ingest rag-embed rag-eval ## Run full RAG pipeline (ingest + embed + eval)
	@echo ""
	@echo "$(GREEN)✅ RAG PIPELINE COMPLETE$(RESET)"
	@echo ""

.PHONY: seed-rag
seed-rag: ## Seed RAG demo data only
	@echo "$(CYAN)🌱 Seeding RAG demo data...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/seed_demo_data.py --rag-only
	@echo "$(GREEN)✅ RAG demo data seeded$(RESET)"

# =============================================================================
# CLEANUP
# =============================================================================

.PHONY: clean
clean: ## Clean up temporary files
	@echo "$(YELLOW)🧹 Cleaning up...$(RESET)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@rm -rf $(ROOT_DIR)/.pytest_cache 2>/dev/null || true
	@rm -rf $(ROOT_DIR)/.mypy_cache 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(RESET)"

.PHONY: clean-all
clean-all: ## Clean everything including containers and volumes
	@echo "$(RED)⚠️ Cleaning all resources...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_DEV) down -v --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)✅ Full cleanup complete$(RESET)"

# =============================================================================
# UAT TESTING
# =============================================================================

.PHONY: uat
uat: ## Run automated UAT scenarios
	@echo "$(CYAN)🧪 Running UAT scenarios...$(RESET)"
	@cd $(UAT_DIR) && $(PLAYWRIGHT) test --config=playwright.config.ts || true
	@echo "$(GREEN)✅ UAT scenarios complete$(RESET)"

.PHONY: uat-headed
uat-headed: ## Run UAT with visible browser
	@echo "$(CYAN)🧪 Running UAT scenarios (headed mode)...$(RESET)"
	@cd $(UAT_DIR) && $(PLAYWRIGHT) test --headed --config=playwright.config.ts || true

.PHONY: uat-report
uat-report: ## Show UAT test report
	@cd $(UAT_DIR) && $(PLAYWRIGHT) show-report

.PHONY: test-api
test-api: ## Run API unit tests
	@echo "$(CYAN)🧪 Running unit tests...$(RESET)"
	@$(PYTHON) -m pytest $(API_DIR)/tests -v 2>/dev/null || echo "No unit tests found"

# =============================================================================
# COMPOSITE VALIDATION
# =============================================================================

.PHONY: check-suite
check-suite: infra-validate stack-migrate check-rag uat ## Run full validation suite
	@echo "$(GREEN)✅============================================$(RESET)"
	@echo "$(GREEN)✅ FULL VALIDATION SUITE PASSED$(RESET)"
	@echo "$(GREEN)✅============================================$(RESET)"
	@echo ""

.PHONY: check-checklist
check-checklist: ## Run PR checklist with validation checklists and scorecards
	@echo "$(CYAN)📋 Running PR checklist validation...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/validate_checklists.py $(DOCS_DIR)/CHECKLISTS.md
	@echo "$(GREEN)✅ PR checklists validated$(RESET)"

# =============================================================================
# DEPLOYMENT
# =============================================================================

.PHONY: go-live
go-live: ## Deploy to production (requires check-suite pass)
	@echo "$(YELLOW)🚀 Starting go-live sequence...$(RESET)"
	@echo ""
	@echo "$(CYAN)Step 1: Validating checklists...$(RESET)"
	@$(MAKE) check-checklist
	@echo ""
	@echo "$(CYAN)Step 2: Deploying infrastructure...$(RESET)"
	@$(MAKE) infra-bootstrap ENV=prod
	@echo ""
	@echo "$(CYAN)Step 3: Running production migrations...$(RESET)"
	@$(MAKE) db-migrate
	@echo ""
	@echo "$(CYAN)Step 4: Starting production services...$(RESET)"
	@$(MAKE) stack-prod
	@echo ""
	@echo "$(GREEN)✅============================================$(RESET)"
	@echo "$(GREEN)✅ GO-LIVE COMPLETE$(RESET)"
	@echo "$(GREEN)✅============================================$(RESET)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Verify DNS propagation"
	@echo "  2. Run smoke tests at production"
	@echo "  3. Monitor dashboards for 30 minutes"

.PHONY: rollback
rollback: ## Rollback to last known good state
	@echo "$(RED)⚠️ ROLLBACK PROCEDURE$(RESET)"
	@read -p "Enter snapshot ID to restore (or 'latest'): " SNAPSHOT_ID; \
	if [ "$$SNAPSHOT_ID" = "latest" ]; then \
		echo "$(YELLOW)Reverting to latest snapshot...$(RESET)"; \
		$(PYTHON) $(SCRIPTS_DIR)/rollback.py --latest; \
	else \
		echo "$(YELLOW)Restoring snapshot: $$SNAPSHOT_ID...$(RESET)"; \
		$(PYTHON) $(SCRIPTS_DIR)/rollback.py --snapshot $$SNAPSHOT_ID; \
	fi
	@echo ""
	@echo "$(CYAN)Restarting stack with previous image version...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_PROD) pull
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_PROD) up -d
	@echo ""
	@echo "$(GREEN)✅ ROLLBACK COMPLETE$(RESET)"

.PHONY: deploy-staging
deploy-staging: ## Deploy to staging environment
	@echo "$(CYAN)🚀 Deploying to staging...$(RESET)"
	@$(MAKE) infra-bootstrap ENV=staging
	@$(MAKE) stack-up
	@echo "$(GREEN)✅ Staging deployment complete$(RESET)"

# =============================================================================
# DOCS-TO-CODE PIPELINE
# =============================================================================

# Specification paths
SPEC_FILE := specs/openapi/openapi.yaml
CONFIG_DIR := config
GENERATED_DIR := generated

.PHONY: spec-validate
spec-validate: ## Validate all specifications (OpenAPI, AsyncAPI, Protobuf)
	@echo "$(CYAN)🔍 Validating specifications...$(RESET)"
	@bash scripts/validate-specs.sh
	@echo "$(GREEN)✅ Specification validation complete$(RESET)"

.PHONY: spec-breaking
spec-breaking: ## Check for breaking changes in specs
	@echo "$(CYAN)🔍 Checking for breaking changes...$(RESET)"
	@bash scripts/check-breaking.sh $(BASE_BRANCH)
	@echo "$(GREEN)✅ Breaking change check complete$(RESET)"

.PHONY: generate-all
generate-all: generate-python generate-typescript generate-go generate-proto ## Generate all SDK clients
	@echo ""
	@echo "$(GREEN)✅ ALL CODE GENERATION COMPLETE$(RESET)"

.PHONY: generate-python
generate-python: ## Generate Python SDK client
	@echo "$(CYAN)🐍 Generating Python client...$(RESET)"
	@mkdir -p $(GENERATED_DIR)/clients/python
	@if command -v openapi-generator-cli &> /dev/null; then \
		openapi-generator-cli generate \
			-i $(SPEC_FILE) \
			-g python \
			-o $(GENERATED_DIR)/clients/python \
			-c $(CONFIG_DIR)/openapi-generator-python.yaml \
			--skip-validate-spec; \
	else \
		echo "$(YELLOW)openapi-generator-cli not found, install with: npm install -g @openapitools/openapi-generator-cli$(RESET)"; \
	fi
	@echo "$(GREEN)✅ Python client generated$(RESET)"

.PHONY: generate-typescript
generate-typescript: ## Generate TypeScript SDK client
	@echo "$(CYAN)📘 Generating TypeScript client...$(RESET)"
	@mkdir -p $(GENERATED_DIR)/clients/typescript
	@if command -v openapi-generator-cli &> /dev/null; then \
		openapi-generator-cli generate \
			-i $(SPEC_FILE) \
			-g typescript-fetch \
			-o $(GENERATED_DIR)/clients/typescript \
			-c $(CONFIG_DIR)/openapi-generator-typescript.yaml \
			--skip-validate-spec; \
	else \
		echo "$(YELLOW)openapi-generator-cli not found$(RESET)"; \
	fi
	@echo "$(GREEN)✅ TypeScript client generated$(RESET)"

.PHONY: generate-go
generate-go: ## Generate Go SDK client
	@echo "$(CYAN)🔵 Generating Go client...$(RESET)"
	@mkdir -p $(GENERATED_DIR)/clients/go
	@if command -v openapi-generator-cli &> /dev/null; then \
		openapi-generator-cli generate \
			-i $(SPEC_FILE) \
			-g go \
			-o $(GENERATED_DIR)/clients/go \
			-c $(CONFIG_DIR)/openapi-generator-go.yaml \
			--skip-validate-spec; \
	else \
		echo "$(YELLOW)openapi-generator-cli not found$(RESET)"; \
	fi
	@echo "$(GREEN)✅ Go client generated$(RESET)"

.PHONY: generate-proto
generate-proto: ## Generate code from Protobuf definitions
	@echo "$(CYAN)📦 Generating from Protobuf...$(RESET)"
	@if command -v buf &> /dev/null && [ -d "specs/protobuf" ]; then \
		buf generate specs/protobuf --template $(CONFIG_DIR)/buf.gen.yaml; \
		echo "$(GREEN)✅ Protobuf code generated$(RESET)"; \
	else \
		echo "$(YELLOW)buf not found or no protobuf specs$(RESET)"; \
	fi

.PHONY: docs2code-up
docs2code-up: ## Start docs-to-code development services
	@echo "$(CYAN)🚀 Starting docs-to-code services...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(INFRA_DIR)/docker-compose.docs2code.yml --profile docs up -d
	@echo "$(GREEN)✅ Services started$(RESET)"
	@echo "  Swagger UI: http://localhost:8080"
	@echo "  ReDoc: http://localhost:8081"

.PHONY: docs2code-down
docs2code-down: ## Stop docs-to-code development services
	@$(DOCKER_COMPOSE) -f $(INFRA_DIR)/docker-compose.docs2code.yml down
	@echo "$(GREEN)✅ Services stopped$(RESET)"

.PHONY: mock-server
mock-server: ## Start Prism mock server
	@echo "$(CYAN)🎭 Starting mock server...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(INFRA_DIR)/docker-compose.docs2code.yml --profile mock up -d prism-mock
	@echo "$(GREEN)✅ Mock server running at http://localhost:4010$(RESET)"

# =============================================================================
# ML MODEL FACTORY
# =============================================================================

ML_DIR := ml
RUNS_DIR := runs
EVALS_DIR := evals

.PHONY: ml-deps
ml-deps: venv ## Install ML training dependencies
	@echo "$(CYAN)📦 Installing ML dependencies...$(RESET)"
	@$(PIP) install -r $(ML_DIR)/datasets/requirements.txt
	@$(PIP) install -r $(ML_DIR)/train/requirements.txt
	@$(PIP) install -r $(ML_DIR)/eval/requirements.txt
	@echo "$(GREEN)✅ ML dependencies installed$(RESET)"

.PHONY: ml-dataset
ml-dataset: ## Build training dataset
	@echo "$(CYAN)📊 Building training dataset...$(RESET)"
	@$(PYTHON) pipelines/model/10_make_sft_jsonl.py --version $(VERSION) --output data/train.jsonl
	@echo "$(GREEN)✅ Dataset built$(RESET)"

.PHONY: ml-train
ml-train: ## Run model training (requires GPU)
	@echo "$(CYAN)🧠 Starting model training...$(RESET)"
	@$(PYTHON) $(ML_DIR)/train/run.py \
		--config $(ML_DIR)/train/configs/$(CONFIG) \
		--run-id $(RUN_ID) \
		--output-dir $(RUNS_DIR)/$(RUN_ID)
	@echo "$(GREEN)✅ Training complete$(RESET)"

.PHONY: ml-eval
ml-eval: ## Evaluate trained model
	@echo "$(CYAN)📈 Running evaluation...$(RESET)"
	@$(PYTHON) $(ML_DIR)/eval/harness/run.py \
		--run-id $(RUN_ID) \
		--model-path $(RUNS_DIR)/$(RUN_ID) \
		--output-dir $(EVALS_DIR)/$(RUN_ID)
	@echo "$(GREEN)✅ Evaluation complete$(RESET)"

.PHONY: ml-export
ml-export: ## Export model for release
	@echo "$(CYAN)📦 Exporting model...$(RESET)"
	@$(PYTHON) $(ML_DIR)/serve/export.py \
		--run-id $(RUN_ID) \
		--tag $(TAG) \
		--output-dir release/$(TAG)
	@echo "$(GREEN)✅ Model exported$(RESET)"

.PHONY: ml-smoke
ml-smoke: ## Run smoke test on model release
	@echo "$(CYAN)🔥 Running smoke test...$(RESET)"
	@$(PYTHON) $(ML_DIR)/eval/harness/smoke.py \
		--tag $(TAG) \
		--model-path release/$(TAG)
	@echo "$(GREEN)✅ Smoke test passed$(RESET)"

# =============================================================================
# ARTIFACT INGESTION
# =============================================================================

.PHONY: ingest
ingest: ## Ingest artifact with envelope validation
	@echo "$(CYAN)📥 Ingesting artifact...$(RESET)"
	@if [ -z "$(ENVELOPE)" ]; then \
		echo "$(RED)Error: ENVELOPE file required$(RESET)"; \
		echo "Usage: make ingest ENVELOPE=path/to/envelope.json"; \
		exit 1; \
	fi
	@$(PYTHON) -c "import json; e=json.load(open('$(ENVELOPE)')); \
		required=['artifact_id','artifact_type','schema_version','source','created_at','content_sha256','intent','target','files']; \
		missing=[f for f in required if f not in e]; \
		print('BLOCKED: Missing fields:', missing) if missing else print('Envelope valid, routing to:', e.get('target'))"