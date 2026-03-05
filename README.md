# Cockpit Next

Date reference: 2026-03-03.

Cockpit Next is now the default product runtime:
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

Direct scripts:

```bash
./scripts/run_cockpit_next_dev.sh
./scripts/run_cockpit_next_tauri.sh
```

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

- [Cockpit Next Runbook](/Users/oliviercloutier/Desktop/Cockpit/docs/COCKPIT_NEXT_RUNBOOK.md)

## Legacy (manual fallback only)

Legacy Python/Qt is no longer the default launch path.

```bash
./launch_cockpit_legacy.sh
```
