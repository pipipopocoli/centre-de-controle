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

## Decision lock - 2026-02-19
### Canonical keys
- `canonical_build_spec`:
  - `/Users/oliviercloutier/Desktop/Cockpit/Centre de controle.spec`
- `canonical_virtualenv`:
  - `/Users/oliviercloutier/Desktop/Cockpit/.venv/`
- `canonical_docs_source_of_truth`:
  - ops evidence: `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/`
  - tournament evidence: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/`
  - tournament evidence: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/`
- `cleanup_exclusions_hard_lock`:
  - skip patterns: `tournament`, `PROMPTS`, `ROUND-`, `JUDGE_FEEDBACK`, `TOURNAMENT_ARENA`
  - protected paths:
    - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/`
    - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v2/`
    - `/Users/oliviercloutier/Desktop/Cockpit/site/`
    - `/Users/oliviercloutier/Desktop/Cockpit/control/examples/`

### Short rationale
- `.gitignore` preserves `Centre de controle.spec` while other `*.spec` files are not canonical by default.
- Active verification and mission flows mostly run with `.venv/bin/python`.
- Operational evidence is already consolidated under `/Users/oliviercloutier/Desktop/Cockpit/docs/reports/`.

### Consequences
- `cockpit.spec` and `cockpit_v5.spec` are legacy references, non-canonical.
- `venv/` remains a temporary fallback path, non-canonical.
- Root `Cockpit_V2_*.pdf` files remain archive references, not the primary ops source of truth.

## Cleanup policy
- No hard delete until explicit owner sign-off.
- archive-first policy enforced for every cleanup pass.
- no hard delete without explicit owner sign-off.
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
- No delete, no archive move, no rename in tournament trees.
- Tournament mode remains dormant by default:
  - no auto-dispatch
  - no auto-judge
  - activation is manual operator action only

## Next cleanup gate
- Run after next V2 implementation checkpoint:
  - align scripts and docs toward `.venv/` as canonical runtime path
  - prune archived local artifacts older than 30 days

## Now / Next / Blockers
- Now:
  - canonical spec/env/docs decisions are locked for cleanup.
  - tournament exclusions are explicitly hard-locked.
- Next:
  - align remaining scripts/docs references toward `.venv/` in non-destructive follow-up.
- Blockers:
  - none
