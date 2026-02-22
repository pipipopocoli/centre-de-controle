"""Verify Skills Policy Engine (ISSUE-CP-0002).

Covers: accepted, rejected, fail-open, fail-closed, batch, events,
empty allowlist, and case sensitivity.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.skills_policy import (  # noqa: E402
    PolicyDecision,
    PolicyUnavailableError,
    SkillsPolicy,
)


def test_accepted_path() -> None:
    policy = SkillsPolicy({"openai-docs", "skill-installer"})
    d = policy.evaluate("openai-docs")
    assert d.allowed is True
    assert d.reason == "curated"
    assert d.mode == "normal"
    print("[PASS] accepted path")


def test_rejected_path() -> None:
    policy = SkillsPolicy({"openai-docs"})
    d = policy.evaluate("random-untrusted-skill")
    assert d.allowed is False
    assert d.reason == "not_in_curated_allowlist"
    assert d.mode == "normal"
    # rejection emits a warning event
    assert len(policy.events) == 1
    assert policy.events[0].event_type == "rejected"
    print("[PASS] rejected path")


def test_fail_open_no_catalog() -> None:
    policy = SkillsPolicy.from_catalog(None, fail_open=True)
    d = policy.evaluate("anything-goes")
    assert d.allowed is True
    assert d.reason == "fail_open"
    assert d.mode == "fail_open"
    # must have at least the initial fail_open_no_catalog event
    types = [e.event_type for e in policy.events]
    assert "fail_open_no_catalog" in types
    print("[PASS] fail-open no catalog")


def test_fail_closed_no_catalog() -> None:
    raised = False
    try:
        SkillsPolicy.from_catalog(None, fail_open=False)
    except PolicyUnavailableError:
        raised = True
    assert raised, "Expected PolicyUnavailableError"
    print("[PASS] fail-closed raises PolicyUnavailableError")


def test_batch_evaluation() -> None:
    policy = SkillsPolicy({"alpha", "beta"})
    results = policy.evaluate_batch(["alpha", "gamma", "beta", "delta"])
    allowed = [r for r in results if r.allowed]
    rejected = [r for r in results if not r.allowed]
    assert len(allowed) == 2
    assert len(rejected) == 2
    assert {a.skill_id for a in allowed} == {"alpha", "beta"}
    assert {r.skill_id for r in rejected} == {"gamma", "delta"}
    print("[PASS] batch evaluation")


def test_event_logging() -> None:
    policy = SkillsPolicy({"ok-skill"})
    policy.evaluate("ok-skill")      # accepted — no event
    policy.evaluate("bad-skill")     # rejected — 1 event
    policy.evaluate("worse-skill")   # rejected — 2 events
    events = policy.events
    assert len(events) == 2
    assert all(e.timestamp for e in events)
    assert all(e.event_type == "rejected" for e in events)
    assert events[0].skill_id == "bad-skill"
    assert events[1].skill_id == "worse-skill"
    print("[PASS] event logging")


def test_empty_allowlist() -> None:
    policy = SkillsPolicy(set())
    d = policy.evaluate("any-skill")
    assert d.allowed is False
    assert d.reason == "not_in_curated_allowlist"
    print("[PASS] empty allowlist rejects all")


def test_case_sensitivity() -> None:
    policy = SkillsPolicy({"MySkill"})
    assert policy.evaluate("MySkill").allowed is True
    assert policy.evaluate("myskill").allowed is False
    assert policy.evaluate("MYSKILL").allowed is False
    print("[PASS] case sensitivity")


def test_from_catalog_extracts_ids() -> None:
    catalog = [
        {"id": "openai-docs", "version": "1.0"},
        {"id": "skill-installer"},
        {"not_an_id": "ignored"},
        {"id": ""},
    ]
    policy = SkillsPolicy.from_catalog(catalog)
    assert policy.evaluate("openai-docs").allowed is True
    assert policy.evaluate("skill-installer").allowed is True
    assert policy.evaluate("ignored").allowed is False
    assert policy.evaluate("").allowed is False
    print("[PASS] from_catalog extracts valid ids")


def main() -> int:
    tests = [
        test_accepted_path,
        test_rejected_path,
        test_fail_open_no_catalog,
        test_fail_closed_no_catalog,
        test_batch_evaluation,
        test_event_logging,
        test_empty_allowlist,
        test_case_sensitivity,
        test_from_catalog_extracts_ids,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1

    print(f"\n--- Results: {passed} passed, {failed} failed ---")
    if failed:
        return 1
    print("OK: skills policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
