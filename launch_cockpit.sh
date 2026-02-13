#!/usr/bin/env bash
# Cockpit launcher (dev helper).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Prefer the repo-standard venv/, but allow .venv/ as a fallback (common local convention).
VENV_PY="$SCRIPT_DIR/venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
  VENV_PY="$SCRIPT_DIR/.venv/bin/python"
fi
if [[ ! -x "$VENV_PY" ]]; then
  echo "ERROR: python venv not found at: $SCRIPT_DIR/venv/bin/python or $SCRIPT_DIR/.venv/bin/python" >&2
  echo "Create it with: python3 -m venv venv && source venv/bin/activate && python -m pip install -r requirements.txt" >&2
  exit 1
fi

# Canonical runtime default is App Support unless explicitly overridden.
export COCKPIT_DATA_DIR="${COCKPIT_DATA_DIR:-app}"

exec "$VENV_PY" app/main.py
