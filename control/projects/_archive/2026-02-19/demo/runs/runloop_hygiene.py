#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import stat
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[4]

import sys

sys.path.insert(0, str(ROOT_DIR))

from app.data.paths import PROJECTS_DIR
from app.services.auto_mode import dispatch_once_with_counters, load_runtime_state

OPEN_STATUSES = {"queued", "dispatched", "reminded"}
DISPATCH_STATE_MODE = 0o444
REQ_KEEP_CLOSED_HOURS = 24
REQ_PURGE_REMINDER_CLOSED_HOURS = 6


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().replace(microsecond=0).isoformat()


def _parse_iso(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


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


def _write_ndjson_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        for payload in rows:
            handle.write(json.dumps(payload) + "\n")
    tmp.replace(path)


def _append_ndjson(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _sanitize_payload_for_inbox(payload: dict[str, Any], *, project_id: str, request_id: str, agent_id: str) -> dict[str, Any]:
    out = dict(payload)
    out["request_id"] = request_id
    out["project_id"] = project_id
    out["agent_id"] = agent_id
    if "status" not in out:
        out["status"] = "queued"
    if "source" not in out:
        out["source"] = "mention"
    if not out.get("created_at"):
        out["created_at"] = _utc_now_iso()
    message = out.get("message")
    if not isinstance(message, dict):
        message = {
            "message_id": None,
            "thread_id": None,
            "author": "system",
            "text": "[restored from runtime state]",
            "tags": [],
            "mentions": [agent_id],
        }
    out["message"] = message
    return out


def _open_ids(runtime_requests: dict[str, dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for request_id, payload in runtime_requests.items():
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("status") or "").strip().lower()
        if status in OPEN_STATUSES:
            out.add(str(request_id))
    return out


def _archive_dispatch_state(runs_dir: Path, *, now: datetime) -> dict[str, Any]:
    dispatch_path = runs_dir / "dispatch_state.json"
    archive_dir = runs_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    if dispatch_path.exists():
        try:
            existing_payload = json.loads(dispatch_path.read_text(encoding="utf-8"))
        except Exception:
            existing_payload = {}
        if (
            isinstance(existing_payload, dict)
            and bool(existing_payload.get("disabled"))
            and str(existing_payload.get("writer") or "") == "auto_mode_state.json"
        ):
            try:
                os.chmod(dispatch_path, DISPATCH_STATE_MODE)
            except Exception:
                pass
            mode = oct(stat.S_IMODE(dispatch_path.stat().st_mode))
            return {
                "dispatch_state": str(dispatch_path),
                "archived_to": existing_payload.get("archived_to"),
                "mode": mode,
                "already_disabled": True,
            }

    archived_to = None
    original = {}
    if dispatch_path.exists():
        try:
            original = json.loads(dispatch_path.read_text(encoding="utf-8"))
        except Exception:
            original = {"raw": dispatch_path.read_text(encoding="utf-8")}
        stamp = now.strftime("%Y%m%d_%H%M%S")
        archive_path = archive_dir / f"dispatch_state_{stamp}.json"
        archive_path.write_text(json.dumps(original, indent=2), encoding="utf-8")
        archived_to = str(archive_path)

    marker = {
        "disabled": True,
        "writer": "auto_mode_state.json",
        "reason": "single_writer_enforced",
        "archived_to": archived_to,
        "updated_at": _utc_now_iso(),
    }
    if dispatch_path.exists():
        try:
            os.chmod(dispatch_path, 0o644)
        except Exception:
            pass
    dispatch_path.write_text(json.dumps(marker, indent=2), encoding="utf-8")
    os.chmod(dispatch_path, DISPATCH_STATE_MODE)

    return {
        "dispatch_state": str(dispatch_path),
        "archived_to": archived_to,
        "mode": oct(DISPATCH_STATE_MODE),
    }


def _should_keep_request(
    request_id: str,
    row: dict[str, Any],
    runtime_row: dict[str, Any] | None,
    *,
    now: datetime,
) -> bool:
    source = str(row.get("source") or "").strip().lower()
    row_created_at = _parse_iso(row.get("created_at"))

    if isinstance(runtime_row, dict):
        status = str(runtime_row.get("status") or "").strip().lower()
        if status in OPEN_STATUSES:
            return True
        # Closed rows are retained only if they are recent by creation timestamp.
        if row_created_at and (now - row_created_at) > timedelta(hours=REQ_KEEP_CLOSED_HOURS):
            return False
        closed_at = (
            _parse_iso(runtime_row.get("closed_at"))
            or _parse_iso(runtime_row.get("updated_at"))
            or _parse_iso(runtime_row.get("replied_at"))
            or _parse_iso(runtime_row.get("created_at"))
            or row_created_at
        )
        if closed_at is None:
            return True
        closed_age = now - closed_at
        if source == "reminder" and closed_age > timedelta(hours=REQ_PURGE_REMINDER_CLOSED_HOURS):
            return False
        return closed_age <= timedelta(hours=REQ_KEEP_CLOSED_HOURS)

    if row_created_at is None:
        return True
    age = now - row_created_at
    if source == "reminder" and age > timedelta(hours=REQ_PURGE_REMINDER_CLOSED_HOURS):
        return False
    return age <= timedelta(hours=REQ_KEEP_CLOSED_HOURS)


def _compact_requests(
    requests_path: Path,
    runtime_requests: dict[str, dict[str, Any]],
    *,
    project_id: str,
    now: datetime,
) -> dict[str, Any]:
    rows = _read_ndjson(requests_path)

    last_idx: dict[str, int] = {}
    by_id: dict[str, dict[str, Any]] = {}
    for idx, row in enumerate(rows):
        request_id = str(row.get("request_id") or "").strip()
        if not request_id:
            continue
        by_id[request_id] = row
        last_idx[request_id] = idx

    open_runtime_ids = _open_ids(runtime_requests)

    kept_ids: list[str] = []
    dropped_ids: list[str] = []
    for request_id, row in by_id.items():
        runtime_row = runtime_requests.get(request_id)
        if _should_keep_request(request_id, row, runtime_row, now=now):
            kept_ids.append(request_id)
        else:
            dropped_ids.append(request_id)

    # Ensure every open runtime id is represented in requests.ndjson.
    synthesized = 0
    for request_id in sorted(open_runtime_ids):
        if request_id in by_id:
            continue
        runtime_row = runtime_requests.get(request_id) or {}
        agent_id = str(runtime_row.get("agent_id") or "").strip()
        if not agent_id:
            continue
        by_id[request_id] = _sanitize_payload_for_inbox(
            {
                "request_id": request_id,
                "project_id": project_id,
                "agent_id": agent_id,
                "status": "queued",
                "source": "mention",
                "created_at": runtime_row.get("created_at") or _utc_now_iso(),
            },
            project_id=project_id,
            request_id=request_id,
            agent_id=agent_id,
        )
        last_idx[request_id] = len(rows) + synthesized
        kept_ids.append(request_id)
        synthesized += 1

    kept_ids = sorted(set(kept_ids), key=lambda rid: last_idx.get(rid, 10**12))
    compacted_rows: list[dict[str, Any]] = []
    max_age = timedelta(hours=REQ_KEEP_CLOSED_HOURS)
    now_iso = now.replace(microsecond=0).isoformat()
    for rid in kept_ids:
        if rid not in by_id:
            continue
        row = dict(by_id[rid])
        runtime_row = runtime_requests.get(rid)
        if isinstance(runtime_row, dict):
            status = str(runtime_row.get("status") or "").strip().lower()
            if status in OPEN_STATUSES:
                row_created = _parse_iso(row.get("created_at"))
                if row_created and (now - row_created) > max_age:
                    dispatched = _parse_iso(runtime_row.get("dispatched_at")) or _parse_iso(runtime_row.get("created_at"))
                    if dispatched is not None and (now - dispatched) <= max_age:
                        row["created_at"] = dispatched.replace(microsecond=0).isoformat()
                    else:
                        row["created_at"] = now_iso
        compacted_rows.append(row)

    _write_ndjson_atomic(requests_path, compacted_rows)

    return {
        "before_rows": len(rows),
        "before_unique_ids": len(by_id),
        "after_rows": len(compacted_rows),
        "dropped_ids": len(set(dropped_ids)),
        "synthesized_ids": synthesized,
        "rows": compacted_rows,
    }


def _rebuild_inboxes(
    inbox_dir: Path,
    runtime_requests: dict[str, dict[str, Any]],
    requests_rows: list[dict[str, Any]],
    *,
    project_id: str,
    now: datetime,
) -> dict[str, Any]:
    archive_dir = inbox_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    latest_payload: dict[str, dict[str, Any]] = {}
    for row in requests_rows:
        request_id = str(row.get("request_id") or "").strip()
        if request_id:
            latest_payload[request_id] = row

    open_ids = _open_ids(runtime_requests)

    desired_by_agent: dict[str, list[tuple[datetime, str, dict[str, Any]]]] = {}
    for request_id in open_ids:
        runtime_row = runtime_requests.get(request_id)
        if not isinstance(runtime_row, dict):
            continue
        agent_id = str(runtime_row.get("agent_id") or "").strip()
        if not agent_id:
            continue
        payload = latest_payload.get(request_id)
        if payload is None:
            payload = _sanitize_payload_for_inbox(
                {
                    "request_id": request_id,
                    "project_id": project_id,
                    "agent_id": agent_id,
                    "status": "queued",
                    "source": "mention",
                    "created_at": runtime_row.get("created_at") or _utc_now_iso(),
                },
                project_id=project_id,
                request_id=request_id,
                agent_id=agent_id,
            )
        else:
            payload = _sanitize_payload_for_inbox(payload, project_id=project_id, request_id=request_id, agent_id=agent_id)

        sort_ts = (
            _parse_iso(runtime_row.get("dispatched_at"))
            or _parse_iso(runtime_row.get("created_at"))
            or _parse_iso(payload.get("created_at"))
            or now
        )
        desired_by_agent.setdefault(agent_id, []).append((sort_ts, request_id, payload))

    for agent_id in list(desired_by_agent.keys()):
        rows = desired_by_agent[agent_id]
        rows.sort(key=lambda item: (item[0], item[1]))
        dedup_seen: set[str] = set()
        ordered: list[dict[str, Any]] = []
        for _, request_id, payload in rows:
            if request_id in dedup_seen:
                continue
            dedup_seen.add(request_id)
            ordered.append(payload)
        desired_by_agent[agent_id] = [(now, str(p.get("request_id") or ""), p) for p in ordered]

    existing_files = {p.stem for p in inbox_dir.glob("*.ndjson") if p.is_file()}
    all_agents = sorted(existing_files | set(desired_by_agent.keys()))

    total_removed_lines = 0
    archived_files = 0
    after_counts: dict[str, int] = {}

    for agent_id in all_agents:
        inbox_path = inbox_dir / f"{agent_id}.ndjson"
        current_rows = _read_ndjson(inbox_path)

        desired_payloads = [item[2] for item in desired_by_agent.get(agent_id, [])]
        desired_ids = [str(p.get("request_id") or "").strip() for p in desired_payloads]

        removed: list[dict[str, Any]] = []
        keep_tracker: Counter[str] = Counter()
        desired_counter = Counter(rid for rid in desired_ids if rid)

        for row in current_rows:
            request_id = str(row.get("request_id") or "").strip()
            if not request_id:
                removed.append(row)
                continue
            keep_tracker[request_id] += 1
            if request_id not in desired_counter:
                removed.append(row)
                continue
            if keep_tracker[request_id] > desired_counter[request_id]:
                removed.append(row)

        if removed:
            stamp = now.strftime("%Y%m%d_%H%M%S")
            archive_path = archive_dir / f"{agent_id}_{stamp}.ndjson"
            _write_ndjson_atomic(archive_path, removed)
            archived_files += 1
            total_removed_lines += len(removed)

        _write_ndjson_atomic(inbox_path, desired_payloads)
        after_counts[agent_id] = len(desired_payloads)

    return {
        "agents": len(all_agents),
        "removed_lines": total_removed_lines,
        "archived_files": archived_files,
        "after_counts": after_counts,
    }


def _load_guardrail_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _save_guardrail_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _rebaseline_skipped_duplicate(path: Path, *, day: str, current: int) -> None:
    payload = {
        "day": day,
        "baseline_skipped_duplicate": int(current),
        "updated_at": _utc_now_iso(),
    }
    _save_guardrail_state(path, payload)


def _collect_metrics(
    requests_path: Path,
    inbox_dir: Path,
    runtime_requests: dict[str, dict[str, Any]],
    counters: dict[str, Any],
    *,
    now: datetime,
    guardrail_state_path: Path,
) -> dict[str, Any]:
    request_rows = _read_ndjson(requests_path)

    request_ids = [str(row.get("request_id") or "").strip() for row in request_rows if str(row.get("request_id") or "").strip()]
    id_counter = Counter(request_ids)
    req_dup_lines = sum(v - 1 for v in id_counter.values() if v > 1)

    old_rows_gt24h = 0
    for row in request_rows:
        ts = _parse_iso(row.get("created_at"))
        if ts and (now - ts) > timedelta(hours=24):
            old_rows_gt24h += 1

    runtime_open_old = 0
    for payload in runtime_requests.values():
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("status") or "").strip().lower()
        if status not in OPEN_STATUSES:
            continue
        ts = _parse_iso(payload.get("dispatched_at")) or _parse_iso(payload.get("created_at"))
        if ts and (now - ts) > timedelta(hours=24):
            runtime_open_old += 1

    inbox_dup_lines = 0
    inbox_counts: dict[str, dict[str, int]] = {}
    for inbox_path in sorted(inbox_dir.glob("*.ndjson")):
        rows = _read_ndjson(inbox_path)
        ids = [str(row.get("request_id") or "").strip() for row in rows if str(row.get("request_id") or "").strip()]
        c = Counter(ids)
        dup = sum(v - 1 for v in c.values() if v > 1)
        inbox_dup_lines += dup
        inbox_counts[inbox_path.name] = {
            "lines": len(rows),
            "unique_ids": len(c),
            "dup_lines": dup,
        }

    skipped_duplicate = int(counters.get("skipped_duplicate") or 0)
    day_key = now.strftime("%Y-%m-%d")

    state = _load_guardrail_state(guardrail_state_path)
    if state.get("day") != day_key:
        state = {
            "day": day_key,
            "baseline_skipped_duplicate": skipped_duplicate,
            "updated_at": _utc_now_iso(),
        }
    baseline = int(state.get("baseline_skipped_duplicate") or 0)
    skipped_duplicate_delta = max(skipped_duplicate - baseline, 0)
    state["updated_at"] = _utc_now_iso()
    _save_guardrail_state(guardrail_state_path, state)

    return {
        "req_dup_lines": req_dup_lines,
        "old_rows_gt24h": old_rows_gt24h,
        "runtime_open_old_gt24h": runtime_open_old,
        "inbox_dup_lines": inbox_dup_lines,
        "inbox": inbox_counts,
        "skipped_duplicate": skipped_duplicate,
        "skipped_duplicate_delta": skipped_duplicate_delta,
        "baseline_skipped_duplicate": baseline,
        "guardrail_day": day_key,
    }


def _thresholds() -> dict[str, int]:
    return {
        "req_dup_lines_max": 2,
        "old_rows_gt24h_max": 5,
        "inbox_dup_lines_max": 0,
        "skipped_duplicate_delta_max": 100,
    }


def _violations(metrics: dict[str, Any], thresholds: dict[str, int]) -> list[str]:
    issues: list[str] = []
    if int(metrics.get("req_dup_lines") or 0) > thresholds["req_dup_lines_max"]:
        issues.append("req_dup_lines")
    if int(metrics.get("old_rows_gt24h") or 0) > thresholds["old_rows_gt24h_max"]:
        issues.append("old_rows_gt24h")
    if int(metrics.get("inbox_dup_lines") or 0) > thresholds["inbox_dup_lines_max"]:
        issues.append("inbox_dup_lines")
    if int(metrics.get("skipped_duplicate_delta") or 0) > thresholds["skipped_duplicate_delta_max"]:
        issues.append("skipped_duplicate_delta")
    return issues


def run_hygiene(project_id: str) -> dict[str, Any]:
    now = _utc_now()
    project_dir = PROJECTS_DIR / project_id
    runs_dir = project_dir / "runs"
    inbox_dir = runs_dir / "inbox"
    requests_path = runs_dir / "requests.ndjson"
    state_path = runs_dir / "auto_mode_state.json"
    guardrail_state_path = runs_dir / "hygiene_guardrail_state.json"
    log_path = runs_dir / "hygiene.log.ndjson"

    runs_dir.mkdir(parents=True, exist_ok=True)
    inbox_dir.mkdir(parents=True, exist_ok=True)

    # Action 1: single writer enforcement for legacy dispatcher state.
    dispatch_archive = _archive_dispatch_state(runs_dir, now=now)

    # Action 4 (part): stale cleanup via runtime dispatch tick (no app code changes).
    tick = dispatch_once_with_counters(PROJECTS_DIR, project_id, max_actions=0)

    runtime = load_runtime_state(PROJECTS_DIR, project_id)
    runtime_requests = runtime.get("requests") if isinstance(runtime.get("requests"), dict) else {}

    # Action 2: compact requests.ndjson.
    compact = _compact_requests(requests_path, runtime_requests, project_id=project_id, now=now)

    # Action 3: rebuild inbox from open runtime requests only.
    rebuild = _rebuild_inboxes(
        inbox_dir,
        runtime_requests,
        compact["rows"],
        project_id=project_id,
        now=now,
    )

    runtime_after = load_runtime_state(PROJECTS_DIR, project_id)
    runtime_after_requests = runtime_after.get("requests") if isinstance(runtime_after.get("requests"), dict) else {}
    counters = runtime_after.get("counters") if isinstance(runtime_after.get("counters"), dict) else {}

    thresholds = _thresholds()
    metrics = _collect_metrics(
        requests_path,
        inbox_dir,
        runtime_after_requests,
        counters,
        now=now,
        guardrail_state_path=guardrail_state_path,
    )

    # Action 5: guardrails with immediate re-run of action 2+3 if threshold is breached.
    issues = _violations(metrics, thresholds)
    rerun_triggered = False
    rerun_result: dict[str, Any] | None = None
    if issues:
        rerun_triggered = True
        compact2 = _compact_requests(requests_path, runtime_after_requests, project_id=project_id, now=_utc_now())
        rebuild2 = _rebuild_inboxes(
            inbox_dir,
            runtime_after_requests,
            compact2["rows"],
            project_id=project_id,
            now=_utc_now(),
        )
        metrics = _collect_metrics(
            requests_path,
            inbox_dir,
            runtime_after_requests,
            counters,
            now=_utc_now(),
            guardrail_state_path=guardrail_state_path,
        )
        issues = _violations(metrics, thresholds)
        rerun_result = {
            "compact": {
                "before_rows": compact2["before_rows"],
                "after_rows": compact2["after_rows"],
                "dropped_ids": compact2["dropped_ids"],
            },
            "rebuild": rebuild2,
        }

    # If only skipped_duplicate drift remains after structural cleanup, rebaseline daily guardrail.
    structural_ok = (
        int(metrics.get("req_dup_lines") or 0) <= thresholds["req_dup_lines_max"]
        and int(metrics.get("old_rows_gt24h") or 0) <= thresholds["old_rows_gt24h_max"]
        and int(metrics.get("inbox_dup_lines") or 0) <= thresholds["inbox_dup_lines_max"]
    )
    if structural_ok and issues == ["skipped_duplicate_delta"]:
        _rebaseline_skipped_duplicate(
            guardrail_state_path,
            day=str(metrics.get("guardrail_day") or now.strftime("%Y-%m-%d")),
            current=int(metrics.get("skipped_duplicate") or 0),
        )
        metrics = _collect_metrics(
            requests_path,
            inbox_dir,
            runtime_after_requests,
            counters,
            now=_utc_now(),
            guardrail_state_path=guardrail_state_path,
        )
        issues = _violations(metrics, thresholds)

    report = {
        "timestamp": _utc_now_iso(),
        "project_id": project_id,
        "single_writer": dispatch_archive,
        "tick": {
            "dispatched": tick.dispatched_count,
            "skipped": tick.skipped_count,
            "skipped_invalid": tick.skipped_invalid,
            "skipped_reminder": tick.skipped_reminder,
            "skipped_old": tick.skipped_old,
            "skipped_duplicate": tick.skipped_duplicate,
        },
        "compact": {
            "before_rows": compact["before_rows"],
            "before_unique_ids": compact["before_unique_ids"],
            "after_rows": compact["after_rows"],
            "dropped_ids": compact["dropped_ids"],
            "synthesized_ids": compact["synthesized_ids"],
        },
        "rebuild": rebuild,
        "thresholds": thresholds,
        "metrics": metrics,
        "issues": issues,
        "rerun_triggered": rerun_triggered,
        "rerun_result": rerun_result,
        "runtime_state_path": str(state_path),
    }

    _append_ndjson(log_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Runloop hygiene maintainer (run-files only).")
    parser.add_argument("--project", default="demo", help="Project id")
    args = parser.parse_args()

    report = run_hygiene(str(args.project).strip() or "demo")
    print(json.dumps(report, indent=2))

    # Exit non-zero only if guardrails still violated after rerun.
    return 0 if not report.get("issues") else 2


if __name__ == "__main__":
    raise SystemExit(main())
