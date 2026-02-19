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
VENV_BIN="$(dirname "$VENV_PY")"
export PATH="$VENV_BIN:$PATH"

BRANCH="$(git -C "$ROOT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"
SHA="$(git -C "$ROOT_DIR" rev-parse --short HEAD 2>/dev/null || echo "unknown")"
DIRTY_FLAG=""
if [[ -n "$(git -C "$ROOT_DIR" status --porcelain --untracked-files=no 2>/dev/null)" ]]; then
  DIRTY_FLAG="*"
fi

VERSION_FILE="$ROOT_DIR/build/version.json"
mkdir -p "$(dirname "$VERSION_FILE")"
THEME_FILE="$ROOT_DIR/app/ui/theme.qss"

"$VENV_PY" - <<PY
import json
from pathlib import Path

payload = {
    "branch": "$BRANCH",
    "sha": "$SHA",
    "dirty": "$DIRTY_FLAG",
    "stamp": "$BRANCH@$SHA$DIRTY_FLAG",
}
target = Path("$VERSION_FILE")
target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(f"Wrote version stamp: {target}")
PY

pyinstaller \
  --specpath build \
  --noconfirm \
  --windowed \
  --name "${APP_NAME}" \
  --add-data "$THEME_FILE:app/ui" \
  --add-data "$VERSION_FILE:app" \
  --collect-submodules PySide6 \
  app/main.py

echo "Built: dist/${APP_NAME}.app"
