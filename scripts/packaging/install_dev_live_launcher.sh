#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_DIR="${1:-$HOME/Applications}"
APP_NAME="Cockpit - Dev Live.app"
APP_PATH="$TARGET_DIR/$APP_NAME"
CMD_PATH="$TARGET_DIR/Cockpit - Dev Live.command"
LOG_PATH="/tmp/cockpit_dev_live.log"

mkdir -p "$TARGET_DIR"

echo "Installing Dev Live launcher into: $TARGET_DIR"

if command -v osacompile >/dev/null 2>&1; then
  TMP_SCRIPT="$(mktemp)"
  ROOT_ESCAPED="${ROOT_DIR//\"/\\\"}"
  cat >"$TMP_SCRIPT" <<OSA
on run
  set projectDir to "$ROOT_ESCAPED"
  do shell script "cd " & quoted form of projectDir & " && ./launch_cockpit.sh >>$LOG_PATH 2>&1 &"
end run
OSA

  rm -rf "$APP_PATH"
  osacompile -o "$APP_PATH" "$TMP_SCRIPT"
  rm -f "$TMP_SCRIPT"

  echo "OK: created app launcher: $APP_PATH"
  echo "Tip: drag this app to Dock and remove old legacy icons."
else
  cat >"$CMD_PATH" <<EOF
#!/usr/bin/env bash
cd "$ROOT_DIR"
exec ./launch_cockpit.sh
EOF
  chmod +x "$CMD_PATH"
  echo "WARNING: osacompile not available, fallback command launcher created:"
  echo "  $CMD_PATH"
fi
