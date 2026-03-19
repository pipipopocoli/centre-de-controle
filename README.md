# Cockpit v3

Multi-agent mission control desktop app for coordinating AI agent teams.

- **Frontend**: React 19 + Vite + TypeScript
- **Desktop shell**: Tauri 2 (Rust)
- **Backend API**: Rust (Axum) — `crates/cockpit-core/`
- **State management**: Zustand

## Launch

Development stack (backend + frontend):

```bash
./launch_cockpit.sh
```

Desktop Tauri mode:

```bash
./launch_cockpit.sh tauri
```

Installed app:

```bash
open "/Applications/Cockpit.app"
```

## OpenRouter key

If you launch `Cockpit.app` from Finder or `open`, put your key in one of these local-only files:

- `~/Library/Application Support/Cockpit/.env`
- `~/.cockpit/.env`
- repo-local `.env` during development

```bash
COCKPIT_OPENROUTER_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

Without a local env file, the installed app can boot but agent chat will stay unavailable because macOS app launches do not inherit your shell exports.

## Project structure

```
agents/          # Agent personality files (clems, victor, leo, nova, vulgarisation)
apps/            # React + Tauri desktop app
crates/          # Rust backend (cockpit-core: Axum + SQLite + PTY)
control/         # MCP server + runtime project data
docs/            # All documentation centralized here
scripts/         # Operational and build scripts
tests/           # Test suite
```

## Documentation

All documentation is centralized in `docs/`:

- [Cockpit Runbook](docs/COCKPIT_RUNBOOK.md)
- [Installation Guide](docs/GUIDE_INSTALLATION.md)
- [Agent System](docs/AGENTS.md)
- [OpenRouter Setup](docs/OPENROUTER_SETUP.md)
- [Releases](docs/releases/)

## Donarg Tileset (local licensed import)

```bash
./scripts/import_office_tileset.sh "/absolute/path/Office Tileset (Donarg).zip"
```

## Pixel reference assets

```bash
./scripts/import_pixel_reference_assets.sh
```

## Testing

```bash
cd apps/cockpit-desktop && npm run build   # frontend build
cd apps/cockpit-desktop && npm run lint    # ESLint
cd crates/cockpit-core && cargo build       # backend build
```
