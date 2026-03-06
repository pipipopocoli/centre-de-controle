# Cockpit Desktop

React + Tauri desktop frontend for Cockpit.

## Key behavior

- Default landing view is Pixel Home.
- Agent creation is available from Pixel Home.
- To Do board is backed by `control/projects/<project_id>/issues/ISSUE-*.md`.
- Model Routing is role-based:
  - Clems: Kimi K2.5 / Sonnet 4.6 / Opus 4.6
  - L1: manual per agent
  - L2: bounded surgical pool
- Chat modes:
  - `direct` (default, Clems responds if no explicit mention)
  - `conceal_room` (L1 fanout + Clems summary)
- Direct chat supports `Talk to Clems` and `Talk to selected agent`.
- Terminal panel supports send, restart, and Open OS terminal.
- Live state comes from Cockpit Core REST + WebSocket.

## Run (frontend only)

```bash
npm install
npm run dev
```

By default, the app expects backend API at:

- `http://127.0.0.1:8787`

Override with:

```bash
export VITE_COCKPIT_CORE_URL=http://127.0.0.1:8787
```

## Build

```bash
npm run build
```

## Tauri desktop shell

```bash
npm run tauri:dev
```

Shell command exposed:

- `open_os_terminal(agentId, cwd?)`
