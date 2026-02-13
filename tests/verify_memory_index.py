#!/usr/bin/env python3
"""Memory index verification (SQLite FTS5)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.memory_index import build_index, search_memory  # noqa: E402


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

    print("OK: memory index verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
