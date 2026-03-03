#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="$ROOT/apps/cockpit-next-desktop/public/local-assets/pixel-reference"
DEST_CHAR_DIR="$DEST_DIR/characters"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

SOURCE_REPO="${1:-https://github.com/pablodelucca/pixel-agents.git}"
SOURCE_DIR="$TMP_DIR/pixel-agents"

echo "[pixel-reference-import] cloning source: $SOURCE_REPO"
git clone --depth 1 "$SOURCE_REPO" "$SOURCE_DIR" >/dev/null

mkdir -p "$DEST_CHAR_DIR"

for idx in 0 1 2 3 4 5; do
  SRC="$SOURCE_DIR/webview-ui/public/assets/characters/char_${idx}.png"
  if [[ ! -f "$SRC" ]]; then
    echo "[pixel-reference-import] missing source file: $SRC" >&2
    exit 1
  fi
  cp "$SRC" "$DEST_CHAR_DIR/char_${idx}.png"
done

WALL_SRC="$SOURCE_DIR/webview-ui/public/assets/walls.png"
if [[ ! -f "$WALL_SRC" ]]; then
  echo "[pixel-reference-import] missing source file: $WALL_SRC" >&2
  exit 1
fi
cp "$WALL_SRC" "$DEST_DIR/walls.png"

echo "[pixel-reference-import] imported assets to: $DEST_DIR"
echo "[pixel-reference-import] files:"
find "$DEST_DIR" -maxdepth 2 -type f | sort
