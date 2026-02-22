# Claims to Evidence Map - competitor-r1-e

| claim_id | claim | evidence | status |
|---|---|---|---|
| C1 | Deterministic replay bundles reduce ambiguity and improve regression triage. | [P1][P5][R3][R4] | SOURCE_BACKED |
| C2 | Multi-suite benchmark portfolios improve robustness vs single benchmark gating. | [P2][P3][P4][R1][R2] | SOURCE_BACKED |
| C3 | Hard/soft gate split lowers unsafe releases while preserving throughput. | [P8][S3] + [A1] | MIXED |
| C4 | Isolation-first memory policy is required to avoid cross-project contamination. | [S1] + governance constraints + [A5] | MIXED |
| C5 | FP/FN calibration should be measured via confusion matrix and incident backfill. | [P3][P4][P7][R1] | SOURCE_BACKED |
| C6 | 40-dev rollout needs ticketized workstreams with strict owner model. | Program operating rules + [A2][A6] | ASSUMPTION_DRIVEN |
| C7 | Cost guardrails can cap token spend without weakening critical safety checks. | [R1][R2][R6] + [A4] | MIXED |

Status legend:
- SOURCE_BACKED: direct source support.
- MIXED: source support + explicit assumptions.
- ASSUMPTION_DRIVEN: operational choice requiring local validation.
