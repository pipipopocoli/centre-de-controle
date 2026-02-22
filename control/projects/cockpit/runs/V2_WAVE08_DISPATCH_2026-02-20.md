# V2 Wave08 Dispatch - 2026-02-20

## Objective
- Close the last Wave07 gaps and remove false degraded runtime signals.

## Priority order
1. Runtime parity fix (`healthcheck` vs real queue state).
2. UI evidence closeout (`ISSUE-CP-0034`).
3. Nova advisory lock (vulgarisation quality + actionability).

## Constraints lock
- WIP max = 5
- Tournament trees preserved and dormant (no auto-dispatch)
- No cross-project contamination
- 2h status cadence (`Now/Next/Blockers`)

## Activation order
1. Send `@victor` prompt.
2. Send `@leo` prompt.
3. Send `@nova` prompt.
4. Wait 15 min for ack.
5. Send specialists (`@agent-1`, `@agent-3`, `@agent-6`, `@agent-7`).

## Dispatch - @victor (CDX lead)
Objective
- Close Wave08 runtime parity: remove false degraded state by aligning runtime state and request ledger.

Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py`
- `/Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/auto_mode_state.json`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/requests.ndjson`
- `/Users/oliviercloutier/Desktop/Cockpit/tests/`

Delegation
- `@agent-1` owns runtime/log parity sync checks
- `@agent-3` owns deterministic healthcheck + non-regression tests

Done
- healthcheck open count matches latest requests ledger
- stale runtime entries are reconciled (no phantom open requests)
- last_tick semantics are explicit and tested

## Dispatch - @leo (AG lead)
Objective
- Close `ISSUE-CP-0034` with final visual evidence and updated scenario statuses.

Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0034-wave07-ui-polish.md`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP01_UI_WAVE07_EVIDENCE.md`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/evidence/`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/project_pilotage.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/project_timeline.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss`

Delegation
- `@agent-6`: scenario matrix pass/fail finalization
- `@agent-7`: screenshot mapping + degraded-state proof

Done
- `CP-0034` moved to Done
- `UI-01/UI-02/UI-03` moved from PENDING to PASS/FAIL with rationale
- screenshot links valid and mapped
- no overlap with Nova service lane

## Dispatch - @nova (AG L1)
Objective
- Lock Wave08 vulgarisation advisory quality for operator decisions.

Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/nova/memory.md`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP01_VULGARISATION_UPGRADE_WAVE07.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md`

Done
- Brief 60s remains deterministic and action-first
- each recommendation has owner + next action + evidence path
- refreshed advisory note has accepted/rejected/pending ledger

## Checkpoints
1. T+15m: ack from Victor/Leo/Nova
2. T+2h: runtime parity patch draft + UI matrix no longer pending
3. T+4h: tests and evidence complete
4. T+6h: closeout packet + STATE/ROADMAP updated
