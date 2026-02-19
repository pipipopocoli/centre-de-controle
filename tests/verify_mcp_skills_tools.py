#!/usr/bin/env python3
"""Verify MCP skills tools (ISSUE-CP-0005)."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import ensure_demo_project  # noqa: E402
from control.mcp_server import handle_list_skills_catalog, handle_sync_skills  # noqa: E402


async def _run() -> None:
    ensure_demo_project()

    listed = await handle_list_skills_catalog(
        {
            "agent_id": "test_agent",
            "project_id": "demo",
        }
    )
    listed_payload = json.loads(listed[0].text)
    listed_expected = {
        "project_id",
        "requested_by",
        "source",
        "skill_count",
        "catalog",
        "warnings",
        "cache_path",
        "timestamp",
        "status",
    }
    assert listed_expected.issubset(set(listed_payload.keys()))
    assert listed_payload.get("project_id") == "demo"
    assert isinstance(listed_payload.get("catalog"), list)
    assert "cache_path" in listed_payload

    dry_sync = await handle_sync_skills(
        {
            "agent_id": "test_agent",
            "project_id": "demo",
            "desired_skills": ["openai-docs", "skill-installer"],
            "dry_run": True,
        }
    )
    dry_payload = json.loads(dry_sync[0].text)
    sync_expected = {
        "requested_by",
        "requested_skills",
        "allowed_skills",
        "rejected_skills",
        "policy_events",
        "catalog_source",
        "catalog_warnings",
        "status",
        "error",
    }
    assert sync_expected.issubset(set(dry_payload.keys()))
    assert dry_payload.get("dry_run") is True
    assert dry_payload.get("requested") == 2
    assert dry_payload.get("status") in {"ok", "error"}
    assert "allowed_skills" in dry_payload
    assert "rejected_skills" in dry_payload

    unknown_sync = await handle_sync_skills(
        {
            "agent_id": "test_agent",
            "project_id": "demo",
            "desired_skills": ["unknown-skill"],
            "dry_run": True,
        }
    )
    unknown_payload = json.loads(unknown_sync[0].text)
    assert "unknown-skill" in unknown_payload.get("rejected_skills", [])
    assert unknown_payload.get("requested") == 0
    assert unknown_payload.get("would_install") == 0


def main() -> int:
    asyncio.run(_run())
    print("OK verify_mcp_skills_tools")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
