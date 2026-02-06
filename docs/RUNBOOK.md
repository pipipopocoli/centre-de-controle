# Centre de controle — Docs/Runbook (PR1)

## Run (Python >= 3.11)

Notes:
- Project targets Python >= 3.11 (3.12 OK).
- The PyPI package "mcp" requires Python >= 3.10, but we standardize higher for simplicity.

```bash
cd /Users/oliviercloutier/Desktop/Cockpit
python3 --version  # must be >= 3.11
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
./launch_cockpit.sh
```

Version check:
- The window title shows: `Centre de controle - <branch>@<sha><*dirty>`
- Sidebar footer shows the same stamp plus `Data: control/projects`

## Run MCP Server (stdio)

```bash
cd /Users/oliviercloutier/Desktop/Cockpit
source venv/bin/activate
python control/mcp_server.py
```

## UI Layout (fixed)

- **Sidebar (left)**: Projects list + `New Project` button.
- **Top center**: Roadmap (timeline + Now/Next/Risks).
- **Center**: Single grid of agents (CDX + AG mixed). Each card shows badge, phase, percent, ETA, status, heartbeat.
- **Right panel**: Chatroom tabs (Global + Threads), composer, `Pack Context` actions, `Ping Leo+Victor`.

## Local Data Structure (V1)

```
control/projects/<project_id>/
  agents/<agent_id>/state.json
  agents/<agent_id>/journal.ndjson
  chat/global.ndjson
  chat/threads/<tag>.ndjson
  roadmap.yml
  ROADMAP.md
  STATE.md
  DECISIONS.md
  settings.json
```

## Screenshot

![Centre de controle UI](images/centre-de-controle.png)
