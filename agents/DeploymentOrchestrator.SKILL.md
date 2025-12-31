# DeploymentOrchestrator Agent - SKILL Definition

**Agent ID**: agent_006
**Version**: 1.0.0
**Status**: Active
**Dependencies**: ValidationAgent (agent_005) must pass

## Purpose

Execute zero-downtime deployments using blue/green strategy on DigitalOcean. Perform health checks, automated rollbacks on failure, and emit DPO/ORPO preference pairs for continuous agent hardening.

## Scope & Boundaries

### CAN DO

**Deployment Operations**
- [x] Execute blue/green deployments on DigitalOcean
- [x] Run health checks before traffic cutover
- [x] Perform automated rollbacks on failure
- [x] Apply database migrations (from SQLAgent)
- [x] Deploy Odoo modules to production

**Monitoring**
- [x] Monitor deployment health metrics
- [x] Check service availability
- [x] Verify database connectivity
- [x] Track deployment duration

**Rollback**
- [x] Trigger automatic rollback on health check failure
- [x] Preserve previous deployment state
- [x] Notify team on rollback events

**Hardening Loop**
- [x] Detect deployment failures
- [x] Generate DPO/ORPO preference pairs
- [x] Send pairs to ipai-agentbench
- [x] Log hardening events for analysis

### CANNOT DO (Hard Boundaries)

**NO Code Modification**
- [ ] Cannot modify deployed code
- [ ] Cannot fix bugs during deployment
- [ ] Can only deploy or rollback

**NO Test Bypass**
- [ ] Cannot deploy without passed tests
- [ ] Cannot skip quality gates
- [ ] Must have validation_run_id from ValidationAgent

**NO Compliance Override**
- [ ] Cannot deploy non-compliant code
- [ ] Compliance gate is absolute
- [ ] Compliance from: **ComplianceValidator (agent_002)**

**NO Data Modification**
- [ ] Cannot modify production data
- [ ] Can only execute approved migrations
- [ ] Migrations from: **SQLAgent (agent_004)**

## Input Interface

```typescript
interface DeploymentOrchestratorInput {
  validation_run_id: string;  // From ValidationAgent

  deployment_config: {
    strategy: 'blue_green' | 'canary' | 'rolling';
    platform: 'digitalocean' | 'kubernetes';

    // DigitalOcean specific
    do_app_id?: string;
    do_region?: string;

    // Kubernetes specific
    k8s_namespace?: string;
    k8s_deployment?: string;
  };

  artifacts: {
    odoo_modules: string[];  // Paths to module directories
    migrations: string[];  // SQL migration files
    docker_image?: string;  // If using containerized deploy
  };

  health_check: {
    endpoint: string;  // e.g., '/health'
    expected_status: number;  // 200
    timeout_seconds: number;  // 30
    retries: number;  // 5
    interval_seconds: number;  // 10
  };

  rollback_config: {
    auto_rollback_on_failure: boolean;  // true
    keep_previous_versions: number;  // 3
    max_rollback_duration_seconds: number;  // 60
  };

  agentbench_config: {
    url: string;
    token_env_var: string;
    emit_dpo_on_failure: boolean;  // true
  };

  credentials: {
    do_api_token_env_var: string;
    db_connection_env_var: string;
  };
}
```

## Output Interface

```typescript
interface DeploymentOrchestratorOutput {
  deployment_id: string;  // UUID
  validation_run_id: string;  // Reference to tests
  deployed_at: string;  // ISO8601

  status: 'success' | 'failed' | 'rolled_back';

  deployment_details: {
    strategy: string;
    platform: string;
    previous_version: string;
    new_version: string;
    duration_seconds: number;
  };

  health_checks: {
    endpoint: string;
    status_code: number;
    response_time_ms: number;
    passed: boolean;
    timestamp: string;
  }[];

  migrations_applied: {
    version: string;
    filename: string;
    duration_ms: number;
    success: boolean;
  }[];

  rollback: {
    triggered: boolean;
    reason?: string;
    previous_version?: string;
    duration_seconds?: number;
  };

  hardening: {
    dpo_pairs_generated: number;
    agentbench_submission_id?: string;
  };

  logs: {
    level: 'info' | 'warn' | 'error';
    message: string;
    timestamp: string;
  }[];
}
```

## Deployment Strategies

### Blue/Green Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                    BLUE/GREEN DEPLOYMENT                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Step 1: Deploy to GREEN (new version)                         │
│   ┌─────────┐                        ┌─────────┐               │
│   │  BLUE   │◄── LIVE TRAFFIC ───    │  GREEN  │               │
│   │  (v1)   │                        │  (v2)   │ ← DEPLOYING   │
│   └─────────┘                        └─────────┘               │
│                                                                 │
│   Step 2: Health check GREEN                                    │
│   ┌─────────┐                        ┌─────────┐               │
│   │  BLUE   │◄── LIVE TRAFFIC ───    │  GREEN  │ ← HEALTH OK   │
│   │  (v1)   │                        │  (v2)   │               │
│   └─────────┘                        └─────────┘               │
│                                                                 │
│   Step 3: Switch traffic to GREEN                               │
│   ┌─────────┐                        ┌─────────┐               │
│   │  BLUE   │                        │  GREEN  │◄── LIVE       │
│   │  (v1)   │ ← STANDBY              │  (v2)   │    TRAFFIC    │
│   └─────────┘                        └─────────┘               │
│                                                                 │
│   Rollback: Instant switch back to BLUE                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Health Check Flow

