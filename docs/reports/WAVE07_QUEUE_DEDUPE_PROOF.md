# Wave07 Queue Dedupe — Proof Report

**Agent:** Victor | **Date:** 2026-02-20

## Problem
`requests.ndjson` contained 17 queued entries, including exact duplicates (same `request_id`) and stale reminders (>6h old). This caused noisy dispatch signals and bloated queue state.

## Root Cause
`record_mentions()` in `app/data/store.py` appended entries without checking if the `request_id` already existed, allowing duplicate lines on repeated calls.

## Fix Applied

### 1. Cleanup Script — `scripts/dedupe_queue.py`
Three-pass deduplication:
- **Pass 1:** Remove exact `request_id` duplicates (keep last) → 3 removed
- **Pass 2:** Close semantic duplicates per `(message_id, agent_id)` → 0 (all were exact)
- **Pass 3:** Close stale queued entries (>6h) → 14 closed

### 2. Prevention Guard — `app/data/store.py`
Added dedup guard in `record_mentions()` that reads existing `request_id`s before appending.

## Results
| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Total entries | 47 | 44 | — |
| Queued | 17 | 0 | ≤3 |
| Exact dupes | 3 | 0 | 0 |
| Stale (>6h) | 14 | 0 | 0 |

## Test Output
```
✅ PASS: No duplicate request_ids.
✅ PASS: Queued count = 0 (target ≤3).
✅ PASS: All 44 closed entries have a closed_reason.
✅ PASS: Dedup guard present in store.py.
Results: 4/4 passed, 0 failed.
```

## Files Changed
- `scripts/dedupe_queue.py` [NEW]
- `tests/verify_queue_dedupe.py` [NEW]
- `app/data/store.py` [MODIFIED] — dedup guard in `record_mentions()`
- `control/projects/cockpit/runs/requests.ndjson` [CLEANED]
