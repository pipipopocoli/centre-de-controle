# 03_CONFLICT_RESOLUTION_LOG

## Rule
Each conflict is resolved once with `adopt`, `reject`, or `defer` and rationale.

## Resolved conflicts

| conflict_id | competing proposals | decision | owner | rationale | impact |
|---|---|---|---|---|---|
| CR-001 | L1 replay contract (r1-a) vs generic replay notes (r1-c) | adopt r1-a core + import r1-c trace tags | L1 | r1-a provides stronger deterministic boundaries | stable replay with routing context |
| CR-002 | Retry model in r1-a vs fallback tiers in r1-c | adopt both with split ownership | L3 | retry local policy and tier fallback are complementary | clearer failover behavior |
| CR-003 | Skill governance minimal model (r1-a/r1-c) vs trust tier full model (r1-b) | adopt r1-b | L2 | stronger supply-chain and audit controls | lower risk of compromised skill execution |
| CR-004 | UI-driven policy hints (r1-f) vs backend-only policy outputs (r1-b) | adopt both, backend canonical | L2/L6 | policy truth stays backend, UX improves operator action speed | fewer policy mistakes |
| CR-005 | Optional semantic retrieval timing in r1-d vs strict FTS-first in r1-f | adopt FTS-first, defer semantic to gated lane | L4 | preserves cost and determinism in early rollout | safer initial release |
| CR-006 | Eval gate strictness in r1-e vs velocity concerns in r1-f | adopt strict gates with override trail | L5 | quality and rollback safety win, override remains possible | controlled release risk |
| CR-007 | Release override authority unclear in some docs | adopt @clems-only for hard fail override | L5 | aligns with locked approval policy | consistent governance |
| CR-008 | Cross-runtime policy parity optional (r1-c) vs required (r1-b) | adopt required parity gate | L2 | prevents provider drift and hidden policy gaps | safer multi-provider operation |
| CR-009 | Cost model granularity medium (r1-a/e) vs deep scenario model (r1-b/c) | adopt deep scenario model | L7 | implementation planning needs quantitative guardrails | better budget control |
| CR-010 | Operator summary verbosity high (r1-e) vs concise pressure mode (r1-f) | adopt concise-first with drill-down | L6 | 60-second requirement prioritized | faster triage |
| CR-011 | Promotion to Global Brain rules vary by detail | adopt strict approval + de-identification proof | L4 | preserves isolation and compliance | reduced contamination risk |
| CR-012 | Memory compaction cadence differs across proposals | defer exact cadence to telemetry gate | L4 | needs measured workload data | avoids premature tuning |
| CR-013 | Queue classes differ (2-class vs multi-class) | adopt 2-class baseline + future expansion defer | L3 | simpler launch with clear migration path | faster implementation |
| CR-014 | Evidence format differs (claim matrix vs free notes) | adopt claim matrix mandatory | L5 | increases traceability and auditability | better post-incident review |
| CR-015 | HTML update cadence manual vs scheduled | adopt manual baseline + optional scheduled mode | L6 | preserves offline safety and control | operationally predictable |
| CR-016 | Skill install trust bootstrapping differs | adopt reviewed candidate tier with no auto-update | L2 | avoids surprise changes and drift | higher reproducibility |
| CR-017 | Deterministic hash scope differs | adopt hash(input, policy, tools, outputs) | L1 | complete deterministic fingerprint needed for replay | robust non-regression |
| CR-018 | FP/FN targets vary across docs | adopt r1-e thresholds as baseline | L5 | r1-e provides explicit calibration method | measurable eval quality |
| CR-019 | Budget stop behavior hard-stop vs warn-only | adopt hard-stop for critical envelope breach | L7 | prevents runaway spend incidents | stronger financial control |
| CR-020 | Stale data UX handling differs | adopt warn >24h, critical >72h | L6 | consistent with strongest operator docs | clearer confidence state |
| CR-021 | Worker lifespan policy differs by strictness | adopt TTL mandatory + forced journal flush | L2 | protects traceability and resource hygiene | cleaner audits |
| CR-022 | Provider fallback tier-1 behavior (same provider retry vs provider switch) | adopt same-provider bounded retry then switch | L3 | balances stability and outage recovery | reduced oscillation |
| CR-023 | Capacity model ownership split between eval and infra | adopt L7 canonical, L5 imported metrics | L7 | one source of truth for cost/capacity | no duplicate budgeting logic |
| CR-024 | Risk panel placement in operator tab varies | adopt action rail fixed position | L6 | pressure-mode decision speed improved | faster blocker resolution |
| CR-025 | Evidence sourcing floor ambiguous in some docs | adopt strict floor from tournament constraints | L5 | prevents weak unsupported claims | consistent quality standard |

## Deferred items
- DF-001: semantic retrieval default enablement criteria
- DF-002: 2-queue to 3-queue migration threshold
- DF-003: long-term retention horizon past initial 16-week program

## Conflict closure status
- Total conflicts logged: 25
- Resolved: 22
- Deferred with gate: 3
- Unresolved without owner: 0
