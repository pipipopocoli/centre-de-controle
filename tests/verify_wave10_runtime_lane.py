#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


def _append_ndjson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_registry(project_dir: Path) -> dict[str, dict]:
    registry_payload = {
        "agent-1": {
            "agent_id": "agent-1",
            "name": "agent-1",
            "engine": "CDX",
            "platform": "codex",
            "level": 2,
            "lead_id": "victor",
            "role": "specialist",
            "skills": ["backend"],
        },
        "agent-2": {
            "agent_id": "agent-2",
            "name": "agent-2",
            "engine": "AG",
            "platform": "antigravity",
            "level": 2,
            "lead_id": "leo",
            "role": "specialist",
            "skills": ["ui"],
        },
        "agent-3": {
            "agent_id": "agent-3",
            "name": "agent-3",
            "engine": "CDX",
            "platform": "codex",
            "level": 2,
            "lead_id": "victor",
            "role": "specialist",
            "skills": ["ops"],
        },
        "agent-4": {
            "agent_id": "agent-4",
            "name": "agent-4",
            "engine": "AG",
            "platform": "antigravity",
            "level": 2,
            "lead_id": "leo",
            "role": "specialist",
            "skills": ["qa"],
        },
        "agent-5": {
            "agent_id": "agent-5",
            "name": "agent-5",
            "engine": "CDX",
            "platform": "codex",
            "level": 2,
            "lead_id": "victor",
            "role": "specialist",
            "skills": ["data"],
        },
    }
    _write_json(project_dir / "agents" / "registry.json", registry_payload)
    return registry_payload


def _check_refresh_decoupling() -> None:
    import app.ui.main_window as main_window_mod

    MainWindow = main_window_mod.MainWindow

    class _FakeWindow:
        def __init__(self) -> None:
            self.current_project_id = "cockpit"
            self.load_project_calls: list[tuple[object, bool, bool]] = []
            self.refresh_bible_calls: list[bool] = []

        def load_project(
            self,
            project: object,
            *,
            refresh_chat_now: bool = True,
            force_portfolio_refresh: bool = False,
        ) -> None:
            self.load_project_calls.append((project, refresh_chat_now, force_portfolio_refresh))

        def refresh_bible(self, *, force: bool = False) -> None:
            self.refresh_bible_calls.append(bool(force))

    fake = _FakeWindow()
    with patch("app.ui.main_window.load_project", return_value={"project_id": "cockpit"}) as mocked_load_project:
        MainWindow.refresh_project(fake)
    mocked_load_project.assert_called_once_with("cockpit")
    assert len(fake.load_project_calls) == 1
    _, refresh_chat_now, force_portfolio_refresh = fake.load_project_calls[0]
    assert refresh_chat_now is False, "project refresh must not force chat rebuild"
    assert force_portfolio_refresh is False
    assert fake.refresh_bible_calls == [False]

    class _FakeTabs:
        def __init__(self, current: object) -> None:
            self._current = current

        def currentWidget(self) -> object:
            return self._current

    class _FakeBible:
        def __init__(self) -> None:
            self.refresh_calls = 0

        def refresh_content(self) -> None:
            self.refresh_calls += 1

    class _FakeBibleWindow:
        pass

    fake_bible_window = _FakeBibleWindow()
    fake_bible_window.current_project_id = "cockpit"
    fake_bible_window.project_bible = _FakeBible()
    fake_bible_window.center_tabs = _FakeTabs(current=object())
    fake_bible_window._last_bible_refresh_at = None
    fake_bible_window._bible_refresh_seconds = 45

    MainWindow.refresh_bible(fake_bible_window, force=False)
    assert fake_bible_window.project_bible.refresh_calls == 0, "inactive bible tab should skip refresh"

    MainWindow.refresh_bible(fake_bible_window, force=True)
    assert fake_bible_window.project_bible.refresh_calls == 1, "forced refresh must bypass tab guard"

    fake_bible_window.center_tabs = _FakeTabs(current=fake_bible_window.project_bible)
    fake_bible_window._last_bible_refresh_at = datetime.now(timezone.utc)
    MainWindow.refresh_bible(fake_bible_window, force=False)
    assert fake_bible_window.project_bible.refresh_calls == 1, "throttle should block rapid refresh"

    fake_bible_window._last_bible_refresh_at = datetime.now(timezone.utc) - timedelta(seconds=90)
    MainWindow.refresh_bible(fake_bible_window, force=False)
    assert fake_bible_window.project_bible.refresh_calls == 2, "refresh should run after throttle window"

    print("[PASS] wave10 cp-0040 refresh decoupling lock")


