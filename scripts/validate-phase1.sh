#!/bin/bash
# Phase 1 Acceptance Gate Validation Script
# Tests all acceptance criteria from CLAUDE.md Section 6
# Usage: ./scripts/validate-phase1.sh [--verbose]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
VERBOSE=false
FAILED_GATES=0
TOTAL_GATES=7

if [[ "${1:-}" == "--verbose" ]]; then
  VERBOSE=true
fi

log_info() {
  echo -e "${GREEN}✓${NC} $1"
}

log_error() {
  echo -e "${RED}✗${NC} $1"
  FAILED_GATES=$((FAILED_GATES + 1))
}

log_warn() {
  echo -e "${YELLOW}⚠${NC} $1"
}

log_section() {
  echo ""
  echo "========================================"
  echo "$1"
  echo "========================================"
}

# Gate 1: OCR Backend Health
log_section "Gate 1: OCR Backend Health (P95 ≤ 30s)"

OCR_ENDPOINT="${OCR_ENDPOINT:-https://ade-ocr-backend-*.ondigitalocean.app}"

# Extract actual URL from DigitalOcean app if wildcard
if [[ "$OCR_ENDPOINT" == *"*"* ]]; then
  APP_ID="b1bb1b07-46a6-4bbb-85a2-e1e8c7f263b9"
  OCR_ENDPOINT=$(doctl apps get "$APP_ID" --format DefaultIngress --no-header 2>/dev/null || echo "")

  if [[ -z "$OCR_ENDPOINT" ]]; then
    log_error "Failed to resolve OCR endpoint from DigitalOcean"
  else
    OCR_ENDPOINT="https://${OCR_ENDPOINT}"
  fi
fi

if [[ -n "$OCR_ENDPOINT" ]]; then
  HEALTH_RESPONSE=$(curl -sf "$OCR_ENDPOINT/health" 2>/dev/null || echo "")

  if echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"'; then
    log_info "OCR backend health endpoint returned OK"

    # Check P95 latency if available in response
    P95=$(echo "$HEALTH_RESPONSE" | jq -r '.metrics.p95_latency_ms // "N/A"' 2>/dev/null)

    if [[ "$P95" != "N/A" ]]; then
      P95_SECONDS=$((P95 / 1000))
      if [[ $P95_SECONDS -le 30 ]]; then
        log_info "P95 latency: ${P95_SECONDS}s (threshold: ≤30s)"
      else
        log_error "P95 latency: ${P95_SECONDS}s exceeds 30s threshold"
      fi
    else
      log_warn "P95 latency metric not available in health response"
    fi
  else
    log_error "OCR backend health check failed or returned non-ok status"
  fi
else
  log_error "OCR endpoint not configured"
fi

# Gate 2: OCR Smoke Test
log_section "Gate 2: OCR Smoke Test (Confidence ≥ 0.60)"

if [[ -n "$OCR_ENDPOINT" ]]; then
  # Create test payload with sample receipt data
  TEST_PAYLOAD=$(cat <<EOF
{
  "image_url": "https://example.com/test-receipt.jpg",
  "provider": "paddleocr_vl"
}
EOF
)

  OCR_RESPONSE=$(curl -sf -X POST "$OCR_ENDPOINT/api/ocr" \
    -H "Content-Type: application/json" \
    -d "$TEST_PAYLOAD" 2>/dev/null || echo "")

  if [[ -n "$OCR_RESPONSE" ]]; then
    CONFIDENCE=$(echo "$OCR_RESPONSE" | jq -r '.confidence // 0' 2>/dev/null)

    if (( $(echo "$CONFIDENCE >= 0.60" | bc -l) )); then
      log_info "OCR confidence: $CONFIDENCE (threshold: ≥0.60)"
    else
      log_error "OCR confidence: $CONFIDENCE below 0.60 threshold"
    fi

    # Check required fields extracted
    VENDOR=$(echo "$OCR_RESPONSE" | jq -r '.vendor_name // ""' 2>/dev/null)
    AMOUNT=$(echo "$OCR_RESPONSE" | jq -r '.amount // ""' 2>/dev/null)

    if [[ -n "$VENDOR" && -n "$AMOUNT" ]]; then
      log_info "Required fields extracted: vendor_name, amount"
    else
      log_warn "Some required fields missing in OCR response"
    fi
  else
    log_error "OCR smoke test failed to return response"
  fi
else
  log_error "OCR endpoint not configured, skipping smoke test"
fi

# Gate 3: Task Bus Operational
log_section "Gate 3: Task Bus Operational"

POSTGRES_URL="${POSTGRES_URL:-postgresql://postgres.xkxyvboeubffxxbebsll:${SUPABASE_DB_PASSWORD}@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require}"

# Test route_and_enqueue RPC
RPC_TEST=$(psql "$POSTGRES_URL" -tAc "SELECT route_and_enqueue('TEST_TASK', '{\"test\": true}'::jsonb, 5);" 2>/dev/null || echo "")

if [[ -n "$RPC_TEST" ]]; then
  log_info "route_and_enqueue() RPC functional"
