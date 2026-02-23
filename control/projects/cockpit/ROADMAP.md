# Roadmap

## Vision
- Ship Cockpit V2 as an operator-first orchestrator for complex existing repositories, with stable runtime control and strict project isolation.

## Current checkpoint
- Wave14 backend and residual lanes complete with proof (CP-0048..CP-0052 all closed).
- Wave15 closeout complete: dual-root recency lock + runbook + closeout sync.

## Priorities
- P0: next feature wave kickoff from green runtime baseline.
- P1: keep mission-critical gate and onboarding stable.
- P2: keep recency cadence stable on repo + AppSupport.
- P3: retain operator clarity (UI evidence + retention reports).
- P4: keep tournament preserved and dormant.

## Wave15 sequence
1. Close Wave14 residual docs: CP-0050 and CP-0051 moved to Ship/Done with proofs.
2. Patch healthcheck recency semantics (`stale_kpi_snapshot` soft warning on fresh pulse).
3. Run deterministic tests and dual-root pulse/check commands.
4. Publish operator recency runbook and closeout receipt.
5. Mark CP-0053, CP-0054, CP-0055 as Done with references.

## Next wave entrypoint
1. Keep lead-first dispatch policy (`@victor`, `@leo`, `@nova`) and 15m ack gate.
2. Open feature issues only after runtime gates stay green at two checkpoints.
3. Preserve provider policy (Codex + Antigravity) and tournament dormant guard.

## Daily control gates
- pending stale (24h+) must be 0
- stale heartbeats (1h+) must be <= 2
- queued runtime requests must be <= 3
- repo root healthcheck must be healthy
- AppSupport root healthcheck must be healthy
- no tournament auto-dispatch during implementation lanes

## Active source of truth
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE13_CP0015_CP0042_CLOSEOUT_2026-02-23T0909Z.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE14_VICTOR_LANE_LOCK_2026-02-23T1026Z.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/WAVE14_CP0050_MEMORY_RETENTION_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/WAVE14_UI_EVIDENCE_MAPPING.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE15_CLOSEOUT_RECEIPT_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE15_OPERATOR_RECENCE_RUNBOOK_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/cockpit_v2_final_plan.docx
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/WAVE14_INPUT_FROM_COCKPIT_V2_FINAL_PLAN_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE14_DISPATCH_2026-02-23.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE_MAP_WAVE15_CP0053_CP0055.md
