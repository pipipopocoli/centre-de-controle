from __future__ import annotations

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from starlette.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.wizard_live import WizardLiveResult  # noqa: E402
from server.config import APISettings  # noqa: E402
from server.main import create_app  # noqa: E402


TEST_OWNER_PASSWORD = "test-owner-pass"


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _fake_result(status: str, run_id: str) -> WizardLiveResult:
    return WizardLiveResult(
        status=status,
        project_id="wizard-demo",
        repo_path="/tmp/repo",
        projects_root="/tmp/projects",
        run_id=run_id,
        trigger="api_test",
        session_active=(status != "stopped"),
        output_json_path=f"/tmp/projects/wizard-demo/runs/{run_id}.json",
        output_md_path=f"/tmp/projects/wizard-demo/runs/{run_id}.md",
        prompt_path=None,
        context_path=None,
        bmad_dir="/tmp/projects/wizard-demo/BMAD",
        runner=None,
        error=None,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        repo_path = Path(tmp) / "repo"
        repo_path.mkdir(parents=True, exist_ok=True)
        settings = APISettings(
            projects_root=projects_root,
            secret_key="wizard-secret",
            issuer="wizard-issuer",
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
            json={"project_id": "wizard-demo", "name": "Wizard Demo", "linked_repo_path": str(repo_path)},
        )
        assert create.status_code == 201

        with patch("server.main.start_wizard_live_session", return_value=_fake_result("ok", "WIZARD_LIVE_START")), patch(
            "server.main.run_wizard_live_turn", return_value=_fake_result("ok", "WIZARD_LIVE_RUN")
        ), patch("server.main.stop_wizard_live_session", return_value=_fake_result("stopped", "WIZARD_LIVE_STOP")), patch(
            "server.main.load_wizard_live_session", return_value={"active": True}
        ):
            start = client.post(
                "/v1/projects/wizard-demo/wizard-live/start",
                headers=_auth_headers(owner),
                json={"trigger": "api_test", "operator_message": "start"},
            )
            assert start.status_code == 200
            assert start.json()["run_id"] == "WIZARD_LIVE_START"

            run = client.post(
                "/v1/projects/wizard-demo/wizard-live/run",
                headers=_auth_headers(owner),
                json={"trigger": "api_test", "operator_message": "run"},
            )
            assert run.status_code == 200
            assert run.json()["run_id"] == "WIZARD_LIVE_RUN"

            stop = client.post(
                "/v1/projects/wizard-demo/wizard-live/stop",
                headers=_auth_headers(owner),
                json={"trigger": "api_test", "operator_message": "stop"},
            )
            assert stop.status_code == 200
            assert stop.json()["run_id"] == "WIZARD_LIVE_STOP"

    print("OK: cloud api wizard-live endpoints verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
