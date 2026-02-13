#!/usr/bin/env python3
"""Memory compaction verification."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from scripts.compact_memory import build_memory_proposal, write_memory_proposal  # noqa: E402


def _append_ndjson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        agent_id = "clems"
        project_dir = projects_root / project_id
        agent_dir = project_dir / "agents" / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)

        memory_path = agent_dir / "memory.md"
        memory_path.write_text(
            (
                "# Memory - clems\n\n"
                "## Role\n- Orchestrator\n\n"
                "## Facts / Constraints\n- Local first\n\n"
                "## Links\n- STATE.md\n"
            ),
            encoding="utf-8",
        )
        (project_dir / "STATE.md").write_text(
            "# State\n\n## Now\n- Stabilize run loop\n\n## Next\n- Ship V3.7\n\n## Blockers\n- None\n",
            encoding="utf-8",
        )
        (project_dir / "ROADMAP.md").write_text(
            "# Roadmap\n\n## Risks\n- Regression risk\n",
            encoding="utf-8",
        )
        (project_dir / "DECISIONS.md").write_text(
            "# Decisions\n\n## ADR-001 Runtime lock\n## ADR-002 Memory compaction\n",
            encoding="utf-8",
        )

        _append_ndjson(
            project_dir / "chat" / "global.ndjson",
            {
                "timestamp": "2026-02-13T12:00:00+00:00",
                "author": "operator",
                "text": "@victor run loop check",
                "mentions": ["victor"],
            },
        )
        _append_ndjson(
            agent_dir / "journal.ndjson",
            {
                "timestamp": "2026-02-13T12:01:00+00:00",
                "event": "mention",
                "from": "operator",
                "text": "Need follow-up",
            },
        )

        before = memory_path.read_text(encoding="utf-8")
        content1 = build_memory_proposal(project_id, agent_id, projects_root=projects_root)
        content2 = build_memory_proposal(project_id, agent_id, projects_root=projects_root)
        assert content1 == content2

        out_path = write_memory_proposal(project_id, agent_id, content1, projects_root=projects_root)
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

    print("OK: memory compaction verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
