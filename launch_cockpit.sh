#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-dev}"

case "$MODE" in
  dev)
    exec "$ROOT/scripts/run_cockpit.sh"
    ;;
  tauri)
    exec "$ROOT/scripts/run_cockpit_tauri.sh"
    ;;
  *)
    echo "Usage: ./launch_cockpit.sh [dev|tauri]" >&2
    exit 1
    ;;
esac
