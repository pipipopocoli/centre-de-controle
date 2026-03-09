# ISSUE-CP-0061 - Pixel Home direct chat + shell ownership

- Owner: leo
- Phase: Implement
- Status: Done
- Source: ai_auto

## Objective
- Restore a usable Pixel Home shell where the agent roster scrolls, the scene stays bounded, and direct chat with @clems is always visible and operable.

## Done (Definition)
- [x] Pixel Home has one scroll owner for the roster and one scroll owner for the active right-side panel.
- [x] Direct chat renders only direct messages, never room messages.
- [x] The direct composer stays visible at all times.
- [x] Sending a direct message to @clems yields a visible reply in Pixel Home.
- [x] Agent cards show runtime status, current task, skills, and scene presence without clipping.

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0063-correction-overlay-bloquant-pixel-home.md (superseded)
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0066-fixer-superposition-chat-pixel-home.md (superseded)

## Risks
- UI can regress if shell containers reintroduce nested overflow or oversized min-height values.

## Evidence
- `curl -s -X POST http://127.0.0.1:8787/v1/projects/cockpit/chat/live-turn -H 'Content-Type: application/json' -d '{"text":"allo","chat_mode":"direct","execution_mode":"chat"}'`
- Result: visible `@clems` direct reply with `reply_source=llm`
