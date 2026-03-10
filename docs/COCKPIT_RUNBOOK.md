# Cockpit Runbook

Date reference: 2026-03-06

## Canonical stack

- Desktop shell: Tauri (`apps/cockpit-desktop/src-tauri`)
- Frontend: React + Vite (`apps/cockpit-desktop`)
- Backend: Rust Axum (`crates/cockpit-core`)
- Data compatibility root: `control/projects/<project_id>`

## Official launch path

Production app:

```bash
open "/Applications/Cockpit.app"
```

Official path:
- `/Applications/Cockpit.app`

Development entrypoints:

```bash
./launch_cockpit.sh
./scripts/run_cockpit.sh
./scripts/run_cockpit_tauri.sh
```

Archived legacy launchers stay historical only and are out of the daily operator path.
Do not use archived Python/Qt launchers for normal Cockpit work.

## Local env for installed app

`Cockpit.app` is launched by macOS, not by your interactive shell. That means shell-only exports do not reach the bundled backend.

Canonical local env path:

```bash
$HOME/Library/Application Support/Cockpit/.env
```

Supported fallback paths:

- `$HOME/.cockpit/.env`
- repo-local `.env` during development

Minimal file:

```bash
COCKPIT_OPENROUTER_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

Rule:
- keep this file local only
- never commit it
- if chat is down but `/healthz` is green, check this file first

## Pre-launch API check (must pass)

```bash
curl -i 'http://127.0.0.1:8787/healthz'
curl -i 'http://127.0.0.1:8787/v1/projects/cockpit/pixel-feed'
curl -i 'http://127.0.0.1:8787/v1/projects/cockpit/chat?limit=10&visibility=all'
curl -i 'http://127.0.0.1:8787/v1/projects/cockpit/chat/approvals?status=pending'
curl -i 'http://127.0.0.1:8787/v1/projects/cockpit/llm-profile'
```

Expected: all responses return `HTTP 200`.

If `/healthz` is `200` but chat still looks dead, verify the OpenRouter env file above before debugging the UI.

## One-time migration note (`com.cockpit.next` -> `com.cockpit`)

If old app data/config is still under previous bundle identity, run once:

```bash
OLD_APP_DIR="$HOME/Library/Application Support/com.cockpit.next"
NEW_APP_DIR="$HOME/Library/Application Support/com.cockpit"
if [ -d "$OLD_APP_DIR" ] && [ ! -d "$NEW_APP_DIR" ]; then
  cp -R "$OLD_APP_DIR" "$NEW_APP_DIR"
fi
```

Compatibility policy:
- Daily operations must use `Cockpit.app` only.
- If an older app bundle still exists on the machine, remove it to avoid wrong launches.

## Local premium assets (Donarg)

```bash
./scripts/import_office_tileset.sh "/absolute/path/Office Tileset (Donarg).zip"
./scripts/build_donarg_catalog.py
```

Imported files are local-only and git-ignored under:
- `apps/cockpit-desktop/public/local-assets/donarg`

## Pixel reference assets (MIT)

```bash
./scripts/import_pixel_reference_assets.sh
```

Imported files:
- `apps/cockpit-desktop/public/local-assets/pixel-reference/characters/char_0..5.png`
- `apps/cockpit-desktop/public/local-assets/pixel-reference/walls.png`

## Locked API contracts

REST:
- `POST /v1/projects/{id}/agents`
- `DELETE /v1/projects/{id}/agents/{agent_id}`
- `POST /v1/projects/{id}/agents/{agent_id}/terminal/open`
- `POST /v1/projects/{id}/agents/{agent_id}/terminal/send`
- `POST /v1/projects/{id}/agents/{agent_id}/terminal/restart`
- `POST /v1/projects/{id}/chat/live-turn`
- `POST /v1/projects/{id}/chat/reset`
- `GET /v1/projects/{id}/chat/approvals?status=pending|approved|rejected`
- `POST /v1/projects/{id}/chat/approvals/{request_id}/approve`
- `POST /v1/projects/{id}/chat/approvals/{request_id}/reject`
- `GET /v1/projects/{id}/pixel-feed`
- `GET /v1/projects/{id}/chat?visibility=operator|all`
- `GET /v1/projects/{id}/layout`
- `PUT /v1/projects/{id}/layout`
- `GET /v1/projects/{id}/llm-profile`
- `PUT /v1/projects/{id}/llm-profile`

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

cd ../../apps/cockpit-desktop
npm run build
npm run lint

cd src-tauri
cargo check

cd ..
npm run tauri:build
```

## Artifacts

- Tauri binary:
  - `apps/cockpit-desktop/src-tauri/target/release/cockpit`
- Tauri macOS app bundle:
  - `apps/cockpit-desktop/src-tauri/target/release/bundle/macos/Cockpit.app`

## Install local app bundle

```bash
./scripts/install_cockpit_app.sh
./scripts/install_cockpit_app.sh "$HOME/Applications"
```
