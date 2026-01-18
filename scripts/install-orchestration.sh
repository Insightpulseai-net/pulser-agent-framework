#!/bin/bash

# ============================================================================
# Pulser Agent Framework - Orchestration Tools Installer
# ============================================================================
# Installs: GSD, Claude Code extensions, Pulser skill overlays
# Usage: ./install-orchestration.sh [--global|--local]
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Determine install scope
SCOPE="${1:---global}"
if [ "$SCOPE" == "--global" ] || [ "$SCOPE" == "-g" ]; then
    CLAUDE_DIR="$HOME/.claude"
    log_info "Installing globally to ~/.claude/"
elif [ "$SCOPE" == "--local" ] || [ "$SCOPE" == "-l" ]; then
    CLAUDE_DIR="./.claude"
    log_info "Installing locally to ./.claude/"
else
    log_error "Unknown option: $SCOPE. Use --global or --local"
    exit 1
fi

mkdir -p "$CLAUDE_DIR/commands"

# ============================================================================
# 1. Install GSD (Get Shit Done)
# ============================================================================

log_info "Checking GSD installation..."

if command -v npx &> /dev/null; then
    if [ ! -f "$CLAUDE_DIR/commands/gsd.md" ]; then
        log_info "Installing GSD..."
        npx get-shit-done-cc@latest "$SCOPE"
        log_success "GSD installed"
    else
        log_success "GSD already installed"
        log_info "Checking for updates..."
        npx get-shit-done-cc@latest "$SCOPE" 2>/dev/null || log_warn "Update check failed, continuing..."
    fi
else
    log_error "npx not found. Install Node.js first."
    exit 1
fi

# ============================================================================
# 2. Create Claude Code permissions for automation
# ============================================================================

log_info "Configuring automation permissions..."

SETTINGS_FILE="$CLAUDE_DIR/settings.json"
if [ ! -f "$SETTINGS_FILE" ]; then
    cat > "$SETTINGS_FILE" << 'EOF'
{
  "permissions": {
    "allow": [
      "Bash(date:*)",
      "Bash(echo:*)",
      "Bash(cat:*)",
      "Bash(ls:*)",
      "Bash(mkdir:*)",
      "Bash(rm:*)",
      "Bash(cp:*)",
      "Bash(mv:*)",
      "Bash(wc:*)",
      "Bash(head:*)",
      "Bash(tail:*)",
      "Bash(sort:*)",
      "Bash(grep:*)",
      "Bash(sed:*)",
      "Bash(awk:*)",
      "Bash(tr:*)",
      "Bash(find:*)",
      "Bash(xargs:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git status:*)",
      "Bash(git log:*)",
      "Bash(git diff:*)",
      "Bash(git tag:*)",
      "Bash(git push:*)",
      "Bash(git pull:*)",
      "Bash(git checkout:*)",
      "Bash(git branch:*)",
      "Bash(git merge:*)",
      "Bash(git stash:*)",
      "Bash(docker:*)",
      "Bash(docker compose:*)",
      "Bash(npm:*)",
      "Bash(npx:*)",
      "Bash(pip:*)",
      "Bash(pip3:*)",
      "Bash(python:*)",
      "Bash(python3:*)",
      "Bash(node:*)",
      "Bash(curl:*)",
      "Bash(wget:*)",
      "Bash(jq:*)"
    ]
  }
}
EOF
    log_success "Created settings.json with automation permissions"
else
    log_success "settings.json already exists"
fi

# ============================================================================
# 3. Install Pulser-specific commands
# ============================================================================

log_info "Installing Pulser skill overlay..."

cat > "$CLAUDE_DIR/commands/pulser.md" << 'EOF'
---
name: pulser
description: Pulser Agent Framework commands for InsightPulse ERP stack
---

# Pulser Framework Commands

## Commands

### /pulser:init

Initialize Pulser session with context verification.

```
- Verify GSD installation
- Check Docker services
- Load project context
- Confirm agent availability
```

### /pulser:odoo <module|migrate|test|deploy>

Odoo 18 CE operations for ipai_* modules.

- `module <name>`: Scaffold new ipai_<name> module
- `migrate`: Run pending migrations
- `test`: Execute module tests
- `deploy`: Deploy to staging/production

### /pulser:bir <1601-C|2550Q|1702-RT|audit>

BIR compliance automation.

- `1601-C`: Monthly withholding tax
- `2550Q`: Quarterly VAT
- `1702-RT`: Annual income tax (regular)
- `audit`: Generate audit trail report

