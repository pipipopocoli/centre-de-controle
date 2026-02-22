# WAVE09 Live App Lock - 2026-02-21

## Objective
- Lock desktop update behavior to avoid operator confusion:
  - Dev Live for implementation,
  - Release app for snapshot distribution.

## Dispatch prompts (copy/paste)

### @victor
```md
@victor
Objective
- Lock desktop runtime mode contract (DEV LIVE vs RELEASE) and prevent false assumptions about auto-update.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/main.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/main_window.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/sidebar.py
- /Users/oliviercloutier/Desktop/Cockpit/docs/PACKAGING.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/RUNBOOK.md

Done
- mode detection exposed (dev live vs release)
- runtime path clarity shown (repo/appsupport)
- docs updated with exact launch policy
- no tournament changes
```

### @leo
```md
@leo
Objective
- Implement operator-visible badges for update mode and live scope.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/sidebar.py
- /Users/oliviercloutier/Desktop/Cockpit/app/ui/theme.qss
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/

Done
- badge "DEV LIVE" or "RELEASE"
- short helper text: what updates live vs after restart vs rebuild
- screenshot evidence normal + degraded
```

### @nova
```md
@nova
Objective
- Publish a 60s operator brief: "how to know the app is up to date".

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/nova/memory.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/

Done
- checklist 60s (mode, stamp, repo head, runtime path)
- top 3 confusion risks + mitigation
- owner/action/evidence mapping
```

## Operator command
- Install Dev Live icon launcher:
```bash
cd /Users/oliviercloutier/Desktop/Cockpit
scripts/packaging/install_dev_live_launcher.sh
```
