# Centre de controle — Docs/Runbook (PR1)

## Run (Python >= 3.11)

```bash
cd /Users/oliviercloutier/Desktop/Cockpit
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app/main.py
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

![Centre de controle UI](docs/images/centre-de-controle.png)
