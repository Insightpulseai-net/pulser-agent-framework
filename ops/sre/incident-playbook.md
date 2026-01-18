# Incident Response Playbook

**Version**: 1.0.0
**Owner**: SRE Team
**Last Updated**: 2024-01-15

---

## Incident Response Overview

This playbook defines how we respond to production incidents. The goal is to minimize customer impact, communicate effectively, and learn from failures.

---

## Incident Severity Levels

| Severity | Definition | Response Time | Examples |
|----------|------------|---------------|----------|
| **SEV1** | Critical - Complete service outage | < 15 min | All users affected, data loss risk |
| **SEV2** | Major - Significant degradation | < 30 min | Core feature broken, subset of users affected |
| **SEV3** | Minor - Isolated issue | < 2 hours | Non-critical feature broken, workaround exists |
| **SEV4** | Low - Minimal impact | Next business day | Minor bug, cosmetic issue |

---

## Roles

### Incident Commander (IC)

**Responsibility**: Coordinate response, make decisions, communicate

**Tasks**:
- [ ] Assess severity and impact
- [ ] Assign roles
- [ ] Coordinate communication
- [ ] Make go/no-go decisions
- [ ] Call for help when needed
- [ ] Declare incident resolved

**Who**: On-call SRE or escalated engineer

### Technical Lead (TL)

**Responsibility**: Lead technical investigation and resolution

**Tasks**:
- [ ] Investigate root cause
- [ ] Propose and implement fixes
- [ ] Coordinate with other engineers
- [ ] Validate fix before deploy
- [ ] Document technical details

**Who**: Senior engineer familiar with affected systems

### Communications Lead

**Responsibility**: Keep stakeholders informed

**Tasks**:
- [ ] Post updates to status page
- [ ] Notify affected customers
- [ ] Update internal stakeholders
- [ ] Coordinate with support team

**Who**: Product manager or designated engineer

### Scribe

**Responsibility**: Document everything

**Tasks**:
- [ ] Maintain incident timeline
- [ ] Record decisions and actions
- [ ] Capture chat logs
- [ ] Note participants

**Who**: Any available team member

---

## Incident Lifecycle

### 1. Detection

**Trigger**: Alert fires, customer report, or engineer notices issue

**Actions**:
```
1. Acknowledge alert in PagerDuty (within 5 min)
2. Join #incidents Slack channel
3. Post initial assessment:
   "Investigating [service] - seeing [symptoms]"
```

### 2. Triage

**Goal**: Understand severity and impact

**Questions to answer**:
- What is the user impact?
- How many users affected?
- Is data at risk?
- Is there a workaround?

**Actions**:
```
1. Check monitoring dashboards
2. Review recent changes (deploys, config)
3. Assign severity level
4. Page additional help if needed (SEV1/SEV2)
```

### 3. Mobilization

**For SEV1/SEV2**:
```
1. IC declares incident: "@here SEV[1/2] declared - [description]"
2. Create incident channel: #incident-YYYYMMDD-brief-name
3. Assign roles: IC, TL, Comms, Scribe
4. Start incident bridge call if needed
5. Post to status page: "Investigating"
```

### 4. Investigation

**Goal**: Find root cause and path to resolution

**Actions**:
```
1. TL leads investigation
2. Check logs, metrics, traces
3. Review recent changes
4. Form hypothesis, test it
5. Communicate findings to IC
```

**Common investigation steps**:
```bash
# Check service health
curl -f https://api.example.com/health

# View recent logs
kubectl logs -l app=workbench-api --since=30m | grep -i error

# Check recent deployments
gh run list --workflow=deploy.yml --limit=5

# View metrics
# Open Grafana dashboard: /dashboards/service-overview
```

### 5. Mitigation

**Goal**: Restore service, even if temporary

**Options** (in order of preference):
1. **Rollback**: Revert recent change
2. **Scale**: Add capacity
3. **Failover**: Switch to backup
4. **Feature flag**: Disable broken feature
5. **Hotfix**: Deploy targeted fix

**Rollback commands**:
```bash
# Application rollback
./scripts/rollback.sh --service=workbench-api --env=production

# Vercel rollback
vercel rollback --scope=insightpulseai

# Database migration rollback
supabase migration repair --status reverted

# Feature flag disable
curl -X POST https://api.launchdarkly.com/api/v2/flags/my-flag/toggle-off
```

### 6. Resolution

**Criteria for resolution**:
- [ ] Service restored to normal operation
- [ ] No elevated error rates
- [ ] SLOs being met
- [ ] Customer impact resolved

**Actions**:
```
1. IC confirms resolution with TL
2. Update status page: "Resolved"
3. Post final update to #incidents
4. Schedule postmortem (SEV1/SEV2)
5. Thank participants
```

### 7. Follow-up

**Within 24 hours**:
- [ ] Create postmortem document
- [ ] Identify action items
- [ ] Assign owners to action items

**Within 1 week**:
- [ ] Complete postmortem review
- [ ] Share learnings with team
- [ ] Track action items to completion

---

## Communication Templates

### Initial Alert

```
:rotating_light: INCIDENT: [Brief description]
Severity: SEV[1/2/3]
Impact: [Who is affected and how]
Status: Investigating
IC: @[name]
```

### Status Update (every 30 min for SEV1/SEV2)