### /pulser:superset <sync|deploy|export>

Apache Superset dashboard operations.

- `sync`: Sync datasets from Odoo
- `deploy`: Push dashboards to production
- `export`: Export dashboard configs

### /pulser:agents

List active Pulser agents and status:

- Claudia (Planner)
- Caca (Coder)
- Basher (DevOps)
- Echo (Validator)
- Dash (Dashboard)

### /pulser:delegate <agent> <task>

Delegate task to specific agent with context handoff.

### /pulser:status

Show current session state, active tasks, and pending items.

## Integration with GSD

Pulser extends GSD phases:

- `/gsd:plan` -> Claudia enriches with Odoo/BIR context
- `/gsd:build` -> Caca follows ipai_* conventions
- `/gsd:debug` -> Basher uses Docker logs
- `/gsd:verify` -> Echo runs BIR compliance checks
- `/gsd:ship` -> Dash triggers CI/CD pipeline
EOF

log_success "Pulser commands installed"

# ============================================================================
# 4. Install Odoo-specific commands
# ============================================================================

log_info "Installing Odoo skill overlay..."

cat > "$CLAUDE_DIR/commands/odoo.md" << 'EOF'
---
name: odoo
description: Odoo 18 CE development commands following Smart Delta / ipai_* conventions
---

# Odoo Development Commands

## Commands

### /odoo:scaffold <module_name>

Create new ipai_<module_name> module with:

- __manifest__.py (AGPL-3, OCA-style)
- models/, views/, security/
- ir.model.access.csv
- README.md (marketplace-ready)

### /odoo:upgrade <module>

Upgrade module in development container:

```bash
docker exec -it odoo-dev odoo -d odoo -u <module> --stop-after-init
```

### /odoo:test <module>

Run module tests:

```bash
docker exec -it odoo-dev odoo -d test_db -i <module> --test-enable --stop-after-init
```

### /odoo:lint

Run pre-commit hooks (OCA conventions):

```bash
pre-commit run --all-files
```

### /odoo:migrate

Apply pending database migrations safely.

### /odoo:shell

Open Odoo shell in container:

```bash
docker exec -it odoo-dev odoo shell -d odoo
```

## Conventions

- All custom modules: `ipai_<functional_area>`
- Use `_inherit` not model replacement
- Views use `<list>` not deprecated `<tree>`
- view_mode: "list,form" not "tree,form"
EOF

log_success "Odoo commands installed"

# ============================================================================
# 5. Create CLAUDE.md if not exists
# ============================================================================

log_info "Checking CLAUDE.md..."

CLAUDE_MD="./CLAUDE.md"
if [ ! -f "$CLAUDE_MD" ]; then
    cat > "$CLAUDE_MD" << 'EOF'
# Project Context

## Stack

- Odoo 18 CE + OCA modules
- ipai_* custom modules (Smart Delta)
- Docker + docker-compose
- Apache Superset (BI)
- PostgreSQL

## Frameworks

- GSD (Get Shit Done) - `/gsd:help`
- Pulser Agent Framework - `/pulser:status`

## Development

```bash
# Start dev environment
cd sandbox/dev && docker compose up -d

# Upgrade module
docker exec -it odoo-dev odoo -d odoo -u ipai_<module> --stop-after-init

# Run Claude Code with automation
claude --dangerously-skip-permissions
```

## Conventions

- Modules: ipai_<name>, AGPL-3, OCA-style
- Views: `<list>` not `<tree>`
- Git: Conventional commits
- Deploy: Version-pinned images only
EOF
    log_success "Created CLAUDE.md"
else
    log_success "CLAUDE.md already exists"
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "=============================================="
echo -e "${GREEN}Orchestration tools installed${NC}"
echo "=============================================="
echo ""
echo "Installed to: $CLAUDE_DIR"
echo ""
echo "Commands available:"
echo "  /gsd:help      - GSD framework help"
echo "  /gsd:plan      - Start planning phase"
echo "  /gsd:build     - Start build phase"
echo "  /pulser:init   - Initialize Pulser session"
echo "  /pulser:agents - List active agents"
echo "  /odoo:scaffold - Create new ipai_* module"
echo ""
echo "Start Claude Code with:"
echo -e "  ${YELLOW}claude --dangerously-skip-permissions${NC}"
echo ""
echo "Verify with:"
echo "  /gsd:help"
echo "  /pulser:status"
echo ""
