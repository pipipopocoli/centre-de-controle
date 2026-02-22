# 01 - Executive Summary (competitor-r1-e)

## Context
Cockpit V2 needs a release gate that prevents quality drift while preserving team speed. The locked constraints require project isolation, explicit approvals for full access, and a stable souls model (persistent clems/victor/leo + ephemeral workers).

## Problem statement
Current planning quality is high, but execution quality can regress if we do not standardize replay packs, benchmark sets, and release-blocking thresholds. We need a non-regression harness that is deterministic, auditable, and cheap enough to run on every merge candidate.

## Proposed design
Build an Eval Control Plane around five components:
1. Scenario Registry (versioned benchmark catalog).
2. Replay Orchestrator (deterministic replay using run bundles).
3. Metrics Aggregator (quality, reliability, latency, cost).
4. Gate Evaluator (hard/soft thresholds with severity policy).
5. Evidence Publisher (signed artifacts for review and rollback).

Variant E emphasis:
- benchmark selection strategy (golden set + stress set + incident replay set),
- patch quality metrics,
- regression gates with release blockers,
- explicit false-positive and false-negative handling.

## Interfaces and contracts
- Run bundle contract: `run_manifest.json`, `events.ndjson`, `patch.diff`, `metrics.json`, `verdict.json`, `env.lock`.
- Gate verdict contract: `PASS`, `SOFT_FAIL`, `HARD_FAIL`, `OVERRIDE_APPROVED`.
- Approval contract: any override of `HARD_FAIL` requires `@clems` + recorded rationale.
- Isolation contract: project memory and artifacts never cross project boundaries by default.

## Failure modes
- Flaky tests inflate false positives.
- Missing replay context causes false negatives.
- Metric drift after harness updates can hide regressions.
- Cost spikes from oversized benchmark suites block developer throughput.

## Validation strategy
- Backtest the harness on last 50 known changes and past incidents.
- Calibrate thresholds using confusion matrix targets (FP <= 5 percent, FN <= 2 percent on critical class).
- Run shadow gates for 2 weeks before full enforcement.
- Track gate precision/recall trend weekly with alerting.

## Rollout/rollback
- Rollout: Shadow mode -> Soft block mode -> Hard block mode by risk tier.
- Rollback: If gate instability appears, revert to previous harness version + freeze new thresholds.
- Emergency mode: temporary override with `@clems` and postmortem within 24h.

## Risks and mitigations
- Risk: over-blocking due to flaky suites.
  - Mitigation: flake quarantine lane + retry policy + owner SLA.
- Risk: under-blocking due to sparse benchmarks.
  - Mitigation: mandatory incident replay promotion each week.
- Risk: governance bypass.
  - Mitigation: signed override trail and weekly audit.

## Resource impact
- Infra: 80 to 120 CPU-hours/day for baseline gate runs at 40-dev scale.
- Storage: 200 to 400 GB/month for replay packs and metrics history.
- Team: 6 FTE platform + 3 FTE quality engineering + rotating owners in each stream.
- Runtime overhead target: median gate wall time <= 25 minutes.

## Evidence pointers
See `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-e/EVIDENCE/01_SOURCE_INDEX.md` and `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-e/EVIDENCE/02_ASSUMPTIONS_TABLE.md`.
