from __future__ import annotations

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from starlette.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from server.config import APISettings  # noqa: E402
from server.llm.agentic_orchestrator import AgenticTurnResult  # noqa: E402
from server.main import create_app  # noqa: E402


TEST_OWNER_PASSWORD = "test-owner-pass"


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        settings = APISettings(
            projects_root=Path(tmp) / "projects",
            secret_key="ws-secret",
            issuer="ws-issuer",
            access_ttl_seconds=3600,
            refresh_ttl_seconds=7200,
            openrouter_api_key="test-openrouter-key",
        )
        os.environ["COCKPIT_API_BOOTSTRAP_OWNER_PASSWORD"] = TEST_OWNER_PASSWORD
        app = create_app(settings)
        client = TestClient(app)
        owner = _login(client, "owner", TEST_OWNER_PASSWORD)

        create = client.post(
            "/v1/projects",
            headers=_auth_headers(owner),
            json={"project_id": "ws-demo", "name": "WebSocket Demo"},
        )
        assert create.status_code == 201

        with client.websocket_connect(f"/v1/projects/ws-demo/events?token={owner}") as websocket:
            first = websocket.receive_json()
            assert first["type"] == "connection.ready"

            chat = client.post(
                "/v1/projects/ws-demo/chat/messages",
                headers=_auth_headers(owner),
                json={"text": "hello ws"},
            )
            assert chat.status_code == 201

            event = websocket.receive_json()
            assert event["type"] == "chat.message.created"
            assert event["project_id"] == "ws-demo"
            assert event["version"] == "v1"

            fake = AgenticTurnResult(
                status="ok",
                mode="scene",
                messages=[
                    {"author": "scene", "text": "scene"},
                    {"author": "victor", "text": "backend"},
                    {"author": "leo", "text": "ui"},
                    {"author": "nova", "text": "research owner=nova next_action=... evidence_path=... decision_tag=adopt"},
                    {"author": "vulgarisation", "text": "simple"},
                    {"author": "clems", "text": "summary"},
                ],
                clems_summary="summary",
                spawned_agents_count=2,
                model_usage={"calls": []},
                error=None,
            )
            with patch("server.main.run_agentic_turn", return_value=fake):
                turn = client.post(
                    "/v1/projects/ws-demo/chat/agentic-turn",
                    headers=_auth_headers(owner),
                    json={"text": "scene run", "mode": "scene"},
                )
            assert turn.status_code == 200, turn.text

            received_types: set[str] = set()
            for _ in range(3):
                event = websocket.receive_json()
                received_types.add(str(event.get("type")))
            assert "agentic.turn.started" in received_types
            assert "scene.spawned" in received_types
            assert "pixel.updated" in received_types

    print("OK: cloud api websocket events verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
