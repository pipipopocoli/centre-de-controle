#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import load_runtime_state, resolve_projects_root  # noqa: E402

OPEN_STATUSES = {"queued", "dispatched", "reminded"}


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _write_ndjson(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _dedupe_keep_latest(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    kept_reversed: list[dict[str, Any]] = []
    for row in reversed(rows):
        request_id = str(row.get("request_id") or "").strip()
        if not request_id or request_id in seen:
            continue
        seen.add(request_id)
        kept_reversed.append(row)
    kept_reversed.reverse()
    return kept_reversed


def _backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_dir = path.parent / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    backup_path = archive_dir / f"{path.stem}_{timestamp}.ndjson"
    shutil.copy2(path, backup_path)
    return backup_path


def _status_for_request(runtime_requests: dict[str, dict[str, Any]], request_id: str) -> str:
    payload = runtime_requests.get(request_id)
    if not isinstance(payload, dict):
        return "closed"
    return str(payload.get("status") or "").strip().lower() or "closed"


def _prune_file(path: Path, runtime_requests: dict[str, dict[str, Any]], dry_run: bool) -> dict[str, Any]:
    rows = _read_ndjson(path)
    before = len(rows)

    open_rows = []
    for row in rows:
        request_id = str(row.get("request_id") or "").strip()
        if not request_id:
            continue
        status = _status_for_request(runtime_requests, request_id)
        if status in OPEN_STATUSES:
            open_rows.append(row)

    deduped = _dedupe_keep_latest(open_rows)
    after = len(deduped)

    backup_path = None
    if not dry_run:
        backup_path = _backup_file(path)
        _write_ndjson(path, deduped)

    return {
        "file": str(path),
        "before": before,
        "after": after,
        "removed": max(before - after, 0),
        "backup": str(backup_path) if backup_path else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune per-agent inbox NDJSON files using runtime open statuses.")
    parser.add_argument("--project", default="cockpit", help="Project id")
    parser.add_argument("--data-dir", default=None, help="Projects root. Special values: repo, app")
    parser.add_argument("--agent", default=None, help="Optional agent id, for example victor")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no write")
    args = parser.parse_args()

    projects_root = resolve_projects_root(args.data_dir)
    runtime = load_runtime_state(projects_root, args.project)
    runtime_requests = runtime.get("requests")
    if not isinstance(runtime_requests, dict):
        runtime_requests = {}

    inbox_dir = projects_root / args.project / "runs" / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    if args.agent:
        files = [inbox_dir / f"{args.agent}.ndjson"]
    else:
        files = sorted(inbox_dir.glob("*.ndjson"))

    summaries: list[dict[str, Any]] = []
    for path in files:
        if path.name == "archive":
            continue
        summaries.append(_prune_file(path, runtime_requests, dry_run=args.dry_run))

    payload = {
        "project": args.project,
        "projects_root": str(projects_root),
        "dry_run": bool(args.dry_run),
        "files": summaries,
        "total_before": sum(int(item.get("before") or 0) for item in summaries),
        "total_after": sum(int(item.get("after") or 0) for item in summaries),
        "total_removed": sum(int(item.get("removed") or 0) for item in summaries),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
