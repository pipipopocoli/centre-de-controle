# R1 Score Detail Internal - Tournament V2

## Scope
- Round: R1 (6 competitors, isolation mode)
- Date: 2026-02-19
- Evaluator lane: @clems internal scoring
- Confidentiality: numeric detail is internal only (operator + @clems)

## Inputs read
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/RUBRIC_SCORE.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-a/*
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-b/*
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-c/*
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-d/*
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-e/*
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/R1/competitor-r1-f/*

## Completeness check (hard package)
- competitor-r1-a: PASS (01..08 + PROMPTS + EVIDENCE)
- competitor-r1-b: PASS (01..08 + PROMPTS + EVIDENCE)
- competitor-r1-c: PASS (01..08 + PROMPTS + EVIDENCE)
- competitor-r1-d: PASS (01..08 + PROMPTS + EVIDENCE)
- competitor-r1-e: PASS (01..08 + PROMPTS + EVIDENCE)
- competitor-r1-f: PASS (01..08 + PROMPTS + EVIDENCE)

## Evidence floor check
- competitor-r1-a: PASS (declared >=8 papers, >=6 repos, >=2 specs)
- competitor-r1-b: PASS (declared 9 papers, 8 repos, 5 specs)
- competitor-r1-c: PASS (papers/repos/specs split in dedicated evidence files)
- competitor-r1-d: PASS (P1..P9, R1..R8, S1..S3)
- competitor-r1-e: PASS (declared 9 papers, 8 repos, 3 specs)
- competitor-r1-f: PASS (declared 9 papers, 8 repos, 4 specs)

## Normalized extraction table

### competitor-r1-a
- Core architecture thesis: stability-first with deterministic Run Bundle Contract, append-only log + materialized views, two-phase commit for critical transitions.
- Memory isolation model: strict project boundary, promotion gate to Global Brain requires @clems approval.
- Skills governance model: workspace-only default, full-access approval token, pinned commit and checksum.
- Eval harness strength: strong replay/crash/corruption suites; good release blocking logic.
- Vulgarisation quality: clear "Persistence Health" panel, 60-second triage questions.
- Resource model quality: quantified categories but lighter than top packages.
- Major risks + mitigations: complexity and replay cost acknowledged with compaction and phased rollout.
- Key assumptions: approval latency, staffing continuity, semantic optionality.

### competitor-r1-b
- Core architecture thesis: supply-chain-centric architecture with trust/provenance layer, policy control layer, runtime enforcement layer.
- Memory isolation model: project memory policy model with promotion gate and compaction contracts.
- Skills governance model: strongest of round; trust tiers T0-T3, lockfile strictness, lifecycle state machine, cross-runtime conformance.
- Eval harness strength: detailed multi-plane non-regression + release thresholds.
- Vulgarisation quality: strong incident script and reason-code contract for fast ops decisions.
- Resource model quality: strong envelopes and guardrails, explicit stress budget handling.
- Major risks + mitigations: review bottlenecks, latency overhead, parity drift; each mapped to controls.
- Key assumptions: usability of approvals at scale, policy parity Codex/Antigravity.

### competitor-r1-c
- Core architecture thesis: router-orchestration-first with control/data/trust planes and Router Orchestration Graph.
- Memory isolation model: explicit query and promotion contracts, isolation by default, optional layers gated.
- Skills governance model: clear assignment and permission matrix, workspace-first policy.
- Eval harness strength: clear benchmark and gate contracts with replay pack requirements.
- Vulgarisation quality: local offline dashboard with freshness and fail-safe behavior.
- Resource model quality: scenario model and budget policy are clear and actionable.
- Major risks + mitigations: complexity growth, optional adapter risk, burst budget variance.
- Key assumptions: provider parity and fairness metrics remain stable under load.

### competitor-r1-d
- Core architecture thesis: memory-engine-focused stack with FTS baseline, optional semantic lane, promotion queue.
- Memory isolation model: very explicit and strong; contamination prevention is central.
- Skills governance model: role-aware scope controls and tokenized elevated access.
- Eval harness strength: memory-specific gates are good, but system-wide breadth is lower.
- Vulgarisation quality: clear memory-specific decision cards and 60-second model.
- Resource model quality: present but shorter and less decision depth than top entries.
- Major risks + mitigations: overfit to semantic early, policy bypass, trust instability.
- Key assumptions: storage envelope, retrieval determinism, comprehension threshold.

### competitor-r1-e
- Core architecture thesis: eval-control-plane-first to enforce non-regression and release quality.
- Memory isolation model: clean isolation and observability contracts, but less deep than memory-specialized plans.
- Skills governance model: practical tiered model with mission templates and auditability.
- Eval harness strength: strongest in category (benchmark portfolio, FP/FN handling, signed evidence artifacts).
- Vulgarisation quality: excellent release-verdict framing for operators.
- Resource model quality: quantified and practical, with compute/storage envelopes.
- Major risks + mitigations: over-blocking, under-blocking, governance bypass all addressed.
- Key assumptions: budget envelope and threshold calibration quality.

### competitor-r1-f
- Core architecture thesis: operator-first vulgarisation loop with deterministic snapshot/render/update contracts.
- Memory isolation model: solid four-layer model with promotion gate and compaction policy.
- Skills governance model: strong practical controls (lockfile, trust tier, audit trail).
- Eval harness strength: robust and balanced, includes comprehension gate and replay thresholds.
- Vulgarisation quality: best in round for readability and pressure-mode behavior.
- Resource model quality: scenario table + telemetry contracts, good operational realism.
- Major risks + mitigations: overload, stale data, policy bypass, coordination bottlenecks.
- Key assumptions: comprehension gains and cadence performance.

## Rubric scoring (locked weights)
- Stability/reliability: 35
- Architecture/engineering quality: 30
- Clarity/vulgarisation quality: 20
- Resource feasibility: 15
- Bonus: +10 max
- Penalty: -20 max

## Score table (internal)

| competitor_id | stability_35 | quality_30 | clarity_20 | feasibility_15 | bonus_10 | penalty_20 | total | dq |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| competitor-r1-b | 33 | 29 | 17 | 13 | 7 | 0 | 99 | no |
| competitor-r1-c | 32 | 28 | 16 | 13 | 6 | 0 | 95 | no |
| competitor-r1-f | 30 | 26 | 19 | 12 | 6 | 0 | 93 | no |
| competitor-r1-e | 29 | 25 | 17 | 12 | 6 | 0 | 89 | no |
| competitor-r1-a | 31 | 24 | 15 | 11 | 4 | 0 | 85 | no |
| competitor-r1-d | 27 | 22 | 14 | 12 | 4 | 0 | 79 | no |

## Bonus/penalty application notes
- competitor-r1-b: +7 (strong lockfile/trust model + deterministic and actionable eval gates).
- competitor-r1-c: +6 (strong deterministic orchestration + robust fairness/fallback contracts).
- competitor-r1-f: +6 (strong operator clarity plus deterministic run/update boundaries).
- competitor-r1-e: +6 (very strong eval harness and evidence discipline).
- competitor-r1-a: +4 (good deterministic persistence model, lower breadth than top 4).
- competitor-r1-d: +4 (memory isolation depth is strong, overall plan breadth lower).
- Penalties: none applied. No approval boundary violation detected. No cross-project memory bypass proposal detected.

## Ranking and tie-break log
1. competitor-r1-b (99)
2. competitor-r1-c (95)
3. competitor-r1-f (93)
4. competitor-r1-e (89)
5. competitor-r1-a (85)
6. competitor-r1-d (79)

Tie-break usage:
- No equal totals, tie-break not required.

## R2 promotion decision
- Promoted top4:
  - competitor-r1-b
  - competitor-r1-c
  - competitor-r1-f
  - competitor-r1-e

## Notes for operator
- This file is internal by contract. Do not send numeric breakdown to competitors.
- Competitor-facing feedback should include only: verdict, required imports, blockers.
