# Cockpit V2 R1 - Competitor r1-f - Executive Summary

## Context
Cockpit V2 needs an operator-facing vulgarisation experience that works under pressure, offline, and within strict isolation rules. This Round 1 package is plan-only and respects locked constraints: project memory isolation, Option A souls, workspace-only default skill execution, and explicit @clems approval for full access actions.

## Problem statement
Current project state is fragmented across files, logs, and chats. Under incident pressure, operators lose time reconstructing the story, miss blockers, or act on stale context. We need a 60-second comprehension surface that remains reliable during partial failures and does not violate policy boundaries. Situation-awareness and visual-perception evidence supports a layered summary-first interface [P8][P9].

## Proposed design
The plan introduces a per-project Vulgarisation Control Loop with four stages:
1. Ingest and normalize project artifacts into a canonical snapshot.
2. Build a deterministic narrative bundle for replay and auditing.
3. Render an offline HTML dashboard with pressure-first visual hierarchy.
4. Enforce policy gates for risky actions and cross-scope access.

Core outcomes:
- 60-second operator comprehension target as release gate.
- Deterministic replay using run bundle contracts inspired by snapshot and consensus principles [P1][P2][P3].
- Tail-latency control and graceful degradation for reliability [P6].
- Traceability from major claims to evidence and assumptions.

## Interfaces and contracts
Primary contracts:
- Input files: `control/projects/<project_id>/STATE.md`, `ROADMAP.md`, `DECISIONS.md`, `agents/*/state.json`, `chat/*.ndjson`, `skills/skills.lock.json`.
- Snapshot output: `control/projects/<project_id>/vulgarisation/snapshot.json`.
- HTML output: `control/projects/<project_id>/vulgarisation/index.html`.
- Run bundle: immutable folder with input hashes, normalized snapshot, rendered output, manifest.
- UI action: `Update Vulgarisation` (manual trigger, idempotent).

Policy boundaries:
- Workspace-only by default.
- Any outside-workspace read/write requires explicit @clems approval.
- Promotion into Global Brain requires approval + provenance record.

## Failure modes
Primary failure classes and behavior:
- Missing inputs: render placeholders, keep last-good HTML, log warning.
- Corrupt input or schema mismatch: reject current build, preserve previous output, emit error card.
- Slow update path: show stale warning at >24h, critical at >72h.
- Partial renderer crash: degrade charts to textual summary fallback.
- Policy denial: block action and surface reason + approval path.

## Validation strategy
Release gates for Variant F:
- Comprehension gate: operators answer 5 critical questions in <=60 seconds with >=85 percent accuracy (target >=90 percent by sprint 2).
- Reliability gate: replay bundle reproduces identical summary fields for same input hash in 99.9 percent of runs.
- Latency gate: p95 update duration <=6s; p99 <=12s on baseline workstation.
- Safety gate: zero unapproved full-access actions in audit log.
- Clarity gate: reduced misread rate on top-5 incident metrics using ranked encodings [P9].

## Rollout/rollback
Rollout phases:
1. Shadow mode: generate snapshots and HTML without operator dependency.
2. Assisted mode: one-click tab with warning banners; operator confirms decisions manually.
3. Default mode: dashboard is primary triage surface, with drill-down links.
4. Hard gate mode: release blocked if comprehension or replay gates fail.

Rollback model:
- Immediate switch to last-good HTML artifact.
- Disable auto-refresh and freeze to read-only summary.
- Revert feature flags per module (ingest, renderer, cost panel, skill panel).
- Use run bundle diff to identify regression origin.

## Risks and mitigations
- Risk: information overload in one-screen summary. Mitigation: strict card cap, progressive disclosure, UX gate from day 1 [P8][ASSUMPTION-A2].
- Risk: stale data drives bad decisions. Mitigation: freshness badges, hard stale alarms, update cadence SLO.
- Risk: policy bypass through helper scripts. Mitigation: approval middleware and immutable audit trail.
- Risk: team coordination bottlenecks in 40-dev program. Mitigation: workstream ownership + dependency map.
- Risk: optional semantic retrieval introduces contamination concerns. Mitigation: keep semantic layer off by default and project-scoped only.

## Resource impact
Estimated 12-week delivery envelope for 40-dev team:
- 8 workstreams, 52 planned tickets, weekly integration train.
- Engineering: 10,800-12,400 person-hours.
- Infra: local-first runtime, low central dependency.
- API/token: bounded by summarization cadence, modeled in budget scenarios.
- Operational gain target: 30-45 percent faster incident triage, pending validation [ASSUMPTION-A1][ASSUMPTION-A2].
