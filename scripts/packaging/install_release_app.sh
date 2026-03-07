#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_DIR="/Applications"

usage() {
  cat <<USAGE
Usage:
  scripts/packaging/install_release_app.sh [--target-dir <dir>]

Defaults:
  --target-dir /Applications

Notes:
  - Canonical product app is Cockpit.app.
  - This wrapper delegates to scripts/install_cockpit_app.sh.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-dir)
      TARGET_DIR="$2"
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

"$ROOT_DIR/scripts/install_cockpit_app.sh" "$TARGET_DIR"
