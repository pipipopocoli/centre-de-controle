# Cockpit

Date reference: 2026-03-03.

Cockpit is the default product runtime:
- Frontend: React + Vite
- Desktop shell: Tauri
- Core backend: Rust (Axum + Tokio)

## Launch (default)

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

Direct scripts:

```bash
./scripts/run_cockpit_next_dev.sh
./scripts/run_cockpit_next_tauri.sh
```

## OpenRouter key for Finder-launched app

If you launch `Cockpit.app` from Finder or `open`, put your key in one of these local-only files:

- `~/Library/Application Support/Cockpit/.env`
- `~/.cockpit/.env`
- repo-local `.env` during development

Recommended contents:

```bash
COCKPIT_OPENROUTER_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

Without a local env file, the installed app can boot but agent chat will stay unavailable because macOS app launches do not inherit your shell exports.

## Donarg Tileset (local licensed import)

Import your purchased pack locally (not tracked in git):

```bash
./scripts/import_office_tileset.sh "/absolute/path/Office Tileset (Donarg).zip"
```

Imported files are stored in:

`apps/cockpit-next-desktop/public/local-assets/donarg`

## Pixel reference assets (MIT style parity)

Import PixelAgent reference sprites locally:

```bash
./scripts/import_pixel_reference_assets.sh
```

This imports:
- `public/local-assets/pixel-reference/characters/char_0..5.png`
- `public/local-assets/pixel-reference/walls.png`

## Runbook

- [Cockpit Runbook](/Users/oliviercloutier/Desktop/Cockpit/docs/COCKPIT_NEXT_RUNBOOK.md)

## Legacy (manual fallback only)

Legacy Python/Qt is no longer the default launch path.

```bash
./launch_cockpit_legacy.sh
```
