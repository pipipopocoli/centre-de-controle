# ISSUE-CP-0061 - Pixel Home direct chat + shell ownership

- Owner: leo
- Phase: Implement
- Status: In Progress
- Source: ai_auto

## Objective
- Restore a usable Pixel Home shell where the agent roster scrolls, the scene stays bounded, and direct chat with @clems is always visible and operable.

## Done (Definition)
- [ ] Pixel Home has one scroll owner for the roster and one scroll owner for the active right-side panel.
- [ ] Direct chat renders only direct messages, never room messages.
- [ ] The direct composer stays visible at all times.
- [ ] Sending a direct message to @clems yields a visible reply in Pixel Home.
- [ ] Agent cards show runtime status, current task, skills, and scene presence without clipping.

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0063-correction-overlay-bloquant-pixel-home.md (superseded)
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0066-fixer-superposition-chat-pixel-home.md (superseded)

## Risks
- UI can regress if shell containers reintroduce nested overflow or oversized min-height values.
