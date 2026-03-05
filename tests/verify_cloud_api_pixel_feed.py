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
            secret_key="pixel-secret",
            issuer="pixel-issuer",
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

        fake_payload = {
            "project_id": "cockpit",
            "window": "24h",
            "bucket_minutes": 60,
            "generated_at_utc": "2026-03-03T00:00:00+00:00",
            "rows": [
                {
                    "agent_id": "victor",
                    "cells": [{"bucket_start": "2026-03-03T00:00:00+00:00", "intensity": 2, "chat_messages": 1, "run_events": 1, "state_updates": 0}],
                }
            ],
        }
        with patch("server.main.build_pixel_feed", return_value=fake_payload):
            response = client.get("/v1/projects/cockpit/pixel-feed?window=24h", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["window"] == "24h"
        assert payload["rows"][0]["agent_id"] == "victor"

    print("OK: cloud api pixel-feed route verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

