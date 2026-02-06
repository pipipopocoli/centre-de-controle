# ISSUE-0009 - Memory compaction tool (V2)

- Owner: victor
- Phase: Plan
- Status: Todo

## Objective
- Add a compaction tool that proposes updates to `memory.md` from recent project signals (chat/journal/decisions), with strict caps.

## Scope (In)
- Script or tool that reads:
  - `control/projects/<id>/STATE.md`
  - `control/projects/<id>/DECISIONS.md`
  - `control/projects/<id>/agents/<agent>/journal.ndjson`
  - `control/projects/<id>/chat/global.ndjson` (last N)
- Produces a proposed `memory.md` update (summary + open loops) with size limits.
- Rotation policy (cap file size, keep older summary in an archive section).
- Deterministic output shape (stable headings).

## Scope (Out)
- Vector DB / embeddings / semantic retrieval.
- Cross-project memory search.
- Auto-writing memory without a review step.

## Now
- Spec acceptance criteria + input caps.

## Next
- Implement script in `scripts/` + basic tests.
- Wire a small UI action later (optional).

## Blockers
- None.

## Done (Definition)
- A single command generates a proposed `memory.md` patch for a given agent+project.
- Output is capped (no runaway files).
- No cross-project contamination (only reads the target project directory).

## Links
- STATE.md: control/projects/demo/STATE.md
- DECISIONS.md: control/projects/demo/DECISIONS.md
- PR:

## Risks
- Over-summarization that drops important constraints.
- Noise if inputs are not capped tightly.

