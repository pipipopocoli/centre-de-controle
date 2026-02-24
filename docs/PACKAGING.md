# Packaging (macOS .app)

Goal: build a local-first macOS app that runs without a venv and keeps data outside the bundle.

## Desktop launch contract (Wave16)

Two channels are supported, but only one is the primary operator icon:

1. Primary operator icon (Release single-icon target)
- Launch source: `/Applications/Centre de controle.app`
- Install source: `dist/Centre de controle.app`
- Behavior: single app icon in Dock/Finder for the main operator path.
- Rebuild required to ship new Python/UI code into the app bundle.

2. Dev Live (engineering lane, optional)
- Launch source: `./launch_cockpit.sh`
- Uses current repo code for iteration.
- QSS updates are live; Python code changes apply after restart.
- Dev Live launcher may still show applet/python split behavior, but this is not the primary operator icon path.

## Data directory
Order of precedence:
- `COCKPIT_DATA_DIR=repo|dev` -> `control/projects` (dev only)
- `COCKPIT_DATA_DIR=app|appsupport` -> `~/Library/Application Support/Cockpit/projects`
- `COCKPIT_DATA_DIR=<absolute path>` -> explicit projects root
- no env var -> `~/Library/Application Support/Cockpit/projects` (canonical default)

## Build release app (PyInstaller)

Install:
- `./.venv/bin/python -m pip install pyinstaller`
- fallback: `python3 -m pip install pyinstaller`

Build:
- `PATH="$PWD/.venv/bin:$PATH" scripts/packaging/build_mac_app.sh`

Output:
- `dist/Centre de controle.app`

Version stamp:
- Build writes `build/version.json` with branch/sha/dirty.
- App reads bundled `app/version.json` when git is not available in bundle runtime.

## Install primary operator icon target

Use this once after each release build (or when replacing stale launcher applets):

```bash
cd /Users/oliviercloutier/Desktop/Cockpit
scripts/packaging/install_release_app.sh
```

CLI options:
- `--source <app_path>` (default: `dist/Centre de controle.app`)
- `--target <app_path>` (default: `/Applications/Centre de controle.app`)
- `--keep-dev-live true|false` (default: `true`)

Behavior:
- Existing target is backed up with timestamp.
- If existing target was an applet launcher (`CFBundleExecutable=applet`), it is still backed up and can be preserved as optional Dev Live launcher when `--keep-dev-live true`.
- Release app is copied into `/Applications/Centre de controle.app`.

Verification:

```bash
plutil -p /Applications/Centre\ de\ controle.app/Contents/Info.plist
# CFBundleExecutable should be "Centre de controle"
```

## Optional: install Dev Live launcher

```bash
cd /Users/oliviercloutier/Desktop/Cockpit
scripts/packaging/install_dev_live_launcher.sh
```

Expected output:
- `~/Applications/Centre de controle - Dev Live.app` (preferred), or
- fallback `~/Applications/Centre de controle - Dev Live.command`

## Codesign (when distributing outside local machine)

```bash
codesign --deep --force --options runtime --sign "Developer ID Application: <NAME>" dist/Centre\ de\ controle.app
```

## QA checklist
- Launch `/Applications/Centre de controle.app`
- Confirm `CFBundleExecutable` is `Centre de controle`
- Verify version stamp is visible in UI
- Open demo project (auto-created if missing)
- Send a chat message and confirm NDJSON writes to data dir
- Verify UI layout and chat actions remain readable

## Notes / risks
- If app opens blank, verify PyInstaller collected Qt plugins (`--collect-submodules PySide6`).
- Version stamp can show `unknown@unknown` when version.json is missing and git is unavailable in bundle runtime.
- Keep release and dev-live channels explicit to avoid launch confusion.
