# Agentic Platform Patterns

Based on Databricks' agentic debugging platform architecture and GPT-5 prompting best practices.

## Overview

This document captures patterns for building scalable, safe, and evaluable agentic systems.

### Key Principles

1. **Foundation First** - Unify data + abstractions + access control before building agents
2. **Tool Abstraction** - Decouple prompts from tool implementations
3. **Regression-Proofing** - Snapshot, replay, and score to prevent regressions

## Architecture Blueprint

```yaml
docs2code_platform:
  control_plane:
    name: docs2code-orchestrator
    responsibilities:
      - authz_policy_enforcement   # per-team, per-resource, per-agent
      - tool_registry              # canonical tool schemas (registry.yaml)
      - docir_state                # intermediate representation state
      - eval_replay_harness        # snapshot + replay + judge scoring

  data_plane:
    sources:
      - name: documentation
        scope: sap, microsoft, odoo, oca, bir, databricks
      - name: generated_code
        scope: odoo modules, migrations, tests
    principle: docir_first  # compile to IR before generation

  tools:
    - name: compile_docir
      io: { in: {source_dir}, out: {docir} }
    - name: gen.odoo.module
      io: { in: {docir, module_name}, out: {files, compliance} }
    - name: gen.sql.migrations
      io: { in: {docir}, out: {migrations} }
    - name: verify.lint
      io: { in: {paths}, out: {passed, errors} }
    - name: verify.tests
      io: { in: {paths}, out: {passed, coverage} }

  eval:
    snapshots:
      source: docir_test_bundles
    judge_model:
      scoring_dimensions: [accuracy, helpfulness, actionability, safety]
```

## The 3 Things That Made It Work

### 1. Foundation First (Safe + Scalable)

Before building any agent, establish:

- **Unified data layer**: DocIR as single source of truth
- **Fine-grained access control**: Per-agent, per-tool permissions
- **Consistent abstractions**: All tools share the same contract schema

```python
# Example: Central index mapping
tenant_tool_map = {
    "tenant_a": {
        "allowed_tools": ["compile_docir", "gen.odoo.module"],
        "denied_tools": ["gen.sql.migrations"],  # Needs DBA approval
    }
}
```

### 2. Tool Abstraction + Fast Iteration

Decouple prompts from tool implementations:

```yaml
# tools/registry.yaml
tools:
  gen.odoo.module:
    name: "Odoo Module Generator"
    input_schema: "schemas/GenOdooModuleInput.json"
    output_schema: "schemas/GenOdooModuleOutput.json"
    guarantees:
      deterministic: true
      idempotent: true
      patch_mode: true
```

The LLM infers inputs/outputs from:
1. JSON Schema definitions
2. Docstrings in tool classes
3. Examples in the registry

### 3. Regression-Proofing

Snapshot production state, replay through the agent, score with a judge:

```python
# eval/run_replay.py pattern

def replay_case(agent, snapshot):
    """Run agent on snapshotted input."""
    convo = agent.run(snapshot.question, context=snapshot.bundle)
    return convo.final_answer, convo.tool_calls

def judge(answer, expected, rubric, judge_model):
    """Score output using judge LLM."""
    return judge_model.score(
        answer=answer,
        expected=expected,
        rubric=rubric
    )

def test_suite(cases, agent, judge_model, thresholds):
    """CI gate: fail if any case regresses below threshold."""
    for case in cases:
        answer, tool_calls = replay_case(agent, case.snapshot)
        scores = judge(answer, case.expected, case.rubric, judge_model)

        assert scores["accuracy"] >= thresholds["accuracy"]
        assert scores["actionability"] >= thresholds["actionability"]
        assert scores["safety"] >= thresholds["safety"]
```

## Minimum Viable Implementation

### Step 1: Central Index Service

Map tenants to allowed tools and data shards:

```python
class CentralIndex:
    def get_allowed_tools(self, tenant_id: str) -> list[str]:
        """Return tools this tenant can use."""
        pass

    def get_data_shard(self, tenant_id: str, resource: str) -> str:
        """Return the shard containing this resource."""
        pass
```

### Step 2: Normalize All Tools

Every tool has:
- Strict input/output JSON schema
- Docstring contract
- Guarantees (deterministic, idempotent, patch_mode)

See: `tools/registry.yaml`

### Step 3: Add Eval Harness

See: `eval/run_replay.py`

Wire into CI:
```yaml
# .github/workflows/docs2code.yml
eval:
  name: Replay Evaluation
  steps:
    - run: python eval/run_replay.py --cases eval/cases --thresholds eval/thresholds.yaml
```

### Step 4: Split Agents by Domain

Once tooling is stable, create specialized agents:

| Agent | Domain | Tools |
|-------|--------|-------|
| DocumentationParser | Extraction | compile_docir |
| ComplianceValidator | Validation | verify.compliance |
| CodeGenerator | Generation | gen.odoo.module, gen.sql.migrations |
| ValidationAgent | Testing | verify.lint, verify.tests |
| DeploymentOrchestrator | Deployment | deploy.blue_green |

## GPT-5 Model Selection

| Task | Model | Reasoning | Verbosity |
|------|-------|-----------|-----------|
| Fast codegen | gpt-5.2 | medium | low |
| Complex problems | gpt-5.2-pro | high | medium |
| Batch processing | gpt-5-mini | none | low |
| Agentic coding | gpt-5.2-codex | medium | low |

See: `tools/prompts/gpt5_coding_guide.yaml`

## Key Metrics

Based on Databricks results:
- **Debugging time**: Target 90% reduction
- **Onboarding time**: New engineers productive in <5 minutes
- **Regression rate**: 0% (blocked by CI)

## References

- OpenAI Cookbook GPT-5 Prompting Guide (Aug 2025)
- OpenAI Cookbook GPT-5.2 Prompting Guide (Dec 2025)
- Databricks Blog: How We Debug 1000s of Databases with AI
