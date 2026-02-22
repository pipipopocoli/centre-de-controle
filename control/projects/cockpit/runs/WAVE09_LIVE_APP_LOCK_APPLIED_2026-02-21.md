# WAVE09 Live App Lock Applied - 2026-02-21

## Objective
- Apply desktop update channel lock and make runtime mode visible in app UI.

## Applied changes
1. Runtime mode and source visibility in UI:
- `app/main.py`
- `app/ui/main_window.py`
- `app/ui/sidebar.py`
- `app/ui/theme.qss`

2. Docs updated:
- `docs/PACKAGING.md`
- `docs/RUNBOOK.md`

3. Governance updated:
- `control/projects/cockpit/DECISIONS.md` (ADR-CP-014)
- `control/projects/cockpit/STATE.md`
- `control/projects/cockpit/ROADMAP.md`

4. Launcher installer added:
- `scripts/packaging/install_dev_live_launcher.sh`
- created launcher on machine:
  - `/Users/oliviercloutier/Applications/Centre de controle - Dev Live.app`

## Verification
- `./.venv/bin/python -m py_compile app/main.py app/ui/main_window.py app/ui/sidebar.py` -> PASS
- `./.venv/bin/python tests/verify_project_context_startup.py` -> PASS
- `./.venv/bin/python tests/verify_wave06_nova.py` -> PASS
- `./.venv/bin/python tests/verify_auto_mode_healthcheck.py` -> PASS
- Healthcheck repo root -> healthy
- Healthcheck AppSupport root -> healthy

## Operator note
- During implementation, launch via Dev Live icon or `./launch_cockpit.sh`.
- Release app remains snapshot-only and requires rebuild for new code/UI.
