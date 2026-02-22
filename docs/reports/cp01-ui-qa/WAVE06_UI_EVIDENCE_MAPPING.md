# Wave 06 UI Evidence Mapping

**Date:** 2026-02-20
**Scope:** Pilotage (Cost, SLO) & Project Timeline
**Status:** Frozen

## Scenario Matrix & Evidence

| ID | Feature | State | Scenario Description | Evidence File (PNG) | Evidence File (HTML) |
|---|---|---|---|---|---|
| **COST-01** | Pilotage / Cost | Normal | Budget configured, monthly estimate available. | `cost_budget_configured.png` | `scenario_COST-01.html` |
| **COST-02** | Pilotage / Cost | Degraded | No budget configured, telemetry not connected. | `cost_no_budget.png` | `scenario_COST-02.html` |
| **SLO-01** | Pilotage / SLO | Normal | SLO Verdict GO, metrics nominal. | `slo_normal_state.png` | `scenario_SLO-01.html` |
| **SLO-02** | Pilotage / SLO | Degraded | SLO Verdict HOLD or Unavailable (fail-open). | `slo_degraded_state.png` | `scenario_SLO-02.html` |
| **TL-01** | Timeline | Normal | Project route with milestones and active stream. | `timeline_normal_state.png` | `scenario_TL-01.html` |
| **TL-02** | Timeline | Degraded | Timeline with missing source files or empty stream. | `timeline_degraded_state.png` | `scenario_TL-02.html` |

## Verification Logic

- **Simple/Tech Mode:** Verified in `app/ui/project_pilotage.py` (toggles detail level).
- **Project/Portfolio Scope:** Verified in `app/ui/project_pilotage.py` (toggles data source).
- **Pass Criteria:**
    - Normal state: renders without error, shows data.
    - Degraded state: shows fallback UI/warnings, no crash.

## Location
All evidence files located in: `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/evidence/`
