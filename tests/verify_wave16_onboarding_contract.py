#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_INTAKE_SCRIPT = ROOT_DIR / "scripts" / "project_intake.py"
EXPECTED_SCHEMA_VERSION = "wave16_onboarding_pack_v1"
EXPECTED_KEYS = {
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


def _run_project_intake(
    repo_path: Path,
    projects_root: Path,
    *,
    run_intake: bool,
    output_pack_path: Path | None = None,
) -> tuple[int, dict, str]:
    cmd = [
        sys.executable,
        str(PROJECT_INTAKE_SCRIPT),
        "--repo-path",
        str(repo_path),
        "--data-dir",
        str(projects_root),
        "--json",
    ]
    if not run_intake:
        cmd.append("--no-run-intake")
    if output_pack_path is not None:
        cmd.extend(["--output-pack-path", str(output_pack_path)])

    proc = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, check=False)
    payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc.returncode, payload, proc.stderr


def _validate_pack(
    payload: dict,
    *,
    project_id: str,
    projects_root: Path,
    repo_path: Path,
    run_intake: bool,
) -> tuple[Path, dict, str]:
    onboarding_pack_path = Path(payload["onboarding_pack_path"])
    assert onboarding_pack_path.exists(), payload
    file_text = onboarding_pack_path.read_text(encoding="utf-8")
    pack = json.loads(file_text)

    assert set(pack.keys()) == EXPECTED_KEYS, pack
    assert pack["schema_version"] == EXPECTED_SCHEMA_VERSION, pack
    assert pack["project_id"] == project_id, pack
    assert pack["projects_root"] == str(projects_root), pack
    assert Path(pack["repo_path"]).resolve() == repo_path.resolve(), pack
    assert pack["run_intake"] is run_intake, pack
    assert pack["command_path"] == "scripts/project_intake.py", pack
    assert pack["issue_seed_paths"] == sorted(pack["issue_seed_paths"]), pack
    assert "timestamp" not in pack, pack
    assert "generated_at" not in pack, pack
    assert file_text == json.dumps(pack, indent=2, sort_keys=True) + "\n", pack
    return onboarding_pack_path, pack, file_text


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        projects_root = base / "projects"
        repo_path = base / "existing-repo"
        (repo_path / "tests").mkdir(parents=True, exist_ok=True)
        (repo_path / "README.md").write_text("# Existing Repo\n", encoding="utf-8")
        (repo_path / "app.py").write_text("print('ok')\n", encoding="utf-8")
        (repo_path / "tests" / "test_app.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

        code_1, payload_1, stderr_1 = _run_project_intake(repo_path, projects_root, run_intake=True)
        assert code_1 == 0, stderr_1
        project_id = str(payload_1["project_id"])
        expected_default_pack = Path(payload_1["project_dir"]) / "runs" / "onboarding_pack_latest.json"
        assert payload_1["onboarding_pack_path"] == str(expected_default_pack), payload_1

        pack_path_1, pack_1, text_1 = _validate_pack(
            payload_1,
            project_id=project_id,
            projects_root=projects_root,
            repo_path=repo_path,
            run_intake=True,
        )
        assert pack_1["issue_seed_paths"] == sorted(payload_1["issue_seed_paths"]), (pack_1, payload_1)

        code_2, payload_2, stderr_2 = _run_project_intake(repo_path, projects_root, run_intake=True)
        assert code_2 == 0, stderr_2
        assert payload_2["project_id"] == project_id, (payload_1, payload_2)
        assert payload_2["onboarding_pack_path"] == str(pack_path_1), payload_2
        _, pack_2, text_2 = _validate_pack(
            payload_2,
            project_id=project_id,
            projects_root=projects_root,
            repo_path=repo_path,
            run_intake=True,
        )
        assert pack_2 == pack_1, (pack_1, pack_2)
        assert text_2 == text_1, (text_1, text_2)

        no_intake_pack = Path(payload_1["project_dir"]) / "runs" / "onboarding_pack_no_intake.json"
        code_3, payload_3, stderr_3 = _run_project_intake(
            repo_path,
            projects_root,
            run_intake=False,
            output_pack_path=no_intake_pack,
        )
        assert code_3 == 0, stderr_3
        assert payload_3["project_id"] == project_id, payload_3
        assert payload_3["run_intake"] is False, payload_3
        assert payload_3["onboarding_pack_path"] == str(no_intake_pack), payload_3
        _, pack_3, _ = _validate_pack(
            payload_3,
            project_id=project_id,
            projects_root=projects_root,
            repo_path=repo_path,
            run_intake=False,
        )
        assert pack_3["issue_seed_paths"] == [], pack_3

    print("OK: wave16 onboarding contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
