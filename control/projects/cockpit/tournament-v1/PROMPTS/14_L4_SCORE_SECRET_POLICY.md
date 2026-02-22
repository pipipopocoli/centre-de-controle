# L4 Secret Scoring Policy

Purpose
- Keep evaluation quality high and avoid score gaming.
- Preserve competition fairness while keeping feedback actionable.

What judges keep private
- Full numeric category scores.
- Weighted subtotal and final total.
- Internal tie-break calculations.
- Internal confidence notes.

What agents receive
1. Verdict:
- win
- lose
2. Imports required for next round (minimum list).
3. Blockers/corrections that must be fixed.

What agents do NOT receive
- Numeric points by category.
- Opponent numeric points.
- Detailed tie-break numbers.

L4 score model reference (judge side only)
- Product + execution quality: 30
- Deep pitch quality: 20
- OpenClaw benchmark quality: 30
- Visual identity + moodboard applicability: 20
- Mac vs server perf/cost model (CAD): 30
- API economics vs Codex/OpenGravity: 25
- Opponent absorption quality: 20
- Massive-scale strategy (50/200/1000): 25
- Total: 200

Tie-break order
1. Massive-scale strategy
2. OpenClaw benchmark
3. API economics
4. Absorption quality

Veto policy
- Any veto condition overrides score and blocks winner lock.
- Veto reasons must be written in judge feedback.

Judge output template (agent-visible)
- Verdict: <win|lose>
- Imports required:
  - <item 1>
  - <item 2>
  - <item 3>
- Blockers:
  - <blocker 1>
  - <blocker 2>

Judge output template (internal)
- Keep full scorecard and rationale in judge file.
- Do not expose numeric values in agent dispatch messages.
