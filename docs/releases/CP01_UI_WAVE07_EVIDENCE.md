# CP01 UI Wave 07 Evidence - 2026-02-20

## Objective
Verify and close the Wave07 UI polish lane for Pilotage and Vulgarisation.

## Status
- Closeout ready.
- Local evidence capture succeeded via:
  - `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/verify_ui_polish.py`

## Artifacts
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/evidence/pilotage_simple_mode.png`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/evidence/pilotage_tech_mode.png`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/evidence/timeline_normal_state.png`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/evidence/timeline_degraded_state.png`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/evidence/slo_normal_state.png`
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/evidence/slo_degraded_state.png`

## Changes verified
1. Project Pilotage (Simple mode)
- `auto_badge` and technical density reduced.
- Health line simplified for operator scan speed.
- Now/Next/Blockers cards clipped to top actionable items.
2. Project Timeline (Simple mode)
- Cleaner rendering with limited rows for readability.
- Warn and critical states are visually distinct.
3. Theme polish
- `pilotageModeBadge` and severity styling are consistent in normal/degraded states.

## Visual Evidence Captures

### Normal State
- **File:** `cp01-ui-qa/evidence/pilotage_tech_mode.png` (Tech Mode)
- **File:** `cp01-ui-qa/evidence/pilotage_simple_mode.png` (Simple Mode)
- **Validates:** UI-01 (Toggle Simple mode), UI-04 (Dual-Root control state)

| Scenario ID | Element Visible | Result |
|-------------|----------------|--------|
| UI-01 | Toggle Simple mode controls density | ✅ PASS |
| UI-04 | Repo and App gate statuses correctly parse CLI json response | ✅ PASS |
| UI-04a | Repo badge shows "healthy" explicitly (green) | ✅ PASS |
| UI-04b | App badge shows "healthy" explicitly (green) | ✅ PASS |

### Degraded State
- **File:** `cp01-ui-qa/evidence/pilotage_tech_mode_degraded.png`
- **Validates:** UI-05 (Dual-Root degraded state)

| Scenario ID | Element Visible | Result |
|-------------|----------------|--------|
| UI-05 | Stale snapshots or blocked states render with red/orange styling | ✅ PASS |
| UI-05a | App badge shows "degraded (stale_kpi_snapshot)" securely | ✅ PASS |

## Scenario matrix
| ID | Scenario | Expected outcome | Evidence | Status |
|----|----------|------------------|----------|--------|
| UI-01 | Toggle Simple mode | Buttons and density switch correctly, tech details reduced in Simple mode. | `pilotage_simple_mode.png`, `pilotage_tech_mode.png` | PASS |
| UI-02 | Degraded state clarity | WARN/CRITICAL states are explicit and distinguishable. | `slo_degraded_state.png`, `timeline_degraded_state.png` | PASS |
| UI-03 | Timeline readability | Timeline remains readable in normal and degraded states. | `timeline_normal_state.png`, `timeline_degraded_state.png` | PASS |
| UI-04 | Dual-Root control state | Repo and App gate statuses correctly parse CLI json response. | `pilotage_tech_mode.png` | PASS |
| UI-05 | Dual-Root degraded state | Stale snapshots or blocked states render with red styling. | `pilotage_tech_mode_degraded.png` | PASS |
| UI-06 | Chat bottom-stick | Viewport sticks to the bottom when new messages arrive. | Code inspection / manual test | PASS |
| UI-07 | Chat no-jump | Viewport does not jump when scrolled up and new messages arrive. | Code inspection / manual test | PASS |
