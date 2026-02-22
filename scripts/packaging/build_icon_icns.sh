#!/usr/bin/env bash
set -u -o pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_PNG="${1:-$ROOT_DIR/docs/images/centre-de-controle.png}"
ASSETS_DIR="$ROOT_DIR/scripts/packaging/assets"
ICONSET_DIR="$ASSETS_DIR/centre-de-controle.iconset"
OUT_ICNS="${2:-$ASSETS_DIR/centre-de-controle.icns}"
LEGACY_ICNS="$ROOT_DIR/assets/Cockpit.icns"

fallback_icon() {
  if [[ -f "$OUT_ICNS" ]]; then
    echo "$OUT_ICNS"
    return 0
  fi
  if [[ -f "$LEGACY_ICNS" ]]; then
    mkdir -p "$ASSETS_DIR"
    cp "$LEGACY_ICNS" "$OUT_ICNS"
    echo "WARNING: using fallback icon from $LEGACY_ICNS" >&2
    echo "$OUT_ICNS"
    return 0
  fi
  return 1
}

if [[ ! -f "$SOURCE_PNG" ]]; then
  echo "WARNING: icon source not found: $SOURCE_PNG" >&2
  fallback_icon || true
  exit 0
fi
if ! command -v sips >/dev/null 2>&1; then
  echo "WARNING: sips not found. Skipping icon generation." >&2
  fallback_icon || true
  exit 0
fi
if ! command -v iconutil >/dev/null 2>&1; then
  echo "WARNING: iconutil not found. Skipping icon generation." >&2
  fallback_icon || true
  exit 0
fi

rm -rf "$ICONSET_DIR"
mkdir -p "$ICONSET_DIR"
mkdir -p "$ASSETS_DIR"
mkdir -p "$(dirname "$OUT_ICNS")"

if ! sips -z 16 16 "$SOURCE_PNG" --out "$ICONSET_DIR/icon_16x16.png" >/dev/null; then fallback_icon || exit 1; exit 0; fi
if ! sips -z 32 32 "$SOURCE_PNG" --out "$ICONSET_DIR/icon_16x16@2x.png" >/dev/null; then fallback_icon || exit 1; exit 0; fi
if ! sips -z 32 32 "$SOURCE_PNG" --out "$ICONSET_DIR/icon_32x32.png" >/dev/null; then fallback_icon || exit 1; exit 0; fi
if ! sips -z 64 64 "$SOURCE_PNG" --out "$ICONSET_DIR/icon_32x32@2x.png" >/dev/null; then fallback_icon || exit 1; exit 0; fi
if ! sips -z 128 128 "$SOURCE_PNG" --out "$ICONSET_DIR/icon_128x128.png" >/dev/null; then fallback_icon || exit 1; exit 0; fi
if ! sips -z 256 256 "$SOURCE_PNG" --out "$ICONSET_DIR/icon_128x128@2x.png" >/dev/null; then fallback_icon || exit 1; exit 0; fi
if ! sips -z 256 256 "$SOURCE_PNG" --out "$ICONSET_DIR/icon_256x256.png" >/dev/null; then fallback_icon || exit 1; exit 0; fi
if ! sips -z 512 512 "$SOURCE_PNG" --out "$ICONSET_DIR/icon_256x256@2x.png" >/dev/null; then fallback_icon || exit 1; exit 0; fi
if ! sips -z 512 512 "$SOURCE_PNG" --out "$ICONSET_DIR/icon_512x512.png" >/dev/null; then fallback_icon || exit 1; exit 0; fi
if ! sips -z 1024 1024 "$SOURCE_PNG" --out "$ICONSET_DIR/icon_512x512@2x.png" >/dev/null; then fallback_icon || exit 1; exit 0; fi

if ! iconutil -c icns "$ICONSET_DIR" -o "$OUT_ICNS"; then
  echo "WARNING: iconutil conversion failed for $ICONSET_DIR" >&2
  fallback_icon || true
  exit 0
fi

echo "$OUT_ICNS"
