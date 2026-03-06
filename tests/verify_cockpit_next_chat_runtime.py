from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8787"
PROJECT_ID = "cockpit"
LEGACY_AGENT_IDS = {"codex", "antigravity", "ollama"}
HTTP_TIMEOUT_SECONDS = 90


def _request(path: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["content-type"] = "application/json"

    request = urllib.request.Request(f"{BASE_URL}{path}", data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8")
        payload = json.loads(raw) if raw else {}
        return error.code, payload


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _verify_websocket_ready() -> None:
    script = f"""
const ws = new WebSocket('ws://127.0.0.1:8787/v1/projects/{PROJECT_ID}/events');
ws.onopen = () => {{}};
ws.onmessage = (event) => {{
  console.log(event.data);
  process.exit(0);
}};
ws.onerror = (error) => {{
  console.error(String(error));
  process.exit(2);
}};
setTimeout(() => {{
  console.error('timeout');
  process.exit(3);
}}, 3000);
"""
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    _assert(result.returncode == 0, f"websocket check failed: {result.stderr.strip() or result.stdout.strip()}")
    message = json.loads(result.stdout.strip())
    _assert(message.get("type") == "connection.ready", f"unexpected ws first event: {message}")


def main() -> int:
    status, health = _request("/healthz")
    _assert(status == 200, f"/healthz returned {status}")
    _assert(health.get("status") == "ok", f"unexpected health payload: {health}")

    status, task_state_before = _request(f"/v1/projects/{PROJECT_ID}/tasks")
    _assert(status == 200, f"tasks before live-turn returned {status}: {task_state_before}")
    before_ids = {
        str(item.get("task_id") or "")
        for item in (task_state_before.get("tasks") or [])
        if isinstance(item, dict)
    }

    try:
        status, response = _request(
            f"/v1/projects/{PROJECT_ID}/chat/live-turn",
            method="POST",
            payload={
                "text": "@leo runtime smoke. Reply in one short sentence only. Do not create tasks.",
                "chat_mode": "direct",
                "execution_mode": "chat",
                "target_agent_id": "leo",
            },
        )
        _assert(status == 200, f"live-turn returned {status}: {response}")
        messages = response.get("messages") or []
        authors = [str(item.get("author") or "") for item in messages if isinstance(item, dict)]
        if "leo" not in authors and response.get("error"):
            raise AssertionError(
                f"live-turn did not reach leo. backend reported: {response.get('error')}. "
                "If Cockpit.app was launched from Finder, verify ~/Library/Application Support/Cockpit/.env."
            )
        _assert("leo" in authors, f"direct target response missing leo: {authors}")
        _assert(response.get("status") in {"completed", "degraded"}, f"unexpected live-turn status: {response}")
    finally:
        status, task_state_after = _request(f"/v1/projects/{PROJECT_ID}/tasks")
        if status == 200:
            for item in task_state_after.get("tasks") or []:
                if not isinstance(item, dict):
                    continue
                task_id = str(item.get("task_id") or "")
                task_path = str(item.get("path") or "")
                if task_id and task_id not in before_ids and task_path:
                    Path(task_path).unlink(missing_ok=True)

    status, feed = _request(f"/v1/projects/{PROJECT_ID}/pixel-feed")
    _assert(status == 200, f"pixel-feed returned {status}: {feed}")
    agents = feed.get("agents") or []
    _assert(isinstance(agents, list), f"invalid pixel-feed agents: {feed}")
    returned_ids = {str(item.get("agent_id") or "") for item in agents if isinstance(item, dict)}
    _assert(returned_ids.isdisjoint(LEGACY_AGENT_IDS), f"legacy ghost agents still visible: {sorted(returned_ids & LEGACY_AGENT_IDS)}")
    leo_row = next((item for item in agents if isinstance(item, dict) and item.get("agent_id") == "leo"), None)
    _assert(isinstance(leo_row, dict), "leo missing from pixel-feed")
    _assert(isinstance(leo_row.get("chat_targetable"), bool), f"chat_targetable missing on leo row: {leo_row}")
    _assert(bool(leo_row.get("chat_targetable")) is True, f"leo should be chat_targetable: {leo_row}")

    _verify_websocket_ready()
    print("OK: cockpit next chat runtime verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
