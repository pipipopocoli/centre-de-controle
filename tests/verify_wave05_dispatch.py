from __future__ import annotations

import itertools
import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import dispatch_once, load_runtime_state
from app.services.task_matcher import RANK_TIE_BREAK_CONTRACT, rank_candidates


def _append_ndjson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _write_settings(project_dir: Path, *, queue_target: int, max_actions_hard_cap: int) -> None:
    settings = {
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
                "queue_target": queue_target,
                "max_actions_hard_cap": max_actions_hard_cap,
            },
        }
    }
    settings_path = project_dir / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def _write_registry(project_dir: Path) -> None:
    registry_payload = {
        "agent-1": {
            "agent_id": "agent-1",
            "name": "agent-1",
            "engine": "CDX",
            "platform": "codex",
            "level": 2,
            "lead_id": "victor",
            "role": "specialist",
            "skills": ["memory", "registry"],
        },
        "agent-2": {
            "agent_id": "agent-2",
            "name": "agent-2",
            "engine": "AG",
            "platform": "antigravity",
            "level": 2,
            "lead_id": "leo",
            "role": "specialist",
            "skills": ["ui", "qa"],
        },
        "agent-3": {
            "agent_id": "agent-3",
            "name": "agent-3",
            "engine": "CDX",
            "platform": "codex",
            "level": 2,
            "lead_id": "victor",
            "role": "specialist",
            "skills": ["backend", "scoring"],
        },
    }
    registry_path = project_dir / "agents" / "registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry_payload, indent=2), encoding="utf-8")


def _append_request(req_path: Path, *, request_id: str, project_id: str, agent_id: str, created_at: str, text: str) -> None:
    _append_ndjson(
        req_path,
        {
            "request_id": request_id,
            "project_id": project_id,
            "agent_id": agent_id,
            "status": "queued",
            "source": "mention",
            "created_at": created_at,
            "message": {"author": "operator", "text": text, "mentions": [agent_id]},
        },
    )


def test_tie_break_deterministic() -> None:
    assert RANK_TIE_BREAK_CONTRACT == ("score_desc", "agent_id_asc", "request_id_asc")
    base = [
        {"agent_id": "agent-2", "request_id": "req-b", "score": 0.777},
        {"agent_id": "agent-1", "request_id": "req-c", "score": 0.777},
        {"agent_id": "agent-1", "request_id": "req-a", "score": 0.777},
    ]
    expected = [("agent-1", "req-a"), ("agent-1", "req-c"), ("agent-2", "req-b")]

    for perm in itertools.permutations(base):
        ranked = rank_candidates(list(perm))
        observed = [(str(item.get("agent_id") or ""), str(item.get("request_id") or "")) for item in ranked]
        assert observed == expected, f"unexpected deterministic order for tie: {observed}"

    print("[PASS] deterministic tie-break agent_id/request_id")


def test_backpressure_basic_queue_target() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        project_dir = projects_root / project_id
        _write_settings(project_dir, queue_target=1, max_actions_hard_cap=5)
        _write_registry(project_dir)

        req_path = project_dir / "runs" / "requests.ndjson"
        _append_request(
            req_path,
            request_id="req_wave05_a",
            project_id=project_id,
            agent_id="agent-1",
            created_at="2026-02-19T12:00:00+00:00",
            text="memory registry hardening",
        )
        _append_request(
            req_path,
            request_id="req_wave05_b",
            project_id=project_id,
            agent_id="agent-2",
            created_at="2026-02-19T12:01:00+00:00",
            text="ui qa screenshot",
        )

        result = dispatch_once(projects_root, project_id, max_actions=1)
        assert result.dispatched_count == 1, f"backpressure queue_target should dispatch 1, got {result.dispatched_count}"
        assert len(result.actions) == 1, "max_actions=1 should yield one action"
        assert result.actions[0].project_id == project_id
        assert result.actions[0].platform in {"codex", "antigravity"}

        runtime = load_runtime_state(projects_root, project_id)
        requests = runtime.get("requests", {})
        dispatched = [rid for rid, payload in requests.items() if payload.get("status") == "dispatched"]
        queued = [rid for rid, payload in requests.items() if payload.get("status") == "queued"]
        assert len(dispatched) == 1, f"expected 1 dispatched request, got {dispatched}"
        assert len(queued) >= 1, f"expected remaining queued request, got {queued}"

    print("[PASS] queue_target cap enforced")


