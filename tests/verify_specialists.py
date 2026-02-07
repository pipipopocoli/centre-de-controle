#!/usr/bin/env python3
"""Specialist Mentions Verification

Ensures @agent-N mentions are accepted and create run requests even when the agent
is not part of the roster yet.

This script is local-first and writes to a temporary COCKPIT_DATA_DIR.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


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
    tmp_root = Path(tempfile.mkdtemp(prefix="cockpit_specialists_"))
    projects_root = tmp_root / "projects"
    os.environ["COCKPIT_DATA_DIR"] = str(projects_root)

    root_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root_dir))

    try:
        from app.data.store import ensure_project_structure, record_mentions, run_requests_path  # noqa: E402
        from app.services.chat_parser import parse_mentions  # noqa: E402

        ensure_project_structure("demo", "Demo")

        text = "Ping @agent-1 et @clem"
        mentions = parse_mentions(text)
        assert "agent-1" in mentions, f"Expected agent-1 mention, got: {mentions}"
        assert "clems" in mentions, f"Expected clem -> clems alias, got: {mentions}"

        payload = {
            "message_id": "msg_test_specialists",
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "author": "operator",
            "text": text,
            "tags": [],
            "mentions": mentions,
        }
        record_mentions("demo", payload)

        reqs = _read_ndjson(run_requests_path("demo"))
        targets = {req.get("agent_id") for req in reqs if isinstance(req, dict)}
        assert "agent-1" in targets, f"Expected run request for agent-1, got: {sorted(targets)}"
        assert "clems" in targets, f"Expected run request for clems, got: {sorted(targets)}"

        agent1_dir = projects_root / "demo" / "agents" / "agent-1"
        assert not agent1_dir.exists(), "record_mentions should not auto-create agent directories"

        print("✅ Specialist mentions create run requests (no auto-create)")
        return 0
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
