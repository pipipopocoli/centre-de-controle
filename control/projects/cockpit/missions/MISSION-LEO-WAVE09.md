# MISSION-LEO-WAVE09

Objective
- Close Wave09 UI lane (CP-0037) with operator-grade control visibility and evidence lock.

Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/project_pilotage.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/project_timeline.py`
- `/Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0037-wave09-pilotage-control-badges.md`

Scope (Out)
- backend cadence/reconciliation logic
- tournament assets and dispatch
- cross-project changes

Delegation
- `@agent-6`: scenario matrix finalization (simple/tech + project/portfolio)
- `@agent-7`: screenshot mapping (normal + degraded)

Done
- Repo/AppSupport control badges visible and unambiguous in Pilotage.
- Scenario matrix complete with repro + expected + final verdict.
- Screenshot pack mapped to scenario IDs.
- Degraded-state evidence included.
- 2h status cadence respected (`Now/Next/Blockers`).

Validation
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/verify_ui_polish.py`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_hybrid_timeline.py`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/tests/verify_vulgarisation_accessibility.py`
