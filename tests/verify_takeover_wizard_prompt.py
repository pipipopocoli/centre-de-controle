from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services import takeover_wizard  # noqa: E402


def main() -> int:
    prompt = takeover_wizard._wizard_prompt(
        project_id="demo",
        repo_path=Path("/tmp/repo"),
        l1_agents=["victor", "leo", "nova"],
        intake={"project_name": "demo", "stack": ["python"], "risks": ["missing tests"]},
        plan={"summary": "test", "tasks": []},
        questions=["What is the goal?"],
    )
    assert "PROJECT LOCK: demo" in prompt
    assert "ASCII ONLY" in prompt
    assert "L1 agents: victor, leo, nova" in prompt
    assert "BMAD artifacts" in prompt
    print("OK: takeover wizard prompt verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

