# Wave22 Multi-Agent UX Patterns

## Direct lane vs orchestration room
- `Pixel Home`
  - one target
  - fast conversational lane
  - zero room fanout semantics
- `Le Conseil`
  - multi-agent room
  - visible participant contributions
  - @clems synthesis after contributions
  - diagnostics separated from primary conversation

## Operator observability model
Every visible agent card should answer:
- who is this
- what model is running
- what task is active
- when did heartbeat last move
- is chat available
- is terminal live
- is the agent on scene or off scene

## Information hierarchy
- Primary surface: action + current answer
- Secondary surface: participants, approvals, diagnostics, cost, recent events
- Archive/debug: release proofs, old reports, obsolete launchers, legacy bridges

## Degraded behavior rules
- Direct lane: visible failure notice plus draft restore if no LLM answer exists
- Room lane: honest @clems coordination reply if participants all fail
- Never show synthetic placeholder success as if it were a real answer

## UX decisions to carry into implementation
- Keep newest messages at bottom in both direct and room lanes
- Cap visible room history by default, then expand progressively
- Keep all heavy diagnostics out of the main compose/read path
- Keep project actions in `Le Conseil`, not in `Overview`
