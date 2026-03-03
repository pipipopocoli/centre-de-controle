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
  if [[ -n "${UI_PID:-}" ]]; then
    kill "${UI_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT

export COCKPIT_CONTROL_ROOT="${COCKPIT_CONTROL_ROOT:-$ROOT/control/projects}"
export COCKPIT_NEXT_PORT="${COCKPIT_NEXT_PORT:-8787}"
export VITE_COCKPIT_CORE_URL="${VITE_COCKPIT_CORE_URL:-http://127.0.0.1:${COCKPIT_NEXT_PORT}}"

PORT_PID="$(lsof -tiTCP:${COCKPIT_NEXT_PORT} -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
if [[ -n "${PORT_PID}" ]]; then
  PORT_CMD="$(ps -p "${PORT_PID}" -o command= 2>/dev/null || true)"
  if [[ "${PORT_CMD}" == *"cockpit-core"* ]]; then
    echo "[cockpit-next] backend already running on :${COCKPIT_NEXT_PORT} (pid ${PORT_PID}), reusing it"
  else
    echo "[cockpit-next] error: port ${COCKPIT_NEXT_PORT} already in use by pid ${PORT_PID}" >&2
    echo "[cockpit-next] command: ${PORT_CMD}" >&2
    echo "[cockpit-next] free it or set COCKPIT_NEXT_PORT to another value" >&2
    exit 1
  fi
else
  echo "[cockpit-next] starting backend on ${VITE_COCKPIT_CORE_URL}"
  (
    cd "$ROOT/crates/cockpit-core"
    cargo run
  ) &
  API_PID=$!
fi

sleep 2

echo "[cockpit-next] starting frontend vite"
(
  cd "$ROOT/apps/cockpit-next-desktop"
  npm run dev -- --host 127.0.0.1 --port 5173
) &
UI_PID=$!

while true; do
  if [[ -n "${API_PID:-}" ]] && ! kill -0 "$API_PID" >/dev/null 2>&1; then
    break
  fi
  if [[ -n "${UI_PID:-}" ]] && ! kill -0 "$UI_PID" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
