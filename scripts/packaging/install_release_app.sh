#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEFAULT_SOURCE="$ROOT_DIR/dist/Centre de controle.app"
SOURCE="$DEFAULT_SOURCE"
TARGET="/Applications/Centre de controle.app"
KEEP_DEV_LIVE="true"

usage() {
  cat <<USAGE
Usage:
  scripts/packaging/install_release_app.sh [--source <app_path>] [--target <app_path>] [--keep-dev-live true|false]

Defaults:
  --source "$DEFAULT_SOURCE"
  --target "/Applications/Centre de controle.app"
  --keep-dev-live true
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      SOURCE="$2"
      shift 2
      ;;
    --target)
      TARGET="$2"
      shift 2
      ;;
    --keep-dev-live)
      KEEP_DEV_LIVE="${2,,}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "$KEEP_DEV_LIVE" != "true" && "$KEEP_DEV_LIVE" != "false" ]]; then
  echo "ERROR: --keep-dev-live must be true or false" >&2
  exit 1
fi

SOURCE="${SOURCE/#\~/$HOME}"
TARGET="${TARGET/#\~/$HOME}"

if [[ ! -d "$SOURCE" ]]; then
  echo "ERROR: source app not found: $SOURCE" >&2
  echo "Build it first with: scripts/packaging/build_mac_app.sh" >&2
  exit 1
fi

if [[ ! -f "$SOURCE/Contents/Info.plist" ]]; then
  echo "ERROR: source path is not a valid macOS app bundle: $SOURCE" >&2
  exit 1
fi

TARGET_DIR="$(dirname "$TARGET")"
mkdir -p "$TARGET_DIR"

timestamp="$(date +%Y%m%d_%H%M%S)"
backup_path="${TARGET}.bak.${timestamp}"

target_executable=""
if [[ -f "$TARGET/Contents/Info.plist" ]]; then
  target_executable="$(plutil -extract CFBundleExecutable raw -o - "$TARGET/Contents/Info.plist" 2>/dev/null || true)"
fi

if [[ -e "$TARGET" ]]; then
  echo "Backing up existing target to: $backup_path"
  mv "$TARGET" "$backup_path"

  if [[ "$target_executable" == "applet" && "$KEEP_DEV_LIVE" == "true" ]]; then
    dev_live_target="${TARGET_DIR}/Centre de controle - Dev Live.app"
    if [[ -e "$dev_live_target" ]]; then
      archived_dev_live="${dev_live_target%.app}.bak.${timestamp}.app"
      echo "Archiving existing Dev Live launcher to: $archived_dev_live"
      mv "$dev_live_target" "$archived_dev_live"
    fi
    echo "Preserving backup copy as optional Dev Live launcher: $dev_live_target"
    ditto "$backup_path" "$dev_live_target"
  fi
fi

echo "Installing release app from: $SOURCE"
mkdir -p "$TARGET_DIR"
ditto "$SOURCE" "$TARGET"

installed_exec="$(plutil -extract CFBundleExecutable raw -o - "$TARGET/Contents/Info.plist" 2>/dev/null || true)"

echo ""
echo "Install complete"
echo "- target: $TARGET"
echo "- CFBundleExecutable: ${installed_exec:-unknown}"
echo ""
echo "Post-install verification"
echo "  plutil -p '$TARGET/Contents/Info.plist'"
echo "  open -a '$TARGET'"
echo ""
if [[ -n "$target_executable" ]]; then
  echo "Previous target executable: $target_executable"
fi
if [[ -e "$backup_path" ]]; then
  echo "Backup path: $backup_path"
fi
