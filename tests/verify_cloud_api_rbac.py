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
TEST_LEAD_PASSWORD = "test-lead-pass"
TEST_VIEWER_PASSWORD = "test-viewer-pass"


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
            secret_key="rbac-secret",
            issuer="rbac-issuer",
            access_ttl_seconds=3600,
            refresh_ttl_seconds=7200,
            openrouter_api_key="test-openrouter-key",
        )
        os.environ["COCKPIT_API_BOOTSTRAP_OWNER_PASSWORD"] = TEST_OWNER_PASSWORD
        os.environ["COCKPIT_API_BOOTSTRAP_LEAD_PASSWORD"] = TEST_LEAD_PASSWORD
        os.environ["COCKPIT_API_BOOTSTRAP_VIEWER_PASSWORD"] = TEST_VIEWER_PASSWORD
        app = create_app(settings)
        client = TestClient(app)

        owner = _login(client, "owner", TEST_OWNER_PASSWORD)
        lead = _login(client, "lead", TEST_LEAD_PASSWORD)
        viewer = _login(client, "viewer", TEST_VIEWER_PASSWORD)

        create = client.post(
            "/v1/projects",
            headers=_auth_headers(owner),
            json={"project_id": "rbac-demo", "name": "RBAC Demo"},
        )
        assert create.status_code == 201

        viewer_state = client.put(
            "/v1/projects/rbac-demo/state",
            headers=_auth_headers(viewer),
            json={
                "phase": "Plan",
                "objective": "Should fail",
                "now": [],
                "next": [],
                "in_progress": [],
                "blockers": [],
                "risks": [],
                "links": [],
            },
        )
        assert viewer_state.status_code == 403

        lead_state = client.put(
            "/v1/projects/rbac-demo/state",
            headers=_auth_headers(lead),
            json={
                "phase": "Implement",
                "objective": "Lead can write",
                "now": ["update state"],
                "next": ["ship"],
                "in_progress": [],
                "blockers": [],
                "risks": [],
                "links": [],
            },
        )
        assert lead_state.status_code == 200

        viewer_read = client.get("/v1/projects/rbac-demo/state", headers=_auth_headers(viewer))
        assert viewer_read.status_code == 200

        owner_create = client.post(
            "/v1/projects",
            headers=_auth_headers(owner),
            json={"project_id": "owner-only", "name": "Owner Only"},
        )
        assert owner_create.status_code == 201

        lead_create = client.post(
            "/v1/projects",
            headers=_auth_headers(lead),
            json={"project_id": "lead-nope", "name": "Lead Nope"},
        )
        assert lead_create.status_code == 403

    print("OK: cloud api RBAC verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
