#!/usr/bin/env python3
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import load_project  # noqa: E402
from app.services.live_activity_feed import build_live_activity_feed  # noqa: E402


def _assert_feed_contract(feed: dict) -> None:
    assert isinstance(feed, dict), "feed must be object"
    assert str(feed.get("generated_at") or ""), "missing generated_at"
    assert str(feed.get("project_id") or ""), "missing project_id"
    assert str(feed.get("repo_source") or ""), "missing repo_source"

    code = feed.get("code")
    assert isinstance(code, dict), "missing code payload"
    repo_path = Path(str(code.get("repo_path") or ""))
    assert repo_path.exists(), f"repo path does not exist: {repo_path}"

    tasks = feed.get("tasks")
    assert isinstance(tasks, dict), "missing tasks payload"
    assert isinstance(tasks.get("now"), list), "tasks.now must be list"
    assert isinstance(tasks.get("next"), list), "tasks.next must be list"
    assert isinstance(tasks.get("blockers"), list), "tasks.blockers must be list"

    agents = feed.get("agents")
    assert isinstance(agents, dict), "missing agents payload"
    levels = agents.get("levels")
    assert isinstance(levels, dict), "missing levels"
    for key in (0, 1, 2):
        assert key in levels, f"missing level {key}"


def main() -> int:
    project = load_project("cockpit")

    feed_full = build_live_activity_feed(project, limit=20)
    _assert_feed_contract(feed_full)

    feed_cached_a = build_live_activity_feed(project, limit=20, include_code=False)
    feed_cached_b = build_live_activity_feed(project, limit=20, include_code=False)
    _assert_feed_contract(feed_cached_a)
    _assert_feed_contract(feed_cached_b)

    # Deterministic ordering for task lists when sources unchanged.
    assert (feed_cached_a.get("tasks") or {}).get("now") == (feed_cached_b.get("tasks") or {}).get("now")
    assert (feed_cached_a.get("tasks") or {}).get("next") == (feed_cached_b.get("tasks") or {}).get("next")

    # Fallback route when linked repo settings are absent/invalid.
    project_fallback = replace(project, settings={"linked_repo_path": "/tmp/path-that-does-not-exist"})
    fallback_feed = build_live_activity_feed(project_fallback, limit=10)
    _assert_feed_contract(fallback_feed)
    assert str(fallback_feed.get("repo_source") or "") == "workspace_fallback"

    print("OK: live activity feed contract + fallback verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
