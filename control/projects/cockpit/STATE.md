# State

## Phase
- Implement

## Objective
- Stabilize the current Cockpit shell around the live `cockpit` project only.

## Now
- CP-0061 is back in flight: remove the extra latest reply surface and finish direct chat visibility in Pixel Home.
- CP-0062 is back in flight: remove the room reply banner and keep fallback diagnostics out of Le Conseil.
- `demo` is out of the active runtime and project catalog. `cockpit` is the only live project flow.

## Next
- Rebuild and reinstall Cockpit with the CP-0061 / CP-0062 UI-state fixes.
- Run direct and room chat QA in the installed app.
- Re-close the issues only after manual UI verification.

## In Progress
- ISSUE-CP-0061 - Pixel Home direct chat + shell ownership
- ISSUE-CP-0062 - Le Conseil room visibility + message window

## Blockers
- none

## Risks
- fallback warnings can still look broken if they surface in the main chat when a visible reply exists.
- operator QA is still needed on the installed app after the latest rebuild.

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0061-fix-z-index-overlay-chat-pixel-home.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0062-impl-menter-pagination-messages-concierge-room.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/COCKPIT_RUNBOOK.md
