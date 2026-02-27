from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.takeover_wizard import apply_takeover_wizard_output  # noqa: E402


def _read_ndjson(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        payload = json.loads(raw)
        if isinstance(payload, dict):
            out.append(payload)
    return out


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "demo"
        project_dir = projects_root / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        run_id = "TAKEOVER_WIZARD_2026-02-27T0000Z"
        output_payload = {
            "wizard_version": "test",
            "generated_at_utc": "2026-02-27T00:00:00Z",
            "project_id": project_id,
            "repo_path": "/tmp/repo",
            "agent_messages": [
                {
                    "agent_id": "victor",
                    "text": "Now:\n- Triage\n\nNext:\n- Intake\n\nBlockers:\n- None",
                    "now": ["Triage"],
                    "next": ["Intake"],
                    "blockers": [],
                    "state_update": {"phase": "Plan", "status": "planning", "current_task": "Kickoff backend lane"},
                },
                {
                    "agent_id": "leo",
                    "text": "Now:\n- UI scan\n\nNext:\n- Tokens\n\nBlockers:\n- None",
                    "now": ["UI scan"],
                    "next": ["Tokens"],
                    "blockers": [],
                    "state_update": {"phase": "Plan", "status": "planning", "current_task": "Kickoff UI lane"},
                },
                {
                    "agent_id": "nova",
                    "text": "Now:\n- Research\n\nNext:\n- Evidence pack\n\nBlockers:\n- None\n\nDeep research item:\n- owner: nova\n- next_action: list sources\n- evidence_path: BMAD/ARCHITECTURE.md\n- decision_tag: adopt",
                    "now": ["Research"],
                    "next": ["Evidence pack"],
                    "blockers": [],
                    "state_update": {"phase": "Plan", "status": "planning", "current_task": "Kickoff research lane"},
                },
            ],
            "bmad": {
                "product_brief_md": "# Product Brief\n\n- Goal: test\n",
                "prd_md": "# PRD\n\n- Requirement: test\n",
                "architecture_md": "# Architecture\n\n- Choice: test\n",
                "stories_md": "# Stories\n\n- Story: test\n",
            },
            "state_sections": {
                "phase": "Plan",
                "objective": "Takeover test",
                "now": ["Run wizard apply"],
                "next": ["Review BMAD docs"],
                "in_progress": [],
                "blockers": [],
                "risks": ["Schema drift"],
                "links": ["BMAD/PRODUCT_BRIEF.md"],
            },
            "roadmap_sections": {
                "now": ["Wizard apply"],
                "next": ["Kickoff issues"],
                "risks": ["Cost burn"],
            },
            "decisions_adrs": [
                {
                    "title": "2026-02-27 - ADR-TW-000 Test decision",
                    "status": "Accepted",
                    "context": "Need deterministic apply test",
                    "decision": "Add verify script",
                    "rationale": "Confidence",
                    "consequences": ["More coverage"],
                    "owners": ["clems"],
                    "references": ["tests/verify_takeover_wizard_output_apply.py"],
                }
            ],
        }

        result = apply_takeover_wizard_output(
            projects_root=projects_root,
            project_id=project_id,
            output_payload=output_payload,
            run_id=run_id,
            repo_path=Path("/tmp/repo"),
            prompt_path=None,
            runner=None,
        )
        assert result.status == "ok"

        bmad_dir = project_dir / "BMAD"
        assert (bmad_dir / "PRODUCT_BRIEF.md").exists()
        assert (bmad_dir / "PRD.md").exists()
        assert (bmad_dir / "ARCHITECTURE.md").exists()
        assert (bmad_dir / "STORIES.md").exists()

        assert (project_dir / "STATE.md").exists()
        assert (project_dir / "ROADMAP.md").exists()
        assert (project_dir / "DECISIONS.md").exists()

        decisions_text = (project_dir / "DECISIONS.md").read_text(encoding="utf-8")
        assert "ADR-TW-000" in decisions_text

        global_chat = _read_ndjson(project_dir / "chat" / "global.ndjson")
        authors = {str(item.get("author") or "") for item in global_chat}
        assert {"victor", "leo", "nova", "system"} <= authors

        victor_state = json.loads((project_dir / "agents" / "victor" / "state.json").read_text(encoding="utf-8"))
        assert victor_state.get("phase") == "Plan"
        assert victor_state.get("status") == "planning"
        assert "Kickoff" in str(victor_state.get("current_task") or "")

        assert Path(result.output_json_path).exists()
        assert Path(result.output_md_path).exists()

    print("OK: takeover wizard output apply verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

