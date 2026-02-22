# Cockpit V2 R1 - Architecture (Variant F UX Vulgarisation)

## Context
This architecture is designed for a project-local, offline-first vulgarisation tab that remains readable under pressure while preserving reliability and policy constraints. The design borrows from deterministic distributed execution ideas (ordered events, snapshots, replay) adapted to local project orchestration [P1][P2][P3].

## Problem statement
Without a strict architecture contract, the dashboard becomes a fragile aggregation script: nondeterministic rendering, stale or conflicting states, and inconsistent operator cues. We need a system that is deterministic, auditable, and fast enough for incident-time decisions.

## Proposed design
### 1) Module map
1. `source_adapters`
- Reads approved project-local artifacts.
- Converts raw records to typed events.

2. `snapshot_builder`
- Applies deterministic ordering and dedupe.
- Produces canonical `snapshot.json`.

3. `narrative_compiler`
- Builds top-line summary, blockers, and recommended actions.
- Uses bounded model calls (optional) and strict token ceilings.

4. `renderer`
- Generates offline HTML, CSS, JS assets.
- Applies visual priority policy for pressure mode.

5. `orchestrator`
- Handles update workflow, retries, timeout/backoff, and idempotency.
- Schedules manual and optional timed updates.

6. `replay_bundle`
- Persists immutable run bundle with hashes and manifest.
- Supports deterministic replay and regression triage.

7. `policy_gate`
- Enforces workspace boundary and approval-required actions.

### 2) Data flow
- Step A: `Update Vulgarisation` command starts `run_id`.
- Step B: adapters collect source files and hash every input.
- Step C: snapshot builder emits canonical state.
- Step D: compiler creates summary layer.
- Step E: renderer writes `index.html` atomically.
- Step F: replay bundle and metrics are committed.
- Step G: UI refreshes and shows freshness metadata.

### 3) Deterministic execution boundaries
- Stable sort keys for all lists (`timestamp`, `source`, `id`).
- Pure function transform from snapshot to summary cards.
- Explicit timezone normalization (UTC storage, local display).
- Replay pass compares output hashes for drift detection.

### 4) State machine for update run
- `QUEUED -> INGESTING -> SNAPSHOTTED -> COMPILED -> RENDERED -> COMMITTED -> DONE`
- Error edges:
  - `INGESTING -> FAILED_INPUT`
  - `COMPILED -> FAILED_MODEL`
  - `RENDERED -> FAILED_RENDER`
  - any failed state can transition to `ROLLED_BACK_LAST_GOOD`
- Retry policy: max 3 retries, exponential backoff (0.5s, 2s, 8s), jitter 10 percent [P6].

## Interfaces and contracts
### Contract A: input boundary
Allowed read roots:
- `control/projects/<project_id>/`

Denied by default:
- Any outside-workspace path without approval token.

### Contract B: canonical snapshot schema
File: `control/projects/<project_id>/vulgarisation/snapshot.json`

```json
{
  "project_id": "cockpit",
  "run_id": "2026-02-18T10:04:12Z_7f2a",
  "generated_at": "2026-02-18T10:04:18Z",
  "source_snapshot": {
    "state_md_sha256": "...",
    "roadmap_md_sha256": "...",
    "decisions_md_sha256": "..."
  },
  "phase": {
    "name": "Implement",
    "confidence": 0.82
  },
  "signals": {
    "blockers_count": 2,
    "failing_tests": 4,
    "open_tickets": 19,
    "stale_hours": 3.1
  },
  "skills": {
    "active": 9,
    "reviewed": 5,
    "untrusted": 0
  }
}
```

### Contract C: run bundle
Path: `control/projects/<project_id>/vulgarisation/runs/<run_id>/`
- `inputs_manifest.json`
- `snapshot.json`
- `summary.json`
- `index.html`
- `metrics.json`
- `manifest.sha256`

Replay rule:
- Same `inputs_manifest.json` and config must regenerate same `summary.json` field values and same `index.html` structural hash.

### Contract D: UI panel API
Each panel receives:
- `data`
- `freshness`
- `status` (`ok|warn|critical|unavailable`)
- `fallback_text`

If `status=unavailable`, panel must still render fallback text.

## Failure modes
- Source drift during run: lock source snapshot at ingestion start and reject mid-run file changes.
- Partial write corruption: write to temp file then atomic rename.
- Chart engine mismatch: use textual fallback and emit warning chip.
- Summary model timeout: degrade to deterministic templated summary.
- Queue saturation: activate fairness policy and per-project concurrency caps [P7].

## Validation strategy
- Architecture contract tests for every interface (schema validation via JSON Schema [S3]).
- Replay determinism suite with fixed fixtures (1000-run batch).
- Chaos tests: killed render process, corrupted input, delayed IO.
- Performance tests: p95 update latency and p99 queue wait by project size.
- Human factors tests: reading order and miss-rate in pressure scenarios [P8][P9].

## Rollout/rollback
Rollout sequence:
1. Enable adapters and snapshot builder in passive mode.
2. Enable renderer with hidden route.
3. Enable operator tab for pilot projects.
4. Enable scheduler and policy gate globally.

Rollback sequence:
1. Freeze scheduler.
2. Serve last-good `index.html`.
3. Disable failing module by feature flag.
4. Re-run replay bundles to locate regression.

## Risks and mitigations
- Nondeterministic summary model outputs. Mitigation: deterministic template mode + bounded model usage.
- Queue head-of-line blocking. Mitigation: weighted fair queue and project quotas.
- Hidden dependency on internet assets. Mitigation: package all assets local, no CDN.
- Scope creep into cross-project analysis. Mitigation: hard path guards and policy checks.

## Resource impact
- Storage: run bundles add 200-600 KB per update run.
- CPU: mostly rendering and schema checks, no heavy server dependency.
- Dev effort: 3 backend pods, 2 frontend pods, 1 platform pod, 1 QA pod.
- Operational overhead: moderate, mostly monitoring queue and stale-rate metrics.
