#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUNDLE_ROOT="$ROOT/apps/cockpit-desktop/src-tauri/target/release/bundle"
INSTALL_DIR="${1:-/Applications}"
CORE_BIN="$ROOT/crates/cockpit-core/target/release/cockpit-core"

if [[ ! -d "$BUNDLE_ROOT" ]]; then
  echo "[cockpit] bundle folder not found: $BUNDLE_ROOT" >&2
  echo "[cockpit] build first: cd apps/cockpit-desktop && npm run tauri:build" >&2
  exit 1
fi

APP_PATH="$(find "$BUNDLE_ROOT" -maxdepth 4 -type d -name 'Cockpit.app' | head -n 1 || true)"
if [[ -z "$APP_PATH" ]]; then
  echo "[cockpit] Cockpit.app not found under $BUNDLE_ROOT" >&2
  echo "[cockpit] build first: cd apps/cockpit-desktop && npm run tauri:build" >&2
  exit 1
fi

mkdir -p "$INSTALL_DIR"
APP_NAME="$(basename "$APP_PATH")"
DEST_PATH="$INSTALL_DIR/$APP_NAME"

if [[ -d "$DEST_PATH" ]]; then
  rm -rf "$DEST_PATH"
fi

cp -R "$APP_PATH" "$DEST_PATH"

echo "[cockpit] building cockpit-core release binary"
(cd "$ROOT/crates/cockpit-core" && cargo build --release)

cp "$CORE_BIN" "$DEST_PATH/Contents/MacOS/cockpit-core"
chmod +x "$DEST_PATH/Contents/MacOS/cockpit-core"

echo "[cockpit] installed: $DEST_PATH"
echo "[cockpit] source:    $APP_PATH"
echo "[cockpit] backend:   $DEST_PATH/Contents/MacOS/cockpit-core"
echo "[cockpit] launch:    open \"$DEST_PATH\""
