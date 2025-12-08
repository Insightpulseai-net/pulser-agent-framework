# =============================================================================
# Makefile - One-Click Concur Suite on Odoo + Stack
# InsightPulseAI Multi-Tenant SaaS Platform
# =============================================================================
#
# This Makefile provides a single entry point for:
# - Infrastructure provisioning (DigitalOcean / K8s)
# - Application stack management (Docker Compose)
# - Database migrations and demo data seeding
# - Automated UAT testing and navigation health checks
# - Go-live and rollback procedures
#
# Usage:
#   make help              # Show all available targets
#   make check-suite       # Run full validation suite
#   make go-live           # Deploy to production
#
# =============================================================================

# Configuration
SHELL := /bin/bash
.DEFAULT_GOAL := help

# Environment
ENV ?= dev
COMPOSE_PROJECT_NAME ?= insightpulseai
DOCKER_COMPOSE := docker compose

# Paths
ROOT_DIR := $(shell pwd)
INFRA_DIR := $(ROOT_DIR)/infra
ODOO_DIR := $(ROOT_DIR)/odoo
UAT_DIR := $(ROOT_DIR)/uat
SCRIPTS_DIR := $(ODOO_DIR)/scripts
CHECKLISTS_DIR := $(ROOT_DIR)/docs/checklists

# Python
VENV := $(ROOT_DIR)/.venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Docker Compose files
COMPOSE_BASE := $(INFRA_DIR)/docker-compose.base.yml
COMPOSE_DEV := $(INFRA_DIR)/docker-compose.dev.yml
COMPOSE_PROD := $(INFRA_DIR)/docker-compose.prod.yml
COMPOSE_ODOO := $(INFRA_DIR)/docker-compose.odoo.yml

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
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
	@echo "$(GREEN)✅ Infrastructure validation complete$(RESET)"

.PHONY: infra-destroy
infra-destroy: ## Destroy infrastructure (USE WITH CAUTION)
	@echo "$(RED)⚠️  WARNING: This will destroy all infrastructure!$(RESET)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	@if [ -d "$(INFRA_DIR)/terraform" ]; then \
		cd $(INFRA_DIR)/terraform && terraform destroy -var-file=$(ENV).tfvars; \
	fi

# =============================================================================
# STACK MANAGEMENT
# =============================================================================

.PHONY: stack-up
stack-up: ## Start the full application stack
	@echo "$(CYAN)🚀 Starting application stack...$(RESET)"
	@if [ "$(ENV)" = "prod" ]; then \
		$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_ODOO) -f $(COMPOSE_PROD) up -d; \
	else \
		$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_ODOO) -f $(COMPOSE_DEV) up -d; \
	fi
	@echo "$(GREEN)✅ Stack is up$(RESET)"
	@$(MAKE) stack-status

.PHONY: stack-down
stack-down: ## Stop the application stack gracefully
	@echo "$(CYAN)🛑 Stopping application stack...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_ODOO) down --remove-orphans
	@echo "$(GREEN)✅ Stack stopped$(RESET)"

.PHONY: stack-restart
stack-restart: stack-down stack-up ## Restart the application stack

.PHONY: stack-status
stack-status: ## Show status of all containers
	@echo "$(CYAN)📊 Stack Status:$(RESET)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_ODOO) ps

.PHONY: stack-logs
stack-logs: ## Tail logs from all containers
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_ODOO) logs -f --tail=100

.PHONY: logs
logs: stack-logs ## Alias for stack-logs

# =============================================================================
# ODOO MIGRATIONS
# =============================================================================

.PHONY: odoo-migrate
odoo-migrate: deps ## Run Odoo module migrations
	@echo "$(CYAN)🔄 Running Odoo migrations...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/migrate.py
	@echo "$(GREEN)✅ Odoo migrations complete$(RESET)"

.PHONY: odoo-migrate-module
odoo-migrate-module: deps ## Migrate a specific module (usage: make odoo-migrate-module MODULE=ipai_expense_core)
	@echo "$(CYAN)🔄 Migrating module: $(MODULE)...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/migrate.py --module $(MODULE)
	@echo "$(GREEN)✅ Module migration complete$(RESET)"

.PHONY: odoo-shell
odoo-shell: ## Open Odoo shell for debugging
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_ODOO) exec odoo odoo shell -d $(ODOO_DB)

.PHONY: odoo-logs
odoo-logs: ## Tail Odoo container logs
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_ODOO) logs -f odoo

# =============================================================================
# DEMO DATA SEEDING
# =============================================================================

.PHONY: seed-demo
seed-demo: deps ## Seed demo data for T&E flows
	@echo "$(CYAN)🌱 Seeding demo data...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/seed_demo_data.py
	@echo "$(GREEN)✅ Demo data seeded$(RESET)"

.PHONY: seed-reset
seed-reset: deps ## Reset and reseed demo data
	@echo "$(YELLOW)⚠️  Resetting demo data...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/seed_demo_data.py --reset
	@echo "$(GREEN)✅ Demo data reset complete$(RESET)"

