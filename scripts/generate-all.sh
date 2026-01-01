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
NC='\033[0m' # No Color

log_info() { echo -e "${CYAN}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
SPEC_FILE="${PROJECT_ROOT}/specs/openapi/openapi.yaml"
OUTPUT_DIR="${PROJECT_ROOT}/generated"
CONFIG_DIR="${PROJECT_ROOT}/config"

# Check dependencies
check_deps() {
    log_info "Checking dependencies..."

    if ! command -v openapi-generator-cli &> /dev/null; then
        log_warn "openapi-generator-cli not found, installing..."
        npm install -g @openapitools/openapi-generator-cli
    fi

    if ! command -v buf &> /dev/null; then
        log_warn "buf not found, please install from https://buf.build"
    fi
}

# Validate specs before generation
validate_specs() {
    log_info "Validating specifications..."

    if [ -f "$SPEC_FILE" ]; then
        if command -v redocly &> /dev/null; then
            redocly lint "$SPEC_FILE" || log_warn "OpenAPI linting failed"
        fi
    fi

    if [ -d "${PROJECT_ROOT}/specs/protobuf" ] && command -v buf &> /dev/null; then
        (cd "${PROJECT_ROOT}/specs/protobuf" && buf lint) || log_warn "Protobuf linting failed"
    fi

    log_success "Specification validation complete"
}

# Generate Python client
generate_python() {
    log_info "Generating Python client..."

    local config="${CONFIG_DIR}/openapi-generator-python.yaml"
    local output="${OUTPUT_DIR}/clients/python"

    mkdir -p "$output"

    if [ -f "$config" ]; then
        openapi-generator-cli generate \
            -i "$SPEC_FILE" \
            -g python \
            -o "$output" \
            -c "$config" \
            --skip-validate-spec
    else
        openapi-generator-cli generate \
            -i "$SPEC_FILE" \
            -g python \
            -o "$output" \
            --additional-properties=packageName=ipai_client,projectName=ipai-client \
            --skip-validate-spec
    fi

    log_success "Python client generated at $output"
}

# Generate TypeScript client
generate_typescript() {
    log_info "Generating TypeScript client..."

    local config="${CONFIG_DIR}/openapi-generator-typescript.yaml"
    local output="${OUTPUT_DIR}/clients/typescript"

    mkdir -p "$output"

    if [ -f "$config" ]; then
        openapi-generator-cli generate \
            -i "$SPEC_FILE" \
            -g typescript-fetch \
            -o "$output" \
            -c "$config" \
            --skip-validate-spec
    else
        openapi-generator-cli generate \
            -i "$SPEC_FILE" \
            -g typescript-fetch \
            -o "$output" \
            --additional-properties=npmName=@ipai/api-client,supportsES6=true \
            --skip-validate-spec
    fi

    log_success "TypeScript client generated at $output"
}

# Generate Go client
generate_go() {
    log_info "Generating Go client..."

    local config="${CONFIG_DIR}/openapi-generator-go.yaml"
    local output="${OUTPUT_DIR}/clients/go"

    mkdir -p "$output"

    if [ -f "$config" ]; then
        openapi-generator-cli generate \
            -i "$SPEC_FILE" \
            -g go \
            -o "$output" \
            -c "$config" \
            --skip-validate-spec
    else
        openapi-generator-cli generate \
            -i "$SPEC_FILE" \
            -g go \
            -o "$output" \
            --additional-properties=packageName=ipaiclient,isGoSubmodule=true \
            --skip-validate-spec
    fi

    log_success "Go client generated at $output"
}

# Generate from Protobuf
generate_proto() {
    log_info "Generating from Protobuf..."

    if ! command -v buf &> /dev/null; then
        log_error "buf is required for protobuf generation"
        return 1
    fi

    local proto_dir="${PROJECT_ROOT}/specs/protobuf"
    local buf_config="${CONFIG_DIR}/buf.gen.yaml"

    if [ -d "$proto_dir" ] && [ -f "$buf_config" ]; then
        buf generate "$proto_dir" --template "$buf_config"
        log_success "Protobuf code generated"
    else
        log_warn "Protobuf directory or buf.gen.yaml not found, skipping"
    fi
}

# Main execution
main() {
    log_info "Starting code generation..."
    log_info "Project root: $PROJECT_ROOT"

    check_deps
    validate_specs

    # Parse arguments
    local generate_all=true
    for arg in "$@"; do
        case $arg in
            --python)
                generate_all=false
                generate_python
                ;;
            --typescript)
                generate_all=false
                generate_typescript
                ;;
            --go)
                generate_all=false
                generate_go
                ;;
            --proto)
                generate_all=false
                generate_proto
                ;;
            --help)
                echo "Usage: $0 [--python] [--typescript] [--go] [--proto]"
                echo "  --python     Generate Python client only"
                echo "  --typescript Generate TypeScript client only"
                echo "  --go         Generate Go client only"
                echo "  --proto      Generate Protobuf code only"
                echo "  (no args)    Generate all clients"
                exit 0
                ;;
        esac
    done

    if [ "$generate_all" = true ]; then
        generate_python
        generate_typescript
        generate_go
        generate_proto
    fi

    log_success "Code generation complete!"
}

main "$@"
