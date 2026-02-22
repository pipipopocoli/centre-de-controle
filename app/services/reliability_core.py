from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class RunBundleRecord:
    run_id: str
    project_id: str
    input_hash: str
    policy_hash: str
    tool_calls: list[dict[str, Any]]
    events_path: str
    outputs_hash: str
    trace_ids: list[str]
    verdict: str
    replay_hash: str
    finalized_at: str


@dataclass(frozen=True)
class EventRecord:
    event_id: str
    event_index: int
    run_id: str
    event_type: str
    timestamp: str
    payload_hash: str
    trace_id: str | None
    tx_id: str | None


@dataclass(frozen=True)
class TransactionRecord:
    tx_id: str
    run_id: str
    op_name: str
    status: str
    timestamp: str
    details: dict[str, Any]


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int
    base_backoff_ms: int
    max_backoff_ms: int
    jitter_seed: str


@dataclass(frozen=True)
class RetryDecision:
    state: str
    attempt: int
    should_retry: bool
    backoff_ms: int
    reason: str


@dataclass(frozen=True)
class WalRecord:
    wal_id: str
    tx_id: str
    record_type: str
    payload: dict[str, Any]
    checksum: str
    created_at: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hash_payload(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def reliability_root(projects_root: Path, project_id: str) -> Path:
    return projects_root / project_id / "runs" / "reliability"


def bundles_dir(projects_root: Path, project_id: str) -> Path:
    return reliability_root(projects_root, project_id) / "bundles"


def bundle_path(projects_root: Path, project_id: str, run_id: str) -> Path:
    return bundles_dir(projects_root, project_id) / f"{run_id}.json"


def events_dir(projects_root: Path, project_id: str) -> Path:
    return reliability_root(projects_root, project_id) / "events"


def event_store_path(projects_root: Path, project_id: str, run_id: str) -> Path:
    return events_dir(projects_root, project_id) / f"{run_id}.ndjson"


def transactions_path(projects_root: Path, project_id: str) -> Path:
    return reliability_root(projects_root, project_id) / "transactions.ndjson"


def wal_path(projects_root: Path, project_id: str) -> Path:
    return reliability_root(projects_root, project_id) / "wal.ndjson"


def quarantine_path(projects_root: Path, project_id: str) -> Path:
    return reliability_root(projects_root, project_id) / "quarantine.ndjson"


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


def _append_ndjson(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as tmp:
            json.dump(payload, tmp, indent=2, sort_keys=True)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, path)
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _load_committed_tx(projects_root: Path, project_id: str) -> dict[str, dict[str, Any]]:
    committed: dict[str, dict[str, Any]] = {}
    for row in _read_ndjson(transactions_path(projects_root, project_id)):
        tx_id = str(row.get("tx_id") or "").strip()
        if not tx_id:
            continue
        if str(row.get("status") or "") in {"committed", "recovered_incomplete"}:
            committed[tx_id] = row
    return committed


def _next_event_index(path: Path) -> int:
    if not path.exists():
        return 1
    for raw in reversed(path.read_text(encoding="utf-8").splitlines()):
        line = raw.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        try:
            return int(row.get("event_index") or 0) + 1
        except (TypeError, ValueError):
            continue
    return 1


def append_wal_record(
    projects_root: Path,
    project_id: str,
    *,
    tx_id: str,
    record_type: str,
    payload: dict[str, Any],
) -> WalRecord:
    created_at = _utc_now_iso()
    wal_id = hashlib.sha256(f"{tx_id}:{record_type}:{created_at}".encode("utf-8")).hexdigest()[:24]
    checksum_payload = {
        "wal_id": wal_id,
        "tx_id": tx_id,
        "record_type": record_type,
        "payload": payload,
        "created_at": created_at,
    }
    checksum = hash_payload(checksum_payload)
    record = WalRecord(
        wal_id=wal_id,
        tx_id=tx_id,
        record_type=record_type,
        payload=payload,
        checksum=checksum,
        created_at=created_at,
    )
    _append_ndjson(wal_path(projects_root, project_id), asdict(record))
    return record


def apply_idempotent_tx(
    projects_root: Path,
    project_id: str,
    *,
    tx_id: str,
    run_id: str,
    op_name: str,
    payload: dict[str, Any],
    apply_fn: Callable[[], dict[str, Any] | None],
) -> TransactionRecord:
    committed = _load_committed_tx(projects_root, project_id)
    if tx_id in committed:
        record = TransactionRecord(
            tx_id=tx_id,
            run_id=run_id,
            op_name=op_name,
            status="already_committed",
            timestamp=_utc_now_iso(),
            details={"tx_id": tx_id},
        )
        return record

    append_wal_record(
        projects_root,
        project_id,
        tx_id=tx_id,
        record_type="begin",
        payload={"run_id": run_id, "op_name": op_name, "payload": payload},
    )

    try:
        result_payload = apply_fn() or {}
        append_wal_record(
            projects_root,
            project_id,
            tx_id=tx_id,
            record_type="commit",
            payload={"run_id": run_id, "op_name": op_name},
        )
        tx = TransactionRecord(
            tx_id=tx_id,
            run_id=run_id,
            op_name=op_name,
            status="committed",
            timestamp=_utc_now_iso(),
            details={"payload": payload, "result": result_payload},
        )
        _append_ndjson(transactions_path(projects_root, project_id), asdict(tx))
        return tx
    except Exception as exc:
        append_wal_record(
            projects_root,
            project_id,
            tx_id=tx_id,
            record_type="error",
            payload={"run_id": run_id, "op_name": op_name, "error": str(exc)},
        )
        tx = TransactionRecord(
            tx_id=tx_id,
            run_id=run_id,
            op_name=op_name,
            status="failed",
            timestamp=_utc_now_iso(),
            details={"payload": payload, "error": str(exc)},
        )
        _append_ndjson(transactions_path(projects_root, project_id), asdict(tx))
        raise


def _find_event_by_tx(path: Path, tx_id: str) -> EventRecord | None:
    for row in reversed(_read_ndjson(path)):
        if str(row.get("tx_id") or "") != tx_id:
            continue
        try:
            return EventRecord(
                event_id=str(row.get("event_id") or ""),
                event_index=int(row.get("event_index") or 0),
                run_id=str(row.get("run_id") or ""),
                event_type=str(row.get("event_type") or ""),
                timestamp=str(row.get("timestamp") or ""),
                payload_hash=str(row.get("payload_hash") or ""),
                trace_id=str(row.get("trace_id") or "") or None,
                tx_id=str(row.get("tx_id") or "") or None,
            )
        except (TypeError, ValueError):
            continue
    return None


def append_event(
    projects_root: Path,
    project_id: str,
    *,
    run_id: str,
    event_type: str,
    payload: dict[str, Any],
    trace_id: str | None = None,
    tx_id: str | None = None,
) -> EventRecord:
    path = event_store_path(projects_root, project_id, run_id)
    written: dict[str, Any] = {}

    def _write_event() -> dict[str, Any]:
        event_index = _next_event_index(path)
        payload_hash = hash_payload(payload)
        timestamp = _utc_now_iso()
        event_id = hashlib.sha256(
            f"{run_id}:{event_index}:{event_type}:{payload_hash}".encode("utf-8")
        ).hexdigest()[:24]
        event = EventRecord(
            event_id=event_id,
            event_index=event_index,
            run_id=run_id,
            event_type=event_type,
            timestamp=timestamp,
            payload_hash=payload_hash,
            trace_id=trace_id,
            tx_id=tx_id,
        )
        written_payload = asdict(event)
        _append_ndjson(path, written_payload)
        written.clear()
        written.update(written_payload)
        return written_payload

    if tx_id:
        tx = apply_idempotent_tx(
            projects_root,
            project_id,
            tx_id=tx_id,
            run_id=run_id,
            op_name="append_event",
            payload={"event_type": event_type, "trace_id": trace_id, "payload_hash": hash_payload(payload)},
            apply_fn=_write_event,
        )
        if tx.status == "already_committed":
            existing = _find_event_by_tx(path, tx_id)
            if existing is not None:
                return existing
        payload_out = dict(written)
    else:
        payload_out = _write_event()
    return EventRecord(
        event_id=str(payload_out.get("event_id") or ""),
        event_index=int(payload_out.get("event_index") or 0),
        run_id=str(payload_out.get("run_id") or ""),
        event_type=str(payload_out.get("event_type") or ""),
        timestamp=str(payload_out.get("timestamp") or ""),
        payload_hash=str(payload_out.get("payload_hash") or ""),
        trace_id=str(payload_out.get("trace_id") or "") or None,
        tx_id=str(payload_out.get("tx_id") or "") or None,
    )


def _build_bundle(
    projects_root: Path,
    project_id: str,
    *,
    run_id: str,
    input_payload: dict[str, Any],
    policy_payload: dict[str, Any],
    tool_calls: list[dict[str, Any]],
    outputs_payload: dict[str, Any],
    trace_ids: list[str],
    verdict: str,
) -> RunBundleRecord:
    input_hash = hash_payload(input_payload)
    policy_hash = hash_payload(policy_payload)
    outputs_hash = hash_payload(outputs_payload)
    events_file = event_store_path(projects_root, project_id, run_id)
    replay_base = {
        "run_id": run_id,
        "project_id": project_id,
        "input_hash": input_hash,
        "policy_hash": policy_hash,
        "tool_calls": tool_calls,
        "events_path": str(events_file),
        "outputs_hash": outputs_hash,
        "trace_ids": trace_ids,
        "verdict": verdict,
    }
    replay_hash = hash_payload(replay_base)
    return RunBundleRecord(
        run_id=run_id,
        project_id=project_id,
        input_hash=input_hash,
        policy_hash=policy_hash,
        tool_calls=tool_calls,
        events_path=str(events_file),
        outputs_hash=outputs_hash,
        trace_ids=trace_ids,
        verdict=verdict,
        replay_hash=replay_hash,
        finalized_at=_utc_now_iso(),
    )


def finalize_run_bundle(
    projects_root: Path,
    project_id: str,
    *,
    run_id: str,
    input_payload: dict[str, Any],
    policy_payload: dict[str, Any],
    tool_calls: list[dict[str, Any]],
    outputs_payload: dict[str, Any],
    trace_ids: list[str],
    verdict: str,
    tx_id: str | None = None,
) -> RunBundleRecord:
    target = bundle_path(projects_root, project_id, run_id)
    written: dict[str, Any] = {}

    def _write_bundle() -> dict[str, Any]:
        bundle = _build_bundle(
            projects_root,
            project_id,
            run_id=run_id,
            input_payload=input_payload,
            policy_payload=policy_payload,
            tool_calls=tool_calls,
            outputs_payload=outputs_payload,
            trace_ids=trace_ids,
            verdict=verdict,
        )
        written_payload = asdict(bundle)
        _atomic_write_json(target, written_payload)
        written.clear()
        written.update(written_payload)
        return written_payload

    if tx_id:
        tx = apply_idempotent_tx(
            projects_root,
            project_id,
            tx_id=tx_id,
            run_id=run_id,
            op_name="finalize_run_bundle",
            payload={"bundle_path": str(target)},
            apply_fn=_write_bundle,
        )
        if tx.status == "already_committed" and target.exists():
            payload = json.loads(target.read_text(encoding="utf-8"))
            return RunBundleRecord(**payload)
        return RunBundleRecord(**written)

    payload = _write_bundle()
    return RunBundleRecord(**payload)


def verify_wal_integrity(projects_root: Path, project_id: str) -> dict[str, Any]:
    wal_rows = _read_ndjson(wal_path(projects_root, project_id))
    quarantine = quarantine_path(projects_root, project_id)
    existing_quarantine = {str(row.get("wal_id") or "") for row in _read_ndjson(quarantine)}

    valid = 0
    quarantined = 0
    for row in wal_rows:
        wal_id = str(row.get("wal_id") or "").strip()
        checksum = str(row.get("checksum") or "")
        checksum_payload = {
            "wal_id": wal_id,
            "tx_id": str(row.get("tx_id") or ""),
            "record_type": str(row.get("record_type") or ""),
            "payload": row.get("payload") if isinstance(row.get("payload"), dict) else {},
            "created_at": str(row.get("created_at") or ""),
        }
        expected = hash_payload(checksum_payload)
        if checksum == expected:
            valid += 1
            continue
        quarantined += 1
        if wal_id in existing_quarantine:
            continue
        _append_ndjson(
            quarantine,
            {
                "timestamp": _utc_now_iso(),
                "reason": "checksum_mismatch",
                "wal_id": wal_id,
                "expected_checksum": expected,
                "observed_checksum": checksum,
                "record": row,
            },
        )

    return {
        "total_records": len(wal_rows),
        "valid_records": valid,
        "quarantined_records": quarantined,
        "wal_path": str(wal_path(projects_root, project_id)),
        "quarantine_path": str(quarantine),
    }


def recover_from_wal(projects_root: Path, project_id: str, *, run_id: str | None = None) -> dict[str, Any]:
    wal_rows = _read_ndjson(wal_path(projects_root, project_id))
    per_tx: dict[str, set[str]] = {}
    for row in wal_rows:
        tx_id = str(row.get("tx_id") or "").strip()
        record_type = str(row.get("record_type") or "").strip()
        if not tx_id or not record_type:
            continue
        per_tx.setdefault(tx_id, set()).add(record_type)

    recovered = 0
    for tx_id, types in per_tx.items():
        if "begin" not in types or "commit" in types:
            continue
        append_wal_record(
            projects_root,
            project_id,
            tx_id=tx_id,
            record_type="recovery_commit",
            payload={"reason": "incomplete_tx", "tx_id": tx_id},
        )
        _append_ndjson(
            transactions_path(projects_root, project_id),
            asdict(
                TransactionRecord(
                    tx_id=tx_id,
                    run_id=run_id or "unknown",
                    op_name="recover_from_wal",
                    status="recovered_incomplete",
                    timestamp=_utc_now_iso(),
                    details={"tx_id": tx_id},
                )
            ),
        )
        recovered += 1

    bundles_rebuilt = 0
    if run_id:
        target_bundle = bundle_path(projects_root, project_id, run_id)
        events_file = event_store_path(projects_root, project_id, run_id)
        if not target_bundle.exists() and events_file.exists():
            finalize_run_bundle(
                projects_root,
                project_id,
                run_id=run_id,
                input_payload={"recovered": True, "run_id": run_id},
                policy_payload={"source": "recover_from_wal"},
                tool_calls=[],
                outputs_payload={"status": "recovered"},
                trace_ids=[],
                verdict="recovered",
                tx_id=f"{run_id}:recover_bundle",
            )
            bundles_rebuilt += 1

    return {
        "recovered_transactions": recovered,
        "bundles_rebuilt": bundles_rebuilt,
        "wal_path": str(wal_path(projects_root, project_id)),
    }


def deterministic_retry_decision(
    policy: RetryPolicy,
    *,
    attempt: int,
    request_id: str,
    error_kind: str,
) -> RetryDecision:
    bounded_attempt = max(int(attempt), 1)
    max_attempts = max(int(policy.max_attempts), 1)
    if bounded_attempt >= max_attempts:
        return RetryDecision(
            state="failed_terminal",
            attempt=bounded_attempt,
            should_retry=False,
            backoff_ms=0,
            reason="max_attempts_reached",
        )

    retryable = str(error_kind).strip().lower() in {"timeout", "transient", "retryable"}
    if not retryable:
        return RetryDecision(
            state="failed_terminal",
            attempt=bounded_attempt,
            should_retry=False,
            backoff_ms=0,
            reason="non_retryable_error",
        )

    base = max(int(policy.base_backoff_ms), 0)
    max_backoff = max(int(policy.max_backoff_ms), base)
    exp_backoff = min(base * (2 ** (bounded_attempt - 1)), max_backoff)
    jitter_key = f"{request_id}:{bounded_attempt}:{policy.jitter_seed}"
    jitter_space = max(base // 4, 1)
    jitter = int(hashlib.sha256(jitter_key.encode("utf-8")).hexdigest()[:8], 16) % jitter_space
    backoff_ms = min(exp_backoff + jitter, max_backoff)

    return RetryDecision(
        state="retrying",
        attempt=bounded_attempt,
        should_retry=True,
        backoff_ms=backoff_ms,
        reason="retryable_error",
    )


def is_retryable_failure(status: str, error: str | None) -> bool:
    status_l = str(status or "").strip().lower()
    err_l = str(error or "").strip().lower()
    if status_l in {"timeout"}:
        return True
    if "timeout" in err_l or "tempor" in err_l or "transient" in err_l:
        return True
    return False
