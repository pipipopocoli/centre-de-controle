from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.wizard_live import build_context_bridge  # noqa: E402


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _append_ndjson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        projects_root = root / "projects"
        project_id = "demo"
        project_dir = projects_root / project_id
        repo_path = root / "repo"
        repo_path.mkdir(parents=True, exist_ok=True)
        _write(repo_path / "README.md", "# Demo Repo\n")

        _write(project_dir / "STATE.md", "# State\n\n## Phase\n- Plan\n")
        _write(project_dir / "ROADMAP.md", "# Roadmap\n\n## Now\n- Setup\n")
        _write(project_dir / "DECISIONS.md", "# Decisions\n\n## 2026-02-27 - ADR-TST-001\n- Status: Accepted\n")
        _write(project_dir / "INTAKE.md", "# Intake\n\n- context\n")
        _write(project_dir / "QUESTIONS.md", "# Questions\n\n- q1\n")
        _write(project_dir / "PLAN.md", "# Plan\n\n- p1\n")
        _write(project_dir / "STARTUP_PACK.md", "# Startup Pack\n\n- sp1\n")
        _write(project_dir / "agents" / "clems" / "memory.md", "# Memory clems\n- loop\n")
        _write(project_dir / "agents" / "victor" / "memory.md", "# Memory victor\n- loop\n")
        _write(project_dir / "agents" / "leo" / "memory.md", "# Memory leo\n- loop\n")
        _write(project_dir / "agents" / "nova" / "memory.md", "# Memory nova\n- loop\n")
        _append_ndjson(
            project_dir / "chat" / "threads" / "wizard-live.ndjson",
            {"timestamp": "2026-02-27T12:00:00+00:00", "author": "operator", "text": "hello"},
        )
        _append_ndjson(
            project_dir / "chat" / "global.ndjson",
            {"timestamp": "2026-02-27T12:01:00+00:00", "author": "system", "text": "ack"},
        )

        context_path = build_context_bridge(
            projects_root=projects_root,
            project_id=project_id,
            repo_path=repo_path,
            include_full_intake=True,
            trigger="test_context",
            operator_message="kickoff",
            l1_agents=["victor", "leo", "nova"],
        )
        assert context_path.exists()
        content = context_path.read_text(encoding="utf-8")
        assert "BMAD Stage Map" in content
        assert "brainstorm -> product brief -> prd -> architecture -> stories" in content
        assert "## Intake and Startup Artifacts" in content
        assert "## Agent Memories" in content
        assert "## Chat Digest (wizard-live thread)" in content

        context_path_2 = build_context_bridge(
            projects_root=projects_root,
            project_id=project_id,
            repo_path=repo_path,
            include_full_intake=False,
            trigger="test_context_short",
            operator_message="followup",
            l1_agents=["victor", "leo", "nova"],
        )
        assert context_path_2.exists()
        content_2 = context_path_2.read_text(encoding="utf-8")
        assert "include_full_intake: false" in content_2

    print("OK: wave19 wizard live context bridge verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
