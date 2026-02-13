from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.skills_installer import sync_skills  # noqa: E402


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_last_ndjson(path: Path) -> dict:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return json.loads(lines[-1]) if lines else {}


def test_first_install() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        summary = sync_skills(
            "cockpit",
            ["openai-docs", "skill-installer"],
            projects_root=projects_root,
            catalog=[
                {"id": "openai-docs", "version": "1.0"},
                {"id": "skill-installer", "version": "1.0"},
            ],
        )
        assert summary.requested == 2
        assert summary.installed == 2
        assert summary.skipped == 0
        assert summary.failed == 0
        state = _read_json(Path(summary.state_path))
        assert "skills" in state
        assert state["skills"]["openai-docs"]["last_status"] == "installed"
        assert state["skills"]["skill-installer"]["last_status"] == "installed"
    print("[PASS] first install")


def test_rerun_idempotent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        catalog = [
            {"id": "openai-docs", "version": "1.0"},
            {"id": "skill-installer", "version": "1.0"},
        ]
        sync_skills("cockpit", ["openai-docs", "skill-installer"], projects_root=projects_root, catalog=catalog)
        summary = sync_skills(
            "cockpit",
            ["openai-docs", "skill-installer"],
            projects_root=projects_root,
            catalog=catalog,
        )
        assert summary.installed == 0
        assert summary.skipped == 2
        assert summary.failed == 0
    print("[PASS] rerun idempotent")


def test_dry_run_no_mutation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        sync_skills(
            "cockpit",
            ["openai-docs"],
            projects_root=projects_root,
            catalog=[{"id": "openai-docs", "version": "1.0"}],
        )
        state_path = projects_root / "cockpit" / "skills" / "install_state.json"
        before = state_path.read_text(encoding="utf-8")
        summary = sync_skills(
            "cockpit",
            ["vercel-deploy"],
            projects_root=projects_root,
            catalog=[{"id": "vercel-deploy", "version": "1.0"}],
            dry_run=True,
        )
        after = state_path.read_text(encoding="utf-8")
        assert summary.would_install >= 1
        assert summary.installed == 0
        assert before == after
    print("[PASS] dry_run no mutation")


def test_partial_failure_tolerant() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"

        def installer(skill_id: str, version: str) -> bool:
            if skill_id == "bad-skill":
                return False
            return True

        summary = sync_skills(
            "cockpit",
            ["ok-skill", "bad-skill"],
            projects_root=projects_root,
            catalog=[
                {"id": "ok-skill", "version": "1.0"},
                {"id": "bad-skill", "version": "1.0"},
            ],
            installer=installer,
        )
        assert summary.installed == 1
        assert summary.failed == 1
        assert summary.requested == 2
    print("[PASS] partial failure tolerant")


def test_counters_in_logs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        summary = sync_skills(
            "cockpit",
            ["openai-docs", "skill-installer"],
            projects_root=projects_root,
            catalog=[
                {"id": "openai-docs", "version": "1.0"},
                {"id": "skill-installer", "version": "1.0"},
            ],
        )
        log_row = _read_last_ndjson(Path(summary.log_path))
        assert "installed" in log_row
        assert "skipped" in log_row
        assert "failed" in log_row
        assert int(log_row["installed"]) == summary.installed
        assert int(log_row["skipped"]) == summary.skipped
        assert int(log_row["failed"]) == summary.failed
    print("[PASS] counters in logs")


def test_version_bump_reinstall() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        sync_skills(
            "cockpit",
            ["openai-docs"],
            projects_root=projects_root,
            catalog=[{"id": "openai-docs", "version": "1.0"}],
        )

        calls: list[tuple[str, str]] = []

        def installer(skill_id: str, version: str) -> bool:
            calls.append((skill_id, version))
            return True

        summary = sync_skills(
            "cockpit",
            ["openai-docs"],
            projects_root=projects_root,
            catalog=[{"id": "openai-docs", "version": "2.0"}],
            installer=installer,
        )
        assert summary.installed == 1
        assert summary.skipped == 0
        assert calls == [("openai-docs", "2.0")]
        state = _read_json(Path(summary.state_path))
        assert state["skills"]["openai-docs"]["version"] == "2.0"
    print("[PASS] version bump reinstall")


def main() -> int:
    tests = [
        test_first_install,
        test_rerun_idempotent,
        test_dry_run_no_mutation,
        test_partial_failure_tolerant,
        test_counters_in_logs,
        test_version_bump_reinstall,
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

    print(f"\n--- Results: {passed} passed, {failed} failed ---")
    if failed:
        return 1
    print("OK: skills installer verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
