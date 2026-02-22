# ISSUE-CP-0035 - Wave09 dual-root control cadence

- Owner: victor
- Phase: Implement
- Status: Done

## Objective
- Lock runtime control cadence so both roots stay healthy during active execution:
  - repo root: `/Users/oliviercloutier/Desktop/Cockpit/control/projects`
  - AppSupport root: `/Users/oliviercloutier/Library/Application Support/Cockpit/projects`

## Scope (In)
- `/Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py`
- `/Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py`
- `/Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/`
- `/Users/oliviercloutier/Library/Application Support/Cockpit/projects/cockpit/runs/`

## Scope (Out)
- Tournament activation
- UI refactor
- Cross-project retrieval changes

## Done (Definition)
- [x] Cadence runbook is documented with exact commands and intervals.
- [x] Repo and AppSupport remain healthy across two consecutive checkpoints.
- [x] Runtime/log reconciliation removes stale/phantom open statuses safely.
- [x] No tournament path changed or auto-dispatch triggered.

## Closeout
- Closed at: 2026-02-20T22:21Z
- Final packet:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE09_RUNTIME_FINAL_LOCK_2026-02-20T2221Z.md`
- Prior cadence packet:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE09_DUAL_ROOT_CADENCE_2026-02-20T2150Z.md`
- Gate evidence:
  - repo root healthy and AppSupport healthy on two live checkpoints
  - `stale_kpi_snapshot` avoided by default cadence snapshot emission

## Test/QA
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --data-dir repo --once --max-actions 0 --no-open --no-clipboard --no-notify`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --once --max-actions 0 --no-open --no-clipboard --no-notify`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --stale-seconds 3600 --max-open 3 --data-dir repo`
- `./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --stale-seconds 3600 --max-open 3`

## Links
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/WAVE09_PRECHECK_2026-02-20.md`
- `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE09_DISPATCH_2026-02-20.md`
