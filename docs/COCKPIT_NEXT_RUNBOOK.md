# Cockpit Next Runbook

Date reference: 2026-03-03

## Canonical stack

- Desktop shell: Tauri (`apps/cockpit-next-desktop/src-tauri`)
- Frontend: React + Vite (`apps/cockpit-next-desktop`)
- Backend: Rust Axum (`crates/cockpit-core`)
- Data compatibility root: `control/projects/<project_id>`

## Launch commands

Default launcher:

```bash
./launch_cockpit.sh
```

Direct development stack:

```bash
./scripts/run_cockpit_next_dev.sh
```

Direct Tauri dev:

```bash
./scripts/run_cockpit_next_tauri.sh
```

Legacy fallback (manual only):

```bash
./launch_cockpit_legacy.sh
```

## Local premium assets (Donarg)

```bash
./scripts/import_office_tileset.sh "/absolute/path/Office Tileset (Donarg).zip"
```

Regenerate expanded furniture extraction catalog:

```bash
./scripts/build_donarg_catalog.py
```

The imported files are local-only and git-ignored under:

- `apps/cockpit-next-desktop/public/local-assets/donarg`

## Pixel reference assets (MIT)

```bash
./scripts/import_pixel_reference_assets.sh
```

Imported files:
- `apps/cockpit-next-desktop/public/local-assets/pixel-reference/characters/char_0..5.png`
- `apps/cockpit-next-desktop/public/local-assets/pixel-reference/walls.png`

## Locked API contracts

REST:

- `POST /v1/projects/{id}/agents`
- `DELETE /v1/projects/{id}/agents/{agent_id}`
- `POST /v1/projects/{id}/agents/{agent_id}/terminal/open`
- `POST /v1/projects/{id}/agents/{agent_id}/terminal/send`
- `POST /v1/projects/{id}/agents/{agent_id}/terminal/restart`
- `POST /v1/projects/{id}/chat/live-turn`
- `POST /v1/projects/{id}/chat/reset`
- `GET /v1/projects/{id}/pixel-feed`
- `GET /v1/projects/{id}/chat?visibility=operator|all`
- `GET /v1/projects/{id}/layout`
- `PUT /v1/projects/{id}/layout`

WebSocket events:

- `connection.ready`
- `agent.created`
- `agent.updated`
- `agent.terminal.status`
- `chat.message.created`
- `chat.turn.started`
- `chat.turn.completed`
- `pixel.updated`
- `layout.updated`

## Build and quality gates

```bash
cd crates/cockpit-core
cargo check
cargo test

cd ../../apps/cockpit-next-desktop
npm run build
npm run lint

cd src-tauri
cargo check

cd ..
npm run tauri:build
```

## Artifacts

- Tauri binary:
  - `apps/cockpit-next-desktop/src-tauri/target/release/cockpit-next-desktop`
- Tauri macOS app bundle:
  - `apps/cockpit-next-desktop/src-tauri/target/release/bundle/macos/Cockpit Next.app`

## Install `.app` locally

```bash
./scripts/install_cockpit_next_app.sh
```

Install to custom path:

```bash
./scripts/install_cockpit_next_app.sh "$HOME/Applications"
```
