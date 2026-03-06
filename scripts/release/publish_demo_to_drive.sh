#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

APP_PATH=""
DRIVE_ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app)
      APP_PATH="$2"
      shift 2
      ;;
    --drive-root)
      DRIVE_ROOT="$2"
      shift 2
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$APP_PATH" || -z "$DRIVE_ROOT" ]]; then
  echo "Usage: $0 --app \"/path/Cockpit.app\" --drive-root \"/path/Google Drive/.../Cockpit/releases\"" >&2
  exit 1
fi

if [[ ! -d "$APP_PATH" ]]; then
  echo "App bundle not found: $APP_PATH" >&2
  exit 1
fi

mkdir -p "$DRIVE_ROOT"

BRANCH="$(git -C "$ROOT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"
SHA="$(git -C "$ROOT_DIR" rev-parse --short HEAD 2>/dev/null || echo "unknown")"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
VERSION_DIR="$DRIVE_ROOT/v3.6.1_${TIMESTAMP}_${SHA}"
mkdir -p "$VERSION_DIR"

APP_NAME="$(basename "$APP_PATH")"
APP_COPY="$VERSION_DIR/$APP_NAME"
ZIP_NAME="${APP_NAME%.app}.zip"
ZIP_PATH="$VERSION_DIR/$ZIP_NAME"
MANIFEST="$VERSION_DIR/release_manifest.txt"

ditto "$APP_PATH" "$APP_COPY"
ditto -c -k --sequesterRsrc --keepParent "$APP_COPY" "$ZIP_PATH"

cat > "$MANIFEST" <<EOF
version=v3.6.1
timestamp=$TIMESTAMP
branch=$BRANCH
commit=$SHA
source_app=$APP_PATH
copied_app=$APP_COPY
zip_path=$ZIP_PATH
host=$(hostname)
EOF

echo "Published release:"
echo "  $VERSION_DIR"
echo "Artifacts:"
echo "  - $APP_COPY"
echo "  - $ZIP_PATH"
echo "  - $MANIFEST"
