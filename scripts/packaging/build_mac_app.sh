#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_NAME="Centre de controle"
# Avoid writing to ~/Library/Application Support in sandboxed environments.
export PYINSTALLER_CONFIG_DIR="${PYINSTALLER_CONFIG_DIR:-$ROOT_DIR/build/pyinstaller-cache}"

VENV_PY="$ROOT_DIR/venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
  VENV_PY="$ROOT_DIR/.venv/bin/python"
fi
if [[ ! -x "$VENV_PY" ]]; then
  echo "ERROR: python venv not found at: $ROOT_DIR/venv/bin/python or $ROOT_DIR/.venv/bin/python" >&2
  exit 1
fi

BRANCH="$(git -C "$ROOT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"
SHA="$(git -C "$ROOT_DIR" rev-parse --short HEAD 2>/dev/null || echo "unknown")"
DIRTY="false"
if [[ -n "$(git -C "$ROOT_DIR" status --porcelain 2>/dev/null)" ]]; then
  DIRTY="true"
fi

"$VENV_PY" - <<PY
import json
from pathlib import Path

root = Path("$ROOT_DIR")
payload = {
    "branch": "$BRANCH",
    "sha": "$SHA",
    "dirty": "$DIRTY" == "true",
}
target = root / "app" / "version.json"
target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(f"Wrote version stamp: {target}")
PY

pyinstaller \
  --noconfirm \
  --windowed \
  --name "${APP_NAME}" \
  --add-data "app/ui/theme.qss:app/ui" \
  --add-data "app/version.json:app" \
  app/main.py

echo "Built: dist/${APP_NAME}.app"
