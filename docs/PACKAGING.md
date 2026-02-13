# Packaging (macOS .app)

Goal: produce a runnable app bundle with tree icon, install it in `/Applications`, and publish a demo release to Google Drive.

## Data directory
Runtime projects root order:
- `COCKPIT_DATA_DIR` (if set)
- repo local `control/projects` (dev mode)
- default `~/Library/Application Support/Cockpit/projects`

## 1) Generate local tree icon (no API)
```bash
cd /Users/oliviercloutier/Desktop/Cockpit
./.venv/bin/python scripts/packaging/generate_tree_icon.py --out /Users/oliviercloutier/Desktop/Cockpit/assets/tree-icon.png
```

## 2) Build `.app` with PyInstaller
Install dependency if needed:
```bash
./.venv/bin/python -m pip install pyinstaller
```

Build:
```bash
cd /Users/oliviercloutier/Desktop/Cockpit
COCKPIT_ICON_SOURCE=/Users/oliviercloutier/Desktop/Cockpit/assets/tree-icon.png scripts/packaging/build_mac_app.sh
```

Expected output:
- `/Users/oliviercloutier/Desktop/Cockpit/dist/Centre de controle.app`
- `/Users/oliviercloutier/Desktop/Cockpit/assets/Cockpit.icns`

## 3) Install app in `/Applications`
```bash
rm -rf "/Applications/Centre de controle.app"
cp -R "/Users/oliviercloutier/Desktop/Cockpit/dist/Centre de controle.app" "/Applications/"
touch /Applications
killall Finder || true
killall Dock || true
```

## 4) Publish demo release to Google Drive
```bash
cd /Users/oliviercloutier/Desktop/Cockpit
scripts/release/publish_demo_to_drive.sh \
  --app "/Users/oliviercloutier/Desktop/Cockpit/dist/Centre de controle.app" \
  --drive-root "/Users/oliviercloutier/Library/CloudStorage/GoogleDrive-oliviier.cloutier@gmail.com/Mon disque/Cockpit/releases"
```

This creates a versioned folder:
- `v3.6.1_<YYYYMMDD_HHMMSS>_<shortsha>/`
- contains `.app`, `.zip`, and `release_manifest.txt`
- old versions are kept

## QA checklist
- Launch from `/Applications/Centre de controle.app`
- Confirm custom tree icon in Finder + Dock
- Confirm version stamp is visible
- Confirm chat + automation panel render correctly
- Mention `@victor` (headless codex path) and `@leo` (AG supervised path)

## Notes
- Build script uses `build/version.json` for build-time stamp (`branch@sha` + optional `*` dirty flag).
- Icon conversion uses `scripts/packaging/build_icon_icns.sh` and macOS tools `sips` + `iconutil`.
- If icon conversion fails, the script falls back to existing `assets/Cockpit.icns` if present.
