# State

## Phase
- Test

## Objective
- Stabilize the live `cockpit` shell and keep direct chat plus Le Conseil reliable on the installed app runtime.

## Now
- Direct `@clems` chat returns a real visible LLM reply on the installed runtime.
- Le Conseil returns a visible `@clems` summary while keeping room diagnostics internal.
- Header and Pilotage expose explicit OpenRouter runtime status.

## Next
- Manual QA in `Cockpit.app` for Pixel Home and Le Conseil.
- Verify create/takeover flows from Le Conseil end to end.
- Keep an eye on room contributor timeouts if the full L1 set stays on Kimi.

## In Progress
- none

## Blockers
- none

## Risks
- Room contributor fanout can still degrade when all active L1 lanes stay on Kimi and OpenRouter is slow.
- Folder picker behavior still needs final manual validation in the installed app.

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0061-fix-z-index-overlay-chat-pixel-home.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0062-impl-menter-pagination-messages-concierge-room.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/COCKPIT_RUNBOOK.md
