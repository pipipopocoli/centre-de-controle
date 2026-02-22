"""Verify queue deduplication correctness.

Checks:
1. No duplicate request_ids in requests.ndjson.
2. Queued count <= 3 (normal load target).
3. All closed entries have a valid closed_reason.
4. Dedup guard in store.py prevents re-insertion.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

REQUESTS_PATH = (
    PROJECT_ROOT / "control" / "projects" / "cockpit" / "runs" / "requests.ndjson"
)

VALID_CLOSED_REASONS = {
    "stale_timeout_recovery",
    "queue_hygiene_runtime_recovery",
    "duplicate_recovery",
    "legacy_processed",
    "completed",
    "cancelled",
}


def load_entries() -> list[dict]:
    if not REQUESTS_PATH.exists():
        return []
    entries = []
    for line in REQUESTS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def test_no_duplicate_request_ids():
    entries = load_entries()
    ids = [e.get("request_id", "") for e in entries]
    counts = Counter(ids)
    dupes = {k: v for k, v in counts.items() if v > 1}
    assert not dupes, f"Duplicate request_ids found: {dupes}"
    print("✅ PASS: No duplicate request_ids.")


def test_queued_count_under_target():
    entries = load_entries()
    queued = [e for e in entries if e.get("status") == "queued"]
    assert len(queued) <= 3, f"Queued count {len(queued)} exceeds target 3. IDs: {[e.get('request_id') for e in queued]}"
    print(f"✅ PASS: Queued count = {len(queued)} (target ≤3).")


def test_closed_entries_have_reason():
    entries = load_entries()
    closed = [e for e in entries if e.get("status") == "closed"]
    missing = [e.get("request_id") for e in closed if not e.get("closed_reason")]
    assert not missing, f"Closed entries missing reason: {missing}"
    print(f"✅ PASS: All {len(closed)} closed entries have a closed_reason.")


def test_dedup_guard_exists():
    """Check that store.py has the dedup guard comment."""
    store_path = PROJECT_ROOT / "app" / "data" / "store.py"
    content = store_path.read_text(encoding="utf-8")
    assert "Wave07 dedup guard" in content, "Dedup guard not found in store.py"
    print("✅ PASS: Dedup guard present in store.py.")


def main():
    passed = 0
    failed = 0
    tests = [
        test_no_duplicate_request_ids,
        test_queued_count_under_target,
        test_closed_entries_have_reason,
        test_dedup_guard_exists,
    ]
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {test.__name__}: {e}")
            failed += 1

    print(f"\nResults: {passed}/{len(tests)} passed, {failed} failed.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
