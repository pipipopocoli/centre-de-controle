#!/usr/bin/env python3
"""Memory index verification (SQLite FTS5)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.memory_index import (  # noqa: E402
    build_agent_memory_indexes,
    build_index,
    search_memory,
)


def _append_ndjson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "cockpit"
        project_dir = projects_root / project_id

        (project_dir / "agents" / "clems").mkdir(parents=True, exist_ok=True)
        (project_dir / "agents" / "victor").mkdir(parents=True, exist_ok=True)

        (project_dir / "STATE.md").write_text(
            "# State\n\n## Now\n- Stabilize run loop\n",
            encoding="utf-8",
        )
        (project_dir / "ROADMAP.md").write_text(
            "# Roadmap\n\n## Risks\n- Dispatch latency spike\n",
            encoding="utf-8",
        )
        (project_dir / "DECISIONS.md").write_text(
            "# Decisions\n\n## ADR-101 Memory index FTS5\n- Status: Accepted\n",
            encoding="utf-8",
        )
        (project_dir / "agents" / "clems" / "memory.md").write_text(
            "# Memory - clems\n\n## Facts / Constraints\n- keep project lock\n",
            encoding="utf-8",
        )
        _append_ndjson(
            project_dir / "agents" / "victor" / "journal.ndjson",
            {
                "timestamp": "2026-02-13T12:00:00+00:00",
                "event": "reply_ack",
                "text": "run loop stabilized",
            },
        )

        report = build_index(project_id, projects_root=projects_root)
        assert report.docs_indexed > 0
        assert Path(report.db_path).exists()

        # CP-0004: deterministic memory.index.json for core roles
        agent_report_1 = build_agent_memory_indexes(project_id, projects_root=projects_root)
        assert agent_report_1.generated_count == 2, "expected indexes for clems and victor"
        assert all(Path(path).exists() for path in agent_report_1.agent_indexes)
        first_payloads = {
            path: Path(path).read_text(encoding="utf-8")
            for path in agent_report_1.agent_indexes
        }

        agent_report_2 = build_agent_memory_indexes(project_id, projects_root=projects_root)
        second_payloads = {
            path: Path(path).read_text(encoding="utf-8")
            for path in agent_report_2.agent_indexes
        }
        assert first_payloads == second_payloads, "agent memory indexes should be deterministic"

        hits_1 = search_memory(project_id, "run loop", limit=5, projects_root=projects_root)
        hits_2 = search_memory(project_id, "run loop", limit=5, projects_root=projects_root)
        assert hits_1, "expected at least one memory hit"
        assert hits_1 == hits_2, "search results should be deterministic"
        assert all("run" in (hit.snippet.lower() + hit.path.lower()) for hit in hits_1[:2])

        # Isolation check: another project should not return cockpit hits.
        other_project = projects_root / "evozina"
        other_project.mkdir(parents=True, exist_ok=True)
        build_index("evozina", projects_root=projects_root)
        other_hits = search_memory("evozina", "run loop", projects_root=projects_root)
        assert not other_hits, "cross-project retrieval must remain isolated"

        # Wave06 lock: incomplete registry must still include canonical nova core when directory exists.
        (project_dir / "agents" / "nova").mkdir(parents=True, exist_ok=True)
        (project_dir / "agents" / "registry.json").write_text(
            json.dumps(
                {
                    "clems": {
                        "agent_id": "clems",
                        "level": 0,
                        "engine": "CDX",
                        "platform": "codex",
                    },
                    "victor": {
                        "agent_id": "victor",
                        "level": 1,
                        "engine": "CDX",
                        "platform": "codex",
                    },
                }
            ),
            encoding="utf-8",
        )

        agent_report_3 = build_agent_memory_indexes(project_id, projects_root=projects_root)
        assert "nova" in agent_report_3.indexed_agents, "nova must be indexed from canonical core fallback"
        assert Path(project_dir / "agents" / "nova" / "memory.index.json").exists(), "nova memory index should exist"

    print("OK: memory index verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
