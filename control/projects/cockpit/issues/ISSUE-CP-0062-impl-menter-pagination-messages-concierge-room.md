# ISSUE-CP-0062 - Le Conseil room visibility + message window

- Owner: leo
- Phase: Implement
- Status: In Progress
- Source: ai_auto

## Objective
- Make Le Conseil a real room surface with visible @clems coordination, bounded message volume, and stable scroll behavior.

## Done (Definition)
- [ ] Le Conseil renders only room messages in the main log.
- [ ] Internal traces stay separate and capped.
- [ ] Latest 8 room messages show by default with Show older / Show latest controls.
- [ ] The room composer stays pinned and reachable.
- [ ] A user room message yields a visible coordinating reply from @clems.

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0064-fix-d-filement-infini-concierge-room.md (superseded)
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0067-stabiliser-d-filement-chat-concierge-room.md (superseded)

## Risks
- Backend fanout logic can still mask room replies if participant targeting drifts away from @clems + active leads.
