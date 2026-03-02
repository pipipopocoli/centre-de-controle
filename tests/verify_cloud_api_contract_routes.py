from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from starlette.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from server.config import APISettings  # noqa: E402
from server.main import create_app  # noqa: E402


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    payload = response.json()
    return str(payload["access_token"])


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        settings = APISettings(
            projects_root=projects_root,
            secret_key="test-secret",
            issuer="test-issuer",
            access_ttl_seconds=3600,
            refresh_ttl_seconds=7200,
        )
        app = create_app(settings)
        client = TestClient(app)

        owner_token = _login(client, "owner", "owner123!")
        headers = _auth_headers(owner_token)

        create_response = client.post(
            "/v1/projects",
            headers=headers,
            json={"project_id": "cockpit", "name": "Cockpit API"},
        )
        assert create_response.status_code == 201

        assert client.get("/v1/projects", headers=headers).status_code == 200
        assert client.get("/v1/projects/cockpit", headers=headers).status_code == 200
        assert client.get("/v1/projects/cockpit/state", headers=headers).status_code == 200
        assert client.put(
            "/v1/projects/cockpit/state",
            headers=headers,
            json={
                "phase": "Plan",
                "objective": "Contract test",
                "now": ["route check"],
                "next": ["rbac check"],
                "in_progress": [],
                "blockers": [],
                "risks": [],
                "links": [],
            },
        ).status_code == 200

        assert client.get("/v1/projects/cockpit/roadmap", headers=headers).status_code == 200
        assert client.put(
            "/v1/projects/cockpit/roadmap",
            headers=headers,
            json={"now": ["now"], "next": ["next"], "risks": ["risk"]},
        ).status_code == 200

        assert client.get("/v1/projects/cockpit/decisions", headers=headers).status_code == 200
        assert client.post(
            "/v1/projects/cockpit/decisions",
            headers=headers,
            json={
                "title": "ADR test",
                "status": "Accepted",
                "context": "Contract test",
                "decision": "Keep API",
                "rationale": "Parity",
                "consequences": ["More complexity"],
                "owners": ["clems"],
                "references": ["docs/CLOUD_API_PROTOCOL.md"],
            },
        ).status_code == 201

        agents_response = client.get("/v1/projects/cockpit/agents", headers=headers)
        assert agents_response.status_code == 200
        agents = agents_response.json()
        assert isinstance(agents, list) and agents
        agent_id = str(agents[0]["agent_id"])
        assert client.patch(
            f"/v1/projects/cockpit/agents/{agent_id}/state",
            headers=headers,
            json={"status": "executing", "current_task": "contract test"},
        ).status_code == 200

        assert client.get("/v1/projects/cockpit/chat", headers=headers).status_code == 200
        assert client.post(
            "/v1/projects/cockpit/chat/messages",
            headers=headers,
            json={"text": "hello api"},
        ).status_code == 201

        assert client.get("/v1/projects/cockpit/runs", headers=headers).status_code == 200
        assert client.get("/v1/projects/cockpit/bmad/brainstorm", headers=headers).status_code == 200
        assert client.put(
            "/v1/projects/cockpit/bmad/brainstorm",
            headers=headers,
            json={"content": "# Brainstorm\n\n- test\n"},
        ).status_code == 200

        assert client.post("/v1/devices/register", headers=headers, json={
            "device_id": "android-01",
            "platform": "android",
            "fcm_token": "token-1",
            "project_ids": ["cockpit"],
        }).status_code == 201
        assert client.delete("/v1/devices/android-01", headers=headers).status_code == 200

    print("OK: cloud api contract routes verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
