# Cockpit V2 R1 - Resource and Budget Model

## Context
This budget models the operating envelope for the Variant F plan: offline-first dashboard generation, deterministic replay, and policy-safe orchestration. Numbers are planning estimates with explicit assumptions and validation paths.

## Problem statement
A plan without quantified resource bounds is not execution-ready. We need a realistic envelope for team capacity, compute, storage, and token/API spend that can be validated and adjusted.

## Proposed design
### Budget model dimensions
1. Team capacity (40-dev program).
2. Runtime compute and storage.
3. Token/API spend for optional summarization.
4. QA and operator testing overhead.

### Baseline workload assumptions
- Active projects: 20 [ASSUMPTION-A1].
- Dashboard updates per project per day: 24 (hourly manual or scheduled) [ASSUMPTION-A3].
- Average snapshot size: 220 KB [ASSUMPTION-A8].
- Average run bundle size: 520 KB.
- Summarization model usage: 35 percent of updates [ASSUMPTION-A6].

### Scenario table
| scenario | projects | updates/day/project | model-use ratio | est monthly token volume | est monthly API cost (USD) |
|---|---:|---:|---:|---:|---:|
| conservative | 10 | 12 | 20% | 4.3M | 40-120 |
| baseline | 20 | 24 | 35% | 30.2M | 250-900 |
| stress | 35 | 36 | 50% | 95.3M | 900-2800 |

Token formula (planning):
- `monthly_tokens = projects * updates_per_day * 30 * model_use_ratio * avg_tokens_per_update`
- `avg_tokens_per_update = 6000` (summary + checks).

## Interfaces and contracts
### Budget telemetry contract
File: `control/projects/<project_id>/vulgarisation/costs.json`

```json
{
  "window": "2026-02",
  "update_runs": 720,
  "model_runs": 252,
  "tokens_input": 12600000,
  "tokens_output": 2100000,
  "api_cost_usd": 410.33,
  "last_updated": "2026-02-18T20:00:00Z"
}
```

### Capacity contract
- Squad-level throughput target: 1.3-1.8 tickets/dev/sprint.
- Max concurrent high-risk tickets: 6.
- Any budget overrun >20 percent requires review with @clems.

## Failure modes
- Underestimated model usage spikes cost unexpectedly.
- Replay storage growth exceeds local disk policy.
- Team over-allocation causes quality regressions.
- Budget dashboard stale, hiding overrun signals.

## Validation strategy
- Weekly budget variance report per scenario envelope.
- Daily usage telemetry checks against forecast bands.
- Monthly recalibration of token assumptions from observed medians.
- Storage growth alarms with archive policy dry-run.

## Rollout/rollback
Rollout:
1. Start with conservative scenario limits.
2. Enable baseline caps after 2 stable sprints.
3. Allow stress mode only during incidents with approval.

Rollback:
- If cost variance >30 percent for 2 weeks, disable optional model summarization.
- If storage exceeds threshold, reduce run-bundle retention window.
- If team velocity drops below floor, freeze non-critical UX enhancements.

## Risks and mitigations
- Risk: API pricing volatility. Mitigation: caps, budget guardrails, fallback deterministic summaries.
- Risk: hidden local hardware bottlenecks. Mitigation: profile baseline workstation and set minimum spec.
- Risk: manual testing time underestimated. Mitigation: reserve recurring operator test windows.
- Risk: scope expansion adds uncontrolled cost. Mitigation: ADR gate for new cost-bearing features.

## Resource impact
### People
- 40 contributors total.
- Approx effort: 11,500 person-hours over 12 weeks.

### Infrastructure
- Storage growth baseline: ~7.5 GB/month across 20 projects.
- CPU/RAM: desktop-friendly; no always-on cloud dependency required for core path.

### Financial
- Monthly API spend target band: 250-900 USD in baseline mode.
- Triggered review threshold: >1,100 USD/month baseline or >20 percent forecast variance.

### Operational
- Added FinOps process for weekly variance review.
- Added QA process for comprehension and replay gates.
