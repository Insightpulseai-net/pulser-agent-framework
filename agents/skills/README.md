# Agent Skills Registry

This directory contains callable skill definitions for the multi-agent DevOps framework.

## Overview

Skills are discrete, reusable capabilities that agents can invoke. Each skill has:
- A defined input/output contract
- Clear permission requirements
- Explicit tool dependencies

## Skill Categories

### Code Generation Skills

| Skill | Agent | Description |
|-------|-------|-------------|
| `gen.odoo.module` | Implementer | Generate Odoo 18 CE module |
| `gen.sql.migrations` | Implementer | Generate SQL migrations |
| `gen.python.models` | Implementer | Generate typed Python models |
| `gen.xml.views` | Implementer | Generate Odoo XML views |
| `gen.tests.unit` | Implementer | Generate unit tests |

### Validation Skills

| Skill | Agent | Description |
|-------|-------|-------------|
| `verify.lint` | Reviewer | Run linting checks |
| `verify.typecheck` | Reviewer | Run type checking |
| `verify.tests` | Reviewer | Execute test suites |
| `verify.compliance` | Reviewer | Validate compliance rules |
| `verify.security` | Policy | Run security scans |

### Deployment Skills

| Skill | Agent | Description |
|-------|-------|-------------|
| `deploy.preview` | Release | Deploy to preview environment |
| `deploy.canary` | Release | Deploy to canary (10% traffic) |
| `deploy.production` | Release | Deploy to production |
| `deploy.rollback` | Release/SRE | Rollback deployment |

### Observability Skills

| Skill | Agent | Description |
|-------|-------|-------------|
| `observe.metrics` | Observability | Query metrics |
| `observe.logs` | Observability | Search logs |
| `observe.traces` | Observability | Query traces |
| `observe.dashboard` | Observability | Generate dashboards |

### Data Skills

| Skill | Agent | Description |
|-------|-------|-------------|
| `data.migrate` | ETL | Execute data migrations |
| `data.backfill` | ETL | Run data backfills |
| `data.profile` | Data Fabcon | Profile data quality |
| `data.lineage` | Data Fabcon | Document data lineage |

## Skill Definition Format

```yaml
skill:
  name: "skill-name"
  version: "1.0.0"
  description: "What this skill does"

  # Which agents can invoke this skill
  authorized_agents:
    - implementer
    - reviewer

  # Input parameters
  input:
    required:
      - name: "param1"
        type: "string"
        description: "Description"
    optional:
      - name: "param2"
        type: "boolean"
        default: true

  # Output format
  output:
    type: "object"
    properties:
      result: "string"
      metadata: "object"

  # Tools this skill uses
  tools:
    - github.pr.create
    - supabase.db.query

  # Permissions required
  permissions:
    read: [codebase, spec]
    write: [codebase]
    execute: [tests]

  # Constraints
  constraints:
    - "Must have validation_id"
    - "Cannot modify production"

  # Example invocation
  example:
    input:
      param1: "value1"
      param2: false
    output:
      result: "success"
      metadata: {}
```

## Adding New Skills

1. Create skill definition in `skills/{category}/{skill-name}.yaml`
2. Register in `registry.yaml` under appropriate agent
3. Implement skill handler in agent code
4. Add tests for skill behavior
5. Document in this README

## Skill Permissions

Skills inherit permissions from the invoking agent. Additional permission checks:

```yaml
# Example permission check flow
1. Agent requests to invoke skill
2. Check agent has skill in authorized_agents
3. Check agent has required tool permissions
4. Check environment allows operation
5. Execute skill
6. Log audit trail
```

## Skill Composition

Skills can be composed into workflows:

```yaml
workflow:
  name: "standard-release"
  steps:
    - skill: gen.tests.unit
      agent: implementer
    - skill: verify.tests
      agent: reviewer
      depends_on: [gen.tests.unit]
    - skill: deploy.preview
      agent: release
      depends_on: [verify.tests]
```

## Monitoring Skills

All skill invocations are logged with:
- Agent ID
- Skill name
- Input hash (not full input for security)
- Output status
- Duration
- Errors (if any)

Query skill metrics:
```sql
SELECT
  skill_name,
  COUNT(*) as invocations,
  AVG(duration_ms) as avg_duration,
  SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors
FROM skill_invocations
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY skill_name
ORDER BY invocations DESC;
```
