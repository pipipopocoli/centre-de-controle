#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import app.data.paths as paths_mod  # noqa: E402
import app.data.store as store_mod  # noqa: E402

SCRIPT_PATH = ROOT_DIR / "scripts" / "wave12_isolation_repair.py"
DISPATCHER_PATH = ROOT_DIR / "scripts" / "dispatcher.py"


@contextmanager
def _projects_root_scope(projects_root: Path):
    old_paths_projects_dir = paths_mod.PROJECTS_DIR
    old_store_projects_dir = store_mod.PROJECTS_DIR
    paths_mod.PROJECTS_DIR = projects_root
    store_mod.PROJECTS_DIR = projects_root
    try:
        yield
    finally:
        paths_mod.PROJECTS_DIR = old_paths_projects_dir
        store_mod.PROJECTS_DIR = old_store_projects_dir


def _run_script(cmd: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, check=False)
    stdout = proc.stdout.strip()
    payload = json.loads(stdout) if stdout else {}
    return proc.returncode, payload


def _check_list_projects_and_load_project_alias() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        projects_root.mkdir(parents=True, exist_ok=True)

        with _projects_root_scope(projects_root):
            store_mod.ensure_project_structure("cockpit", "Cockpit")
            store_mod.ensure_project_structure("evozina", "Evozina")
            store_mod.ensure_project_structure("motherload", "Motherload")

            (projects_root / "_archive").mkdir(parents=True, exist_ok=True)

            demo_link = projects_root / "demo"
            if demo_link.exists() or demo_link.is_symlink():
                demo_link.unlink()
            demo_link.symlink_to(projects_root / "cockpit", target_is_directory=True)

            listed = store_mod.list_projects()
            assert "cockpit" in listed, listed
            assert "evozina" in listed, listed
            assert "motherload" in listed, listed
            assert "demo" not in listed, listed
            assert "_archive" not in listed, listed

            demo_project = store_mod.load_project("demo")
            assert demo_project.project_id == "cockpit", demo_project.project_id
            assert demo_project.path.name == "cockpit", demo_project.path

    print("[PASS] wave12 list/load canonical alias filtering")


def _check_ensure_demo_project_behavior() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        projects_root.mkdir(parents=True, exist_ok=True)

        with _projects_root_scope(projects_root):
            store_mod.ensure_project_structure("cockpit", "Cockpit")

            with patch.object(store_mod, "_is_appsupport_projects_root", return_value=True):
                project_app = store_mod.ensure_demo_project()
                assert project_app.project_id == "cockpit", project_app.project_id
                assert (projects_root / "cockpit").exists(), "cockpit should exist"
                assert not (projects_root / "demo").exists(), "demo should not be created in appsupport lock"

            with patch.object(store_mod, "_is_appsupport_projects_root", return_value=False):
                project_non_app = store_mod.ensure_demo_project()
                assert project_non_app.project_id == "demo", project_non_app.project_id
                assert (projects_root / "demo").exists(), "legacy demo bootstrap should remain for non-app roots"

    print("[PASS] wave12 ensure_demo_project appsupport lock + non-app legacy")


def _check_wave12_script_audit_and_apply() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        projects_root.mkdir(parents=True, exist_ok=True)

        with _projects_root_scope(projects_root):
            store_mod.ensure_project_structure("cockpit", "Cockpit")

        demo_link = projects_root / "demo"
        if demo_link.exists() or demo_link.is_symlink():
            demo_link.unlink()
        demo_link.symlink_to(projects_root / "cockpit", target_is_directory=True)

        audit_cmd = [
            sys.executable,
            str(SCRIPT_PATH),
            "--project",
            "cockpit",
            "--data-dir",
            str(projects_root),
        ]
        code_audit, audit_payload = _run_script(audit_cmd)
        assert code_audit == 0, audit_payload
        assert audit_payload.get("mode") == "audit", audit_payload
        assert audit_payload.get("pre_audit", {}).get("demo", {}).get("type") == "symlink", audit_payload
        assert bool(audit_payload.get("pre_audit", {}).get("alias_to_cockpit")) is True, audit_payload
        audit_report = Path(str(audit_payload.get("report_path") or ""))
        assert audit_report.exists(), audit_report

        apply_cmd = [
            sys.executable,
            str(SCRIPT_PATH),
            "--project",
            "cockpit",
            "--data-dir",
            str(projects_root),
            "--apply",
        ]
        code_apply, apply_payload = _run_script(apply_cmd)
        assert code_apply == 0, apply_payload
        assert apply_payload.get("mode") == "apply", apply_payload

        action = apply_payload.get("actions") or {}
        assert bool(action.get("archived")) is True, action
        archived_demo_path = Path(str(action.get("archived_demo_path") or ""))
        assert archived_demo_path.exists(), archived_demo_path
        assert archived_demo_path.name.startswith("demo_"), archived_demo_path

        assert not (projects_root / "demo").exists(), "demo alias should be archived"
        assert (projects_root / "cockpit").exists(), "cockpit must stay intact"

        post_contract = apply_payload.get("post_contract") or {}
        listed_after = post_contract.get("list_projects") or []
        assert "cockpit" in listed_after, listed_after
        assert "demo" not in listed_after, listed_after
        assert "_archive" not in listed_after, listed_after
        assert apply_payload.get("blockers") == [], apply_payload

        apply_report = Path(str(apply_payload.get("report_path") or ""))
        assert apply_report.exists(), apply_report

    print("[PASS] wave12 isolation repair script audit/apply")


def _check_dispatcher_default() -> None:
    body = DISPATCHER_PATH.read_text(encoding="utf-8")
    assert 'DEFAULT_PROJECT = "cockpit"' in body, "dispatcher default project should be cockpit"
    assert "COCKPIT_PROJECT_ID or cockpit" in body, "dispatcher help text should reference cockpit"
    print("[PASS] wave12 dispatcher default cockpit")


def main() -> int:
    checks = [
        _check_list_projects_and_load_project_alias,
        _check_ensure_demo_project_behavior,
        _check_wave12_script_audit_and_apply,
        _check_dispatcher_default,
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
    print("OK: wave12 isolation verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