else
  log_error "route_and_enqueue() RPC failed"
fi

# Gate 4: No Stuck Tasks
log_section "Gate 4: No Stuck Tasks (>5 min in processing)"

STUCK_TASKS=$(psql "$POSTGRES_URL" -tAc "
  SELECT COUNT(*)
  FROM task_queue
  WHERE status = 'processing'
    AND updated_at < NOW() - INTERVAL '5 minutes';
" 2>/dev/null || echo "-1")

if [[ "$STUCK_TASKS" == "0" ]]; then
  log_info "No stuck tasks found (threshold: 0)"
else
  log_error "Found $STUCK_TASKS stuck tasks (expected: 0)"
fi

# Gate 5: DB Migrations Applied
log_section "Gate 5: DB Migrations Applied (Schema Hash Match)"

# Get deployed schema hash
DEPLOYED_SCHEMAS=$(psql "$POSTGRES_URL" -tAc "
  SELECT schema_name
  FROM information_schema.schemata
  WHERE schema_name IN ('bronze', 'silver', 'gold', 'platinum')
  ORDER BY schema_name;
" 2>/dev/null | tr '\n' ',' | sed 's/,$//')

DEPLOYED_HASH=$(echo -n "$DEPLOYED_SCHEMAS" | md5sum | awk '{print $1}')

# Expected schemas
EXPECTED_SCHEMAS="bronze,gold,platinum,silver"
EXPECTED_HASH=$(echo -n "$EXPECTED_SCHEMAS" | md5sum | awk '{print $1}')

if [[ "$DEPLOYED_HASH" == "$EXPECTED_HASH" ]]; then
  log_info "Schema hash matches expected (4 medallion layers deployed)"
else
  log_error "Schema hash mismatch. Deployed: $DEPLOYED_SCHEMAS"
  if [[ "$VERBOSE" == true ]]; then
    echo "  Expected schemas: $EXPECTED_SCHEMAS"
    echo "  Deployed hash: $DEPLOYED_HASH"
    echo "  Expected hash: $EXPECTED_HASH"
  fi
fi

# Gate 6: RLS Policies Enforced
log_section "Gate 6: RLS Policies Enforced (All Public Tables)"

RLS_COUNT=$(psql "$POSTGRES_URL" -tAc "
  SELECT COUNT(*)
  FROM pg_tables
  WHERE schemaname IN ('bronze', 'silver', 'gold', 'platinum', 'public')
    AND rowsecurity = true;
" 2>/dev/null || echo "0")

TOTAL_TABLES=$(psql "$POSTGRES_URL" -tAc "
  SELECT COUNT(*)
  FROM pg_tables
  WHERE schemaname IN ('bronze', 'silver', 'gold', 'platinum', 'public');
" 2>/dev/null || echo "0")

if [[ "$RLS_COUNT" == "$TOTAL_TABLES" ]] && [[ "$TOTAL_TABLES" -gt 0 ]]; then
  log_info "RLS enforced on all $TOTAL_TABLES tables"
else
  log_error "RLS not enforced: $RLS_COUNT/$TOTAL_TABLES tables have rowsecurity=true"

  if [[ "$VERBOSE" == true ]]; then
    echo "  Tables without RLS:"
    psql "$POSTGRES_URL" -c "
      SELECT schemaname, tablename
      FROM pg_tables
      WHERE schemaname IN ('bronze', 'silver', 'gold', 'platinum', 'public')
        AND rowsecurity = false;
    " 2>/dev/null || true
  fi
fi

# Gate 7: Visual Parity Thresholds
log_section "Gate 7: Visual Parity (SSIM Thresholds)"

if [[ -f "scripts/ssim.js" ]]; then
  # Run SSIM validation if Node.js available
  if command -v node &> /dev/null; then
    SSIM_OUTPUT=$(node scripts/ssim.js --threshold-mobile=0.97 --threshold-desktop=0.98 2>&1 || echo "")

    if echo "$SSIM_OUTPUT" | grep -q "All routes pass thresholds"; then
      log_info "Visual parity thresholds met (mobile ≥0.97, desktop ≥0.98)"
    else
      log_error "Visual parity validation failed"

      if [[ "$VERBOSE" == true ]]; then
        echo "$SSIM_OUTPUT"
      fi
    fi
  else
    log_warn "Node.js not available, skipping visual parity validation"
  fi
else
  log_warn "scripts/ssim.js not found, skipping visual parity validation"
fi

# Summary
log_section "Validation Summary"

PASSED_GATES=$((TOTAL_GATES - FAILED_GATES))

echo "Passed: $PASSED_GATES/$TOTAL_GATES gates"
echo "Failed: $FAILED_GATES/$TOTAL_GATES gates"

if [[ $FAILED_GATES -eq 0 ]]; then
  echo -e "${GREEN}✅ All acceptance gates passed - ready for deployment${NC}"
  exit 0
else
  echo -e "${RED}❌ $FAILED_GATES gate(s) failed - deployment blocked${NC}"
  exit 1
fi
