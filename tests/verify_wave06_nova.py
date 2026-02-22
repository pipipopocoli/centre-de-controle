#!/usr/bin/env python3
"""Wave06 Nova verification: roster + mention parser."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import app.data.paths as paths  # noqa: E402
import app.data.store as store  # noqa: E402
from app.services.agent_registry import load_agent_registry, resolve_agent_platform  # noqa: E402
from app.services.chat_parser import parse_mentions  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        projects_root.mkdir(parents=True, exist_ok=True)

        paths.PROJECTS_DIR = projects_root
        store.PROJECTS_DIR = projects_root

        project_id = "cockpit"
        store.ensure_project_structure(project_id, "Cockpit")
        project = store.load_project(project_id)
        by_id = {agent.agent_id: agent for agent in project.agents}

        assert "nova" in by_id, "nova missing from project agents"
        assert by_id["nova"].level == 1
        assert by_id["nova"].lead_id == "clems"
        assert by_id["nova"].platform == "antigravity"
        assert by_id["nova"].role == "creative_science_lead"

        registry = load_agent_registry(project_id, projects_root)
        assert resolve_agent_platform("nova", registry) == "antigravity"

        # Legacy/backfill lock: missing nova in registry must be repaired by store defaults.
        registry_path = projects_root / project_id / "agents" / "registry.json"
        broken_registry = {key: value for key, value in registry.items() if key != "nova"}
        registry_path.write_text(
            json.dumps(
                {
                    key: {
                        "agent_id": value.agent_id,
                        "name": value.name,
                        "engine": value.engine,
                        "platform": value.platform,
                        "level": value.level,
                        "lead_id": value.lead_id,
                        "role": value.role,
                        "skills": list(value.skills),
                    }
                    for key, value in broken_registry.items()
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        project_backfill = store.load_project(project_id)
        backfill_by_id = {agent.agent_id: agent for agent in project_backfill.agents}
        assert "nova" in backfill_by_id, "nova should be backfilled into project agents"
        assert backfill_by_id["nova"].level == 1
        assert backfill_by_id["nova"].lead_id == "clems"
        assert backfill_by_id["nova"].platform == "antigravity"

        repaired_registry = load_agent_registry(project_id, projects_root)
        assert "nova" in repaired_registry, "nova should be restored in registry defaults"
        assert resolve_agent_platform("nova", repaired_registry) == "antigravity"

        # Missing default state file should be recreated on load.
        nova_state_path = projects_root / project_id / "agents" / "nova" / "state.json"
        assert nova_state_path.exists(), "nova state should exist after initial bootstrap"
        nova_state_path.unlink()
        assert not nova_state_path.exists(), "nova state should be deleted for regression setup"

        project_rehydrated = store.load_project(project_id)
        assert nova_state_path.exists(), "nova state should be recreated on load_project"
        nova_state_payload = json.loads(nova_state_path.read_text(encoding="utf-8"))
        assert str(nova_state_payload.get("agent_id") or "") == "nova"
        assert int(nova_state_payload.get("level") or -1) == 1
        assert str(nova_state_payload.get("lead_id") or "") == "clems"
        assert str(nova_state_payload.get("platform") or "") == "antigravity"

        rehydrated_by_id = {agent.agent_id: agent for agent in project_rehydrated.agents}
        assert "nova" in rehydrated_by_id, "nova should remain in loaded agents after state recreation"
        assert rehydrated_by_id["nova"].level == 1

        mentions = parse_mentions("Ping @nova @leo @agent-1 @unknown")
        assert "nova" in mentions
        assert "leo" in mentions
        assert "agent-1" in mentions
        assert "unknown" not in mentions

    print("OK: wave06 nova roster + mentions verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
