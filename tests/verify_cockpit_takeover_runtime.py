from __future__ import annotations

import json
from pathlib import Path
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8787"
PROJECT_ID = "cockpit"
REPO_ROOT = Path(__file__).resolve().parents[1]


def _request(path: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["content-type"] = "application/json"

    request = urllib.request.Request(f"{BASE_URL}{path}", data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8")
        payload = json.loads(raw) if raw else {}
        return error.code, payload


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    status, updated = _request(
        f"/v1/projects/{PROJECT_ID}/settings",
        method="PUT",
        payload={"linked_repo_path": str(REPO_ROOT)},
    )
    _assert(status == 200, f"settings update returned {status}: {updated}")

    status, takeover = _request(
        f"/v1/projects/{PROJECT_ID}/takeover/start",
        method="POST",
        payload={"linked_repo_path": str(REPO_ROOT)},
    )
    _assert(status == 200, f"takeover returned {status}: {takeover}")
    _assert(takeover.get("project_id") == PROJECT_ID, f"unexpected takeover payload: {takeover}")
    _assert(isinstance(takeover.get("summary_human"), str), f"missing summary_human: {takeover}")
    _assert(isinstance(takeover.get("summary_tech"), list), f"missing summary_tech: {takeover}")
    _assert(isinstance(takeover.get("roadmap_sections"), dict), f"missing roadmap_sections: {takeover}")
    _assert(isinstance(takeover.get("suggested_tasks"), list), f"missing suggested_tasks: {takeover}")
    _assert(isinstance(takeover.get("suggested_skills"), list), f"missing suggested_skills: {takeover}")
    _assert(isinstance(takeover.get("repo_findings"), dict), f"missing repo_findings: {takeover}")

    print("OK: cockpit takeover runtime verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
