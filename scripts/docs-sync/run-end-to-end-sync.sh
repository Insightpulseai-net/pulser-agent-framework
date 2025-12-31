#!/bin/bash
# =============================================================================
# End-to-End Google Docs Sync - Complete CLI Automation
# =============================================================================
#
# This script executes the complete sync workflow:
# 1. Share Google Doc with service account
# 2. Verify service account access
# 3. Trigger GitHub workflow
# 4. Monitor workflow execution
# 5. Verify synced content
#
# Prerequisites:
# - client_oauth.json (OAuth Desktop Client) in repo root
# - .venv with google-api-python-client installed
# - GITHUB_TOKEN environment variable set
#
# Usage:
#   ./scripts/docs-sync/run-end-to-end-sync.sh
#
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}Google Docs Sync - End-to-End CLI Automation${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""

# Configuration
SA_EMAIL="ipai-docs2code-runner@gen-lang-client-0909706188.iam.gserviceaccount.com"
DRIVE_IDS="1Qp4nf8nl7M8MnaNtmrBgP4B1mw2aSUqEzYMKmFBCzH4"
REPO="Insightpulseai-net/pulser-agent-framework"
BRANCH="claude/data-engineering-workbench-01Pk6KXASta9H4oeCMY8EBAE"
WF="sync-google-docs.yml"

# Check prerequisites
echo -e "${BLUE}[1/5] Checking prerequisites...${NC}"

if [ ! -f "$PROJECT_ROOT/client_oauth.json" ]; then
    echo -e "${RED}❌ client_oauth.json not found${NC}"
    echo ""
    echo "Please create OAuth Desktop Client:"
    echo "1. Go to: https://console.cloud.google.com/apis/credentials?project=gen-lang-client-0909706188"
    echo "2. Create 'Desktop app' OAuth client"
    echo "3. Download JSON → save as 'client_oauth.json' in repo root"
    exit 1
fi

if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found, creating...${NC}"
    python3 -m venv "$PROJECT_ROOT/.venv"
fi

source "$PROJECT_ROOT/.venv/bin/activate"

echo -e "${GREEN}✅ Prerequisites OK${NC}"
echo ""

# Share document with service account
echo -e "${BLUE}[2/5] Sharing Google Doc with service account...${NC}"

export SA_EMAIL="$SA_EMAIL"
export DRIVE_IDS="$DRIVE_IDS"

cd "$PROJECT_ROOT"
python scripts/docs-sync/share_drive.py

echo -e "${GREEN}✅ Document shared${NC}"
echo ""

# Verify access
echo -e "${BLUE}[3/5] Verifying service account access...${NC}"

export GOOGLE_APPLICATION_CREDENTIALS="$PROJECT_ROOT/secrets/ipai-docs2code-runner.json"

if python scripts/docs-sync/verify_sa_access.py; then
    echo -e "${GREEN}✅ Service account can access document${NC}"
else
    echo -e "${RED}❌ Service account cannot access document${NC}"
    echo "Please check Drive sharing permissions"
    exit 1
fi
echo ""

# Trigger workflow
echo -e "${BLUE}[4/5] Triggering GitHub workflow...${NC}"

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}❌ GITHUB_TOKEN not set${NC}"
    exit 1
fi

gh workflow run "$WF" -R "$REPO" --ref "$BRANCH"

echo -e "${GREEN}✅ Workflow triggered${NC}"
echo ""

# Monitor workflow
echo -e "${BLUE}[5/5] Monitoring workflow execution...${NC}"
echo "Waiting for workflow to start..."
sleep 10

RUN_ID=$(gh run list -R "$REPO" --workflow "$WF" --limit 1 --json databaseId --jq '.[0].databaseId')

if [ -z "$RUN_ID" ]; then
    echo -e "${RED}❌ Could not find workflow run${NC}"
    exit 1
fi

echo "Workflow Run ID: $RUN_ID"
echo "Watching logs..."
echo ""

gh run watch -R "$REPO" "$RUN_ID"

echo ""
echo -e "${GREEN}✅ Workflow completed${NC}"
echo ""

# Verify result
echo -e "${BLUE}Verifying synced content...${NC}"

git fetch origin

if git show "origin/$BRANCH:docs/testing/COMPREHENSIVE_TESTING_STRATEGY.md" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Synced file exists${NC}"
    echo ""
    echo "Preview (first 20 lines):"
    git show "origin/$BRANCH:docs/testing/COMPREHENSIVE_TESTING_STRATEGY.md" | head -20
else
    echo -e "${YELLOW}⚠️  File not found (may not have changed)${NC}"
fi

echo ""
echo -e "${BLUE}==============================================================================${NC}"
echo -e "${GREEN}End-to-End Sync Complete!${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""
echo "Next steps:"
echo "1. Review the PR created by the workflow"
echo "2. Merge the PR to apply changes to main branch"
echo ""
