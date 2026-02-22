# 01_EXEC_SUMMARY

## Context
Cockpit V2 Round 1 requires a decision-complete planning package under strict constraints: Global Brain stays available, project memory stays isolated by default, souls use Option A (persistent clems/victor/leo, project-scoped ephemeral workers), and full access actions require @clems approval. This competitor variant focuses on stability and persistence first.

## Problem statement
The current risk is not lack of features. The risk is state loss, partial writes, replay drift, and low confidence during crash recovery. Without deterministic persistence contracts, a larger multi-agent runtime will accumulate hidden corruption and expensive incident loops [P2][P6][R1].

## Proposed design
Use a stability-first architecture with atomic persistence, deterministic run bundles, and an explicit retry state machine.

Key decisions:
- D1: Introduce a Run Bundle Contract (RBC) that snapshots input, tool calls, approvals, outputs, and hash chain for deterministic replay.
- D2: Split mutable runtime state into append-only event logs plus materialized views rebuilt from replay [P7][R3].
- D3: Require two-phase commit semantics for critical transitions: `prepare -> commit` with idempotency keys [P8][R1].
- D4: Enforce isolation boundaries: project memory read/write stays project-scoped unless promotion is approved by @clems.
- D5: Add corruption guardrails: checksums, sequence monotonicity, WAL, and periodic consistency probes [R6][P4].

## Interfaces and contracts
High-level contracts:
- Run API: `create_run`, `append_event`, `close_run`, `replay_run`.
- Bundle API: `seal_bundle`, `verify_bundle`, `rehydrate_bundle`.
- Approval API: `request_full_access`, `grant_full_access`, `deny_full_access`, with immutable audit events.
- Memory API: `project_put`, `project_get`, `promote_to_global` where promotion always requires policy gate.

Contract properties:
- Idempotent write keys for every transition.
- Causal ordering by `(project_id, run_id, seq)`.
- Replay determinism validation hash.
- Explicit timeout/backoff policy with jitter and cap.

## Failure modes
Critical failure modes:
- FM1: Crash during commit after side effect call.
- FM2: Duplicate event append from retry storm.
- FM3: Corrupted WAL segment.
- FM4: Split-brain scheduler writing conflicting states.
- FM5: Unapproved full-access action.

## Validation strategy
Validation gates:
- Replay determinism: rerun same bundle and compare hash.
- Crash injection: kill process at each transition boundary and verify recovery.
- Corruption test: mutate WAL byte range and ensure quarantine path triggers.
- Timeout/backoff test: force dependency timeout and verify state machine transitions.
- Policy gate test: assert that all full-access attempts require explicit approval event.

## Rollout/rollback
Rollout:
1. Shadow mode: generate bundles while old path remains primary.
2. Dual write mode: old path + new append-only path.
3. Read switch for selected project(s).
4. Full switch with rollback checkpoint every stage.

Rollback:
- Trigger rollback on determinism mismatch, checksum failure, or policy breach.
- Revert to last validated snapshot and replay event log delta.
- Freeze risky workers and escalate to @clems with incident packet.

## Risks and mitigations
- RISK-A1: Added persistence complexity slows delivery.
  - Mitigation: strict milestone slicing and 40-dev ticket ownership model.
- RISK-A2: Replay cost growth.
  - Mitigation: compaction windows and periodic checkpoints.
- RISK-A3: False confidence from partial tests.
  - Mitigation: mandatory non-regression harness with chaos scenarios.

## Resource impact
- Team: 40 dev plan across platform, memory, policy, reliability, and eval lanes.
- Time: 16-week staged delivery with freeze points.
- Infra: moderate persistent storage increase for event logs and snapshots.
- API/tokens: bounded by approval and workspace-only defaults.

Evidence tags used: [P1][P2][P4][P6][P7][P8][R1][R3][R6][S1][S2].
