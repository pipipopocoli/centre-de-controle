#!/usr/bin/env python3
"""
Strict project routing verification for cockpit.post_message.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import ensure_demo_project  # noqa: E402
from control.mcp_server import PROJECT_ID_ERROR, TOOL_DEFINITIONS, handle_post_message  # noqa: E402


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8").splitlines())


async def _run() -> None:
    post_tool = next((tool for tool in TOOL_DEFINITIONS if tool.name == "cockpit.post_message"), None)
    assert post_tool is not None, "post_message tool definition missing"
    required = post_tool.inputSchema.get("required", [])
    assert "project_id" in required, "post_message schema must require project_id"

    project = ensure_demo_project()
    chat_path = project.path / "chat" / "global.ndjson"
    before = _line_count(chat_path)

    missing = await handle_post_message(
        {
            "agent_id": "test_agent",
            "content": "No project id",
            "metadata": {"project_id": "demo"},
        }
    )
    missing_payload = json.loads(missing[0].text)
    assert missing_payload.get("error") == PROJECT_ID_ERROR
    assert _line_count(chat_path) == before, "missing project_id should not write chat"

    mismatch = await handle_post_message(
        {
            "agent_id": "test_agent",
            "project_id": "demo",
            "content": "Mismatched metadata",
            "metadata": {"project_id": "cockpit"},
        }
    )
    mismatch_payload = json.loads(mismatch[0].text)
    assert mismatch_payload.get("error") == PROJECT_ID_ERROR
    assert _line_count(chat_path) == before, "mismatch should not write chat"

    ok = await handle_post_message(
        {
            "agent_id": "test_agent",
            "project_id": "demo",
            "content": "Valid strict message",
            "metadata": {"project_id": "demo"},
        }
    )
    ok_payload = json.loads(ok[0].text)
    assert ok_payload.get("status") == "posted"
    assert _line_count(chat_path) == before + 1, "valid message should write chat"


def main() -> int:
    asyncio.run(_run())
    print("OK verify_mcp_project_routing_strict")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
