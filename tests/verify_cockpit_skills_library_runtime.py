from __future__ import annotations

import json
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8787"
PROJECT_ID = "cockpit"


def _request(path: str) -> tuple[int, dict]:
    request = urllib.request.Request(f"{BASE_URL}{path}", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8")
        return error.code, json.loads(raw) if raw else {}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    status, payload = _request(f"/v1/projects/{PROJECT_ID}/skills/library")
    _assert(status == 200, f"skills library returned {status}: {payload}")
    _assert(payload.get("project_id") == PROJECT_ID, f"unexpected project id: {payload}")
    skills = payload.get("skills")
    _assert(isinstance(skills, list), f"skills should be a list: {payload}")

    for skill in skills[:5]:
        _assert(isinstance(skill, dict), f"invalid skill row: {skill}")
        for field in ("skill_id", "name", "description", "source_path", "assigned_agents"):
            _assert(field in skill, f"missing field {field}: {skill}")
        _assert(isinstance(skill["assigned_agents"], list), f"assigned_agents must be a list: {skill}")

    print("OK: cockpit skills library runtime verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
