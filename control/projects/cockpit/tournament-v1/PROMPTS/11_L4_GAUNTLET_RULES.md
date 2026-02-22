# L4 Gauntlet Rules (Multi-Step Deep Round)

Context lock
- PROJECT LOCK: cockpit
- Round id: L4_GAUNTLET
- Currency lock: CAD
- Scoring details are secret from agents.

Entrants policy
- Winners only from L3 (`F13`, `F14`, `F15`).
- If odd entrant count, inject wildcard next free id (`agent-18`, then `agent-19`, ...).
- Pair sequentially after ordering by source fight id.

Mandatory outputs
1. Stage A markdown final:
   - `<agent_id>_SUBMISSION_V4_FINAL.md`
2. Stage B html pitch:
   - `<agent_id>_FINAL_HTML/index.html`
3. Stage C evidence json:
   - `<agent_id>_EVIDENCE_V4.json`

Epreuve A - Product Pitch Extreme
- A1 Executive pitch:
  - problem
  - why now
  - why this wins
- A2 Operator pitch:
  - daily flow
  - decision latency
  - blocker loop
- A3 Technical pitch:
  - architecture
  - failure containment
  - reversibility

Epreuve B - OpenClaw Competitive Benchmark
- B1 Compare against OpenClaw online site.
- B2 Compare against OpenClaw online code/repo.
- B3 Explain why this proposal is better for this operator context.
- B4 Explicitly list where OpenClaw is stronger, plus mitigation.
- Evidence required:
  - at least 2 URLs (site + code)
  - checked timestamp for each URL in evidence JSON.

Epreuve C - Visual Identity + Moodboard
- C1 Propose 3 routes:
  - safe
  - bold
  - extreme
- C2 Define per route:
  - palette
  - typography
  - motion style
  - component language
- C3 App update path:
  - what to change first
  - what to change second
  - what to change third

Epreuve D - Runtime Economics (Mac vs Server)
- D1 Mac baseline assumptions.
- D2 Online server options:
  - small
  - medium
  - large
- D3 CAD monthly cost, perf gain estimate, break-even.
- D4 Migration and rollback path.

Epreuve E - API Economics + Scale + Absorption
- E1 API economics in CAD vs Codex + OpenGravity.
- E2 Scale architecture targets:
  - 50 agents
  - 200 agents
  - 1000 agents
- E3 Opponent absorption ledger:
  - accepted
  - rejected
  - deferred
  - each with reason and proof path
- E4 Top 10 risks plus contingency matrix.

Stage A markdown hard requirements
- >=900 lines.
- >=6 new features.
- >=10 risky problems with mitigation.
- >=4 accepted opponent ideas.
- >=2 rejected weak own ideas.
- Include CAD tables for runtime economics and API economics.

Stage B html hard requirements
- Must open in `file://`.
- No required external assets for core rendering.
- Required sections:
  1. executive summary
  2. OpenClaw compare board
  3. visual moodboard (3 routes)
  4. Mac vs server CAD calculator table
  5. API economics compare table
  6. scale map (50/200/1000)
  7. absorption ledger
  8. top risks
  9. why this wins

Stage C evidence json hard requirements
- Must include:
  - openclaw_sources (site + code URLs with ISO-8601 checked_at)
  - cost_cad block
  - api_economics block
  - absorption block
  - scale_targets array `[50, 200, 1000]`
  - veto_checks block

Scoring v2 (secret)
- Total 200 points.
- Category weights:
  - Product + execution quality: 30
  - Deep pitch quality: 20
  - OpenClaw benchmark quality: 30
  - Visual identity + moodboard applicability: 20
  - Mac vs server perf/cost (CAD): 30
  - API economics vs Codex/OpenGravity: 25
  - Opponent absorption quality: 20
  - Massive-scale strategy: 25

Tie-break (L4)
1. Massive-scale strategy score
2. OpenClaw benchmark score
3. API economics score
4. Absorption score

Veto conditions
- Any mandatory output missing.
- OpenClaw online evidence missing.
- CAD economics tables missing.
- Absorption ledger missing.
- HTML not opening via `file://`.

Judge disclosure policy
- Agents receive:
  - verdict
  - imports required
  - blockers
- Numeric category/sub-scores remain hidden.
