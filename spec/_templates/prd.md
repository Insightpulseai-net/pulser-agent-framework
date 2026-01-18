# {Project Name} - Product Requirements Document

**Slug**: `{slug}`
**Version**: 0.1.0
**Status**: Draft | In Review | Approved | Implemented
**Constitution**: [constitution.md](./constitution.md)
**Owner**: {owner}
**Last Updated**: {date}

---

## Executive Summary

> 2-3 sentences summarizing what we're building and why.

{summary}

## Problem Statement

### Current State

{Description of the current situation and its pain points}

### User Pain Points

1. **{Pain Point 1}**: {description}
2. **{Pain Point 2}**: {description}

### Business Impact

- {impact_1}
- {impact_2}

## Proposed Solution

### Overview

{High-level description of the solution}

### Key Features

#### Feature 1: {Name}

**Description**: {what_it_does}

**User Story**: As a {role}, I want to {action} so that {benefit}.

**Acceptance Criteria**:
- [ ] {criterion_1}
- [ ] {criterion_2}
- [ ] {criterion_3}

**Priority**: P0 | P1 | P2

#### Feature 2: {Name}

**Description**: {what_it_does}

**User Story**: As a {role}, I want to {action} so that {benefit}.

**Acceptance Criteria**:
- [ ] {criterion_1}
- [ ] {criterion_2}

**Priority**: P0 | P1 | P2

## User Experience

### User Flows

```
[Start] --> [Step 1] --> [Decision?]
                            |
                     Yes    |    No
                      v     v
                 [Step 2] [Step 3]
                      \     /
                       v   v
                      [End]
```

### Wireframes / Mockups

> Link to Figma or include diagrams

{wireframe_links_or_descriptions}

## Technical Requirements

### API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | /api/v1/{resource} | List resources | JWT |
| POST | /api/v1/{resource} | Create resource | JWT |
| PUT | /api/v1/{resource}/{id} | Update resource | JWT |
| DELETE | /api/v1/{resource}/{id} | Delete resource | JWT + Admin |

### Data Model

```yaml
{ModelName}:
  id: uuid (primary key)
  created_at: timestamp
  updated_at: timestamp
  {field_1}: {type}
  {field_2}: {type}
```

### Performance Requirements

| Metric | Requirement |
|--------|-------------|
| Response Time (P50) | < 100ms |
| Response Time (P99) | < 500ms |
| Throughput | > 1000 req/s |
| Availability | 99.9% |

### Security Requirements

- [ ] Authentication: {method}
- [ ] Authorization: {method}
- [ ] Data encryption at rest: {yes/no}
- [ ] Data encryption in transit: {yes/no}
- [ ] Audit logging: {yes/no}
- [ ] RLS policies: {yes/no}

## Non-Functional Requirements

### Scalability

{How the system should scale}

### Observability

- **Logs**: {log_format_and_retention}
- **Metrics**: {key_metrics_to_track}
- **Traces**: {tracing_approach}
- **Dashboards**: {dashboard_links}

### Disaster Recovery

- **RPO**: {recovery_point_objective}
- **RTO**: {recovery_time_objective}
- **Backup Strategy**: {description}

## Milestones

| Milestone | Description | Target Date | Status |
|-----------|-------------|-------------|--------|
| M1: Foundation | Core infrastructure setup | | Not Started |
| M2: MVP | Basic feature set | | Not Started |
| M3: Beta | Full feature set, limited users | | Not Started |
| M4: GA | General availability | | Not Started |

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| {risk_1} | High/Med/Low | High/Med/Low | {mitigation_strategy} |
| {risk_2} | High/Med/Low | High/Med/Low | {mitigation_strategy} |

## Success Metrics

| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|-------------------|
| {metric_1} | {current} | {target} | {how_measured} |
| {metric_2} | {current} | {target} | {how_measured} |

## Open Questions

1. {question_1}
2. {question_2}

## Appendix

### References

- [Link to related documents]
- [Link to API specs]
- [Link to design files]

### Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | {date} | {author} | Initial draft |

---

*PRD approved by: {approver_name} on {date}*
