#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT_DIR / "scripts" / "project_intake.py"
sys.path.insert(0, str(ROOT_DIR))


def _seed_keys(issues_dir: Path) -> list[str]:
    keys: list[str] = []
    for issue_path in sorted(issues_dir.glob("ISSUE-*.md")):
        content = issue_path.read_text(encoding="utf-8")
        for raw in content.splitlines():
            line = raw.strip()
            if line.startswith("- Seed-Key:"):
                keys.append(line.split(":", 1)[1].strip())
                break
    return keys


def _run_cli(repo_path: Path, projects_root: Path) -> dict:
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--repo-path",
        str(repo_path),
        "--data-dir",
        str(projects_root),
        "--json",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        projects_root = base / "projects"
        repo_path = base / "existing-repo"
        (repo_path / "tests").mkdir(parents=True, exist_ok=True)
        (repo_path / "README.md").write_text("# Existing Repo\n", encoding="utf-8")
        (repo_path / "app.py").write_text("print('ok')\n", encoding="utf-8")
        (repo_path / "tests" / "test_app.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

        os.environ["COCKPIT_DATA_DIR"] = str(projects_root)

        from app.data.store import project_dir
        from app.services.brain_manager import BrainManager

        manager = BrainManager()
        project_id_first = manager.create_project_from_repo(repo_path)
        result_first = manager.run_intake(project_id_first, repo_path)

        project_id_second = manager.create_project_from_repo(repo_path)
        result_second = manager.run_intake(project_id_second, repo_path)

        assert project_id_first == project_id_second, (project_id_first, project_id_second)
        assert result_first.project_id == result_second.project_id == project_id_first

        issues_dir = project_dir(project_id_first) / "issues"
        issue_files = sorted(issues_dir.glob("ISSUE-*.md"))
        assert issue_files, "startup issues should be seeded"
        assert len(issue_files) == len(result_first.issue_seed_paths), "issue seed list should match file count"
        assert sorted(result_first.issue_seed_paths) == sorted(result_second.issue_seed_paths), "seed paths must be stable"

        keys = _seed_keys(issues_dir)
        assert len(keys) == len(issue_files), "each seeded issue should include Seed-Key"
        assert len(set(keys)) == len(keys), "Seed-Key values must be unique"

        startup_pack = project_dir(project_id_first) / "STARTUP_PACK.md"
        assert startup_pack.exists(), "STARTUP_PACK.md must exist"
        startup_text = startup_pack.read_text(encoding="utf-8")
        for section in (
            "## Objective",
            "## Scope (In)",
            "## Scope (Out)",
            "## Initial risks",
            "## Issue seeds",
            "## Dispatch hints",
        ):
            assert section in startup_text, f"missing startup section: {section}"
        assert "scripts/project_intake.py --repo-path" in startup_text, "startup command hint missing"

        cli_first = _run_cli(repo_path, projects_root)
        cli_second = _run_cli(repo_path, projects_root)
        assert cli_first["project_id"] == cli_second["project_id"] == project_id_first
        assert cli_first["startup_pack_path"] == cli_second["startup_pack_path"] == str(startup_pack)
        assert sorted(cli_first["issue_seed_paths"]) == sorted(cli_second["issue_seed_paths"])
        assert sorted(cli_first["issue_seed_paths"]) == sorted(result_first.issue_seed_paths)
        onboarding_pack_path = project_dir(project_id_first) / "runs" / "onboarding_pack_latest.json"
        assert cli_first["onboarding_pack_path"] == str(onboarding_pack_path), cli_first
        assert cli_second["onboarding_pack_path"] == str(onboarding_pack_path), cli_second
        assert onboarding_pack_path.exists(), "onboarding pack should be written by intake CLI"

        onboarding_first = json.loads(onboarding_pack_path.read_text(encoding="utf-8"))
        expected_keys = {
            "schema_version",
            "project_id",
            "project_dir",
            "projects_root",
            "repo_path",
            "run_intake",
            "startup_pack_path",
            "issue_seed_paths",
            "command_path",
        }
        assert set(onboarding_first.keys()) == expected_keys, onboarding_first
        assert onboarding_first["schema_version"] == "wave16_onboarding_pack_v1", onboarding_first
        assert onboarding_first["project_id"] == project_id_first, onboarding_first
        assert onboarding_first["run_intake"] is True, onboarding_first
        assert onboarding_first["issue_seed_paths"] == sorted(onboarding_first["issue_seed_paths"]), onboarding_first
        assert "generated_at" not in onboarding_first, onboarding_first

        onboarding_second = json.loads(onboarding_pack_path.read_text(encoding="utf-8"))
        assert onboarding_second == onboarding_first, (onboarding_first, onboarding_second)

    print("OK: wave14 startup pack deterministic onboarding verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
