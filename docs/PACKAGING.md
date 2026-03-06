# Packaging (legacy Python app archived, Cockpit active)

## Status

- Legacy Python packaging (`Centre de controle.app`) is archived.
- Official daily operator app is `Cockpit.app`.
- Canonical launch command:

```bash
open "/Applications/Cockpit.app"
```

- Canonical runbook:
  - `docs/COCKPIT_NEXT_RUNBOOK.md`

## Daily operator policy

1. Use only `Cockpit.app` for production daily workflow.
2. Keep `Centre de controle.app` references for historical evidence only.
3. If a legacy package script is used, mark the run as debug/manual.

## Build and install Cockpit app

```bash
cd <repo-root>
npm --prefix apps/cockpit-next-desktop run tauri:build
./scripts/install_cockpit_next_app.sh /Applications
```

## Verify installed app target

```bash
ls -ld "/Applications/Cockpit.app"
/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "/Applications/Cockpit.app/Contents/Info.plist"
```

Expected:
- app path exists at `/Applications/Cockpit.app`
- bundle id is `com.cockpit`

## One-time compatibility note

If previous app identity exists (`Cockpit Next`), keep one release cycle migration note and copy-forward instructions in:
- `docs/COCKPIT_NEXT_RUNBOOK.md`
