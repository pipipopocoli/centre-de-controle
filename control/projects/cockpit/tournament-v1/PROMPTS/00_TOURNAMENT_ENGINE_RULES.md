# Tournament Prompt Engine Rules (V5 - L4 Gauntlet)

## Core principle
- Tournament is prompt-driven.
- Every active match has explicit read-only inputs and write-only outputs.
- Rounds L3+ use dual-stage outputs, and L4 adds mandatory evidence JSON.

## Project lock
- PROJECT LOCK is always `cockpit`.
- Any mismatch between declared project and output paths is invalid.

## Round policy lock
- One winner per match.
- A round may have multiple winners because it has multiple matches.
- If entrant count is odd, inject wildcard with next free id (`agent-17`, `agent-18`, ...).

## Output contracts by round
- L3 contract:
  - Output A: `<agent_id>_SUBMISSION_V3_FINAL.md`
  - Output B: `<agent_id>_FINAL_HTML/index.html`
- L4 contract (Gauntlet):
  - Output A: `<agent_id>_SUBMISSION_V4_FINAL.md`
  - Output B: `<agent_id>_FINAL_HTML/index.html`
  - Output C: `<agent_id>_EVIDENCE_V4.json`

## L4 entry policy
- Entrants are winners from L3 fights (`F13`, `F14`, `F15`).
- Sort by source fight id order (`F13`, `F14`, `F15`).
- If odd, append wildcard next free id.
- Pair sequentially.

## L4 gauntlet mandatory content
1. Detailed pitch (executive, operator, technical).
2. OpenClaw comparison against online site and online code/repo.
3. Visual identity moodboard with 3 directions.
4. Runtime economics in CAD (Mac local vs online server options).
5. API economics in CAD (vs Codex + OpenGravity).
6. Opponent idea absorption (accept/reject/defer with proof).
7. Massive scale plan (50/200/1000 agents).
8. Top risks and contingency matrix.

## L4 hard gates
- Stage A markdown:
  - >=900 lines
  - >=6 new features
  - >=10 risks with mitigation
  - >=4 accepted opponent ideas
  - >=2 rejected weak own ideas
  - CAD tables present for runtime and API economics
- Stage B HTML:
  - opens via `file://`
  - no required external assets for core content
  - includes required sections from gauntlet
- Stage C JSON evidence:
  - includes OpenClaw sources with timestamps
  - includes CAD runtime and API economics fields
  - includes absorption and veto checks

## Scoring models
- L3 scoring (secret): 125 total
  - technical 100 + pitch 25
- L4 scoring (secret): 200 total
  - Product + execution quality: 30
  - Deep pitch quality: 20
  - OpenClaw benchmark quality: 30
  - Visual identity + moodboard applicability: 20
  - Mac vs server perf/cost (CAD): 30
  - API economics vs Codex/OpenGravity: 25
  - Opponent absorption quality: 20
  - Massive-scale strategy: 25

## Tie-break (L4)
1. Massive-scale strategy score
2. OpenClaw benchmark score
3. API economics score
4. Absorption score

## Veto (disqualifying)
- Missing mandatory output file (MD/HTML/JSON).
- No OpenClaw online evidence.
- No CAD economics tables.
- No absorption ledger.
- HTML does not open in `file://`.

## Confidential scoring policy
- Numeric scoring details are secret from agents.
- Agents receive only:
  - verdict (win/lose)
  - required imports for next round
  - blockers/corrections

## Read/write discipline
- Read only files listed in README/prompt.
- Write only output paths listed in README/prompt.
- Missing required input must return blocker with exact absolute path.
