# ISSUE-0012 - Clems auto-reply + steps clarity (V2.1)

- Owner: clems
- Phase: Ship
- Status: Done

## Objective
- Make Clems respond to operator messages and clarify next steps in the UI.

## Scope (In)
- Auto-reply for operator messages.
- Follow-up reminders (agents + operator).
- Show Phase/Objective/Next in roadmap area.
- Split personas into per-agent files.

## Scope (Out)
- Full LLM integration or external API.
- Voice/micro input.
- Cross-project memory.

## Now
- Auto-reply + reminders working in app.
- Personas split into agents/ files.
- QA done (no reply loops).

## Next
- None.

## Blockers
- None.

## Done (Definition)
- Clems replies to operator messages in chat.
- No reply loops (no system/clems echo).
- Phase/Objective/Next visible in roadmap area.
- Personas split into agents/ files.

## Links
- STATE.md: control/projects/demo/STATE.md
- DECISIONS.md: control/projects/demo/DECISIONS.md
- PR:

## Risks
- Reminders may become noisy if misused.
