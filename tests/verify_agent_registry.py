#!/usr/bin/env python3
"""Agent registry verification (L0/L1/L2 strict defaults + overrides)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import app.data.paths as paths  # noqa: E402
import app.data.store as store  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        projects_root.mkdir(parents=True, exist_ok=True)

        # Redirect store/paths to isolated temp root for this test.
        paths.PROJECTS_DIR = projects_root
        store.PROJECTS_DIR = projects_root

        project_id = "cockpit"
        store.ensure_project_structure(project_id, "Cockpit")
        store.ensure_agent_files(project_id, "agent-1", "agent-1", "CDX")
        store.ensure_agent_files(project_id, "agent-2", "agent-2", "AG")

        project = store.load_project(project_id)
        by_id = {agent.agent_id: agent for agent in project.agents}

        assert by_id["clems"].level == 0 and by_id["clems"].lead_id is None
        assert by_id["victor"].level == 1 and by_id["victor"].lead_id == "clems"
        assert by_id["leo"].level == 1 and by_id["leo"].lead_id == "clems"
        assert by_id["nova"].level == 1 and by_id["nova"].lead_id == "clems"
        assert by_id["nova"].role == "creative_science_lead"
        assert by_id["agent-1"].level == 2 and by_id["agent-1"].lead_id == "victor"
        assert by_id["agent-2"].level == 2 and by_id["agent-2"].lead_id == "leo"

        # Override one relationship and ensure save/load persistence.
        by_id["agent-2"].lead_id = "victor"
        by_id["agent-2"].role = "qa_specialist"
        store.save_project(project)
        reloaded = store.load_project(project_id)
        reload_map = {agent.agent_id: agent for agent in reloaded.agents}
        assert reload_map["agent-2"].lead_id == "victor"
        assert reload_map["agent-2"].role == "qa_specialist"

        registry_path = projects_root / project_id / "agents" / "registry.json"
        assert registry_path.exists()
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        assert registry["agent-2"]["lead_id"] == "victor"
        assert registry["agent-2"]["level"] == 2

    print("OK: agent registry verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
