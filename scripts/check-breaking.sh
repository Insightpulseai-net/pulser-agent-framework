#!/usr/bin/env bash
# GENERATED FILE - DO NOT EDIT MANUALLY
# Source: docs-to-code-pipeline
# Generated: 2026-01-01T00:00:00Z
# Regenerate: Managed by repository template

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${CYAN}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[BREAKING]${NC} $1"; }

BASE_BRANCH="${1:-main}"
BREAKING_FOUND=0

# Check OpenAPI breaking changes
check_openapi_breaking() {
    log_info "Checking OpenAPI for breaking changes against $BASE_BRANCH..."

    local spec_file="${PROJECT_ROOT}/specs/openapi/openapi.yaml"

    if [ ! -f "$spec_file" ]; then
        log_warn "OpenAPI spec not found, skipping"
        return 0
    fi

    if ! command -v oasdiff &> /dev/null; then
        log_warn "oasdiff not installed, installing..."
        go install github.com/tufin/oasdiff@latest 2>/dev/null || {
            log_error "Failed to install oasdiff, skipping OpenAPI breaking check"
            return 0
        }
    fi

    # Get base spec from git
    local base_spec
    base_spec=$(mktemp)
    if git show "origin/${BASE_BRANCH}:specs/openapi/openapi.yaml" > "$base_spec" 2>/dev/null; then
        # Check for breaking changes
        local result
        result=$(oasdiff breaking "$base_spec" "$spec_file" --format text 2>&1) || true

        if [ -n "$result" ] && [ "$result" != "No breaking changes" ]; then
            log_error "OpenAPI breaking changes detected:"
            echo "$result"
            BREAKING_FOUND=1
        else
            log_success "No OpenAPI breaking changes"
        fi

        rm -f "$base_spec"
    else
        log_warn "Could not get base spec from $BASE_BRANCH (new file?)"
    fi
}

# Check Protobuf breaking changes
check_protobuf_breaking() {
    log_info "Checking Protobuf for breaking changes against $BASE_BRANCH..."

    local proto_dir="${PROJECT_ROOT}/specs/protobuf"

    if [ ! -d "$proto_dir" ]; then
        log_warn "Protobuf directory not found, skipping"
        return 0
    fi

    if ! command -v buf &> /dev/null; then
        log_warn "buf not installed, skipping protobuf breaking check"
        return 0
    fi

    # Check against base branch
    local result
    result=$(cd "$proto_dir" && buf breaking --against "../../.git#branch=${BASE_BRANCH},subdir=specs/protobuf" 2>&1) || true

    if [ -n "$result" ]; then
        log_error "Protobuf breaking changes detected:"
        echo "$result"
        BREAKING_FOUND=1
    else
        log_success "No Protobuf breaking changes"
    fi
}

# Summary
print_summary() {
    echo ""
    echo "=================================="
    if [ $BREAKING_FOUND -eq 0 ]; then
        log_success "No breaking changes detected"
    else
        log_error "Breaking changes were detected!"
        echo ""
        echo "To proceed with breaking changes:"
        echo "  1. Update API version (e.g., /v1 -> /v2)"
        echo "  2. Add 'breaking-change-approved' label to PR"
        echo "  3. Document migration path"
    fi
    echo "=================================="
}

# Main execution
main() {
    log_info "Checking for breaking changes against: $BASE_BRANCH"
    log_info "Project root: $PROJECT_ROOT"

    check_openapi_breaking
    check_protobuf_breaking

    print_summary

    exit $BREAKING_FOUND
}

main "$@"
