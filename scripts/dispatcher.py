#!/usr/bin/env python3
"""
Run request dispatcher (local-first).

Reads control/projects/<id>/runs/requests.ndjson and writes per-agent inbox files:
  control/projects/<id>/runs/inbox/<agent_id>.ndjson

Dedupes by request_id using a state file to avoid re-dispatching.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PROJECT = "cockpit"
MAX_PROCESSED_IDS = 2000


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            items.append(payload)
    return items


def _append_ndjson(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _load_state(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []
    processed = payload.get("processed")
    if not isinstance(processed, list):
        return []
    return [str(item) for item in processed if str(item).strip()]


def _save_state(path: Path, processed: list[str]) -> None:
    trimmed = processed[-MAX_PROCESSED_IDS:]
    payload = {
        "processed": trimmed,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _dispatch_once(project_id: str, state_path: Path) -> dict[str, int]:
    requests_path = ROOT_DIR / "control" / "projects" / project_id / "runs" / "requests.ndjson"
    inbox_dir = ROOT_DIR / "control" / "projects" / project_id / "runs" / "inbox"

    processed = _load_state(state_path)
    processed_set = set(processed)

    dispatched = 0
    skipped = 0

    for payload in _read_ndjson(requests_path):
        request_id = str(payload.get("request_id") or "").strip()
        agent_id = str(payload.get("agent_id") or "").strip()
        source = str(payload.get("source") or "").strip()

        if not request_id or not agent_id:
            skipped += 1
            continue
        if source == "reminder":
            skipped += 1
            continue
        if request_id in processed_set:
            skipped += 1
            continue

        inbox_path = inbox_dir / f"{agent_id}.ndjson"
        _append_ndjson(inbox_path, payload)

        processed.append(request_id)
        processed_set.add(request_id)
        dispatched += 1

    _save_state(state_path, processed)

    return {"dispatched": dispatched, "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatch run requests into per-agent inbox files.")
    parser.add_argument("--project", default=None, help="Project id (default: COCKPIT_PROJECT_ID or cockpit)")
    parser.add_argument("--interval", type=float, default=5.0, help="Polling interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument(
        "--state-file",
        default=None,
        help="Custom dispatch state file path (default: runs/dispatch_state.json)",
    )

    args = parser.parse_args()
    project_id = args.project or os.environ.get("COCKPIT_PROJECT_ID") or DEFAULT_PROJECT

    if args.state_file:
        state_path = Path(args.state_file)
    else:
        state_path = ROOT_DIR / "control" / "projects" / project_id / "runs" / "dispatch_state.json"

    if args.once:
        stats = _dispatch_once(project_id, state_path)
        print(f"Dispatched: {stats['dispatched']} | Skipped: {stats['skipped']}")
        return 0

    while True:
        stats = _dispatch_once(project_id, state_path)
        if stats["dispatched"]:
            print(f"Dispatched: {stats['dispatched']} | Skipped: {stats['skipped']}")
        time.sleep(max(args.interval, 0.5))


if __name__ == "__main__":
    raise SystemExit(main())
