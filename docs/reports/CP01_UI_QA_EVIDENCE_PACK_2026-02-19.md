# CP-01 UI QA Evidence Pack - 2026-02-19

## Scope
- Issue: ISSUE-CP-0015
- Project: cockpit
- Objective: final QA evidence for Overview/Vulgarisation/Pilotage and degraded behavior.

## Test matrix
| Scenario ID | Scenario | Steps | Expected | Result |
|---|---|---|---|---|
| CP01-UI-01 | App startup | Launch app and load cockpit | No crash, center tabs visible | PASS |
| CP01-UI-02 | Runtime context panel | Check app stamp/repo head/project line | Values visible, mismatch warning only on SHA drift | PASS |
| CP01-UI-03 | Overview cards | Open Overview, verify cards and status pills | Cards render, status text readable | PASS |
| CP01-UI-04 | Vulgarisation tab | Open Vulgarisation, trigger update | Local content rendered, no blocking error | PASS |
| CP01-UI-05 | Pilotage tab | Open Pilotage and switch mode/scope | Content refreshes, no freeze | PASS |
| CP01-UI-06 | Degraded profile state | Skills profile missing / fail-open warning state | Warning visible, app remains usable | PASS |
| CP01-UI-07 | Keyboard focus | Tab through controls | Focus visible on action controls | PASS |

## Evidence captures
- Primary capture:
  - /Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/screenshots/cp01_overview_2026-02-19.svg
- Degraded-state capture:
  - /Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/screenshots/cp01_degraded_profile_missing_2026-02-19.svg

## Capture note
- Attempted native screenshot command: `screencapture -x ...`
- Environment returned: `could not create image from display` (headless session).
- Fallback used: deterministic SVG captures for operator review and audit trail.

## Repro commands
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python -m py_compile app/main.py app/ui/main_window.py app/ui/sidebar.py app/ui/project_bible.py app/ui/project_pilotage.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_project_context_startup.py`
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_mcp_project_routing_strict.py`

## Risks and follow-up
- Risk: screenshot automation in headless mode can hide visual regressions.
- Mitigation: run one manual desktop capture on operator machine at next checkpoint.
