# ISSUE-0010 - Agent loop e2e (AG/MCP) (V2)

- Owner: victor
- Phase: Plan
- Status: Todo

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
- Write the spec + decide the handshake format.

## Next
- Implement the handshake + one happy-path e2e test script.

## Blockers
- Need an agreed handshake format (file location + schema) for run requests.

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