def test_backpressure_hard_cap() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        project_dir = projects_root / project_id
        _write_settings(project_dir, queue_target=10, max_actions_hard_cap=1)
        _write_registry(project_dir)

        req_path = project_dir / "runs" / "requests.ndjson"
        _append_request(
            req_path,
            request_id="req_wave05_hard_1",
            project_id=project_id,
            agent_id="agent-1",
            created_at="2026-02-19T12:00:00+00:00",
            text="memory hardening",
        )
        _append_request(
            req_path,
            request_id="req_wave05_hard_2",
            project_id=project_id,
            agent_id="agent-2",
            created_at="2026-02-19T12:01:00+00:00",
            text="ui hardening",
        )
        _append_request(
            req_path,
            request_id="req_wave05_hard_3",
            project_id=project_id,
            agent_id="agent-3",
            created_at="2026-02-19T12:02:00+00:00",
            text="backend hardening",
        )

        result = dispatch_once(projects_root, project_id, max_actions=3)
        assert result.dispatched_count == 1, f"hard cap should dispatch 1, got {result.dispatched_count}"

        runtime = load_runtime_state(projects_root, project_id)
        requests = runtime.get("requests", {})
        dispatched = [rid for rid, payload in requests.items() if payload.get("status") == "dispatched"]
        assert len(dispatched) == 1, f"hard cap expected 1 dispatched request, got {dispatched}"

    print("[PASS] hard cap enforced")


def test_backpressure_overload_strict_zero() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        project_dir = projects_root / project_id
        _write_settings(project_dir, queue_target=1, max_actions_hard_cap=5)
        _write_registry(project_dir)

        state_path = project_dir / "runs" / "auto_mode_state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_payload = {
            "schema_version": 3,
            "processed": ["inflight_1"],
            "requests": {
                "inflight_1": {
                    "request_id": "inflight_1",
                    "project_id": project_id,
                    "agent_id": "agent-1",
                    "status": "dispatched",
                    "created_at": "2026-02-19T10:00:00+00:00",
                    "dispatched_at": "2026-02-19T10:00:00+00:00",
                    "updated_at": "2026-02-19T10:00:00+00:00",
                }
            },
            "counters": {},
            "updated_at": "2026-02-19T10:00:00+00:00",
        }
        state_path.write_text(json.dumps(state_payload, indent=2), encoding="utf-8")

        req_path = project_dir / "runs" / "requests.ndjson"
        _append_ndjson(
            req_path,
            {
                "request_id": "inflight_1",
                "project_id": project_id,
                "agent_id": "agent-1",
                "status": "dispatched",
                "source": "mention",
                "created_at": "2026-02-19T10:00:00+00:00",
            },
        )
        _append_request(
            req_path,
            request_id="req_wave05_overload_1",
            project_id=project_id,
            agent_id="agent-2",
            created_at="2026-02-19T12:01:00+00:00",
            text="ui qa overload",
        )

        result = dispatch_once(projects_root, project_id, max_actions=1)
        assert result.dispatched_count == 0, f"strict overload cap should dispatch 0, got {result.dispatched_count}"
        assert len(result.actions) == 0, "no action expected when cap is 0"

        runtime = load_runtime_state(projects_root, project_id)
        requests = runtime.get("requests", {})
        assert requests.get("inflight_1", {}).get("status") == "dispatched"
        assert requests.get("req_wave05_overload_1", {}).get("status") == "queued"

    print("[PASS] strict overload cap enforced")


def main() -> int:
    tests = [
        test_tie_break_deterministic,
        test_backpressure_basic_queue_target,
        test_backpressure_hard_cap,
        test_backpressure_overload_strict_zero,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as exc:
            print(f"[FAIL] {test.__name__}: {exc}")
            failed += 1

    print(f"--- Results: {passed} passed, {failed} failed ---")
    if failed:
        return 1
    print("OK: wave05 dispatch scoring/backpressure verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
