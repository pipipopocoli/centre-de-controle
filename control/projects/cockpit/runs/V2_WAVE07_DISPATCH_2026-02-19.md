# V2 Wave07 Dispatch - 2026-02-19

## Wave07 objective
- Hardening-first pass after Wave06 closeout.
- Keep runtime control green while improving reliability, readability, and operator decision speed.

## Constraints lock
- WIP max = 5
- Tournament trees preserved and dormant (no auto-dispatch)
- No cross-project contamination
- 2h status cadence (Now/Next/Blockers)

## Dispatch - @victor
Objective
- Lock backend hardening lane for Wave07.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/execution_router.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/task_matcher.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/cost_telemetry.py
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/
- /Users/oliviercloutier/Desktop/Cockpit/tests/

Done
- telemetry/error contracts stable and documented
- no queue regression under control gate checks
- tests green for router/dispatch/cost lanes
- report every 2h in Now/Next/Blockers

## Dispatch - @leo
Objective
- Lock Wave07 UI polish lane for Pilotage/Vulgarisation clarity.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/project_pilotage.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/project_timeline.py
- /Users/oliviercloutier/Desktop/Cockpit/app/services/project_bible.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/

Done
- improve readability in Simple mode without losing Tech detail
- degraded-state visual clarity validated with evidence
- updated scenario matrix + screenshots linked
- report every 2h in Now/Next/Blockers

## Dispatch - @nova
Objective
- Operate as creative/science advisory L1 and tighten decision quality.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/nova/memory.md

Done
- publish 60s operator brief refresh at each checkpoint
- provide top 5 recommendations with risk + mitigation
- keep memory updated with accepted/rejected guidance
- report every 2h in Now/Next/Blockers

## Gate checklist
- pending_stale_gt24h == 0
- queued_runtime_requests <= 3
- stale_heartbeats_gt1h <= 2
- tournament_auto_dispatch == false
- wave07 evidence pack linked before closeout
