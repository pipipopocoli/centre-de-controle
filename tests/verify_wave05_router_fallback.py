from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.antigravity_runner import RunnerResult as AgRunnerResult  # noqa: E402
from app.services.auto_mode import AutoModeAction
from app.services.codex_runner import RunnerResult as CodexRunnerResult  # noqa: E402
from app.services.cost_telemetry import COST_EVENT_SCHEMA_VERSION, validate_cost_event
from app.services.ollama_runner import RunnerResult as OllamaRunnerResult  # noqa: E402
from app.services.execution_router import route_action


def _read_cost_events(path: Path) -> list[dict]:
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _assert_cost_event_schema(event: dict, project_id: str) -> None:
    assert event.get("schema_version") == COST_EVENT_SCHEMA_VERSION
    assert event.get("project_id") == project_id
    assert event.get("currency") == "CAD"
    assert isinstance(event.get("input_tokens"), int)
    assert isinstance(event.get("output_tokens"), int)
    assert isinstance(event.get("cached_tokens"), int)
    assert isinstance(event.get("cached_input_tokens"), int)
    assert event.get("cached_tokens") == event.get("cached_input_tokens")
    assert isinstance(event.get("elapsed_ms"), int) and event.get("elapsed_ms") >= 0
    assert isinstance(event.get("cost_cad_estimate"), (int, float)) and float(event.get("cost_cad_estimate")) >= 0.0
    assert isinstance(event.get("ts"), (int, float))
    datetime.fromisoformat(str(event.get("timestamp")).replace("Z", "+00:00"))
    is_valid, reason = validate_cost_event(event, project_id=project_id)
    assert is_valid, f"cost event should validate, got: {reason}"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        project_dir = projects_root / project_id
        (project_dir / "runs").mkdir(parents=True, exist_ok=True)

        settings = {
            "automation": {
                "router": {
                    "providers_order": ["codex", "antigravity", "ollama"],
                    "ollama_enabled": False,
                },
                "codex": {"enabled": True},
                "antigravity": {"enabled": True},
                "timeouts": {"codex_seconds": 60},
            },
            "cost": {"currency": "CAD"},
        }

        action = AutoModeAction(
            request_id="req_wave05_router",
            project_id=project_id,
            agent_id="agent-1",
            platform="antigravity",
            execution_mode="antigravity_supervised",
            prompt_text=f"PROJECT LOCK: {project_id}\nTask:\nwave05 fallback",
            app_to_open="Codex",
            notify_text="",
        )

        codex_failed = CodexRunnerResult(
            runner="codex",
            status="failed",
            success=False,
            launched=True,
            completed=True,
            returncode=1,
            stdout="",
            stderr="failure",
            error="failure",
            started_at="2026-02-19T00:00:00+00:00",
            finished_at="2026-02-19T00:00:01+00:00",
            duration_seconds=1.0,
            output_path=None,
            output_text="",
        )
        ag_launched = AgRunnerResult(
            runner="antigravity",
            status="launched",
            success=True,
            launched=True,
            completed=False,
            returncode=0,
            stdout="",
            stderr="",
            error=None,
            started_at="2026-02-19T00:00:01+00:00",
            finished_at="2026-02-19T00:00:02+00:00",
            duration_seconds=1.0,
            command=["antigravity", "chat"],
        )

        with patch("app.services.execution_router.run_codex", return_value=codex_failed), patch(
            "app.services.execution_router.launch_chat", return_value=ag_launched
        ):
            result = route_action(action, project_id, projects_root=projects_root, settings=settings)

        assert result.runner == "antigravity", f"expected AG fallback, got {result.runner}"
        assert result.status == "launched", f"unexpected status: {result.status}"

        cost_events_path = project_dir / "runs" / "cost_events.ndjson"
        assert cost_events_path.exists(), "cost_events.ndjson must exist"
        events = _read_cost_events(cost_events_path)
        assert len(events) == 2, f"expected exactly 2 cost events (codex + ag), got {len(events)}"
        providers = [str(item.get("provider") or "") for item in events]
        assert providers == ["codex", "antigravity"], f"strict order mismatch: {providers}"
        for event in events:
            _assert_cost_event_schema(event, project_id)

        slo_path = project_dir / "runs" / "slo_verdict_latest.json"
        assert slo_path.exists(), "slo verdict file should be generated"
        slo_payload = json.loads(slo_path.read_text(encoding="utf-8"))
        assert "verdict" in slo_payload

        project_id_ollama = "cockpit_ollama"
        project_dir_ollama = projects_root / project_id_ollama
        (project_dir_ollama / "runs").mkdir(parents=True, exist_ok=True)

        settings_ollama = {
            "automation": {
                "router": {
                    "providers_order": ["codex", "antigravity", "ollama"],
                    "ollama_enabled": True,
                    "ollama_model": "llama3.2",
                },
                "codex": {"enabled": True},
                "antigravity": {"enabled": True},
                "timeouts": {"codex_seconds": 60, "ollama_seconds": 60},
            },
            "cost": {"currency": "CAD"},
        }

        action_ollama = AutoModeAction(
            request_id="req_wave05_router_ollama",
            project_id=project_id_ollama,
            agent_id="agent-2",
            platform="antigravity",
            execution_mode="antigravity_supervised",
            prompt_text=f"PROJECT LOCK: {project_id_ollama}\nTask:\nwave05 ollama fallback",
            app_to_open="Codex",
            notify_text="",
        )

        ag_failed = AgRunnerResult(
            runner="antigravity",
            status="failed",
            success=False,
            launched=False,
            completed=False,
            returncode=1,
            stdout="",
            stderr="ag_failure",
            error="ag_failure",
            started_at="2026-02-19T00:00:02+00:00",
            finished_at="2026-02-19T00:00:03+00:00",
            duration_seconds=1.0,
            command=["antigravity", "chat"],
        )
        ollama_success = OllamaRunnerResult(
            runner="ollama",
            status="completed",
            success=True,
            launched=True,
            completed=True,
            returncode=0,
            stdout="ok",
            stderr="",
            error=None,
            started_at="2026-02-19T00:00:03+00:00",
            finished_at="2026-02-19T00:00:04+00:00",
            duration_seconds=1.0,
            output_path=None,
            output_text="ok",
            model="llama3.2",
        )

        with patch("app.services.execution_router.run_codex", return_value=codex_failed), patch(
            "app.services.execution_router.launch_chat", return_value=ag_failed
        ), patch("app.services.execution_router.run_ollama", return_value=ollama_success):
            result_ollama = route_action(
                action_ollama,
                project_id_ollama,
                projects_root=projects_root,
                settings=settings_ollama,
            )

        assert result_ollama.runner == "ollama", f"expected ollama fallback, got {result_ollama.runner}"
        assert result_ollama.closed is True, "ollama success should close the request"
        assert result_ollama.status == "completed", f"unexpected ollama status: {result_ollama.status}"

        cost_events_path_ollama = project_dir_ollama / "runs" / "cost_events.ndjson"
        events_ollama = _read_cost_events(cost_events_path_ollama)
        providers_ollama = [str(item.get("provider") or "") for item in events_ollama]
        assert providers_ollama == ["codex", "antigravity", "ollama"], f"strict fallback mismatch: {providers_ollama}"
        for event in events_ollama:
            _assert_cost_event_schema(event, project_id_ollama)

    print("OK: wave05 router fallback + cost + slo artifacts verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
