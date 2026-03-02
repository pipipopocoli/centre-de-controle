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
    return str(response.json()["access_token"])


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        settings = APISettings(
            projects_root=Path(tmp) / "projects",
            secret_key="ws-secret",
            issuer="ws-issuer",
            access_ttl_seconds=3600,
            refresh_ttl_seconds=7200,
        )
        app = create_app(settings)
        client = TestClient(app)
        owner = _login(client, "owner", "owner123!")

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

    print("OK: cloud api websocket events verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
