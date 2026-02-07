# ISSUE-0011 - Packaging research (macOS .app) (V2)

- Owner: victor
- Phase: Ship
- Status: Done

## Objective
- Research and prototype packaging Cockpit as a macOS .app (double-click run), without breaking local-first behavior.

## Scope (In)
- Pick a packaging tool (PyInstaller, Briefcase, etc.) and document why.
- Prototype a build that runs on the same machine without venv.
- Confirm file paths / data dir behavior.
- Document the build command + troubleshooting.

## Scope (Out)
- Code signing / notarization.
- Windows/Linux builds.
- Auto-update system.

## Now
- Build + QA done (packaged app launched; data dir ok).

## Next
- Optional: verify on a clean user account (best effort).

## Blockers
- None.

## Done (Definition)
- Documented prototype exists (build command + run steps).
- App launches and can open the demo project.
- Version stamp visible via build-time version.json.

## Links
- STATE.md: control/projects/demo/STATE.md
- DECISIONS.md: control/projects/demo/DECISIONS.md
- docs/PACKAGING.md
- scripts/packaging/build_mac_app.sh
- PR:

## Risks
- Packaging churn and time sink.
- Runtime path bugs (resources vs working dir).

## Research Notes (Options)

### Option A — PyInstaller (recommendation for V2 prototype)
Pros:
- Mature, widely used for PySide6 on macOS.
- Can generate a native `.app` bundle (`--windowed`) and run offline.
- Minimal project structure changes; spec file handles data files.
Cons:
- Larger binaries; build artifacts can be heavy.
- Qt plugin collection can be finicky (platforms, imageformats).
- `--onefile` extracts to temp at runtime; slower cold start.
Expected Steps:
- Create a `.spec` file and add data files (QSS, templates, `control/` defaults).
- Build: `pyinstaller --windowed --name "Centre de controle" app/main.py`.
- Verify `.app` launches and reads/writes data dir outside bundle.
Risks:
- Missing Qt plugins -> blank window or crash.
- App resources path differs from dev (need path helper).

### Option B — Briefcase (BeeWare)
Pros:
- Produces a proper macOS app bundle with standard structure.
- Good for long-term distribution if we commit to the tooling.
Cons:
- Requires project packaging setup (pyproject, app config).
- Qt/PySide6 support is less turnkey; more moving parts.
Expected Steps:
- Add Briefcase config; package app + dependencies.
- Run `briefcase create` / `briefcase build` / `briefcase run`.
Risks:
- Toolchain friction and slower iteration.
- Dependency compatibility and template constraints.

### Option C — Nuitka (compiled, standalone)
Pros:
- Compiles Python to C, can reduce runtime overhead.
- Standalone app bundle; good performance.
Cons:
- Longer builds; more complex flags.
- Troubleshooting is heavier vs PyInstaller.
Expected Steps:
- Build with `nuitka --standalone --macos-app-name=... app/main.py`.
- Include Qt plugins/resources manually if needed.
Risks:
- Build complexity; bigger surface for platform-specific issues.

## Local-first Constraints
- Data dir must live outside the `.app` bundle (e.g., `~/Library/Application Support/...`).
- App should run fully offline with local `control/projects/...` state.
- Version stamp must remain visible post-packaging.

## Recommendation (Draft)
- Start with **PyInstaller** for the V2 prototype: fastest path to a working `.app`.
- Re-evaluate Briefcase/Nuitka only if PyInstaller proves unstable.

## Prototype Attempt (Local)
- Install: `./.venv/bin/python -m pip install pyinstaller`
- Build: `PATH="$PWD/.venv/bin:$PATH" scripts/packaging/build_mac_app.sh`
- Output: `dist/Centre de controle.app`
- Notes:
  - Build script uses `pyinstaller` CLI + `--noconfirm`.
  - Set `PYINSTALLER_CONFIG_DIR` to `build/pyinstaller-cache` to avoid permission errors.
  - Verified `theme.qss` is bundled at `Contents/Resources/app/ui/theme.qss`.

## QA (Final)
- ✅ App launched and created data dir at:
  - `~/Library/Application Support/Cockpit/projects/demo`
- ✅ Local-first structure created (STATE/ROADMAP/DECISIONS/agents/chat).
- ✅ Version stamp visible (build-time version.json).
- ✅ Send message -> `chat/global.ndjson` writes in data dir.
