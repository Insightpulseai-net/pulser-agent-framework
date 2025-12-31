# ComplianceValidator Agent - SKILL Definition

**Agent ID**: agent_002
**Version**: 1.0.0
**Status**: Active
**Dependencies**: DocumentationParser (agent_001)

## Purpose

Validate extracted business logic and generated code against Philippine regulatory requirements (BIR, PFRS, DOLE), international accounting standards, and enterprise compliance frameworks. Block non-compliant code from advancing to code generation.

## Scope & Boundaries

### CAN DO

**Regulatory Validation**
- [x] Validate against BIR 36 official tax forms (1700, 1601-C, 2550-Q, 2306, etc.)
- [x] Enforce 2024 Philippine progressive tax brackets
- [x] Check PFRS/IAS accounting standards compliance
- [x] Verify DOLE labor law requirements
- [x] Validate SOX Section 404 controls (where applicable)

**Compliance Checking**
- [x] Validate data field mappings against regulatory schemas
- [x] Check calculation logic against official formulas
- [x] Verify required fields and thresholds
- [x] Ensure segregation of duties (SoD) rules

**Reporting**
- [x] Generate detailed compliance reports
- [x] Provide remediation guidance for failures
- [x] Cite regulatory sources for each check
- [x] Track compliance history in Supabase

**Blocking**
- [x] Block CodeGenerator from proceeding on failure
- [x] Send alerts on critical compliance violations
- [x] Require human review for edge cases

### CANNOT DO (Hard Boundaries)

**NO Code Generation**
- [ ] Cannot write or modify code
- [ ] Cannot create database migrations
- [ ] Task delegated to: **CodeGenerator agent (agent_003)**

**NO Interpretation**
- [ ] Cannot interpret tax law beyond official documentation
- [ ] Cannot make business decisions on ambiguous cases
- [ ] Must flag for human review

**NO Deployment**
- [ ] Cannot touch any production system
- [ ] Can only read from knowledge base
- [ ] Task delegated to: **DeploymentOrchestrator agent (agent_006)**

**NO Data Modification**
- [ ] Cannot modify extracted documentation
- [ ] Can only add compliance annotations
- [ ] Read-only access to docs_* tables

## Input Interface

```typescript
interface ComplianceValidatorInput {
  extraction_id: string;  // From DocumentationParser
  validation_scope: 'full' | 'incremental' | 'specific';

  business_rules: {
    rule_id: string;
    rule_type: 'tax_calculation' | 'labor_compliance' | 'accounting_standard' | 'sod_control';
    source_chunk_ids: string[];
    logic: Record<string, any>;
  }[];

  generated_code?: {
    module_name: string;
    code_content: string;
    language: 'python' | 'sql';
  }[];

  regulatory_context: {
    country: 'PH';
    tax_year: number;  // 2024
    standards: ('BIR' | 'PFRS' | 'DOLE' | 'SOX')[];
  };

  supabase_connection: {
    url: string;
    anon_key: string;
  };
}
```

## Output Interface

```typescript
interface ComplianceValidatorOutput {
  validation_id: string;  // UUID
  extraction_id: string;  // Reference to source
  validated_at: string;  // ISO8601

  is_compliant: boolean;  // Master gate

  summary: {
    total_checks: number;
    passed: number;
    failed: number;
    warnings: number;
    human_review_required: number;
  };

  checks: {
    check_id: string;
    regulation_type: 'BIR_FORM' | 'PFRS_STANDARD' | 'DOLE_RULE' | 'SOX_CONTROL';
    regulation_code: string;  // 'BIR_1700', 'PFRS_16', etc.
    check_name: string;
    status: 'PASS' | 'FAIL' | 'WARN' | 'REVIEW';

    details: {
      expected: any;
      actual: any;
      deviation: string;
    };

    citation: {
      source_url: string;
      source_section: string;
      effective_date: string;
    };
  }[];

  remediation: {
    issue: string;
    field_or_rule: string;
    suggested_fix: string;
    priority: 'critical' | 'high' | 'medium' | 'low';
    regulatory_reference: string;
  }[];

  blocked_reasons: string[];  // Why code generation is blocked
}
```

