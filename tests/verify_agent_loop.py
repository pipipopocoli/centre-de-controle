#!/usr/bin/env python3
"""
Agent Loop E2E Verification
===========================
Ensures a mention creates a run request record and an agent reply lands in chat.
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import ensure_demo_project, run_requests_path  # noqa: E402
from control.mcp_server import handle_post_message  # noqa: E402


def _read_ndjson(path: Path) -> list[dict]:
    if not path.exists():
        return []
    items: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            items.append(payload)
    return items


def main() -> int:
    ensure_demo_project()

    req_path = run_requests_path("demo")
    before = _read_ndjson(req_path)

    asyncio.run(
        handle_post_message(
            {
                "agent_id": "operator",
                "content": "Ping @leo",
                "metadata": {"project_id": "demo"},
            }
        )
    )

    after = _read_ndjson(req_path)
    new_entries = after[len(before) :]
    assert new_entries, "Expected a run request entry"
    entry = new_entries[-1]
    assert entry.get("agent_id") == "leo"
    assert entry.get("status") == "queued"
    assert entry.get("source") == "mention"

    asyncio.run(
        handle_post_message(
            {
                "agent_id": "leo",
                "content": "Ack from Leo",
                "metadata": {"project_id": "demo"},
            }
        )
    )

    global_path = ROOT_DIR / "control" / "projects" / "demo" / "chat" / "global.ndjson"
    messages = _read_ndjson(global_path)
    assert messages, "Expected chat messages"
    last = messages[-1]
    assert last.get("author") == "leo"

    print("✅ Agent loop e2e check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
