# Centre de controle - Docs/Runbook

## Run (Python >= 3.11)

Notes:
- Project target: Python >= 3.11 (3.12 OK).
- PyPI package `mcp` requires Python >= 3.10, but project baseline stays at 3.11+.

```bash
cd /Users/oliviercloutier/Desktop/Cockpit
python3 --version  # must be >= 3.11
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
./launch_cockpit.sh
```

## Daily launch policy (Wave16)

Primary operator launch path:
- Open `/Applications/Centre de controle.app`
- This should be the packaged release app target (single-icon operator path).

Install/update primary target:

```bash
cd /Users/oliviercloutier/Desktop/Cockpit
scripts/packaging/install_release_app.sh
```

Optional engineering path (Dev Live):
- `./launch_cockpit.sh`
- Use this for fast code iteration only, not as the primary operator icon path.

Runtime panel expectations:
- `Mode: RELEASE` -> packaged snapshot mode.
- `Mode: DEV LIVE` -> engineering live mode.

Version checks:
- Window title: `Centre de controle - <branch>@<sha><*dirty>`
- Sidebar footer: version stamp + active data root path.
- Canonical default data root: `~/Library/Application Support/Cockpit/projects`
- Use `COCKPIT_DATA_DIR=repo` only for explicit repo-local sessions.

## Verify installed app target

```bash
plutil -p /Applications/Centre\ de\ controle.app/Contents/Info.plist
# CFBundleExecutable should be "Centre de controle"
```

## Run MCP Server (stdio)

```bash
cd /Users/oliviercloutier/Desktop/Cockpit
source venv/bin/activate
python control/mcp_server.py
```

## Runtime drift recovery (AppSupport canonical)

Strict inbox prune (with archive backup):

```bash
cd /Users/oliviercloutier/Desktop/Cockpit
./.venv/bin/python scripts/auto_mode_inbox_prune.py --project cockpit --data-dir app --agent victor
```

Dry-run first:

```bash
cd /Users/oliviercloutier/Desktop/Cockpit
./.venv/bin/python scripts/auto_mode_inbox_prune.py --project cockpit --data-dir app --agent victor --dry-run
```

Rollback:
- Restore latest file from `~/Library/Application Support/Cockpit/projects/<project>/runs/inbox/archive/`.

## UI layout (fixed)

- Sidebar: Projects + `New Project`
- Top center: Roadmap (timeline + Now/Next/Risks)
- Center: single grid of agents (CDX + AG mixed), each card with phase/percent/eta/status
- Right panel: Chatroom tabs (Global + Threads), composer, `Pack Context` actions

## Local data structure

```text
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
