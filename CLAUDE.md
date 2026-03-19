# Cockpit v3

## Stack

- **Frontend**: React 19 + Vite + TypeScript — `apps/cockpit-desktop/`
- **Desktop shell**: Tauri 2 (Rust) — `apps/cockpit-desktop/src-tauri/`
- **Backend API**: Rust (Axum) — `crates/cockpit-core/`
- **MCP Server**: Python — `control/mcp_server.py`
- **State management**: Zustand — `apps/cockpit-desktop/src/store/index.ts`
- **API client**: `apps/cockpit-desktop/src/lib/cockpitClient.ts`

## Launch

```bash
./launch_cockpit.sh          # dev (backend + frontend)
./launch_cockpit.sh tauri    # desktop Tauri mode
```

Backend default port: `8787` (override via `VITE_COCKPIT_CORE_URL`).
Tauri spawns `cockpit-core` automatically on startup.

## Code style

- **TypeScript**: ESLint 9 flat config (`apps/cockpit-desktop/eslint.config.js`)
- **Rust**: standard rustfmt
- **Python** (MCP server only): snake_case, type hints
- **Files**: kebab-case
- **Exports**: camelCase (TS), snake_case (Python/Rust)
- **CSS**: Plain CSS in `App.css` — no CSS-in-JS

## Commit convention

```
type: description
```

Types: `fix`, `refactor`, `chore`, `docs`, `merge`, `feat`, `perf`, `style`, `test`

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

## Frontend architecture

```
src/
├── App.tsx          # Coordinator (~300 lines) — imports hooks + tabs
├── App.css          # Design system (CSS variables, all component styles)
├── store/index.ts   # Zustand store (single source of truth)
├── lib/cockpitClient.ts  # API client (all REST calls to cockpit-core)
├── types.ts         # Shared TypeScript types
├── hooks/           # Custom hooks (state logic, side effects)
│   ├── usePolling.ts       # Clock tick, viewport RAF, media cleanup
│   ├── useWebSocket.ts     # WS connection, fallback polling
│   ├── useDataSync.ts      # Bootstrap, refresh callbacks, agent sync
│   ├── useAgentActions.ts  # Create/delete/select agents
│   ├── useChatActions.ts   # Send/reset chat, voice recording
│   ├── useTaskActions.ts   # Create/save/move tasks
│   └── useProjectActions.ts # Takeover, LLM profile, project CRUD
├── tabs/            # Tab components (one per top-level view)
│   ├── PixelHomeTab.tsx      # Main canvas + agent workspace
│   ├── ConciergeRoomTab.tsx  # Multi-agent board room
│   ├── OverviewTab.tsx       # Project summary + roadmap
│   ├── PilotageTab.tsx       # Live operations dashboard
│   ├── DocsTab.tsx           # Runbook + skills + project docs
│   ├── TodoTab.tsx           # Kanban task board
│   └── ModelRoutingTab.tsx   # LLM model assignments
└── panels/          # Pixel Home sub-panels
    ├── LeftRail.tsx         # Navigation buttons + agent counts
    ├── WorkspacePanel.tsx   # Agent roster / layout editor / settings
    ├── CenterStage.tsx      # Pixel canvas + zoom controls
    └── WorkbenchPanel.tsx   # Chat / terminal / approvals / events
```

## Agent hierarchy

- **L0**: `clems` — orchestrator, coordinates all agents
- **L1**: `victor` (backend), `leo` (UI), `nova` (research), `vulgarisation` (simplification)
- **L2**: `agent-*` — spawned specialist workers

## Key conventions

- New UI components go into separate files under `src/tabs/`, `src/panels/`, or `src/hooks/`
- All components consume state via `useCockpitStore()` (Zustand)
- API calls go through `cockpitClient.*` functions in `lib/cockpitClient.ts`
- Agent personality files in `agents/*.md` — do not modify without operator approval
- Runtime data in `control/projects/<id>/` — this is state, not source code
- Backend API is Rust only (`crates/cockpit-core`) — no Python backend

## Testing

```bash
cd apps/cockpit-desktop && npm run build   # frontend build (tsc + vite)
cd apps/cockpit-desktop && npm run lint    # ESLint
cd crates/cockpit-core && cargo build      # backend build
```
