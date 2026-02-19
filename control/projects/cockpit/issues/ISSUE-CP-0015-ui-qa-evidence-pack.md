# ISSUE-CP-0015 - UI QA evidence pack for checkpoint

- Owner: leo
- Phase: Test
- Status: Done

## Objective
- Produce final UI QA evidence pack for CP-01 (screenshots + manual steps + pass/fail).

## Scope (In)
- Manual scenario matrix.
- Screenshot capture list.
- Final pass/fail summary.

## Scope (Out)
- New feature implementation.
- Backend API changes.

## Now
- Evidence pack published under `docs/reports`.
- Scenario matrix and degraded-state capture included.

## Next
- Keep one manual desktop screenshot pass at next operator checkpoint.
- Track visual regressions with same matrix IDs.

## Blockers
- None.

## Done (Definition)
- Evidence pack stored in repo and linked from state docs.
- Each scenario has pass/fail and reproduction steps.
- Includes at least one degraded-state screenshot.

## Links
- STATE.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- DECISIONS.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md
- Evidence: /Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP01_UI_QA_EVIDENCE_PACK_2026-02-19.md
- Capture: /Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/screenshots/cp01_overview_2026-02-19.svg
- Capture: /Users/oliviercloutier/Desktop/Cockpit/docs/reports/cp01-ui-qa/screenshots/cp01_degraded_profile_missing_2026-02-19.svg
- Delta matrix: /Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP0015_QA_SCENARIO_MATRIX_DELTA_2026-02-19.md
- PR: main (V2-WAVE-03)

## Risks
- Missing evidence can block checkpoint signoff.

## Proof
- Evidence pack exists with pass/fail matrix and repro commands.
- Degraded-state capture included via fallback deterministic SVG in headless environment.
