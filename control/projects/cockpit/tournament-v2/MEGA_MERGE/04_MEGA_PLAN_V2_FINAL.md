# 04_MEGA_PLAN_V2_FINAL

## 1) Executive summary
This document is the canonical merged plan for Cockpit V2, built from all six R1 competitors using a layered hybrid model and anti-overlap contracts.

Goal:
- Deliver a stable, auditable, operator-clear, resource-feasible multi-agent system plan before any runtime implementation.

Core strategy:
- Keep deterministic reliability and strict policy boundaries.
- Add scalable router orchestration with controlled fallback tiers.
- Keep memory isolated per project with explicit global promotion gate.
- Enforce non-regression release gates.
- Provide operator-first vulgarisation that works offline and under pressure.
- Quantify capacity and cost with hard budget guardrails.

## 2) Locked constraints
- Global Brain is available for generic learnings only.
- Project memory is isolated by default.
- Souls Option A is fixed:
  - clems L0 persistent
  - victor L1 persistent
  - leo L1 persistent
  - workers ephemeral and project-scoped
- Skills are executable and workspace-only by default.
- Full access actions require explicit @clems approval.

## 3) Target architecture (7-layer)

### L1 Reliability core (owner: competitor-r1-a)
- Deterministic run bundle contract.
- Append-only event log + materialized views.
- Idempotent write boundaries.
- Crash recovery and checksum integrity checks.

### L2 Skills supply chain + governance (owner: competitor-r1-b)
- Trust tiers and signed lockfile.
- Skill lifecycle state machine.
- Approval gate for full access.
- Quarantine and revocation flow.
- Cross-runtime policy parity gate.

### L3 Router/orchestration multi-agents (owner: competitor-r1-c)
- Router front-door contract.
- Weighted fair scheduler with anti-starvation rules.
- Burst protection and anti-thundering-herd controls.
- Fallback tiers T0..T3.
- Budget envelope enforcement in dispatch path.

### L4 Memory engine + isolation (owner: competitor-r1-d)
- Project-scoped namespaces for memory.
- FTS-first retrieval baseline.
- Optional semantic lane behind gate.
- Compaction and retention contracts.
- Global promotion queue with approval and de-identification proof.

### L5 Eval harness + non-regression (owner: competitor-r1-e)
- Scenario registry and replay bundle schema.
- Metric contracts and threshold policy.
- FP/FN calibration with confusion matrix.
- Release verdict policy (pass/soft_fail/hard_fail/override).
- Override audit trail.

### L6 UX vulgarisation + operator flow (owner: competitor-r1-f)
- 60-second comprehension target.
- Action-first card hierarchy.
- Pressure mode display behavior.
- Freshness and stale warning contracts.
- Evidence links and accessibility fallback mode.

### L7 Resource/cost/capacity (owner: competitor-r1-b)
- Cost telemetry event schema.
- small/medium/large/xlarge usage scenarios.
- Budget guardrails and alert routing.
- Capacity SLO and staffing model.
- Break-even matrix subscription vs API.

## 4) Canonical interfaces and data contracts

### 4.1 Run bundle contract
- `run_id`
- `project_id`
- `input_hash`
- `policy_hash`
- `tool_calls[]`
- `events.ndjson`
- `outputs_hash`
- `trace_ids[]`
- `verdict`

### 4.2 skills.lock contract
- `skill_id`
- `repo_url`
- `commit_sha`
- `artifact_digest`
- `trust_tier`
- `approved_by`
- `approved_at`
- `scope`
- `status`

### 4.3 Router request contract
- `run_id`
- `project_id`
- `requested_capability`
- `priority`
- `budget_envelope`
- `approval_ref`
- `trace_context`

### 4.4 Memory request contract
- `project_id`
- `query`
- `mode` (`fts` or `hybrid`)
- `top_k`
- `streams[]`

### 4.5 Eval contract
- `scenario_id`
- `suite_id`
- `metrics`
- `thresholds`
- `verdict`
- `override_ref`

