# Roadmap

## Vision
- Ship Cockpit V2 as an operator-first orchestrator for complex existing repositories, with stable runtime control and strict project isolation.

## Current checkpoint
- Wave16 codex-only consolidation active due AG outage.
- Wave16 backend/advisory lock is in repository and moving to final push closeout.

## Priorities
- P0: codex-only outage mode + credit guard until Feb 26.
- P1: keep onboarding + mission-critical gate deterministic.
- P2: keep dual-root recency healthy via pulse/check cadence.
- P3: keep retention operator digest current and actionable.
- P4: keep tournament preserved and dormant.

## Wave16 sequence
1. Lock codex-only outage mode (`CP-0056`) and pause AG/UI lane.
2. Apply credit guard policy (`CP-0058`) with effective action cap = 1.
3. Validate onboarding + recency tests + codex-only dispatch test.
4. Run dual-root pulse/check cadence and publish runbook (`CP-0059`).
5. Publish retention advisory digest (`CP-0060`).
6. Consolidate/push snapshot with receipt (`CP-0057`).

## Next wave entrypoint
1. Keep lead-first dispatch policy (`@victor`, `@nova`) while AG is unavailable.
2. Keep `@leo` lane paused until AG credits recover.
3. Open feature issues only after runtime gates stay green at two checkpoints.
4. Preserve tournament dormant guard.

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
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE_MAP_WAVE16_CP0056_CP0060.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE16_BACKEND_ONBOARDING_RECENCY_2026-02-23T1318Z.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/WAVE16_RETENTION_VISIBILITY_ADVISORY_2026-02-23.md
