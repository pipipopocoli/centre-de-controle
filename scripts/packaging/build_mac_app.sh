#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_NAME="Centre de controle"
ICON_PIPELINE="$ROOT_DIR/scripts/packaging/build_iconset.sh"
ICON_SOURCE="$ROOT_DIR/docs/images/centre-de-controle.png"
ICON_FILE="$ROOT_DIR/assets/Cockpit.icns"
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

ICON_ARGS=()
if [[ -x "$ICON_PIPELINE" ]]; then
  if "$ICON_PIPELINE" "$ICON_SOURCE" "$ICON_FILE"; then
    if [[ -f "$ICON_FILE" ]]; then
      ICON_ARGS=(--icon "$ICON_FILE")
      echo "Using app icon: $ICON_FILE"
    fi
  elif [[ -f "$ICON_FILE" ]]; then
    echo "WARNING: icon pipeline failed, reusing existing icon: $ICON_FILE"
    ICON_ARGS=(--icon "$ICON_FILE")
  else
    echo "WARNING: icon pipeline failed and no icon file exists. Continuing without custom icon."
  fi
else
  echo "WARNING: icon pipeline script missing at $ICON_PIPELINE. Continuing without custom icon."
fi

pyinstaller \
  --noconfirm \
  --windowed \
  --name "${APP_NAME}" \
  "${ICON_ARGS[@]}" \
  --add-data "app/ui/theme.qss:app/ui" \
  --add-data "build/version.json:app" \
  --collect-submodules PySide6 \
  app/main.py

echo "Built: dist/${APP_NAME}.app"
