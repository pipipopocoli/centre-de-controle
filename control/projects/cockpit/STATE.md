# State

## Phase
- Review

## Objective
- Stabilize the current Cockpit shell around the live `cockpit` project only.

## Now
- CP-0061 is closed: Pixel Home direct chat is isolated, compact, and visible.
- CP-0062 is closed: Le Conseil renders room traffic cleanly and keeps `@clems` visible.
- `demo` is out of the active runtime and project catalog. `cockpit` is the only live project flow.

## Next
- Run operator QA in the installed app on real takeover flow.
- Validate native folder picker from `Overview` on a real repo path.
- Confirm `Pixel Home`, `Le Conseil`, and `Docs > Project` with fresh screenshots before the next feature wave.

## In Progress
- none

## Blockers
- none

## Risks
- operator QA is still needed on the installed app after the latest rebuild.
- room visibility can regress if direct and room message pools get mixed again.

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0061-fix-z-index-overlay-chat-pixel-home.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0062-impl-menter-pagination-messages-concierge-room.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/COCKPIT_RUNBOOK.md
