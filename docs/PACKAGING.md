# Packaging (macOS .app)

Goal: build a local-first macOS .app that runs without a venv and keeps data outside the bundle.

## Data directory
Order of precedence:
- COCKPIT_DATA_DIR=repo|dev -> control/projects (dev only)
- COCKPIT_DATA_DIR=app|appsupport -> ~/Library/Application Support/Cockpit/projects
- COCKPIT_DATA_DIR=<absolute path> -> explicit projects root
- No env var -> ~/Library/Application Support/Cockpit/projects (canonical default)

## PyInstaller prototype (recommended)

Install:
- ./.venv/bin/python -m pip install pyinstaller
- (fallback) python3 -m pip install pyinstaller

Build (windowed .app):
- PATH="$PWD/.venv/bin:$PATH" scripts/packaging/build_mac_app.sh

Output:
- dist/Centre de controle.app

Version stamp:
- The build script writes `build/version.json` with branch/sha/dirty.
- The app reads the bundled `app/version.json` when git is unavailable inside the bundle.

Notes:
- The build script sets `PYINSTALLER_CONFIG_DIR=build/pyinstaller-cache` to avoid permissions errors in
  `~/Library/Application Support/pyinstaller`.
- If you see Qt plugin errors, keep `--collect-submodules PySide6` in the build command.
- Version stamp is written at build time to `build/version.json` and bundled into the app as `app/version.json`.
- The `*` indicates a dirty repo **at build time**, not runtime.
- If you see "python: command not found", use the venv command above.
If the app launches with the *old* UI, ensure you're opening:
- `dist/Centre de controle.app` (not a previously installed copy in /Applications).
If you distribute outside your dev machine, codesign the app:
```
codesign --deep --force --options runtime --sign "Developer ID Application: <NAME>" dist/<App>.app
```

## QA checklist
- Launch the .app
- Verify version stamp is visible (or fallback string)
- Open demo project (auto-created if missing)
- Send a chat message and confirm NDJSON writes to the data dir
- Verify UI layout (Paper Ops) and chat buttons are not clipped

## Notes / Risks
- Qt plugins can be finicky; if the app opens blank, verify PyInstaller collected Qt plugins.
- Version stamp will show unknown@unknown if version.json is missing and git is not available inside the bundle.
- Build artifacts can be large; use dist/ cleanup as needed.
