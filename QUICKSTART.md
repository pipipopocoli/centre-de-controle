# Cockpit Quickstart

Date reference: 2026-03-03.

## Product launch (Cockpit default)

Use these commands for the actual app runtime:

```bash
./scripts/run_cockpit.sh
./scripts/run_cockpit_tauri.sh
open "/Applications/Cockpit.app"
```

`./launch_cockpit.sh` points to Cockpit by default.

### Local env for agent chat

If you launch the installed app from Finder, add your OpenRouter key to:

```bash
mkdir -p "$HOME/Library/Application Support/Cockpit"
cat > "$HOME/Library/Application Support/Cockpit/.env" <<'EOF'
COCKPIT_OPENROUTER_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
EOF
```

This keeps the key outside git and lets `Cockpit.app` start chat-capable agents without needing a terminal export.

## MCP quickstart (integration only)

This section is only for MCP integration with external agents, not for launching the product UI.

### 1. Verify Python version

```bash
python3 --version
```

Target: Python >= 3.11.

### 2. Create virtual environment

```bash
cd /Users/oliviercloutier/Desktop/Cockpit
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Setup doctor

```bash
python scripts/setup_doctor.py
```

Expected: `PySide6: OK` and `mcp: OK`.

### 5. MCP basic test

```bash
python tests/verify_mcp_basic.py
```

Expected: all checks pass.

### 6. Configure MCP client

```json
{
  "mcpServers": {
    "cockpit": {
      "command": "/Users/oliviercloutier/Desktop/Cockpit/venv/bin/python",
      "args": ["/Users/oliviercloutier/Desktop/Cockpit/control/mcp_server.py"],
      "env": {
        "COCKPIT_PROJECT_ID": "cockpit"
      }
    }
  }
}
```

### 7. Historical note

The old Python/Qt runtime is archived and should not be used for normal Cockpit work.
