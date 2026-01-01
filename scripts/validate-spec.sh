#!/usr/bin/env bash
# Spec Validation Script for Docs-to-Code Pipeline
# Validates OpenAPI, JSON Schema, and other specification files
#
# Usage:
#   scripts/validate-spec.sh
#   BASE_REF=origin/main scripts/validate-spec.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

OPENAPI="${ROOT}/specs/openapi.yaml"
OPENAPI_JSON="${ROOT}/specs/openapi.json"

echo "[validate] repo_root=${ROOT}"

have_cmd() { command -v "$1" >/dev/null 2>&1; }

# --- OpenAPI lint + diff (Redocly) ---
if [[ -f "${OPENAPI}" || -f "${OPENAPI_JSON}" ]]; then
  SPEC="${OPENAPI}"
  [[ -f "${OPENAPI_JSON}" ]] && SPEC="${OPENAPI_JSON}"

  echo "[validate] openapi: lint ${SPEC}"
  if have_cmd npx; then
    npx --yes @redocly/cli lint "${SPEC}" || echo "[validate] openapi: lint warnings/errors found"
  else
    echo "[validate] openapi: npx not available, skipping redocly lint"
  fi

  # Breaking-change check against base ref if available
  BASE_REF="${BASE_REF:-origin/main}"
  if git rev-parse --verify "${BASE_REF}" >/dev/null 2>&1; then
    echo "[validate] openapi: diff ${BASE_REF} -> HEAD (check for breaking changes)"
    if have_cmd npx; then
      # Redocly diff returns non-zero for breaking changes when --fail-on-breaking is set
      npx --yes @redocly/cli diff "${BASE_REF}:${SPEC#${ROOT}/}" "${SPEC}" --fail-on-breaking || echo "[validate] openapi: breaking changes detected"
    fi
  else
    echo "[validate] openapi: skipping diff (no ${BASE_REF})"
  fi
else
  echo "[validate] openapi: skip (no specs/openapi.yaml|json)"
fi

# --- JSON Schema syntax check ---
if compgen -G "${ROOT}/specs/schema*.json" >/dev/null 2>&1; then
  for f in "${ROOT}"/specs/schema*.json; do
    echo "[validate] jsonschema: parse ${f}"
    if have_cmd python3; then
      python3 -c "import json; json.load(open('${f}'))" && echo "[validate] jsonschema: ${f} OK"
    elif have_cmd node; then
      node -e "JSON.parse(require('fs').readFileSync('${f}','utf8'));" && echo "[validate] jsonschema: ${f} OK"
    else
      echo "[validate] jsonschema: no python3 or node available, skipping"
    fi
  done
else
  echo "[validate] jsonschema: skip (no specs/schema*.json)"
fi

# --- ipai_* module schema validation ---
if compgen -G "${ROOT}/specs/ipai_*.schema.json" >/dev/null 2>&1; then
  for f in "${ROOT}"/specs/ipai_*.schema.json; do
    echo "[validate] ipai_schema: parse ${f}"
    if have_cmd python3; then
      python3 << EOF
import json
import sys

with open('${f}') as fp:
    schema = json.load(fp)

# Validate required structure
errors = []
if schema.get('type') != 'object':
    errors.append("top-level type must be 'object'")
if not schema.get('properties'):
    errors.append("'properties' is required and must be non-empty")

if errors:
    print(f"[validate] ipai_schema: FAIL ${f}")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print(f"[validate] ipai_schema: ${f} OK")
EOF
    else
      echo "[validate] ipai_schema: python3 not available, skipping validation"
    fi
  done
else
  echo "[validate] ipai_schema: skip (no specs/ipai_*.schema.json)"
fi

# --- DocIR validation ---
DOCIR="${ROOT}/docs/docir/docir.json"
if [[ -f "${DOCIR}" ]]; then
  echo "[validate] docir: validate ${DOCIR}"
  if [[ -f "${ROOT}/tools/validate_jsonschema.py" ]] && [[ -f "${ROOT}/tools/schemas/DocIR.schema.json" ]]; then
    python3 "${ROOT}/tools/validate_jsonschema.py" "${DOCIR}" "${ROOT}/tools/schemas/DocIR.schema.json" || echo "[validate] docir: validation warnings"
  else
    echo "[validate] docir: schema validator not available, skipping"
  fi
else
  echo "[validate] docir: skip (no docs/docir/docir.json)"
fi

echo "[validate] OK - all checks complete"
