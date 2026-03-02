from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.codex_runner import RunnerResult  # noqa: E402
from app.services.wizard_live import run_wizard_live_turn  # noqa: E402


def _fixture_payload(project_id: str, repo_path: Path) -> dict:
    return {
        "wizard_version": "wave19_test",
        "generated_at_utc": "2026-02-27T00:00:00Z",
        "project_id": project_id,
        "repo_path": str(repo_path),
        "trigger": "test_runner_flags",
        "agent_messages": [
            {
                "agent_id": "victor",
                "text": "Now:- backend Next:- service Blockers:- none",
                "now": ["backend"],
                "next": ["service"],
                "blockers": [],
                "state_update": {"phase": "Plan", "status": "planning", "current_task": "backend lane"},
            },
            {
                "agent_id": "leo",
                "text": "Now:- ui Next:- wire Blockers:- none",
                "now": ["ui"],
                "next": ["wire"],
                "blockers": [],
                "state_update": {"phase": "Plan", "status": "planning", "current_task": "ui lane"},
            },
            {
                "agent_id": "nova",
                "text": "Now:- research Next:- digest Blockers:- none owner: nova next_action: publish "
                "evidence_path: BMAD/ARCHITECTURE.md decision_tag: adopt",
                "now": ["research"],
                "next": ["digest"],
                "blockers": [],
                "state_update": {"phase": "Plan", "status": "planning", "current_task": "research lane"},
            },
            {
                "agent_id": "vulgarisation",
                "text": "Now:- simplify Next:- brief Blockers:- none",
                "now": ["simplify"],
                "next": ["brief"],
                "blockers": [],
                "state_update": {"phase": "Plan", "status": "planning", "current_task": "summary lane"},
            },
        ],
        "clems_summary": {
            "text": "Decision: keep guardrails and launch wave19.",
            "now": ["kickoff"],
            "next": ["first issue"],
            "blockers": [],
            "state_update": {"phase": "Plan", "status": "executing", "current_task": "wave19"},
        },
        "bmad": {
            "brainstorm_md": "# Brainstorm\n\n- idea\n",
            "product_brief_md": "# Product Brief\n\n- brief\n",
            "prd_md": "# PRD\n\n- req\n",
            "architecture_md": "# Architecture\n\n- arch\n",
            "stories_md": "# Stories\n\n- story\n",
        },
        "state_sections": {
            "phase": "Plan",
            "objective": "Runner flags test",
            "now": ["execute"],
            "next": ["verify"],
            "in_progress": [],
            "blockers": [],
            "risks": ["none"],
            "links": [],
        },
        "roadmap_sections": {"now": ["run"], "next": ["check"], "risks": ["none"]},
        "decisions_adrs": [],
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        projects_root = root / "projects"
        project_id = "demo"
        project_dir = projects_root / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        repo_path = root / "repo"
        repo_path.mkdir(parents=True, exist_ok=True)
        (repo_path / "README.md").write_text("# Demo\n", encoding="utf-8")

        captured: dict = {}
        payload = _fixture_payload(project_id, repo_path)

        def _fake_run_codex_exec(
            prompt: str,
            cwd: Path,
            timeout_s: int,
            *,
            sandbox_mode: str,
            approval_policy: str,
            output_schema_path: Path | None,
            output_last_message_path: Path | None,
            ephemeral: bool,
        ) -> RunnerResult:
            captured["prompt"] = prompt
            captured["cwd"] = cwd
            captured["sandbox_mode"] = sandbox_mode
            captured["approval_policy"] = approval_policy
            captured["output_schema_path"] = output_schema_path
            captured["output_last_message_path"] = output_last_message_path
            captured["ephemeral"] = ephemeral
            return RunnerResult(
                runner="codex",
                status="completed",
                success=True,
                launched=True,
                completed=True,
                returncode=0,
                stdout="ok",
                stderr="",
                error=None,
                started_at="2026-02-27T00:00:00+00:00",
                finished_at="2026-02-27T00:00:01+00:00",
                duration_seconds=1.0,
                output_path=str(output_last_message_path) if output_last_message_path is not None else "",
                output_text=json.dumps(payload),
            )

        with patch("app.services.wizard_live.run_codex_exec", side_effect=_fake_run_codex_exec):
            result = run_wizard_live_turn(
                projects_root=projects_root,
                project_id=project_id,
                repo_path=repo_path,
                trigger="test_runner_flags",
                operator_message="hello",
                include_full_intake=True,
                timeout_s=60,
                session_active=True,
            )

        assert result.status == "ok"
        assert captured.get("sandbox_mode") == "read-only"
        assert captured.get("approval_policy") == "never"
        assert captured.get("ephemeral") is True
        output_schema_path = captured.get("output_schema_path")
        assert isinstance(output_schema_path, Path)
        assert output_schema_path.name == "wizard_live_output.schema.json"

    print("OK: wave19 wizard live runner flags verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