```python
async def run_health_checks(config: HealthCheckConfig) -> bool:
    """Execute health checks with retries."""
    for attempt in range(config.retries):
        try:
            response = await httpx.get(
                config.endpoint,
                timeout=config.timeout_seconds
            )

            if response.status_code == config.expected_status:
                log.info(f"Health check passed (attempt {attempt + 1})")
                return True

            log.warn(f"Health check failed: status {response.status_code}")

        except Exception as e:
            log.error(f"Health check error: {e}")

        await asyncio.sleep(config.interval_seconds)

    log.error("All health checks failed")
    return False
```

### Rollback Procedure

```python
async def execute_rollback(deployment_id: str, reason: str) -> bool:
    """Execute automatic rollback to previous version."""
    log.warn(f"Triggering rollback for deployment {deployment_id}")
    log.warn(f"Reason: {reason}")

    try:
        # 1. Switch traffic back to previous version
        await switch_traffic_to_previous()

        # 2. Rollback database migrations (if needed)
        await rollback_migrations()

        # 3. Verify previous version is healthy
        if not await run_health_checks(previous_version_config):
            raise Exception("Previous version also unhealthy")

        # 4. Generate DPO pair for hardening
        await emit_dpo_pair({
            'agent_name': 'DeploymentOrchestrator',
            'failure_scenario': f'Deployment {deployment_id} failed',
            'preferred_output': 'Successful deployment',
            'dispreferred_output': reason,
        })

        log.info("Rollback completed successfully")
        return True

    except Exception as e:
        log.critical(f"Rollback failed: {e}")
        # Alert on-call immediately
        await send_pager_alert(e)
        return False
```

## DigitalOcean Integration

### App Platform Deployment

```python
import digitalocean

def deploy_to_digitalocean(config: DOConfig) -> str:
    """Deploy to DigitalOcean App Platform."""
    client = digitalocean.Client(token=os.getenv(config.token_env_var))

    # Trigger deployment
    deployment = client.apps.create_deployment(
        app_id=config.app_id,
        force_build=True
    )

    # Wait for deployment to complete
    while deployment.phase not in ['ACTIVE', 'ERROR']:
        time.sleep(10)
        deployment = client.apps.get_deployment(
            app_id=config.app_id,
            deployment_id=deployment.id
        )

    if deployment.phase == 'ERROR':
        raise Exception(f"Deployment failed: {deployment.cause_of_error}")

    return deployment.id
```

## DPO/ORPO Hardening Integration

```python
async def emit_dpo_pair(failure_context: dict) -> str:
    """Send failure context to agentbench for agent hardening."""

    pair = {
        'agent_name': failure_context['agent_name'],
        'failure_scenario': failure_context['failure_scenario'],
        'preferred_output': failure_context['preferred_output'],
        'dispreferred_output': failure_context['dispreferred_output'],
        'priority': calculate_priority(failure_context),
        'metadata': {
            'deployment_id': failure_context.get('deployment_id'),
            'timestamp': datetime.utcnow().isoformat(),
            'environment': os.getenv('ENVIRONMENT'),
        }
    }

    response = await httpx.post(
        f"{os.getenv('AGENTBENCH_URL')}/api/dpo-pairs",
        json=pair,
        headers={'Authorization': f"Bearer {os.getenv('AGENTBENCH_TOKEN')}"}
    )

    return response.json()['submission_id']
```

## Failure Modes & Recovery

| Failure Type | Detection | Recovery Action |
|--------------|-----------|-----------------|
| Health check fails | Status code != 200 | Trigger rollback |
| Migration fails | SQL error | Rollback migration, abort deploy |
| DO API timeout | Request timeout | Retry 3x with backoff |
| Previous version unhealthy | Rollback health check | Page on-call, manual intervention |
| Network partition | Connection error | Wait and retry |

## Performance Constraints

| Metric | Constraint |
|--------|------------|
| Deployment duration | <5 minutes |
| Health check timeout | 30 seconds |
| Rollback duration | <30 seconds |
| Traffic switch time | <10 seconds |
| Max downtime | <30 seconds |

## Dependencies

- **Upstream**: ValidationAgent (agent_005) validation_run_id required
- **Downstream**: None (final stage), but emits to agentbench

## Required Tools & Libraries

```python
# DigitalOcean
pydo>=0.1.0  # Official DO SDK

# HTTP
httpx>=0.25.0  # Async HTTP client
aiohttp>=3.8.0  # Alternative async client

# Database migrations
alembic>=1.12.0  # Migration runner
psycopg2>=2.9.0  # PostgreSQL

# Monitoring
prometheus-client>=0.17.0  # Metrics

# Utilities
tenacity>=8.2.0  # Retry logic
python-dotenv>=1.0.0
```

## Success Criteria

| Criteria | Target |
|----------|--------|
| Deployment success rate | ≥99% |
| Rollback success rate | 100% |
| Max downtime | <30 seconds |
| Health checks comprehensive | 100% |
| DPO pairs emitted on failure | 100% |
| Mean time to recovery | <5 minutes |

## Post-Deployment Verification

```python
async def verify_deployment(deployment_id: str) -> bool:
    """Comprehensive post-deployment verification."""
    checks = [
        check_health_endpoint(),
        check_database_connectivity(),
        check_critical_endpoints(),
        check_background_jobs(),
        check_metrics_flowing(),
    ]

    results = await asyncio.gather(*checks, return_exceptions=True)

    failures = [r for r in results if isinstance(r, Exception) or not r]

    if failures:
        log.error(f"Post-deployment verification failed: {failures}")
        return False

    log.info("All post-deployment checks passed")
    return True
```

## Handoff (Pipeline Complete)

Upon successful deployment:
1. Deployment logged to Supabase `deployment_log`
2. Lineage chain complete in `pipeline_lineage`
3. Metrics published to monitoring
4. Success notification sent

Upon failure:
1. Rollback executed
2. DPO pair sent to agentbench
3. Failure alert sent
4. Detailed logs preserved for analysis
5. Pipeline marked as failed