def _check_context_ref_pipeline() -> None:
    original_data_dir = os.environ.get("COCKPIT_DATA_DIR")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            projects_root = Path(tmp) / "projects"
            os.environ["COCKPIT_DATA_DIR"] = str(projects_root)

            import app.data.paths as paths_mod
            import app.data.store as store_mod
            import app.ui.chatroom as chatroom_mod
            import app.ui.main_window as main_window_mod
            from PySide6.QtWidgets import QApplication

            importlib.reload(paths_mod)
            importlib.reload(store_mod)
            importlib.reload(chatroom_mod)
            importlib.reload(main_window_mod)

            ensure_project_structure = store_mod.ensure_project_structure
            run_requests_path = store_mod.run_requests_path
            ChatroomWidget = chatroom_mod.ChatroomWidget
            MainWindow = main_window_mod.MainWindow

            app = QApplication.instance() or QApplication([])
            ensure_project_structure("demo", "Demo")

            class _FakeWindow:
                def __init__(self) -> None:
                    self.current_project_id = "demo"
                    self.chatroom = ChatroomWidget()

                def _make_message_id(self, author: str) -> str:
                    return f"msg_wave10_{author}"

                def run_auto_mode_tick(self) -> None:
                    return

                def _auto_reply(self, payload: dict) -> None:
                    return

                def refresh_chat(self) -> None:
                    return

            fake = _FakeWindow()
            MainWindow.on_ui_context_selected(
                fake,
                {
                    "kind": "agent",
                    "id": "victor",
                    "title": "Victor",
                },
            )
            selected_context = fake.chatroom.current_context_ref()
            assert isinstance(selected_context, dict), "context badge should hold selected context before send"

            fake.chatroom.input.setText("Ping @victor #wave10")
            MainWindow.on_send_message(fake)

            rows = []
            for raw in run_requests_path("demo").read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line:
                    continue
                rows.append(json.loads(line))

            assert rows, "run requests should be created from mention message"
            latest = rows[-1]
            top_context = latest.get("context_ref")
            message = latest.get("message") if isinstance(latest.get("message"), dict) else {}
            msg_context = message.get("context_ref")

            for context_ref in (top_context, msg_context):
                assert isinstance(context_ref, dict), "context_ref must be persisted in request and message payload"
                for key in ("kind", "id", "title", "source_path", "source_uri", "selected_at"):
                    assert key in context_ref, f"missing context key: {key}"
                assert str(context_ref.get("kind") or "") == "agent"
                assert str(context_ref.get("id") or "") == "victor"
                assert str(context_ref.get("title") or "") == "Victor"
                assert str(context_ref.get("source_path") or "").endswith("/agents/victor/state.json")
                assert str(context_ref.get("source_uri") or "").startswith("file://")
                assert str(context_ref.get("selected_at") or "").strip(), "selected_at must be populated"

            app.quit()
    finally:
        if original_data_dir is None:
            os.environ.pop("COCKPIT_DATA_DIR", None)
        else:
            os.environ["COCKPIT_DATA_DIR"] = original_data_dir

    print("[PASS] wave10 cp-0041 context_ref pipeline lock")


def _check_balanced_throughput_backpressure() -> None:
    from app.services.auto_mode import dispatch_once, load_runtime_state

    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        project_dir = projects_root / project_id
        requests_path = project_dir / "runs" / "requests.ndjson"

        settings_payload = {
            "dispatch": {
                "scoring": {
                    "enabled": True,
                    "weights": {
                        "skill_match": 0.45,
                        "availability": 0.20,
                        "cost": 0.15,
                        "history": 0.20,
                    },
                },
                "backpressure": {
                    "enabled": True,
                    "queue_target": 3,
                    "max_actions_hard_cap": 5,
                },
            },
            "auto_mode": {
                "max_actions": 2,
            },
        }
        _write_json(project_dir / "settings.json", settings_payload)
        registry_payload = _write_registry(project_dir)

        agent_ids = ["agent-1", "agent-2", "agent-3", "agent-4", "agent-5"]
        for idx, agent_id in enumerate(agent_ids, start=1):
            _append_ndjson(
                requests_path,
                {
                    "request_id": f"req_wave10_{idx}",
                    "project_id": project_id,
                    "agent_id": agent_id,
                    "status": "queued",
                    "source": "mention",
                    "created_at": f"2026-02-22T16:0{idx}:00+00:00",
                    "message": {
                        "author": "operator",
                        "text": f"Task for @{agent_id}",
                        "mentions": [agent_id],
                    },
                },
            )

        result = dispatch_once(projects_root, project_id, max_actions=2)
        assert result.dispatched_count == 3, f"backpressure gate should dispatch 3, got {result.dispatched_count}"
        assert len(result.actions) == 2, f"balanced max_actions should emit 2 actions, got {len(result.actions)}"

        runtime = load_runtime_state(projects_root, project_id)
        requests_map = runtime.get("requests")
        assert isinstance(requests_map, dict)

        dispatched = [rid for rid, payload in requests_map.items() if str(payload.get("status") or "") == "dispatched"]
        queued = [rid for rid, payload in requests_map.items() if str(payload.get("status") or "") == "queued"]
        assert len(dispatched) == 3, f"expected exactly 3 dispatched requests, got {dispatched}"
        assert len(queued) >= 2, f"expected remaining queued requests, got {queued}"

        for action in result.actions:
            expected_platform = str(registry_payload[action.agent_id]["platform"])
            assert action.platform == expected_platform, (
                f"platform drift for {action.agent_id}: expected {expected_platform}, got {action.platform}"
            )

    print("[PASS] wave10 cp-0043 balanced throughput lock")


def main() -> int:
    checks = [
        _check_refresh_decoupling,
        _check_context_ref_pipeline,
        _check_balanced_throughput_backpressure,
    ]

    passed = 0
    failed = 0
    for check in checks:
        try:
            check()
            passed += 1
        except Exception as exc:
            print(f"[FAIL] {check.__name__}: {exc}")
            failed += 1

    print(f"--- Results: {passed} passed, {failed} failed ---")
    if failed:
        return 1
    print("OK: wave10 runtime/backend lane verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
