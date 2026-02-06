#!/usr/bin/env bash
# Cockpit launcher (dev helper).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PY="$SCRIPT_DIR/venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
  echo "ERROR: venv python not found at: $VENV_PY" >&2
  echo "Create it with: python3 -m venv venv && source venv/bin/activate && python -m pip install -r requirements.txt" >&2
  exit 1
fi

exec "$VENV_PY" app/main.py
