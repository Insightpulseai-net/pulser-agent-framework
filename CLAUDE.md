# Project Context

## Stack

- Odoo 18 CE + OCA modules
- ipai_* custom modules (Smart Delta)
- Docker + docker-compose
- Apache Superset (BI)
- PostgreSQL
- Supabase (Backend as a Service)

## Frameworks

- GSD (Get Shit Done) - `/gsd:help`
- Pulser Agent Framework - `/pulser:status`

## Pulser Agents

| Agent   | Role      | Responsibility                          |
|---------|-----------|----------------------------------------|
| Claudia | Planner   | Context enrichment, Odoo/BIR planning  |
| Caca    | Coder     | ipai_* module development              |
| Basher  | DevOps    | Docker operations, infrastructure      |
| Echo    | Validator | BIR compliance checks, testing         |
| Dash    | Dashboard | CI/CD triggers, Superset operations    |

## Development

```bash
# Install orchestration tools
./scripts/install-orchestration.sh --global

# Start dev environment
cd sandbox/dev && docker compose up -d

# Upgrade Odoo module
docker exec -it odoo-dev odoo -d odoo -u ipai_<module> --stop-after-init

# Run Claude Code with automation
claude --dangerously-skip-permissions
```

## Quick Start

```bash
# One-liner GSD install
npx get-shit-done-cc@latest --global && echo "GSD ready - run /gsd:help"

# Verify installation
/gsd:help
/pulser:agents
```

## Conventions

- Modules: `ipai_<name>`, AGPL-3, OCA-style
- Views: `<list>` not `<tree>`
- view_mode: `"list,form"` not `"tree,form"`
- Git: Conventional commits
- Deploy: Version-pinned images only

## Key Directories

| Directory    | Purpose                              |
|--------------|--------------------------------------|
| `agents/`    | Pulser agent definitions             |
| `odoo/`      | Odoo modules and configurations      |
| `scripts/`   | Automation and deployment scripts    |
| `specs/`     | API and module specifications        |
| `infra/`     | Infrastructure configurations        |
| `supabase/`  | Supabase migrations and functions    |

## BIR Compliance

The framework supports Philippine BIR tax automation:

- `1601-C`: Monthly withholding tax
- `2550Q`: Quarterly VAT
- `1702-RT`: Annual income tax (regular)
- Audit trail generation

## GSD Phase Mapping

| GSD Phase     | Pulser Agent | Action                        |
|---------------|--------------|-------------------------------|
| `/gsd:plan`   | Claudia      | Enrich with Odoo/BIR context  |
| `/gsd:build`  | Caca         | Follow ipai_* conventions     |
| `/gsd:debug`  | Basher       | Use Docker logs               |
| `/gsd:verify` | Echo         | Run BIR compliance checks     |
| `/gsd:ship`   | Dash         | Trigger CI/CD pipeline        |
