# 02 - Architecture (Eval-first Cockpit V2)

## Context
Cockpit V2 coordinates multiple agents and needs deterministic, reviewable outputs. We need architecture that supports non-regression gating without violating project isolation or approval policy.

## Problem statement
Without a dedicated evaluation architecture, release quality depends on ad-hoc checks. This creates blind spots: low replay fidelity, inconsistent metrics, and fragile approval decisions.

## Proposed design
### 1) Logical architecture
- Control Plane:
  - `scenario-registry`: benchmark metadata, versioning, risk tags.
  - `eval-scheduler`: queueing, shard planning, fairness, retries.
  - `gate-engine`: applies threshold policies by severity.
  - `report-service`: publishes human + machine readable evidence.
- Data Plane:
  - `runner-workers`: execute replay packs in hermetic workspaces.
  - `artifact-store`: immutable replay bundles.
  - `metrics-store`: timeseries and run summaries.
- Governance Plane:
  - `approval-service`: full-access/override gating with @clems authority.
  - `audit-log`: append-only decision records.

### 2) Data flow
1. Candidate patch enters eval queue.
2. Scheduler builds run plan from scenario registry.
3. Workers execute deterministic replay.
4. Metrics aggregator computes quality signals.
5. Gate engine emits verdict.
6. Report service publishes release packet.

### 3) Deterministic replay bundle
Bundle fields:
- `bundle_id`, `project_id`, `git_sha`, `scenario_set_version`
- `env.lock` (toolchain and dependency pinning)
- `inputs/` (fixtures, seeds, policy context)
- `events.ndjson` (ordered trace)
- `outputs/` (patch, logs, metrics)

Replay rule:
- identical bundle + identical runtime image must produce equivalent verdict with tolerance bands.

## Interfaces and contracts
### API contracts
- `POST /eval/runs`
  - Input: `{project_id, git_sha, scenario_profile, mode}`
  - Output: `{run_id, status, eta_minutes}`
- `GET /eval/runs/{run_id}`
  - Output: run status + partial metrics + gate preview.
- `POST /eval/gates/adjudicate`
  - Input: `{run_id, action, reason, actor}`
  - Action in: `APPROVE_OVERRIDE`, `REJECT_OVERRIDE`, `RETRY`, `QUARANTINE`.

### Contract invariants
- No cross-project artifact lookup by default.
- Override on hard fail requires `actor=@clems`.
- Every gate decision references immutable bundle hash.

## Failure modes
- Queue starvation under peak load.
- Non-hermetic runners create nondeterminism.
- Stale registry definitions invalidate benchmark meaning.
- Metric ingestion lag causes delayed blocking signal.

## Validation strategy
- Chaos tests on scheduler and artifact store.
- Replay determinism test on fixed seed matrix.
- Contract tests for gate API and audit trail.
- Weekly benchmark curation review with drift report.

## Rollout/rollback
- Phase 1: deploy control plane with read-only shadow reports.
- Phase 2: enforce soft gates on medium risk streams.
- Phase 3: enforce hard gates on all release paths.
- Rollback: route to previous gate policy version and disable new scenario profiles.

## Risks and mitigations
- Risk: architecture complexity overrun.
  - Mitigation: strict MVP boundaries and ticketized workstream slicing.
- Risk: false confidence from partial datasets.
  - Mitigation: mandatory incident replay import and red-team scenarios.
- Risk: operational burden for 40-dev scale.
  - Mitigation: auto-sharding, nightly heavy suites, and owner rotation.

## Resource impact
- Compute: burst capacity for parallel workers (20 to 60 concurrent jobs).
- Storage: immutable artifacts with retention tiers.
- Ops: 24x5 observability with on-call for gate outages.
- DevEx: target 95th percentile gate runtime <= 45 minutes.

## References
Key sources: [P1][P2][P3][P4][P8][R1][R2][R3][R5][S1][S3].
