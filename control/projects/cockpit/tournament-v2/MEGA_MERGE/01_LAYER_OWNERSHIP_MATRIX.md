# 01_LAYER_OWNERSHIP_MATRIX

## Layer ownership table

| layer | owner | mandate | required imports | primary outputs | out of scope |
|---|---|---|---|---|---|
| L1 Reliability core | competitor-r1-a | deterministic reliability and recovery foundation | competitor-r1-b policy hardening, competitor-r1-c retry routing | run bundle contract, idempotent writes, crash recovery model | UI decisions, benchmark policy design |
| L2 Skills supply chain + governance | competitor-r1-b | trust chain, lockfile, lifecycle, revocation | competitor-r1-f operator policy cues, competitor-r1-e gate metrics | trust tier model, skills.lock schema, approval policy | queue scheduling and memory ranking |
| L3 Router/orchestration multi-agents | competitor-r1-c | scheduler, queue fairness, fallback tiers, provider routing | competitor-r1-b conformance policy, competitor-r1-a deterministic replay boundaries | router contracts, scheduling policy, fallback state machine | skill trust model internals |
| L4 Memory engine + isolation | competitor-r1-d | project isolation, retrieval, compaction, promotion gate | competitor-r1-a durability patterns, competitor-r1-e eval observability | memory contracts, compaction and retention policy | provider dispatch and UI layout |
| L5 Eval harness + non-regression | competitor-r1-e | benchmark strategy, release gates, FP/FN calibration | competitor-r1-c scale scenarios, competitor-r1-b security gates | eval schemas, threshold policy, release verdict policy | runtime queue internals |
| L6 UX vulgarisation + operator flow | competitor-r1-f | 60-second comprehension and pressure-mode operation | competitor-r1-e release verdict clarity, competitor-r1-c freshness and health signals | tab spec, card hierarchy, fallback rendering behavior | trust-tier lifecycle internals |
| L7 Resource/cost/capacity | competitor-r1-b | team/cost/capacity model and cost guardrails | competitor-r1-c scenario load realism, competitor-r1-f operator cost readability | resource budget model, telemetry schema, break-even matrix | low-level retry algorithm |

## Canonical interface ownership

| interface domain | canonical owner layer | secondary import layers |
|---|---|---|
| Run bundle and replay contracts | L1 | L3, L5 |
| Skill lock and trust contracts | L2 | L5, L6 |
| Router scheduler and fallback contracts | L3 | L1, L7 |
| Memory retrieval and promotion contracts | L4 | L1, L5 |
| Eval metrics and release verdict contracts | L5 | L2, L6 |
| Operator summary and decision UI contracts | L6 | L5, L7 |
| Cost telemetry and budget policy contracts | L7 | L3, L5 |

## Ownership guardrails
- No layer may redefine another layer's canonical interface.
- Import content is allowed only as extension, not replacement, unless conflict log marks explicit `adopt` override.
- Every layer must expose:
  - inputs
  - outputs
  - owner
  - DoD
  - test_gate

## Stream readiness checks
- Each layer has at least 2 required imports (pass).
- Each layer has one owner only (pass).
- Each interface domain maps to one canonical owner (pass).
