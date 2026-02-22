# eval_contracts.md

## Stream
- Stream S5 L5 Eval harness
- Generated at: 2026-02-18T20:38:59+00:00
- Policy version: l5-default-v1

## Registry schema
| field | type | required | notes |
|---|---|---|---|
| version | string | yes | non-empty version id |
| scenarios[] | list<object> | yes | sorted by scenario_id |
| scenario_id | string | yes | unique |
| suite_id | enum(B0,B1,B2,B3) | yes | benchmark lane |
| risk_tags | list<string> | yes | non-empty tags |
| active | boolean | yes | scenario enabled flag |
| owner_role | string | yes | accountable owner |

## Replay manifest schema
| field | type | required | notes |
|---|---|---|---|
| run_id | string | yes | replay run key |
| project_id | string | yes | project isolation key |
| git_sha | string | yes | candidate revision |
| scenario_profile | string | yes | suite profile |
| toolchain_hash | string | yes | deterministic runtime id |
| policy_version | string | yes | gate policy id |
| created_at | ISO-8601 | yes | event timestamp |
| seed | int/string | no | deterministic seed |
| trace_id | string | no | trace correlation id |

## Metrics schema
| field | type | required |
|---|---|---|
| suite | string | yes |
| pass_rate | float | yes |
| critical_regressions | int | yes |
| flake_delta_pp | float | yes |
| p95_runtime_min | float | yes |
| token_cost_usd | float | yes |
| policy_violation_count | int | yes |
| replay_fidelity_score | float | yes |
| baselines | object | yes |

## Verdict schema
| field | type |
|---|---|
| verdict | PASS \| SOFT_FAIL \| HARD_FAIL \| OVERRIDE_APPROVED |
| blocking_reasons | list<string> |
| soft_reasons | list<string> |
| policy_version | string |
| override_ref | string or null |

## Override audit schema
| field | type | required |
|---|---|---|
| run_id | string | yes |
| project_id | string | yes |
| actor | string | yes (@clems only for hard-fail override) |
| approval_ref | string | yes |
| rationale | string | yes |
| verdict_before | string | yes |
| verdict_after | string | yes |
| policy_version | string | yes |
| created_at | ISO-8601 | yes |

## CAP mapping
| capability_id | implementation | test gate |
|---|---|---|
| CAP-L5-001 | scenario_registry schema validation | benchmark catalog versioning pass |
| CAP-L5-002 | replay_manifest schema validation | replay bundle schema validation pass |
| CAP-L5-003 | threshold policy parser and validator | gate threshold parser and validation pass |
| CAP-L5-004 | confusion matrix + target validation | fp/fn confusion matrix target pass |
| CAP-L5-005 | release verdict policy engine | pass/soft_fail/hard_fail policy applied |
| CAP-L5-006 | override audit append with approval gate | override requires approval + rationale |

## Default threshold policy
- Hard rules:
  - critical_regressions > 0
  - pass_rate < 0.99 on B1
  - policy_violation_count > 0
  - replay_fidelity_score < 0.95
- Soft rules:
  - flake_delta_pp > 1.0
  - p95_runtime_min > baseline * 1.25
  - token_cost_usd > baseline * 1.20

## Override authority
- Hard-fail override requires `@clems`.
- `approval_ref` and rationale are mandatory.
- Every approved override must be appended to project-local audit NDJSON.
