# Packaging (macOS .app)

Goal: build a local-first macOS .app that runs without a venv and keeps data outside the bundle.

## Data directory
Order of precedence:
- COCKPIT_DATA_DIR (projects root)
- Repo local: control/projects (if present)
- Default: ~/Library/Application Support/Cockpit/projects

## PyInstaller prototype (recommended)

Install:
- ./.venv/bin/python -m pip install pyinstaller
- (fallback) python3 -m pip install pyinstaller

Build (windowed .app):
- PATH="$PWD/.venv/bin:$PATH" scripts/packaging/build_mac_app.sh

Output:
- dist/Centre de controle.app

Notes:
- The build script sets `PYINSTALLER_CONFIG_DIR=build/pyinstaller-cache` to avoid permissions errors in
  `~/Library/Application Support/pyinstaller`.
- If you see "python: command not found", use the venv command above.
If the app launches with the *old* UI, ensure you're opening:
- `dist/Centre de controle.app` (not a previously installed copy in /Applications).

## QA checklist
- Launch the .app
- Verify version stamp is visible (or fallback string)
- Open demo project (auto-created if missing)
- Send a chat message and confirm NDJSON writes to the data dir
- Verify UI layout (Paper Ops) and chat buttons are not clipped

## Notes / Risks
- Qt plugins can be finicky; if the app opens blank, verify PyInstaller collected Qt plugins.
- Version stamp will show unknown@unknown if git is not available inside the bundle.
- Build artifacts can be large; use dist/ cleanup as needed.
