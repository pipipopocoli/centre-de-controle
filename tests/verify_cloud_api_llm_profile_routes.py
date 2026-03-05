from __future__ import annotations

import sys
import os
import tempfile
from pathlib import Path

from starlette.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from server.config import APISettings  # noqa: E402
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
            secret_key="profile-secret",
            issuer="profile-issuer",
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

        get_profile = client.get("/v1/projects/cockpit/llm-profile", headers=headers)
        assert get_profile.status_code == 200
        profile = get_profile.json()["profile"]
        assert profile["l1_model"], profile

        updated = client.put(
            "/v1/projects/cockpit/llm-profile",
            headers=headers,
            json={
                "voice_stt_model": "google/gemini-2.5-flash",
                "l1_model": "liquid/lfm-2.5-1.2b-thinking:free",
                "l2_scene_model": "arcee-ai/trinity-large-preview:free",
                "lfm_spawn_max": 4,
                "stream_enabled": False,
            },
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["profile"]["lfm_spawn_max"] == 4
        assert updated.json()["profile"]["stream_enabled"] is False

    print("OK: cloud api llm-profile routes verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

