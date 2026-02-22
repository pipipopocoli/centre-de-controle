from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.reliability_core import (  # noqa: E402
    RetryPolicy,
    append_event,
    append_wal_record,
    apply_idempotent_tx,
    bundle_path,
    deterministic_retry_decision,
    event_store_path,
    finalize_run_bundle,
    is_retryable_failure,
    quarantine_path,
    recover_from_wal,
    verify_wal_integrity,
    wal_path,
)


def _read_ndjson(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
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


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        projects_root = Path(tmp) / "projects"
        project_id = "demo"
        run_id = "run_cap_l1_001"

        # CAP-L1-001: replay hash stable across 10 replays.
        replay_hashes: list[str] = []
        for _ in range(10):
            bundle = finalize_run_bundle(
                projects_root,
                project_id,
                run_id=run_id,
                input_payload={"request": "ping"},
                policy_payload={"mode": "workspace_only"},
                tool_calls=[{"tool": "codex", "step": 1}],
                outputs_payload={"status": "ok"},
                trace_ids=[run_id],
                verdict="success",
            )
            replay_hashes.append(bundle.replay_hash)
        assert len(set(replay_hashes)) == 1, "replay hash must stay stable over repeated finalize"

        # CAP-L1-002: append-only invariants and monotonic event_index.
        e1 = append_event(
            projects_root,
            project_id,
            run_id=run_id,
            event_type="dispatch",
            payload={"step": 1},
            trace_id=run_id,
            tx_id=f"{run_id}:evt:1",
        )
        append_event(
            projects_root,
            project_id,
            run_id=run_id,
            event_type="retry",
            payload={"step": 2},
            trace_id=run_id,
            tx_id=f"{run_id}:evt:2",
        )
        append_event(
            projects_root,
            project_id,
            run_id=run_id,
            event_type="complete",
            payload={"step": 3},
            trace_id=run_id,
            tx_id=f"{run_id}:evt:3",
        )
        event_path = event_store_path(projects_root, project_id, run_id)
        rows_before = _read_ndjson(event_path)
        assert len(rows_before) == 3, "event store should have 3 rows"
        assert [int(r.get("event_index") or 0) for r in rows_before] == [1, 2, 3], "event index must be monotonic"

        e1_dup = append_event(
            projects_root,
            project_id,
            run_id=run_id,
            event_type="dispatch",
            payload={"step": 1},
            trace_id=run_id,
            tx_id=f"{run_id}:evt:1",
        )
        rows_after = _read_ndjson(event_path)
        assert len(rows_after) == 3, "duplicate tx should not append a new event"
        assert e1_dup.event_id == e1.event_id, "duplicate tx should resolve to the original event"

        # CAP-L1-003: duplicate write test shows idempotent behavior.
        counter = {"calls": 0}

        def _apply_once() -> dict[str, int]:
            counter["calls"] += 1
            return {"calls": counter["calls"]}

        tx1 = apply_idempotent_tx(
            projects_root,
            project_id,
            tx_id=f"{run_id}:tx:idempotent",
            run_id=run_id,
            op_name="idempotent_probe",
            payload={"kind": "probe"},
            apply_fn=_apply_once,
        )
        tx2 = apply_idempotent_tx(
            projects_root,
            project_id,
            tx_id=f"{run_id}:tx:idempotent",
            run_id=run_id,
            op_name="idempotent_probe",
            payload={"kind": "probe"},
            apply_fn=_apply_once,
        )
        assert tx1.status == "committed"
        assert tx2.status == "already_committed"
        assert counter["calls"] == 1, "idempotent tx must execute apply_fn exactly once"

        # CAP-L1-004: timeout/retry chaos scenario pass.
        policy = RetryPolicy(max_attempts=3, base_backoff_ms=100, max_backoff_ms=1000, jitter_seed="seed-42")
        d1 = deterministic_retry_decision(policy, attempt=1, request_id="req-retry", error_kind="timeout")
        d1_again = deterministic_retry_decision(policy, attempt=1, request_id="req-retry", error_kind="timeout")
        d2 = deterministic_retry_decision(policy, attempt=2, request_id="req-retry", error_kind="transient")
        d3 = deterministic_retry_decision(policy, attempt=3, request_id="req-retry", error_kind="timeout")
        assert d1.should_retry is True and d1.state == "retrying"
        assert d1.backoff_ms == d1_again.backoff_ms, "retry backoff must be deterministic"
        assert d2.should_retry is True and d2.backoff_ms >= d1.backoff_ms
        assert d3.should_retry is False and d3.state == "failed_terminal"
        assert is_retryable_failure("timeout", None) is True
        assert is_retryable_failure("failed", "transient network") is True
        assert is_retryable_failure("failed", "fatal parse error") is False

        # CAP-L1-005: checksum corruption quarantine works.
        append_wal_record(
            projects_root,
            project_id,
            tx_id=f"{run_id}:tx:wal-good",
            record_type="begin",
            payload={"ok": True},
        )
        wal_file = wal_path(projects_root, project_id)
        corrupted = {
            "wal_id": "wal_corrupted_001",
            "tx_id": f"{run_id}:tx:wal-bad",
            "record_type": "begin",
            "payload": {"bad": True},
            "checksum": "invalid_checksum",
            "created_at": "2026-02-19T00:00:00+00:00",
        }
        with wal_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(corrupted) + "\n")

        integrity = verify_wal_integrity(projects_root, project_id)
        assert int(integrity.get("quarantined_records") or 0) >= 1, "corrupted WAL entry must be quarantined"
        quarantined_rows = _read_ndjson(quarantine_path(projects_root, project_id))
        assert quarantined_rows, "quarantine file must contain corrupted records"

        # CAP-L1-006: crash injection recovery pass.
        recover_run = "run_cap_l1_006"
        append_event(
            projects_root,
            project_id,
            run_id=recover_run,
            event_type="seed",
            payload={"warmup": True},
            trace_id=recover_run,
            tx_id=f"{recover_run}:evt:seed",
        )
        append_wal_record(
            projects_root,
            project_id,
            tx_id=f"{recover_run}:tx:crash",
            record_type="begin",
            payload={"run_id": recover_run, "note": "simulated crash"},
        )
        recovery = recover_from_wal(projects_root, project_id, run_id=recover_run)
        assert int(recovery.get("recovered_transactions") or 0) >= 1, "recovery should close incomplete tx"
        assert bundle_path(projects_root, project_id, recover_run).exists(), "recovery should rebuild missing bundle"

    print("OK: reliability core verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
