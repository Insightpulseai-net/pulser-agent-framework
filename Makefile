# Makefile at repo root

.PHONY: db-migrate db-migrate-ci db-schema-dump docs-schema-md docs-filetree seed-demo-data

# Default local DB URL (override via env if needed)
DB_URL ?= postgres://postgres:postgres@localhost:5432/archi_agent

# Apply all SQL migrations using scripts/migrate.py
db-migrate:
	@echo "Applying migrations to $(DB_URL)"
	python scripts/migrate.py --dsn "$(DB_URL)"

# CI variant (same for now; you can add flags later)
db-migrate-ci:
	@echo "Applying migrations in CI to $(DB_URL)"
	python scripts/migrate.py --dsn "$(DB_URL)"

# Dump schema-only SQL to db/schema.sql
db-schema-dump:
	@mkdir -p db
	@echo "Dumping schema from $(DB_URL) to db/schema.sql"
	pg_dump --schema-only --no-owner --no-privileges "$(DB_URL)" > db/schema.sql

# Generate markdown docs from db/schema.sql (stub-friendly)
docs-schema-md:
	@mkdir -p docs
	@if [ -f scripts/schema_to_md.py ]; then \
	  echo "Generating docs/SCHEMA.md from db/schema.sql"; \
	  python scripts/schema_to_md.py db/schema.sql > docs/SCHEMA.md; \
	else \
	  echo "scripts/schema_to_md.py not found, creating placeholder docs/SCHEMA.md"; \
	  echo "# Schema Documentation (placeholder)" > docs/SCHEMA.md; \
	fi

# Inject auto-generated file tree into README.md between markers
docs-filetree:
	@if [ -f scripts/inject_tree.py ]; then \
	  echo "Injecting repo file tree into README.md"; \
	  python scripts/inject_tree.py README.md; \
	else \
	  echo "scripts/inject_tree.py not found, skipping file tree injection"; \
	fi

# Seed demo data into DB
seed-demo-data:
	@echo "Seeding demo data into $(DB_URL)"
	python scripts/seed_demo_data.py --dsn "$(DB_URL)"
