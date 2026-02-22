# 01_EXEC_SUMMARY - competitor-r1-c (Variant C Router Orchestration)

## Context
- Round 1 isolated tournament plan for Cockpit V2.
- Variant C focus: router runtime, orchestration graph, scheduling policy, queue model, fallback tiers, anti-thundering-herd fairness.
- Locked constraints are respected: Global Brain available, project memory isolated, Souls Option A, workspace-only by default, full access gates via @clems.

## Problem statement
- Cockpit V2 needs a deterministic orchestration core that can coordinate many agents and providers without state drift, runaway retries, or budget shocks.
- Current planning baseline lacks a decision-complete contract for provider routing, queue fairness, and durable replay.

## Proposed design
- Adopt a three-plane model:
  - Control plane: mission intake, policy checks, approval gates.
  - Data plane: execution queues, provider adapters, replay bundles.
  - Trust plane: skills and memory isolation policy checks.
- Use a Router Orchestration Graph (ROG) with explicit nodes:
  - RouterFrontDoor
  - PolicyGate
  - Scheduler
  - QueueStore
  - ProviderAdapter(Codex)
  - ProviderAdapter(Antigravity)
  - OptionalProviderAdapter(disabled by default)
  - ReplayWriter
  - EvalGate
- Scheduling policy:
  - Two queues: interactive and batch.
  - Weighted fair scheduling with starvation guard.
  - Anti-thundering-herd jitter and token bucket admission controls.
- Fallback tiers:
  - Tier 0: same provider retry with bounded backoff.
  - Tier 1: alternate provider in same capability class.
  - Tier 2: degraded safe-mode workflow with reduced tooling.
  - Tier 3: hold-and-escalate to @clems.

## Interfaces and contracts
- Router request contract:
  - run_id
  - project_id
  - mission_id
  - actor_role
  - requested_capability
  - budget_envelope
  - trace_context
- Scheduler contract:
  - queue_class
  - priority_weight
  - fairness_credit
  - deadline_hint
- Replay bundle contract:
  - event_log
  - tool_call_log
  - policy_decision_log
  - trace_ids
  - checksum
- Approval contract:
  - approval_id
  - requester
  - reason
  - scope
  - status

## Failure modes
- Queue surge causes thundering herd and latency collapse.
- Provider outage causes repeated retries and cost spikes.
- Policy gate bypass causes unsafe scope escalation.
- Replay bundle corruption blocks incident analysis.
- Memory contamination across projects.

## Validation strategy
- Deterministic replay pass rate >= 99 percent on replay corpus.
- p95 queue wait under target for interactive class.
- Starvation incidents = 0 in mixed-load soak tests.
- Policy bypass incidents = 0 in adversarial eval.
- Cross-project memory retrieval attempts blocked by default.

## Rollout/rollback
- Rollout:
  - Phase 1: router skeleton + queue + replay writer.
  - Phase 2: fairness logic + fallback tiers.
  - Phase 3: eval gates + cost guardrails.
- Rollback:
  - Feature flags per fallback tier.
  - Immediate disable of optional provider adapter.
  - Revert to single-provider safe mode.

## Risks and mitigations
- Risk: complexity expansion beyond team bandwidth.
  - Mitigation: strict ticketized WBS and dependency gates in 06_ROADMAP_40DEVS.md.
- Risk: unstable optional provider adapter.
  - Mitigation: disabled by default until eval gate pass.
- Risk: budget variance from burst workloads.
  - Mitigation: budget envelopes with hard stop and escalation.

## Resource impact
- People: 40-dev parallel plan across 7 workstreams.
- Time: 4 delivery milestones, 16 weeks total.
- Infra: queue store, telemetry pipeline, replay storage.
- Cost: modeled in 07_RESOURCE_BUDGET.md with small/medium/large/xlarge scenarios.

## Decision summary
- Choose orchestration-first architecture with durable replay and fair scheduling.
- Keep policy and memory isolation as first-class constraints.
- Prioritize stability and deterministic behavior over raw throughput.

## Source pointers
- Evidence map: `EVIDENCE/04_CLAIM_MATRIX.md`.
- Key references: SRC-P1, SRC-P5, SRC-P6, SRC-P8, SRC-P9, SRC-P10, SRC-R1, SRC-R2, SRC-R4, SRC-D1, SRC-D2.
