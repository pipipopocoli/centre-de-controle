#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Centre de controle"

python -m pyinstaller \
  --windowed \
  --name "${APP_NAME}" \
  --add-data "app/ui/theme.qss:app/ui" \
  app/main.py

echo "Built: dist/${APP_NAME}.app"
