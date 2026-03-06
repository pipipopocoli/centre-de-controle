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
        assert profile["clems_model"] == "moonshotai/kimi-k2.5", profile
        assert profile["l1_models"]["victor"], profile
        assert profile["l2_default_model"], profile

        updated = client.put(
            "/v1/projects/cockpit/llm-profile",
            headers=headers,
            json={
                "voice_stt_model": "google/gemini-2.5-flash",
                "clems_model": "anthropic/claude-sonnet-4.6",
                "l1_models": {
                    "victor": "openai/gpt-5.4",
                    "leo": "anthropic/claude-opus-4.6",
                    "nova": "google/gemini-3.1-pro-preview",
                    "vulgarisation": "moonshotai/kimi-k2.5",
                },
                "l2_default_model": "moonshotai/kimi-k2.5",
                "l2_pool": [
                    "minimax/minimax-m2.5",
                    "moonshotai/kimi-k2.5",
                    "deepseek/deepseek-chat-v3.1",
                ],
                "lfm_spawn_max": 4,
                "stream_enabled": False,
            },
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["profile"]["lfm_spawn_max"] == 4
        assert updated.json()["profile"]["stream_enabled"] is False
        assert updated.json()["profile"]["l1_models"]["leo"] == "anthropic/claude-opus-4.6"
        assert updated.json()["profile"]["l1_model"] == "openai/gpt-5.4"
        assert updated.json()["profile"]["l2_scene_model"] == "moonshotai/kimi-k2.5"

    print("OK: cloud api llm-profile routes verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