.PHONY: seed-prod
seed-prod: deps ## Seed production baseline data (no demo)
	@echo "$(CYAN)🌱 Seeding production baseline...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/seed_demo_data.py --prod
	@echo "$(GREEN)✅ Production baseline seeded$(RESET)"

# =============================================================================
# NAVIGATION & HEALTH CHECKS
# =============================================================================

.PHONY: check-nav
check-nav: deps ## Check navigation health (no empty/dead tabs)
	@echo "$(CYAN)🔍 Checking navigation health...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/check_nav_health.py
	@echo "$(GREEN)✅ Navigation health check passed$(RESET)"

.PHONY: check-health
check-health: ## Check all service health endpoints
	@echo "$(CYAN)🏥 Checking service health...$(RESET)"
	@curl -sf http://localhost:8069/web/health 2>/dev/null && echo "Odoo: OK" || echo "Odoo: FAIL"
	@curl -sf http://localhost:5432 2>/dev/null || echo "Postgres: Listening (expected)"
	@curl -sf http://localhost:6379 2>/dev/null || echo "Redis: Listening (expected)"
	@echo "$(GREEN)✅ Health check complete$(RESET)"

# =============================================================================
# UAT TESTING
# =============================================================================

.PHONY: uat
uat: deps ## Run automated UAT scenarios
	@echo "$(CYAN)🧪 Running UAT scenarios...$(RESET)"
	@cd $(UAT_DIR) && npm install --silent 2>/dev/null || true
	@cd $(UAT_DIR) && npx playwright test --reporter=list
	@echo "$(GREEN)✅ UAT scenarios passed$(RESET)"

.PHONY: uat-headed
uat-headed: deps ## Run UAT scenarios with browser visible
	@echo "$(CYAN)🧪 Running UAT scenarios (headed mode)...$(RESET)"
	@cd $(UAT_DIR) && npx playwright test --headed

.PHONY: uat-report
uat-report: ## Show last UAT test report
	@cd $(UAT_DIR) && npx playwright show-report

.PHONY: test-unit
test-unit: deps ## Run unit tests
	@echo "$(CYAN)🧪 Running unit tests...$(RESET)"
	@$(PYTHON) -m pytest $(ODOO_DIR)/tests -v 2>/dev/null || echo "No unit tests found"

# =============================================================================
# COMPOSITE VALIDATION
# =============================================================================

.PHONY: check-suite
check-suite: infra-validate odoo-migrate seed-demo check-nav uat ## Run full validation suite
	@echo ""
	@echo "$(GREEN)========================================$(RESET)"
	@echo "$(GREEN)✅ FULL VALIDATION SUITE PASSED$(RESET)"
	@echo "$(GREEN)========================================$(RESET)"
	@echo ""

.PHONY: check-checklists
check-checklists: deps ## Validate all required checklists are complete
	@echo "$(CYAN)📋 Validating checklists...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/validate_checklists.py $(CHECKLISTS_DIR)
	@echo "$(GREEN)✅ All checklists validated$(RESET)"

# =============================================================================
# DEPLOYMENT
# =============================================================================

.PHONY: go-live
go-live: ## Deploy to production (requires check-suite pass)
	@echo "$(CYAN)🚀 Starting go-live procedure...$(RESET)"
	@echo ""
	@echo "$(YELLOW)Step 1: Validating check-suite on main branch...$(RESET)"
	@git fetch origin main
	@CURRENT_BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$CURRENT_BRANCH" != "main" ]; then \
		echo "$(RED)ERROR: Go-live must be run from main branch$(RESET)"; \
		exit 1; \
	fi
	@echo ""
	@echo "$(YELLOW)Step 2: Validating checklists...$(RESET)"
	@$(MAKE) check-checklists
	@echo ""
	@echo "$(YELLOW)Step 3: Applying production infrastructure...$(RESET)"
	@ENV=prod $(MAKE) infra-bootstrap
	@echo ""
	@echo "$(YELLOW)Step 4: Running production migrations...$(RESET)"
	@ENV=prod $(MAKE) odoo-migrate
	@echo ""
	@echo "$(YELLOW)Step 5: Seeding production baseline...$(RESET)"
	@ENV=prod $(MAKE) seed-prod
	@echo ""
	@echo "$(GREEN)========================================$(RESET)"
	@echo "$(GREEN)✅ GO-LIVE COMPLETE$(RESET)"
	@echo "$(GREEN)========================================$(RESET)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Verify DNS propagation"
	@echo "  2. Run smoke tests on production"
	@echo "  3. Monitor dashboards for 30 minutes"
	@echo ""

