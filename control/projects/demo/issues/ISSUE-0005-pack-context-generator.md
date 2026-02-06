# ISSUE-0005 - Pack Context generator (Light/Full)

- Owner: victor (@victor)
- Phase: Implement
- Status: In progress

## Objective
- Add a 1-click way to generate a context pack (Light/Full) from the project state, for pasting into external agents or posting back into chat.

## Scope (In)
- Define the exact inputs (sources of truth) and limits.
- Implement a generator that outputs Markdown in 2 formats:
  - Light: <= 30 lines
  - Full: 1-2 pages max
- UI wiring (minimal): a button or menu item to generate + copy to clipboard.
- Optional: "Post to chat" (global) as a second action.

## Scope (Out)
- RAG / embeddings / vector DB.
- Cross-project memory retrieval.
- Fancy UI redesign (this is functional wiring only).

## Now
- None.

## Next
- Spec the format + data sources:
  - `control/projects/<id>/STATE.md`
  - `control/projects/<id>/ROADMAP.md`
  - `control/projects/<id>/DECISIONS.md`
  - `control/projects/<id>/issues/*.md` (open issues only)
  - `control/projects/<id>/agents/<agent>/memory.md` (target agent)
  - `control/projects/<id>/chat/global.ndjson` (N=20 light, N=200 full)
- Decide where to surface it in UI (sidebar action vs per-agent action).
- Implement + tests (at least deterministic output shape).

## Blockers
- None.

## Done (Definition)
- 1 click produces a coherent Markdown pack in Light + Full formats.
- Light is <= 30 lines. Full is 1-2 pages max.
- Copy-to-clipboard works reliably.
- Does not break existing MCP/chat wiring.
- Reversible (single PR, minimal surface area).

## Links
- STATE.md: control/projects/demo/STATE.md
- DECISIONS.md: control/projects/demo/DECISIONS.md
- PR:

## Risks
- Output becomes noisy without strict limits (must enforce caps).
- Pack drifts from source-of-truth files if we "invent" missing data.
