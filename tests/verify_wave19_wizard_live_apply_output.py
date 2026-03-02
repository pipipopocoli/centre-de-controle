from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.wizard_live import apply_wizard_live_output  # noqa: E402


def _read_ndjson(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        projects_root = root / "projects"
        project_id = "demo"
        project_dir = projects_root / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        payload = {
            "wizard_version": "wave19_test",
            "generated_at_utc": "2026-02-27T00:00:00Z",
            "project_id": project_id,
            "repo_path": "/tmp/repo",
            "trigger": "test_apply",
            "agent_messages": [
                {
                    "agent_id": "victor",
                    "text": "Now:\n- backend\nNext:\n- service\nBlockers:\n- none",
                    "now": ["backend"],
                    "next": ["service"],
                    "blockers": [],
                    "state_update": {"phase": "Plan", "status": "planning", "current_task": "backend lane"},
                },
                {
                    "agent_id": "leo",
                    "text": "Now:\n- ui\nNext:\n- wire\nBlockers:\n- none",
                    "now": ["ui"],
                    "next": ["wire"],
                    "blockers": [],
                    "state_update": {"phase": "Plan", "status": "planning", "current_task": "ui lane"},
                },
                {
                    "agent_id": "nova",
                    "text": "Now:\n- research\nNext:\n- digest\nBlockers:\n- none\nowner: nova\nnext_action: publish\n"
                    "evidence_path: BMAD/ARCHITECTURE.md\ndecision_tag: adopt",
                    "now": ["research"],
                    "next": ["digest"],
                    "blockers": [],
                    "state_update": {"phase": "Plan", "status": "planning", "current_task": "research lane"},
                },
                {
                    "agent_id": "vulgarisation",
                    "text": "Now:\n- simplify\nNext:\n- operator brief\nBlockers:\n- none",
                    "now": ["simplify"],
                    "next": ["operator brief"],
                    "blockers": [],
                    "state_update": {"phase": "Plan", "status": "planning", "current_task": "summary lane"},
                },
            ],
            "clems_summary": {
                "text": "Decision: start with backend and keep guardrails active.",
                "now": ["launch wizard live"],
                "next": ["open first delivery issue"],
                "blockers": [],
                "state_update": {"phase": "Plan", "status": "executing", "current_task": "Wave19 wizard live"},
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
                "objective": "Apply output test",
                "now": ["write docs"],
                "next": ["verify"],
                "in_progress": [],
                "blockers": [],
                "risks": ["drift"],
                "links": ["BMAD/PRD.md"],
            },
            "roadmap_sections": {"now": ["wave19"], "next": ["run"], "risks": ["cost"]},
            "decisions_adrs": [
                {
                    "title": "2026-02-27 - ADR-TST-002 Apply output",
                    "status": "Accepted",
                    "context": "Need deterministic apply output test",
                    "decision": "add test fixture",
                    "rationale": "confidence",
                    "consequences": ["coverage"],
                    "owners": ["clems"],
                    "references": ["tests/verify_wave19_wizard_live_apply_output.py"],
                }
            ],
        }

        result = apply_wizard_live_output(
            projects_root=projects_root,
            project_id=project_id,
            output_payload=payload,
            run_id="WIZARD_LIVE_2026-02-27T0000Z",
            repo_path=Path("/tmp/repo"),
            trigger="test_apply",
            operator_message="kickoff",
            prompt_path=None,
            context_path=None,
            runner=None,
            session_active=True,
        )
        assert result.status == "ok"

        bmad_dir = project_dir / "BMAD"
        assert (bmad_dir / "BRAINSTORM.md").exists()
        assert (bmad_dir / "PRODUCT_BRIEF.md").exists()
        assert (bmad_dir / "PRD.md").exists()
        assert (bmad_dir / "ARCHITECTURE.md").exists()
        assert (bmad_dir / "STORIES.md").exists()

        assert (project_dir / "STATE.md").exists()
        assert (project_dir / "ROADMAP.md").exists()
        assert (project_dir / "DECISIONS.md").exists()

        chat_rows = _read_ndjson(project_dir / "chat" / "global.ndjson")
        authors = {str(item.get("author") or "") for item in chat_rows}
        assert {"victor", "leo", "nova", "vulgarisation", "clems", "system"} <= authors

        for agent_id in ["victor", "leo", "nova", "vulgarisation", "clems"]:
            state_path = project_dir / "agents" / agent_id / "state.json"
            assert state_path.exists()
            state_payload = json.loads(state_path.read_text(encoding="utf-8"))
            assert state_payload.get("heartbeat")
            assert state_payload.get("updated_at")

        assert Path(result.output_json_path).exists()
        assert Path(result.output_md_path).exists()

    print("OK: wave19 wizard live apply output verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
