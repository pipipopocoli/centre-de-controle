# State

## Phase
- Implement

## Objective
- Stabilize the live `cockpit` shell with Le Conseil as the only project action surface and OpenRouter as first-class runtime status.

## Now
- Live `cockpit` settings are pruned to the minimal schema only.
- Le Conseil owns `Create new project` and `Take over a project`.
- Header and Pilotage expose explicit OpenRouter runtime status.

## Next
- Run the shell and backend gates.
- Rebuild and reinstall Cockpit.app.
- Verify create/takeover flows from Le Conseil and confirm OpenRouter status is coherent in header + Pilotage.

## In Progress
- ISSUE-CP-0061 - Pixel Home direct chat + shell ownership
- ISSUE-CP-0062 - Le Conseil room visibility + message window

## Blockers
- none

## Risks
- Direct chat and room chat still need installed-app QA after rebuild.
- Folder picker behavior depends on the desktop Tauri bridge and needs manual validation.

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0061-fix-z-index-overlay-chat-pixel-home.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0062-impl-menter-pagination-messages-concierge-room.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/COCKPIT_RUNBOOK.md
