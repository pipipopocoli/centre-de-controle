# ISSUE-0010 - Agent loop e2e (AG/MCP) (V2)

- Owner: victor
- Phase: Ship
- Status: Done

## Objective
- Make pings lead to real replies by wiring an end-to-end loop between Cockpit chat and an external agent (AG/MCP).

## Scope (In)
- Define the minimal loop:
  - Operator sends message with `@leo` / `@victor`.
  - Cockpit records mention + updates state/journal (already V1).
  - Cockpit emits a run request payload (file or tool call) that AG/Codex can consume.
  - Agent posts a reply back via MCP tool `cockpit.post_message`.
- Add a tiny "Run requests" log (ndjson) to make it observable.
- Keep it local-first (no remote services required).

## Scope (Out)
- Full scheduler / multi-agent orchestrator.
- Background daemon for auto-runs without user intent.
- Notifications.

## Now
- Run requests logged to NDJSON on mentions.
- E2E verify script added (mention -> run request -> agent reply).

## Next
- Optional: add a small UI panel for run requests (post-V2).

## Blockers
- None.

## Done (Definition)
- A ping produces a run request record.
- A simulated agent can consume it and post a response back into chat.
- Logs are auditable (ndjson) and do not pollute tracked demo files.

## Links
- STATE.md: control/projects/demo/STATE.md
- DECISIONS.md: control/projects/demo/DECISIONS.md
- PR:

## Risks
- Too much scope (keep it minimal).
- Hard to test without a real agent (use a mock script first).