## Regulatory Rules Database

### BIR Forms (36 Total)

| Form | Description | Key Validations |
|------|-------------|-----------------|
| BIR 1700 | Annual Income Tax | Progressive brackets, deductions, exemptions |
| BIR 1601-C | Monthly Withholding Tax | Correct withholding rates |
| BIR 2550-Q | Quarterly VAT | 12% VAT calculations |
| BIR 2306 | Creditable Withholding | Rate matrices |
| BIR 1701 | Self-employed Annual | Business income rules |
| ... | (31 more forms) | ... |

### 2024 Philippine Progressive Tax Brackets

| Annual Income | Tax Rate |
|---------------|----------|
| ₱0 - ₱250,000 | 0% |
| ₱250,001 - ₱400,000 | 15% of excess over ₱250,000 |
| ₱400,001 - ₱800,000 | ₱22,500 + 20% of excess over ₱400,000 |
| ₱800,001 - ₱2,000,000 | ₱102,500 + 25% of excess over ₱800,000 |
| ₱2,000,001 - ₱8,000,000 | ₱402,500 + 30% of excess over ₱2,000,000 |
| Over ₱8,000,000 | ₱2,202,500 + 35% of excess over ₱8,000,000 |

### PFRS Standards

| Standard | Key Requirements |
|----------|------------------|
| PFRS 16 | Lease capitalization, right-of-use assets |
| PAS 1 | Financial statement presentation |
| PAS 12 | Deferred tax accounting |
| PFRS 15 | Revenue recognition (5-step model) |

## Failure Modes & Recovery

| Failure Type | Detection | Recovery Action |
|--------------|-----------|-----------------|
| Regulatory rule missing | Rule lookup fails | Flag for human review, do not auto-pass |
| Calculation deviation | Expected vs actual mismatch | Generate remediation, block CodeGen |
| Critical violation | BIR/PFRS mandatory failure | Immediate alert + full block |
| Ambiguous interpretation | Multiple valid readings | List all, require human selection |
| Supabase read failure | Database error | Retry 3x, then fail validation |

## Performance Constraints

| Metric | Constraint |
|--------|------------|
| Validation per module | <30 seconds |
| Total validation run | <5 minutes |
| Memory usage | 1GB max |
| Concurrent validations | 1 (sequential for auditability) |

## Dependencies

- **Upstream**: DocumentationParser (agent_001) extraction_id required
- **Downstream**: CodeGenerator (agent_003) only if is_compliant=true

## Required Tools & Libraries

```python
# Core validation
pydantic>=2.0.0  # Schema validation
decimal  # Precise financial calculations

# Regulatory data
json  # Rules stored as JSON
yaml  # Alternative rule format

# Database
supabase>=2.0.0

# Utilities
python-dotenv>=1.0.0
```

## Success Criteria

| Criteria | Target |
|----------|--------|
| BIR form validation coverage | 100% of 36 forms |
| Tax bracket accuracy | 100% |
| PFRS standard coverage | Core standards (16, PAS 1, 12, 15) |
| False positive rate | <1% |
| False negative rate | 0% (critical) |
| Remediation guidance provided | 100% of failures |

## Example Usage

```bash
# Run via CLI
./scripts/docs2code build

# Compliance is checked as part of build stage
# If compliance fails, build exits with error and report

# Direct Python call
python -m pipelines.build.compliance_validator \
  --extraction-id "abc123" \
  --supabase-url $SUPABASE_URL \
  --supabase-key $SUPABASE_ANON_KEY \
  --output /tmp/compliance_report.json
```

## Handoff to Next Agent

Upon successful validation (is_compliant=true):
1. Validation report stored in Supabase
2. All checks logged with citations
3. Lineage updated in `pipeline_lineage`
4. **CodeGenerator (agent_003)** triggered with validation_id
5. If is_compliant=false, pipeline STOPS

Upon failure (is_compliant=false):
1. Detailed remediation report generated
2. Alert sent to compliance team
3. CodeGenerator blocked
4. Manual review required before retry
