from __future__ import annotations

import base64
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from starlette.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from server.config import APISettings  # noqa: E402
from server.llm.openrouter_client import OpenRouterChatResult, OpenRouterUsage  # noqa: E402
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
            secret_key="voice-secret",
            issuer="voice-issuer",
            access_ttl_seconds=3600,
            refresh_ttl_seconds=7200,
            openrouter_api_key="test-openrouter-key",
        )
        os.environ["COCKPIT_API_BOOTSTRAP_OWNER_PASSWORD"] = TEST_OWNER_PASSWORD
        app = create_app(settings)
        client = TestClient(app)
        owner = _login(client, "owner", TEST_OWNER_PASSWORD)
        headers = _auth_headers(owner)

        create = client.post("/v1/projects", headers=headers, json={"project_id": "cockpit", "name": "Cockpit"})
        assert create.status_code == 201

        fake = OpenRouterChatResult(
            status="ok",
            model="google/gemini-2.5-flash",
            text="bonjour cockpit",
            usage=OpenRouterUsage(input_tokens=4, output_tokens=3, reasoning_tokens=0, raw={}),
            raw={},
            error=None,
        )
        audio_base64 = base64.b64encode(b"RIFF....WAVE").decode("ascii")
        with patch("server.main.OpenRouterClient.transcribe_audio", return_value=fake):
            response = client.post(
                "/v1/projects/cockpit/voice/transcribe",
                headers=headers,
                json={"audio_base64": audio_base64, "format": "wav"},
            )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["status"] == "ok", payload
        assert payload["text"] == "bonjour cockpit", payload
        assert payload["model"] == "google/gemini-2.5-flash", payload

    print("OK: cloud api voice transcribe route verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