```
:hourglass: UPDATE: [Service] incident
Status: [Investigating/Identified/Mitigating]
What we know: [Brief summary]
Current actions: [What's being done]
ETA: [If known, otherwise "TBD"]
Next update: [Time]
```

### Resolution

```
:white_check_mark: RESOLVED: [Service] incident
Duration: [X hours Y minutes]
Impact: [Summary of user impact]
Root cause: [Brief description]
Resolution: [What fixed it]
Postmortem: [Link - coming soon for SEV1/SEV2]
```

### Customer Communication (for major incidents)

```
Subject: [Service Name] Service Disruption - [Date]

We experienced a service disruption affecting [description].

Timeline:
- [Time] - Issue began
- [Time] - Issue detected
- [Time] - Service restored

Impact: [What customers experienced]

Root cause: [Brief, non-technical explanation]

We apologize for the inconvenience and are taking steps to prevent
similar issues in the future.

If you have questions, please contact support@example.com.
```

---

## Escalation Paths

### Technical Escalation

```
Level 1: On-call engineer
   |
   v (15 min no progress)
Level 2: Team lead / Senior engineer
   |
   v (30 min no progress)
Level 3: Engineering manager
   |
   v (1 hour no progress)
Level 4: VP Engineering
```

### Business Escalation (SEV1)

```
Immediately notify:
- Engineering Manager
- Product Manager
- Customer Success (if customer-facing)

Within 1 hour:
- Executive team (if prolonged outage)
```

---

## Common Scenarios

### Scenario: High Error Rate

**Symptoms**: 5xx errors spiking, alerts firing

**Investigation**:
```bash
1. Check error logs
   kubectl logs -l app=api --since=10m | grep -i "error\|exception"

2. Check recent deploys
   gh run list --workflow=deploy.yml --limit=5

3. Check database
   psql -c "SELECT state, count(*) FROM pg_stat_activity GROUP BY state"

4. Check dependencies
   curl -f https://api.supabase.co/health
```

**Resolution paths**:
- If recent deploy: Rollback
- If database: Scale connections, kill queries
- If dependency: Implement circuit breaker

---

### Scenario: Performance Degradation

**Symptoms**: High latency, slow responses, timeouts

**Investigation**:
```bash
1. Check resource usage
   kubectl top pods -l app=api

2. Check database queries
   SELECT query, calls, mean_exec_time
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC LIMIT 10;

3. Check for traffic spike
   # View request rate in Grafana

4. Check cache hit rate
   redis-cli info stats | grep hit
```

**Resolution paths**:
- High CPU: Scale horizontally
- Slow queries: Add indexes, optimize queries
- Cache miss: Warm cache, increase TTL
- Traffic spike: Scale, enable rate limiting

---

### Scenario: Service Unreachable

**Symptoms**: Connection refused, timeouts, health check failures

**Investigation**:
```bash
1. Check if pods are running
   kubectl get pods -l app=api

2. Check for OOM kills
   kubectl describe pod [pod-name] | grep -i oom

3. Check network
   kubectl exec -it [pod] -- curl localhost:8000/health

4. Check DNS
   nslookup api.example.com
```

**Resolution paths**:
- Pods crashing: Check logs, increase resources
- OOM: Increase memory limits
- Network: Check ingress, security groups

---

## Postmortem Template

After SEV1/SEV2 incidents, create a postmortem:

```markdown
# Incident Postmortem: [Title]

**Date**: [Date]
**Duration**: [X hours Y minutes]
**Severity**: SEV[1/2]
**Author**: [Name]

## Summary
[2-3 sentence summary of what happened]

## Impact
- Users affected: [Number or percentage]
- Duration of impact: [Time]
- Revenue impact: [If applicable]

## Timeline (all times UTC)
- HH:MM - [Event]
- HH:MM - [Event]
- HH:MM - [Event]

## Root Cause
[Technical explanation of what caused the incident]

## Resolution
[What was done to fix the issue]

## What Went Well
- [Thing that worked]
- [Thing that worked]

## What Could Be Improved
- [Thing to improve]
- [Thing to improve]

## Action Items
| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| [Action] | @name | [Date] | Open |
| [Action] | @name | [Date] | Open |

## Lessons Learned
[Key takeaways for the team]
```

---

## Quick Reference

### Emergency Contacts

| Role | Contact | When to page |
|------|---------|--------------|
| Primary On-Call | PagerDuty | Any SEV1/SEV2 |
| Secondary On-Call | PagerDuty | No response in 15m |
| Engineering Manager | @[name] | SEV1, escalation needed |
| Security Team | #security-alerts | Security incidents |

### Key Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| Service Overview | `/grafana/service-overview` | All services at a glance |
| Error Analysis | `/grafana/errors` | Error breakdown |
| Database | `/grafana/database` | DB performance |
| Incidents | `/grafana/incidents` | Incident history |

### Key Commands

```bash
# Quick health check
./scripts/health-check.sh --all

# Emergency rollback
./scripts/rollback.sh --service=all --env=production

# Enable maintenance mode
./scripts/maintenance.sh --enable --message="Emergency maintenance"

# Disable maintenance mode
./scripts/maintenance.sh --disable
```

---

*Playbook reviewed quarterly. Last review: 2024-01-15*
