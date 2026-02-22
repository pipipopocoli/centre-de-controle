# ISSUE-CP-0013 - UI observability badges for sync and memory

- Owner: leo
- Phase: Ship
- Status: Done

## Objective
- Add clear badges for sync health, memory index freshness, and warning states.

## Scope (In)
- Badge components.
- Health state mapping.
- Tooltip copy.

## Scope (Out)
- Deep analytics page.
- Historical charting.

## Now
- ObservabilityBadge widget implemented with ok/warn/fail health states.
- Sync + Memory badges integrated in SkillsOpsPanel.
- QSS styles for color-coded dots. 23/23 tests pass.

## Next
- Implement badge state map.
- Add snapshot coverage for main states.

## Blockers
- None.

## Done (Definition)
- Badges reflect runtime states correctly.
- Warning state is visible and understandable.
- QA screenshot set includes ok/warn/fail variants.

## Links
- STATE.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- DECISIONS.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md
- PR: TDB

## Risks
- Color/state ambiguity for users.
