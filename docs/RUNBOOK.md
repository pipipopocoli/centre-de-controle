# Legacy Runbook - Centre de controle (archived)

## Status

- Archived reference only (legacy Python app path).
- Official daily operator workflow is now Cockpit:
  - Runbook: `docs/COCKPIT_NEXT_RUNBOOK.md`
  - App path: `/Applications/Cockpit.app`
  - Launch command: `open "/Applications/Cockpit.app"`

## Legacy scope note

This file is kept for historical troubleshooting only.
Do not use legacy Python packaging or `Centre de controle.app` for daily operations.

## Legacy launch (manual debug only)

```bash
./launch_cockpit_legacy.sh
```

## Canonical runtime data structure

```text
control/projects/<project_id>/
  agents/<agent_id>/state.json
  agents/<agent_id>/journal.ndjson
  chat/global.ndjson
  chat/threads/<tag>.ndjson
  roadmap.yml
  ROADMAP.md
  STATE.md
  DECISIONS.md
  settings.json
```

## Legacy image reference

![Centre de controle UI](images/centre-de-controle.png)
