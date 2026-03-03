#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZIP_PATH="${1:-}"

if [[ -z "$ZIP_PATH" ]]; then
  echo "Usage: ./scripts/import_office_tileset.sh \"/absolute/path/Office Tileset (Donarg).zip\"" >&2
  exit 1
fi

if [[ ! -f "$ZIP_PATH" ]]; then
  echo "[donarg-import] zip not found: $ZIP_PATH" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
DEST_DIR="$ROOT/apps/cockpit-next-desktop/public/local-assets/donarg"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

unzip -o -q "$ZIP_PATH" \
  "Office Tileset/Office Tileset All 16x16 no shadow.png" \
  "Office Tileset/Office Tileset All 16x16.png" \
  "Office Tileset/Office VX Ace/A2 Office Floors.png" \
  "Office Tileset/Office VX Ace/A4 Office Walls.png" \
  "Office Tileset/Office VX Ace/A5 Office Floors & Walls.png" \
  "Office Tileset/Office VX Ace/B-C-D-E Office 1 No Shadows.png" \
  "Office Tileset/Office VX Ace/B-C-D-E Office 2 No Shadows.png" \
  "Office Tileset/Office Designs/Office Level 3.png" \
  "Office Tileset/Office Designs/Office Level 4.png" \
  -d "$TMP_DIR"

mkdir -p "$DEST_DIR"

cp "$TMP_DIR/Office Tileset/Office Tileset All 16x16 no shadow.png" "$DEST_DIR/Office Tileset All 16x16 no shadow.png"
cp "$TMP_DIR/Office Tileset/Office Tileset All 16x16.png" "$DEST_DIR/Office Tileset All 16x16.png"
cp "$TMP_DIR/Office Tileset/Office VX Ace/A2 Office Floors.png" "$DEST_DIR/A2 Office Floors.png"
cp "$TMP_DIR/Office Tileset/Office VX Ace/A4 Office Walls.png" "$DEST_DIR/A4 Office Walls.png"
cp "$TMP_DIR/Office Tileset/Office VX Ace/A5 Office Floors & Walls.png" "$DEST_DIR/A5 Office Floors & Walls.png"
cp "$TMP_DIR/Office Tileset/Office VX Ace/B-C-D-E Office 1 No Shadows.png" "$DEST_DIR/B-C-D-E Office 1 No Shadows.png"
cp "$TMP_DIR/Office Tileset/Office VX Ace/B-C-D-E Office 2 No Shadows.png" "$DEST_DIR/B-C-D-E Office 2 No Shadows.png"
cp "$TMP_DIR/Office Tileset/Office Designs/Office Level 3.png" "$DEST_DIR/Office Level 3.png"
cp "$TMP_DIR/Office Tileset/Office Designs/Office Level 4.png" "$DEST_DIR/Office Level 4.png"

echo "[donarg-import] assets imported to: $DEST_DIR"
echo "[donarg-import] files:"
ls -1 "$DEST_DIR"

if command -v python3 >/dev/null 2>&1; then
  echo "[donarg-import] generating furniture catalog"
  python3 "$ROOT/scripts/build_donarg_catalog.py"
fi
