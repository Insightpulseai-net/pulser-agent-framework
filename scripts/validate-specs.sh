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
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; }

ERRORS=0

# Validate OpenAPI spec
validate_openapi() {
    log_info "Validating OpenAPI specification..."

    local spec_file="${PROJECT_ROOT}/specs/openapi/openapi.yaml"

    if [ ! -f "$spec_file" ]; then
        log_warn "OpenAPI spec not found at $spec_file"
        return 0
    fi

    # Lint with redocly if available
    if command -v redocly &> /dev/null; then
        if redocly lint "$spec_file" --format stylish; then
            log_success "OpenAPI lint passed"
        else
            log_error "OpenAPI lint failed"
            ((ERRORS++))
        fi
    else
        log_warn "redocly not installed, skipping OpenAPI lint"
    fi

    # Validate with swagger-cli if available
    if command -v swagger-cli &> /dev/null; then
        if swagger-cli validate "$spec_file"; then
            log_success "OpenAPI schema validation passed"
        else
            log_error "OpenAPI schema validation failed"
            ((ERRORS++))
        fi
    fi
}

# Validate AsyncAPI spec
validate_asyncapi() {
    log_info "Validating AsyncAPI specification..."

    local spec_dir="${PROJECT_ROOT}/specs/asyncapi"

    if [ ! -d "$spec_dir" ]; then
        log_warn "AsyncAPI directory not found"
        return 0
    fi

    if ! command -v asyncapi &> /dev/null; then
        log_warn "asyncapi CLI not installed, skipping validation"
        return 0
    fi

    for file in "$spec_dir"/*.yaml "$spec_dir"/*.yml; do
        if [ -f "$file" ]; then
            log_info "Validating $file"
            if asyncapi validate "$file"; then
                log_success "AsyncAPI validation passed: $file"
            else
                log_error "AsyncAPI validation failed: $file"
                ((ERRORS++))
            fi
        fi
    done
}

# Validate Protobuf
validate_protobuf() {
    log_info "Validating Protobuf definitions..."

    local proto_dir="${PROJECT_ROOT}/specs/protobuf"

    if [ ! -d "$proto_dir" ]; then
        log_warn "Protobuf directory not found"
        return 0
    fi

    if ! command -v buf &> /dev/null; then
        log_warn "buf not installed, skipping protobuf validation"
        return 0
    fi

    if (cd "$proto_dir" && buf lint); then
        log_success "Protobuf lint passed"
    else
        log_error "Protobuf lint failed"
        ((ERRORS++))
    fi
}

# Validate JSON Schemas
validate_json_schemas() {
    log_info "Validating JSON Schemas..."

    local schema_dir="${PROJECT_ROOT}/specs/json-schema"
    local artifact_schema="${PROJECT_ROOT}/specs/artifacts/artifact_envelope.schema.json"

    if ! command -v ajv &> /dev/null; then
        log_warn "ajv-cli not installed, skipping JSON Schema validation"
        return 0
    fi

    # Validate schemas in json-schema directory
    if [ -d "$schema_dir" ]; then
        for schema in "$schema_dir"/*.schema.json; do
            if [ -f "$schema" ]; then
                log_info "Validating $schema"
                if ajv compile -s "$schema" --spec=draft2020 -c ajv-formats 2>/dev/null; then
                    log_success "JSON Schema valid: $schema"
                else
                    log_error "JSON Schema invalid: $schema"
                    ((ERRORS++))
                fi
            fi
        done
    fi

    # Validate artifact envelope schema
    if [ -f "$artifact_schema" ]; then
        log_info "Validating artifact envelope schema"
        if ajv compile -s "$artifact_schema" --spec=draft2020 -c ajv-formats 2>/dev/null; then
            log_success "Artifact envelope schema valid"
        else
            log_error "Artifact envelope schema invalid"
            ((ERRORS++))
        fi
    fi
}

# Summary
print_summary() {
    echo ""
    echo "=================================="
    if [ $ERRORS -eq 0 ]; then
        log_success "All validations passed!"
    else
        log_error "$ERRORS validation(s) failed"
    fi
    echo "=================================="
}

# Main execution
main() {
    log_info "Starting specification validation..."
    log_info "Project root: $PROJECT_ROOT"

    validate_openapi
    validate_asyncapi
    validate_protobuf
    validate_json_schemas

    print_summary

    exit $ERRORS
}

main "$@"
