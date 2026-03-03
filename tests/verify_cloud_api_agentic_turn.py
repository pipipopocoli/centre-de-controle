from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from starlette.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from server.config import APISettings  # noqa: E402
from server.llm.agentic_orchestrator import AgenticTurnResult  # noqa: E402
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
            secret_key="agentic-secret",
            issuer="agentic-issuer",
            access_ttl_seconds=3600,
            refresh_ttl_seconds=7200,
            openrouter_api_key="test-openrouter-key",
        )
        app = create_app(settings)
        client = TestClient(app)
        owner = _login(client, "owner", "owner123!")
        headers = _auth_headers(owner)

        create = client.post("/v1/projects", headers=headers, json={"project_id": "cockpit", "name": "Cockpit"})
        assert create.status_code == 201

        fake = AgenticTurnResult(
            status="ok",
            mode="chat",
            messages=[
                {"author": "victor", "text": "backend"},
                {"author": "leo", "text": "ui"},
                {"author": "nova", "text": "research owner=nova next_action=... evidence_path=... decision_tag=adopt"},
                {"author": "vulgarisation", "text": "simple"},
                {"author": "clems", "text": "summary"},
            ],
            clems_summary="summary",
            spawned_agents_count=0,
            model_usage={"calls": []},
            error=None,
        )

        with patch("server.main.run_agentic_turn", return_value=fake):
            response = client.post(
                "/v1/projects/cockpit/chat/agentic-turn",
                headers=headers,
                json={"text": "launch", "mode": "chat"},
            )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["status"] == "ok", payload
        assert payload["run_id"].startswith("AGENTIC_TURN_"), payload
        assert len(payload["messages"]) >= 2, payload

        runs = client.get("/v1/projects/cockpit/runs", headers=headers)
        assert runs.status_code == 200
        assert any(str(item.get("run_id", "")).startswith("AGENTIC_TURN_") for item in runs.json()), runs.json()

    print("OK: cloud api agentic-turn route verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

