# ISSUE-CP-0012 - UI Sync now with feedback

- Owner: leo
- Phase: Ship
- Status: Done

## Objective
- Add `Sync now` action with immediate user feedback and disabled/loading states.

## Scope (In)
- Button action + loading state.
- Success/failure feedback message.
- Basic latency display.

## Scope (Out)
- Policy decision logic.
- Installer backend implementation.

## Now
- Button + loading/success/error states implemented.
- Wired to brainfs.ensure_profile via main_window.
- 12/12 verify tests pass.

## Next
- Connect to sync endpoint with optimistic UI.
- Add QA checklist.

## Blockers
- None.

## Done (Definition)
- User can trigger sync from UI.
- UI shows clear success or failure state.
- No duplicate trigger while request is running.

## Links
- STATE.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- DECISIONS.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md
- PR: TDB

## Risks
- Double-click race conditions.
