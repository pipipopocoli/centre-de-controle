#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Canonical ops reference: docs/COCKPIT_NEXT_RUNBOOK.md

if ! command -v cargo >/dev/null 2>&1; then
  if [[ -f "$HOME/.cargo/env" ]]; then
    # shellcheck source=/dev/null
    source "$HOME/.cargo/env"
  fi
fi

if ! command -v cargo >/dev/null 2>&1; then
  echo "[cockpit-next] error: cargo not found. Install Rust or add ~/.cargo/bin to PATH." >&2
  echo "[cockpit-next] quick fix: source \$HOME/.cargo/env" >&2
  exit 1
fi

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then
    kill "${API_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT

export COCKPIT_CONTROL_ROOT="${COCKPIT_CONTROL_ROOT:-$ROOT/control/projects}"
export COCKPIT_NEXT_PORT="${COCKPIT_NEXT_PORT:-8787}"
export VITE_COCKPIT_CORE_URL="${VITE_COCKPIT_CORE_URL:-http://127.0.0.1:${COCKPIT_NEXT_PORT}}"

echo "[cockpit-next] starting backend on ${VITE_COCKPIT_CORE_URL}"
(
  cd "$ROOT/crates/cockpit-core"
  cargo run
) &
API_PID=$!

sleep 2

echo "[cockpit-next] starting tauri desktop"
cd "$ROOT/apps/cockpit-next-desktop"
npm run tauri:dev
