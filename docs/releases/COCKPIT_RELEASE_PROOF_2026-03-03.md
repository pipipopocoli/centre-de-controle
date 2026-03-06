# Cockpit Release Proof

Date: 2026-03-03
Gate level: Hard Gate
Target: Local Desktop Release
Legacy policy: Immediate Cutover

## Quality gates

- `crates/cockpit-core`: `cargo check && cargo test` -> PASS
- `apps/cockpit-next-desktop`: `npm run build` -> PASS
- `apps/cockpit-next-desktop`: `npm run lint` -> PASS
- `apps/cockpit-next-desktop/src-tauri`: `cargo check` -> PASS
- `apps/cockpit-next-desktop`: `npm run tauri:build` -> PASS

## Runtime gates

Stack started with `./scripts/run_cockpit_next_dev.sh`.

- Backend health: `GET /healthz` -> 200 PASS
- Frontend root: `GET http://127.0.0.1:5173/` -> 200 PASS
- Agent create -> terminal auto-created -> PASS
- Direct chat (`allo`) -> Clems default reply -> PASS
- Conceal room toggle -> multi-agent responses + Clems summary -> PASS
- Terminal send/restart -> WS events observed (`agent.terminal.status`) -> PASS

## Desktop packaging gates

- `.app` artifact generated:
  - `apps/cockpit-next-desktop/src-tauri/target/release/bundle/macos/Cockpit.app`
- Local install helper run:
  - `./scripts/install_cockpit_next_app.sh` -> PASS
- App launch check:
  - `open /Applications/Cockpit.app` -> process detected -> PASS

## Cutover gates

- Root launcher default switched to Cockpit Next:
  - `launch_cockpit.sh` -> `scripts/run_cockpit_next_dev.sh` (default)
- Legacy launcher kept manual only:
  - `launch_cockpit_legacy.sh`
- Root docs now point to Cockpit Next commands first:
  - `README.md`, `QUICKSTART.md`

## Verdict

GO
