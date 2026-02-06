#!/usr/bin/env python3
"""Memory compaction verification."""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import ensure_demo_project  # noqa: E402
from scripts.compact_memory import build_memory_proposal, write_memory_proposal  # noqa: E402


def main() -> int:
    ensure_demo_project()
    project_id = "demo"
    agent_id = "clems"

    memory_path = ROOT_DIR / "control" / "projects" / project_id / "agents" / agent_id / "memory.md"
    before = memory_path.read_text(encoding="utf-8")

    content1 = build_memory_proposal(project_id, agent_id)
    content2 = build_memory_proposal(project_id, agent_id)
    assert content1 == content2

    out_path = write_memory_proposal(project_id, agent_id, content1)
    assert out_path.exists()
    assert out_path.read_text(encoding="utf-8") == content1

    after = memory_path.read_text(encoding="utf-8")
    assert before == after

    lines = content1.strip().splitlines()
    assert len(lines) <= 120

    required_sections = [
        "## Role",
        "## Facts / Constraints",
        "## Decisions (refs ADR)",
        "## Open Loops",
        "## Now",
        "## Next",
        "## Blockers",
        "## Links",
        "## Recent Signals (autogen, last 10)",
    ]
    for section in required_sections:
        assert section in content1

    print("✅ Memory compaction checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
