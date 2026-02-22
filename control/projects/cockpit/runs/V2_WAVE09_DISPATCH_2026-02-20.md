# V2 Wave09 Dispatch - 2026-02-20

## Objective
- Start next implementation sprint without falling back to degraded runtime.
- Lock dual-root control cadence first, then continue implementation lanes.

## Priority order
1. Runtime parity and cadence lock (`repo` + AppSupport).
2. UI control visibility and evidence closeout.
3. Nova advisory lock and residual risk communication.

## Constraints lock
- WIP max = 5
- Tournament trees preserved and dormant (no auto-dispatch)
- No cross-project contamination
- 2h status cadence (`Now/Next/Blockers`)

## Activation order
1. Send `@victor` prompt.
2. Send `@leo` prompt.
3. Send `@nova` prompt.
4. Wait 15 minutes for ack from Victor/Leo/Nova.
5. Send specialists (`@agent-1`, `@agent-3`, `@agent-6`, `@agent-7`).

## Dispatch - @victor (CDX lead)
Objective
- Lock Wave09 dual-root control cadence so healthchecks stay green over time (repo + AppSupport).

Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py`
- `/Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py`
- `/Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/`
- `/Users/oliviercloutier/Library/Application Support/Cockpit/projects/cockpit/runs/`

Delegation
- `@agent-1` owns cadence execution runbook + stale reconciliation checks
- `@agent-3` owns deterministic validation on health/test lane

Done
- both roots remain healthy through checkpoint window
- cadence command/runbook finalized
- no tournament impact
- report every 2h in Now/Next/Blockers

## Dispatch - @leo (AG lead)
Objective
- Expose dual-root control state in Pilotage with clear operator readability (simple + tech).

Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/project_pilotage.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/project_timeline.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/`

Delegation
- `@agent-6` owns scenario matrix updates
- `@agent-7` owns screenshot evidence mapping (normal + degraded)

Done
- repo/app gate status visible and unambiguous
- evidence pack updated with mapped screenshots
- no overlap with backend cadence logic

## Dispatch - @nova (AG L1)
Objective
- Publish Wave09 operator advisory: what is locked, what remains risky, what is deferred.
- Run continuous creative-science RnD scouting and push deep recommendations at each phase.

Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/nova/memory.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-NOVA-WAVE09-RESEARCH.md`

Done
- Brief 60s includes dual-root status
- top 3 residual risks + mitigation
- explicit deferred debt reminder (`CP-0015` non-blocking)
- one deep RnD item per checkpoint (code/literature/technology)

## Dispatch - @agent-1 (CDX)
Objective
- Implement and document dual-root cadence execution checks.

Constraints
- No UI edits
- No tournament edits

Done
- cadence runbook with exact commands and expected outputs
- stale closure/reconcile checks documented
- report Now/Next/Blockers

## Dispatch - @agent-3 (CDX)
Objective
- Harden health/test contract for elapsed-time behavior.

Scope
- `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_auto_mode_healthcheck.py`
- `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave07_queue_recovery.py`
- `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave07_control_gates.py`
- `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_auto_mode.py`

Done
- all tests green
- deterministic outputs over repeated runs
- concise proof report

## Dispatch - @agent-6 (AG)
Objective
- Update Wave09 UI QA matrix for dual-root control visibility.

Done
- matrix complete with repro and expected outcomes
- simple vs tech coverage
- report Now/Next/Blockers

## Dispatch - @agent-7 (AG)
Objective
- Produce Wave09 screenshot evidence for dual-root control states.

Done
- screenshots mapped by scenario id
- normal + degraded examples
- report Now/Next/Blockers

## Operator cadence commands (every 30-45 minutes)
1. Repo pulse
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --data-dir repo --once --max-actions 0 --no-open --no-clipboard --no-notify`
2. App pulse
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --once --max-actions 0 --no-open --no-clipboard --no-notify`
3. Repo check
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --stale-seconds 3600 --max-open 3 --data-dir repo`
4. App check
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --stale-seconds 3600 --max-open 3`

## Checkpoints
1. T+15m: ack from Victor/Leo/Nova
2. T+2h: cadence patch and first deterministic checks
3. T+4h: UI evidence + advisory updates
4. T+6h: closeout packet and `STATE.md`/`ROADMAP.md`/`DECISIONS.md` update