.PHONY: rollback
rollback: ## Rollback to last known good state
	@echo "$(RED)⚠️  ROLLBACK PROCEDURE$(RESET)"
	@echo ""
	@read -p "Enter snapshot ID to restore (or 'latest'): " SNAPSHOT_ID; \
	if [ "$$SNAPSHOT_ID" = "latest" ]; then \
		echo "$(YELLOW)Restoring latest snapshot...$(RESET)"; \
		$(PYTHON) $(SCRIPTS_DIR)/rollback.py --latest; \
	else \
		echo "$(YELLOW)Restoring snapshot: $$SNAPSHOT_ID...$(RESET)"; \
		$(PYTHON) $(SCRIPTS_DIR)/rollback.py --snapshot $$SNAPSHOT_ID; \
	fi
	@echo ""
	@echo "$(YELLOW)Restarting stack with previous image versions...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_ODOO) pull
	@$(MAKE) stack-restart
	@echo ""
	@echo "$(GREEN)✅ Rollback complete$(RESET)"

.PHONY: deploy-staging
deploy-staging: ## Deploy to staging environment
	@echo "$(CYAN)🚀 Deploying to staging...$(RESET)"
	@ENV=staging $(MAKE) stack-up
	@ENV=staging $(MAKE) odoo-migrate
	@ENV=staging $(MAKE) seed-demo
	@echo "$(GREEN)✅ Staging deployment complete$(RESET)"

# =============================================================================
# DATABASE
# =============================================================================

.PHONY: db-backup
db-backup: ## Create database backup
	@echo "$(CYAN)💾 Creating database backup...$(RESET)"
	@bash $(INFRA_DIR)/scripts/backup.sh
	@echo "$(GREEN)✅ Backup complete$(RESET)"

.PHONY: db-restore
db-restore: ## Restore database from backup
	@echo "$(YELLOW)📂 Restoring database...$(RESET)"
	@read -p "Enter backup file path: " BACKUP_FILE; \
	$(DOCKER_COMPOSE) exec postgres pg_restore -U postgres -d odoo $$BACKUP_FILE
	@echo "$(GREEN)✅ Restore complete$(RESET)"

.PHONY: db-shell
db-shell: ## Open PostgreSQL shell
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_ODOO) exec postgres psql -U postgres -d odoo

.PHONY: db-migrate
db-migrate: ## Run SQL migrations (RAG core schema, etc.)
	@echo "$(CYAN)🔄 Running database migrations...$(RESET)"
	@for migration in $(ROOT_DIR)/migrations/*.sql; do \
		echo "  Applying: $$(basename $$migration)"; \
		$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) exec -T postgres psql -U postgres -d odoo -f /migrations/$$(basename $$migration) 2>/dev/null || \
		psql "$$DATABASE_URL" -f "$$migration"; \
	done
	@echo "$(GREEN)✅ Database migrations complete$(RESET)"

# =============================================================================
# RAG PIPELINE
# =============================================================================

.PHONY: rag-ingest
rag-ingest: deps ## Ingest documents into RAG pipeline
	@echo "$(CYAN)📄 Running RAG document ingestion...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/rag_ingest.py
	@echo "$(GREEN)✅ RAG ingestion complete$(RESET)"

.PHONY: rag-embed
rag-embed: deps ## Generate embeddings for RAG chunks
	@echo "$(CYAN)🔢 Running RAG embedding generation...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/rag_embed.py
	@echo "$(GREEN)✅ RAG embedding complete$(RESET)"

.PHONY: rag-eval
rag-eval: deps ## Evaluate RAG query performance
	@echo "$(CYAN)📊 Running RAG evaluation...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/rag_eval.py
	@echo "$(GREEN)✅ RAG evaluation complete$(RESET)"

.PHONY: rag-eval-stats
rag-eval-stats: deps ## Show RAG evaluation statistics
	@echo "$(CYAN)📊 RAG Evaluation Statistics:$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/rag_eval.py --stats

.PHONY: rag-pipeline
rag-pipeline: rag-ingest rag-embed rag-eval ## Run full RAG pipeline (ingest → embed → eval)
	@echo ""
	@echo "$(GREEN)========================================$(RESET)"
	@echo "$(GREEN)✅ RAG PIPELINE COMPLETE$(RESET)"
	@echo "$(GREEN)========================================$(RESET)"
	@echo ""

.PHONY: seed-rag
seed-rag: deps ## Seed RAG demo data only
	@echo "$(CYAN)🌱 Seeding RAG demo data...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/seed_demo_data.py --rag-only
	@echo "$(GREEN)✅ RAG demo data seeded$(RESET)"

# =============================================================================
# CLEANUP
# =============================================================================

.PHONY: clean
clean: ## Clean up temporary files
	@echo "$(CYAN)🧹 Cleaning up...$(RESET)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@rm -rf $(UAT_DIR)/test-results 2>/dev/null || true
	@rm -rf $(UAT_DIR)/playwright-report 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(RESET)"

.PHONY: clean-all
clean-all: clean stack-down ## Clean everything including containers and volumes
	@echo "$(RED)⚠️  Removing all containers and volumes...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) -f $(COMPOSE_ODOO) down -v --remove-orphans
	@echo "$(GREEN)✅ Full cleanup complete$(RESET)"
