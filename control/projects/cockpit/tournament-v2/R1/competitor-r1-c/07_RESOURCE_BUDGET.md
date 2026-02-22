# 07_RESOURCE_BUDGET - Operating Envelope and Cost Model

## Context
- Variant C adds orchestration complexity and must remain feasible under budget constraints.
- This budget aligns with the cost model note and introduces scenario-based limits.

## Problem statement
- Without explicit resource limits, router retries and fanout can create unpredictable token and runtime costs.
- Team capacity can be overloaded by parallel high-risk workstreams.

## Proposed design
### 1) Scenario model
- Small:
  - 120 runs/month
  - 4 agents/run
  - avg input 45k, output 15k, cached input 25k tokens
- Medium:
  - 400 runs/month
  - 6 agents/run
  - avg input 70k, output 25k, cached input 40k
- Large:
  - 900 runs/month
  - 8 agents/run
  - avg input 110k, output 40k, cached input 60k
- XLarge:
  - 1600 runs/month
  - 10 agents/run
  - avg input 150k, output 55k, cached input 80k

### 2) Cost controls
- Budget envelope per run is required at router ingress.
- Hard stop when projected monthly budget exceeds cap.
- Tiered fallback reduces expensive provider usage during spikes.

### 3) Team bandwidth model
- 40 dev team split across 7 workstreams.
- WIP cap per stream to avoid context thrash.
- High-risk stream concurrency limited to 2 major tickets at once.

### 4) Hardware and infra envelope
- Queue store: HA pair with persistent volumes.
- Event store: append-log + compaction workers.
- Replay storage: checksum bundles with retention policy.
- Observability: trace collector and metrics time series backend.

## Interfaces and contracts
### Cost event contract
- run_id
- project_id
- agent_id
- provider
- model
- input_tokens
- output_tokens
- cached_input_tokens
- estimated_cost_usd
- estimated_cost_cad
- timestamp

### Budget policy contract
- monthly_cap_cad
- run_cap_cad
- per_project_cap_cad
- escalation_threshold
- stop_action

## Failure modes
- FM-BUD-01: hidden retries inflate cost above cap.
- FM-BUD-02: missing cost telemetry blocks forecast.
- FM-BUD-03: team over-allocates to same critical path.

## Validation strategy
- Weekly cost report and variance analysis.
- Scenario replay with conservative and optimistic assumptions.
- Load tests to validate run cap and stop action behavior.

## Rollout/rollback
- Rollout:
  - start with conservative caps in M1.
  - tune after M2 telemetry.
- Rollback:
  - lower run caps and disable optional provider paths.

## Risks and mitigations
- Risk: CAD/USD volatility affects budget predictability.
  - Mitigation: monthly sensitivity analysis and reserve margin.
- Risk: cost model misses cached-token effects.
  - Mitigation: explicit cached input field in telemetry schema.

## Resource impact
### People
- 40 dev delivery budget in 16 weeks.
- 2 FTE equivalent for ongoing ops and reporting after launch.

### Time
- Build phase: 16 weeks.
- Stabilization phase: 4 additional weeks.

### Cost assumptions
- See `EVIDENCE/05_ASSUMPTIONS.md` ASSUMPTION-A2 and ASSUMPTION-A5.
- API spend beyond baseline requires @clems approval.