### 4.6 Cost event schema
- `run_id`
- `agent_id`
- `model`
- `input_tokens`
- `output_tokens`
- `cached_tokens`
- `elapsed_ms`
- `cost_estimate`

## 5) End-to-end flow
1. Intake receives mission packet.
2. Policy gate validates scope and approvals.
3. Router schedules run in interactive or batch lane.
4. Skills execute under lockfile and trust-tier policy.
5. Memory read/write remains project-scoped.
6. Replay bundle and telemetry events are persisted.
7. Eval harness computes verdict.
8. Operator tab shows decision summary and next action.
9. Release decision follows verdict policy.

## 6) 40-dev implementation structure

### Stream map
- Stream S1 Reliability core (8 dev)
- Stream S2 Skills governance (7 dev)
- Stream S3 Router orchestration (7 dev)
- Stream S4 Memory isolation (6 dev)
- Stream S5 Eval harness (5 dev)
- Stream S6 Operator UX (4 dev)
- Stream S7 Resource/cost model (3 dev)

Total: 40 dev

### Program timeline (16 weeks)
- Phase P1 (weeks 1-4): contracts + baseline skeleton
- Phase P2 (weeks 5-8): core implementation + dual-write and shadow gates
- Phase P3 (weeks 9-12): hardening, conformance, non-regression
- Phase P4 (weeks 13-16): operator polish, load tuning, release readiness

## 7) Dependencies and ordering
- L1 and L2 must reach gate pass before L3 hard rollout.
- L3 scheduler must be stable before large-scale eval benchmarking.
- L4 promotion queue cannot open until L2 approval pipeline is live.
- L5 hard-fail gates require L1 run bundle stability.
- L6 pressure mode relies on L5 verdict payload and L7 freshness metrics.
- L7 budget guardrails must be active before high-volume tests.

## 8) Risk model and mitigations

### Top risks
- R1: policy drift across runtimes.
- R2: replay non-determinism under retries.
- R3: cost spikes during scale tests.
- R4: contamination risk in memory promotion.
- R5: operator overload from dense dashboards.

### Mitigations
- Runtime parity conformance gate (L2).
- Idempotent boundaries and replay hash checks (L1).
- Hard budget envelopes and alerting (L7).
- Approval + de-identification gate on promotion (L4).
- Action-first cards and pressure mode drills (L6).

## 9) Test and acceptance plan

### Gate tests
- G1 Reliability:
  - crash injection recovery
  - replay determinism 10x
- G2 Governance:
  - no full-access without approval
  - lockfile signature validation
- G3 Router:
  - fairness and starvation
  - fallback tier transitions
- G4 Memory:
  - cross-project contamination sentinel
  - compaction and restore
- G5 Eval:
  - threshold correctness
  - fp/fn calibration integrity
- G6 UX:
  - 60-second comprehension drill >=85 percent
  - stale warning behavior
- G7 Cost:
  - scenario model consistency
  - hard-stop budget triggers

### Acceptance criteria
- No unresolved conflict in capability registry.
- Constraint compliance is 100 percent.
- Every stream has DoD + verification evidence.
- Operator summary is understandable in <=60 seconds.

## 10) Rollout and rollback

### Rollout strategy
- Stage 1: shadow contracts and telemetry only.
- Stage 2: dual-write and soft policy enforcement.
- Stage 3: hard policy and hard release gates.
- Stage 4: scale validation and final readiness packet.

### Rollback strategy
- Rollback by layer with feature flags.
- Keep last known good run bundle and policy bundle ids.
- Disable optional semantic and optional provider features first.
- Escalate critical rollback decisions to @clems.

## 11) Operational cadence
- Daily: state review, blockers, gate drift checks.
- Weekly: conflict/defer review, risk trend review, budget trend review.
- Milestone: phase gate review with evidence packet.

## 12) Final implementation lock
This plan is decision-complete for implementation planning.
No further architecture decisions are required before dispatching execution streams.
