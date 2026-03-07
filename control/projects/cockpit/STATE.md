# State

## Phase
- Implement

## Objective
- Stabilize the current Cockpit shell around the live `cockpit` project only.

## Now
- CP-0061: Pixel Home direct chat and shell ownership are being hardened.
- CP-0062: Le Conseil room scroll, message window, and reply visibility are being stabilized.
- `demo` is being removed from active runtime, repo flow, and operator docs.

## Next
- Rebuild and reinstall `Cockpit.app` on the latest head.
- Validate direct chat with `@clems`, room chat in Le Conseil, folder picker, and takeover wizard handoff.
- Push the current shell fix and governance cleanup together.

## In Progress
- ISSUE-CP-0061-fix-z-index-overlay-chat-pixel-home.md
- ISSUE-CP-0062-impl-menter-pagination-messages-concierge-room.md

## Blockers
- none

## Risks
- old room messages can still hide room replies if message mode filtering regresses.
- stale local artifacts can confuse operator truth if `demo` is not fully removed.

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0061-fix-z-index-overlay-chat-pixel-home.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0062-impl-menter-pagination-messages-concierge-room.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/COCKPIT_RUNBOOK.md
