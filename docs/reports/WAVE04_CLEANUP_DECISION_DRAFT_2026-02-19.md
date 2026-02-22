# Wave04 Cleanup Decision Draft - 2026-02-19

## Scope
- Canonical build spec
- Canonical virtualenv path
- Canonical V2 docs source-of-truth

## Proposed canonical choices (draft)
1. Build spec canonical:
- `cockpit.spec` (recommended)
2. Virtualenv canonical:
- `.venv/` (recommended)
3. V2 docs source-of-truth:
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/` for tournament packs
- `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/` for operational evidence

## Hard exclusions
- Never delete or archive tournament trees in this pass.
- Exclude any path containing:
  - `tournament`
  - `PROMPTS`
  - `ROUND-`
  - `JUDGE_FEEDBACK`
  - `TOURNAMENT_ARENA`

## Required review
- Owner review: @agent-11
- Final lock: @clems
