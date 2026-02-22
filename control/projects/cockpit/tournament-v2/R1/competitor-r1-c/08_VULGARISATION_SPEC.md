# 08_VULGARISATION_SPEC - Operator Clarity Under Pressure

## Context
- Variant C can become hard to reason about during incidents.
- We need an operator-facing vulgarisation spec that keeps comprehension under 60 seconds.

## Problem statement
- Deep orchestration systems fail operationally when dashboards are dense, stale, or ambiguous.
- Operators need a reliable local dashboard with deterministic update semantics.

## Proposed design
### 1) Product contract
- One local offline HTML dashboard per project.
- Update action regenerates content from local project state.
- No mandatory network dependency.

### 2) Required UI sections
- Project summary (phase, mission, next milestone).
- Router health (queue depth, provider health, fallback tier status).
- Timeline (runs, approvals, regressions).
- Progress panel (tickets, blockers, gate status).
- Cost panel (run count, token estimate, budget trend).
- Skill inventory (trust tier, scope, status).

### 3) Required diagrams
- High-level architecture block diagram.
- Orchestration state-flow diagram.
- Timeline chart.
- Metrics bar chart.

### 4) Update cadence
- Manual update action plus freshness display.
- stale warning >24h, critical >72h.

## Interfaces and contracts
### Dashboard config contract
- project_id
- title
- phase
- metrics_sources
- freshness_thresholds
- section_toggles

### Update command contract
- read local state
- regenerate html atomically
- write update log
- refresh tab view

## Failure modes
- FM-VUL-01: missing data source causes blank panel.
- FM-VUL-02: malformed metrics break rendering.
- FM-VUL-03: stale dashboard misleads operator.

## Validation strategy
- Offline open test via file path.
- Missing-data graceful degradation tests.
- Freshness warning behavior tests.
- 60-second operator comprehension drills.

## Rollout/rollback
- Rollout:
  - pilot on cockpit project.
  - verify operator comprehension tests.
- Rollback:
  - keep last known good html and log failures.

## Risks and mitigations
- Risk: dashboard complexity mirrors system complexity.
  - Mitigation: strict information hierarchy and defaults.
- Risk: stale metrics presented as fresh.
  - Mitigation: mandatory generated_at and source snapshot.

## Resource impact
- UI dev effort: 3 devs in WS-07.
- Runtime overhead: low, local generation only.
- Operational gain: faster incident triage and fewer coordination loops.

## Source pointers
- SRC-D1,SRC-D2,SRC-R7 and VULGARISATION_TAB_SPEC baseline.
