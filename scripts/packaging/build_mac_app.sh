#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_NAME="Centre de controle"
# Avoid writing to ~/Library/Application Support in sandboxed environments.
export PYINSTALLER_CONFIG_DIR="${PYINSTALLER_CONFIG_DIR:-$ROOT_DIR/build/pyinstaller-cache}"

pyinstaller \
  --noconfirm \
  --windowed \
  --name "${APP_NAME}" \
  --add-data "app/ui/theme.qss:app/ui" \
  app/main.py

echo "Built: dist/${APP_NAME}.app"
