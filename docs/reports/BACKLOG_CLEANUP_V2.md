# BACKLOG CLEANUP V2

## Goal
- Keep Cockpit V2 operationally clean while preserving tournament capability.
- Remove ambiguity between active assets and legacy/duplicate assets.

## Active keep set
- Keep and maintain:
  - `/Users/oliviercloutier/Desktop/Cockpit/app/`
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/`
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/`
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/`
  - `/Users/oliviercloutier/Desktop/Cockpit/site/`
  - `/Users/oliviercloutier/Desktop/Cockpit/scripts/`
  - `/Users/oliviercloutier/Desktop/Cockpit/tests/`
  - `/Users/oliviercloutier/Desktop/Cockpit/tools/`

## Already archived in this pass
- Projects moved from active path to archive:
  - `control/projects/demo/`
  - `control/projects/motherload/`
  - `control/projects/test-proj/`
- Location:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/_archive/2026-02-19/`

## Local artifact archive (non-destructive)
- Moved to:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/_archive_local/2026-02-19/`
- Contains:
  - `.cockpit.lock`
  - `Cockpit-v5-Release/`
  - `build-v5/`
  - `dist/_archive/`

## Candidate duplicates and decisions needed
- Spec files:
  - `Centre de controle.spec` vs `cockpit.spec` vs `cockpit_v5.spec`
  - Decision needed: single canonical build spec.
- Python env:
  - `.venv/` vs `venv/`
  - Decision needed: keep one env path as standard.
- Legacy docs:
  - root `Cockpit_V2_*.pdf` and generated docs variants
  - Decision needed: keep source of truth folder for V2 docs.

## Cleanup policy
- No hard delete until explicit owner sign-off.
- Archive first, delete later.
- Never touch tournament trees in cleanup passes.

## Tournament exclusion rules (hard lock)
- Cleanup pass must skip any path containing:
  - `tournament`
  - `PROMPTS`
  - `ROUND-`
  - `JUDGE_FEEDBACK`
  - `TOURNAMENT_ARENA`
- Do not delete or archive out of active scope:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/`
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/`
  - `/Users/oliviercloutier/Desktop/Cockpit/site/` (arena and ops visibility files)
  - `/Users/oliviercloutier/Desktop/Cockpit/control/examples/` files used for tournament ops
- Tournament mode remains dormant by default:
  - no auto-dispatch
  - no auto-judge
  - activation is manual operator action only

## Next cleanup gate
- Run after next V2 implementation checkpoint:
  - choose canonical spec file
  - choose canonical virtualenv path
  - prune archived local artifacts older than 30 days
