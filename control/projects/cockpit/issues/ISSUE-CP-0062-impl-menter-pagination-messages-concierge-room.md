# ISSUE-CP-0062 - Le Conseil room visibility + message window

- Owner: leo
- Phase: Implement
- Status: Done
- Source: ai_auto

## Objective
- Make Le Conseil a real room surface with visible @clems coordination, bounded message volume, and stable scroll behavior.

## Done (Definition)
- [x] Le Conseil renders only room messages in the main log.
- [x] Internal traces stay separate and capped.
- [x] Latest 8 room messages show by default with Show older / Show latest controls.
- [x] The room composer stays pinned and reachable.
- [x] A user room message yields a visible coordinating reply from @clems.

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0064-fix-d-filement-infini-concierge-room.md (superseded)
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0067-stabiliser-d-filement-chat-concierge-room.md (superseded)

## Risks
- Backend fanout logic can still mask room replies if participant targeting drifts away from @clems + active leads.

## Evidence
- `curl -s -X POST http://127.0.0.1:8787/v1/projects/cockpit/chat/live-turn -H 'Content-Type: application/json' -d '{"text":"fais un point rapide","chat_mode":"conceal_room","execution_mode":"chat"}'`
- Result: visible `@clems` room summary with `reply_source=llm`, internal contributor traces kept separate
