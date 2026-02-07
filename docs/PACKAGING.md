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
- ./.venv/bin/python -m pyinstaller --windowed --name "Centre de controle" \
  --add-data "app/ui/theme.qss:app/ui" \
  app/main.py

Output:
- dist/Centre de controle.app

If you see "python: command not found", use the venv command above.

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
