# ISSUE-CP-0014 - UI fail-open and network-down states

- Owner: leo
- Phase: Ship
- Status: Done

## Objective
- Make fail-open and network-down behavior explicit in UI without blocking workflows.

## Scope (In)
- Warning banner component.
- Message copy for fail-open mode.
- Recovery hint action.

## Scope (Out)
- Backend retry policies.
- New persistence layers.

## Now
- StatusBanner widget (warning/error severity, dismiss button) implemented.
- Integrated at top of SidebarWidget.
- Wired to BrainFS errors in main_window. 23/23 tests pass.

## Next
- Implement banner states.
- Validate with offline simulation.

## Blockers
- None.

## Done (Definition)
- Offline/fail-open state has explicit banner.
- User can continue work and see what degraded.
- QA evidence includes screenshot of degraded state.

## Links
- STATE.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- DECISIONS.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md
- PR: TDB
- Evidence: [CP01_SLO_COST_EVIDENCE_2026-02-19.md](/Users/oliviercloutier/Desktop/Cockpit/docs/reports/CP01_SLO_COST_EVIDENCE_2026-02-19.md)

## Risks
- Over-noisy alerts if not throttled.
