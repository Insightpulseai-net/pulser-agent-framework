#!/usr/bin/env bash
# Generate Odoo modules from JSON Schema specifications
#
# Usage:
#   scripts/generate-odoo-from-schema.sh
#   OUT_DIR=./custom-addons scripts/generate-odoo-from-schema.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${OUT_DIR:-${ROOT}/addons}"

mkdir -p "${OUT_DIR}"

# Deterministic timestamp for generated headers
# If SOURCE_DATE_EPOCH is set (e.g., by CI), use it; otherwise default to 0
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-0}"

echo "[odoo-gen] output_dir=${OUT_DIR}"
echo "[odoo-gen] source_date_epoch=${SOURCE_DATE_EPOCH}"

shopt -s nullglob
SCHEMAS=("${ROOT}"/specs/ipai_*.schema.json)
shopt -u nullglob

if [ ${#SCHEMAS[@]} -eq 0 ]; then
  echo "[odoo-gen] no specs/ipai_*.schema.json found; skipping"
  exit 0
fi

for s in "${SCHEMAS[@]}"; do
  echo "[odoo-gen] generating from ${s}"
  python3 "${ROOT}/generators/schema_to_odoo.py" --schema "${s}" --out "${OUT_DIR}"
done

echo "[odoo-gen] done -> ${OUT_DIR}"
echo "[odoo-gen] generated ${#SCHEMAS[@]} module(s)"
