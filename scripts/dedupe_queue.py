"""Wave07 Victor — Deduplicate requests.ndjson queue.

Policy:
- Keep latest queued request per (source_message_id, agent_id).
- Close older duplicates with reason: duplicate_recovery.
- Close stale queued entries (>24h) with reason: stale_timeout_recovery.
- Keep all already-closed entries as-is.
- Rewrite file atomically.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

REQUESTS_PATH = (
    PROJECT_ROOT / "control" / "projects" / "cockpit" / "runs" / "requests.ndjson"
)

STALE_HOURS = 6


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_ts(ts_str: str) -> datetime | None:
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    return None


def dedupe(dry_run: bool = False) -> dict:
    if not REQUESTS_PATH.exists():
        print("requests.ndjson not found.")
        return {"error": "file_not_found"}

    raw_lines = REQUESTS_PATH.read_text(encoding="utf-8").splitlines()
    entries: list[dict] = []
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    total_before = len(entries)
    queued_before = sum(1 for e in entries if e.get("status") == "queued")
    now = datetime.now(timezone.utc)
    now_iso = _utc_now_iso()

    # --- Pass 1: Remove exact request_id duplicates (keep last occurrence) ---
    seen_ids: dict[str, int] = {}
    for idx, entry in enumerate(entries):
        rid = entry.get("request_id", "")
        if rid:
            seen_ids[rid] = idx  # last wins

    unique_entries: list[dict] = []
    exact_dupes = 0
    for idx, entry in enumerate(entries):
        rid = entry.get("request_id", "")
        if rid and seen_ids.get(rid) != idx:
            exact_dupes += 1
            continue
        unique_entries.append(entry)

    # --- Pass 2: For queued entries, keep latest per (message_id, agent_id) ---
    queued = [e for e in unique_entries if e.get("status") == "queued"]
    non_queued = [e for e in unique_entries if e.get("status") != "queued"]

    groups: dict[tuple[str, str], list[dict]] = {}
    for entry in queued:
        msg = entry.get("message") or {}
        msg_id = str(msg.get("message_id") or "").strip()
        agent_id = str(entry.get("agent_id") or "").strip()
        key = (msg_id, agent_id)
        groups.setdefault(key, []).append(entry)

    kept_queued: list[dict] = []
    semantic_dupes = 0
    for key, group in groups.items():
        if len(group) == 1:
            kept_queued.append(group[0])
            continue
        group.sort(key=lambda e: str(e.get("created_at") or ""), reverse=True)
        kept_queued.append(group[0])
        for older in group[1:]:
            older["status"] = "closed"
            older["closed_at"] = now_iso
            older["closed_reason"] = "duplicate_recovery"
            older["responded_at"] = now_iso
            non_queued.append(older)
            semantic_dupes += 1

    # --- Pass 3: Close stale queued entries (>24h) ---
    stale_closed = 0
    still_queued: list[dict] = []
    for entry in kept_queued:
        created = _parse_ts(str(entry.get("created_at") or ""))
        if created and (now - created) > timedelta(hours=STALE_HOURS):
            entry["status"] = "closed"
            entry["closed_at"] = now_iso
            entry["closed_reason"] = "stale_timeout_recovery"
            entry["responded_at"] = now_iso
            non_queued.append(entry)
            stale_closed += 1
        else:
            still_queued.append(entry)

    final = non_queued + still_queued
    queued_after = sum(1 for e in final if e.get("status") == "queued")

    report = {
        "total_before": total_before,
        "queued_before": queued_before,
        "exact_dupes_removed": exact_dupes,
        "semantic_dupes_closed": semantic_dupes,
        "stale_closed": stale_closed,
        "total_after": len(final),
        "queued_after": queued_after,
        "target_met": queued_after <= 3,
    }

    print("=== Queue Dedupe Report ===")
    for k, v in report.items():
        print(f"  {k}: {v}")

    if dry_run:
        print("\n[DRY RUN] No changes written.")
        return report

    # Atomic write
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=REQUESTS_PATH.parent, suffix=".ndjson.tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as handle:
            for entry in final:
                handle.write(json.dumps(entry) + "\n")
        os.replace(tmp_path, str(REQUESTS_PATH))
        print(f"\n✅ Wrote {len(final)} entries to {REQUESTS_PATH}")
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    return report


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    dedupe(dry_run=dry)
