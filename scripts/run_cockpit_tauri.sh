#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Canonical ops reference: docs/COCKPIT_RUNBOOK.md

if ! command -v cargo >/dev/null 2>&1; then
  if [[ -f "$HOME/.cargo/env" ]]; then
    # shellcheck source=/dev/null
    source "$HOME/.cargo/env"
  fi
fi

if ! command -v cargo >/dev/null 2>&1; then
  echo "[cockpit] error: cargo not found. Install Rust or add ~/.cargo/bin to PATH." >&2
  echo "[cockpit] quick fix: source \$HOME/.cargo/env" >&2
  exit 1
fi

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then
    kill "${API_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT

export COCKPIT_CONTROL_ROOT="${COCKPIT_CONTROL_ROOT:-$ROOT/control/projects}"
export COCKPIT_HOST="${COCKPIT_HOST:-127.0.0.1}"
export COCKPIT_PORT="${COCKPIT_PORT:-${COCKPIT_NEXT_PORT:-8787}}"
export COCKPIT_NEXT_PORT="${COCKPIT_NEXT_PORT:-$COCKPIT_PORT}"
export VITE_COCKPIT_CORE_URL="${VITE_COCKPIT_CORE_URL:-http://${COCKPIT_HOST}:${COCKPIT_PORT}}"
PROJECT_ID="${COCKPIT_DEFAULT_PROJECT_ID:-cockpit}"

load_local_env() {
  local candidate
  for candidate in \
    "$ROOT/.env" \
    "$HOME/Library/Application Support/Cockpit/.env" \
    "$HOME/.cockpit/.env"
  do
    if [[ -f "$candidate" ]]; then
      # shellcheck source=/dev/null
      source "$candidate"
      break
    fi
  done

  if [[ -z "${COCKPIT_OPENROUTER_API_KEY:-}" && -n "${OPENROUTER_API_KEY:-}" ]]; then
    export COCKPIT_OPENROUTER_API_KEY="$OPENROUTER_API_KEY"
  fi
}

load_local_env

if [[ -z "${COCKPIT_OPENROUTER_API_KEY:-}" ]]; then
  echo "[cockpit] warning: COCKPIT_OPENROUTER_API_KEY is not set." >&2
  echo "[cockpit] warning: Finder-launched Cockpit.app needs \$HOME/Library/Application Support/Cockpit/.env for agent chat." >&2
fi

wait_for_health() {
  local base_url="$1"
  local tries=40
  local i
  for ((i=1; i<=tries; i++)); do
    if curl -fsS "${base_url}/healthz" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

assert_route_200() {
  local base_url="$1"
  local path="$2"
  local code
  code="$(curl -sS -o /dev/null -w "%{http_code}" "${base_url}${path}" || true)"
  if [[ "$code" != "200" ]]; then
    echo "[cockpit] preflight failed for ${path}: HTTP ${code}" >&2
    return 1
  fi
  return 0
}

preflight_api_contracts() {
  local base_url="$1"
  local project_id="$2"
  if ! wait_for_health "$base_url"; then
    echo "[cockpit] backend did not become healthy on ${base_url}/healthz" >&2
    return 1
  fi
  assert_route_200 "$base_url" "/v1/projects/${project_id}/chat/approvals?status=pending"
  assert_route_200 "$base_url" "/v1/projects/${project_id}/llm-profile"
}

echo "[cockpit] starting backend on ${VITE_COCKPIT_CORE_URL}"
PORT_PID="$(lsof -tiTCP:${COCKPIT_PORT} -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
if [[ -n "${PORT_PID}" ]]; then
  PORT_CMD="$(ps -p "${PORT_PID}" -o command= 2>/dev/null || true)"
  if [[ "${PORT_CMD}" == *"cockpit-core"* ]]; then
    echo "[cockpit] backend already running on :${COCKPIT_PORT} (pid ${PORT_PID}), reusing it"
  else
    echo "[cockpit] error: port ${COCKPIT_PORT} already in use by pid ${PORT_PID}" >&2
    echo "[cockpit] command: ${PORT_CMD}" >&2
    echo "[cockpit] free it or set COCKPIT_PORT to another value" >&2
    exit 1
  fi
else
  echo "[cockpit] starting backend on ${VITE_COCKPIT_CORE_URL}"
  (
    cd "$ROOT/crates/cockpit-core"
    cargo run
  ) &
  API_PID=$!
fi

echo "[cockpit] preflight checks: approvals + llm-profile"
preflight_api_contracts "$VITE_COCKPIT_CORE_URL" "$PROJECT_ID"

echo "[cockpit] starting tauri desktop"
cd "$ROOT/apps/cockpit-desktop"
npm run tauri:dev
