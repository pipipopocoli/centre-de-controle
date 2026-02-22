from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import asdict, replace
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.skills_governance import (  # noqa: E402
    PolicyContext,
    SkillLockEntry,
    build_entry_signature,
    evaluate_policy,
    quarantine_skill,
    requires_full_access_approval,
    revoke_skill,
    validate_lifecycle_transition,
    validate_provenance,
    validate_skills_lock,
    validate_tier_upgrade,
)


def _sample_entry() -> SkillLockEntry:
    entry = SkillLockEntry(
        skill_id="openai-docs",
        repo_url="https://github.com/openai/openai-cookbook",
        commit_sha="a1b2c3d4",
        content_hash="deadbeefcafebabe",
        trust_tier="T2",
        status="active",
        workspace_scope="workspace_only",
        approved_by="clems",
        approved_at="2026-02-18T00:00:00+00:00",
        approval_ref="APR-001",
        signature="",
        provenance={
            "source_uri": "https://github.com/openai/openai-cookbook",
            "builder": "ci-bot",
            "source_digest": "a1b2c3d4e5f6",
            "build_digest": "0f1e2d3c4b5a",
            "timestamp": "2026-02-18T00:00:00+00:00",
        },
    )
    return replace(entry, signature=build_entry_signature(entry))


def test_lock_schema_and_signature_valid() -> None:
    entry = _sample_entry()
    payload = {"schema_version": 1, "skills": [asdict(entry)], "audit": []}
    ok, errors, _entries = validate_skills_lock(payload)
    assert ok is True
    assert errors == []
    print("[PASS] lock schema valid + signature valid")


def test_signature_tamper_rejected() -> None:
    entry = _sample_entry()
    tampered = asdict(entry)
    tampered["content_hash"] = "ffffffffffffffff"
    payload = {"schema_version": 1, "skills": [tampered], "audit": []}
    ok, errors, _entries = validate_skills_lock(payload)
    assert ok is False
    assert any("invalid_signature" in err for err in errors)
    print("[PASS] signature tamper rejected")


def test_provenance_contract_rejected_when_missing() -> None:
    entry = _sample_entry()
    bad = replace(entry, provenance={"source_uri": "x"})
    assert validate_provenance(bad) is False
    print("[PASS] invalid provenance rejected")


def test_trust_tier_upgrade_policy() -> None:
    ok1, reason1 = validate_tier_upgrade("T1", "T2", approval_ref=None)
    assert ok1 is False
    assert reason1 == "approval_ref_required_for_t2_t3"

    ok2, reason2 = validate_tier_upgrade("T1", "T2", approval_ref="APR-002")
    assert ok2 is True
    assert reason2 == "tier_upgrade_allowed"

    ok3, reason3 = validate_tier_upgrade("T2", "T3", approval_ref="APR-003", security_reviewed=False)
    assert ok3 is False
    assert reason3 == "security_review_required_for_t3"

    ok4, reason4 = validate_tier_upgrade("T2", "T3", approval_ref="APR-003", security_reviewed=True)
    assert ok4 is True
    assert reason4 == "tier_upgrade_allowed"
    print("[PASS] trust tier upgrade checks")


def test_lifecycle_transitions() -> None:
    assert validate_lifecycle_transition("proposed", "verified") is True
    assert validate_lifecycle_transition("verified", "approved") is True
    assert validate_lifecycle_transition("approved", "installed") is True
    assert validate_lifecycle_transition("installed", "active") is True
    assert validate_lifecycle_transition("active", "revoked") is True
    assert validate_lifecycle_transition("active", "verified") is False
    print("[PASS] lifecycle transitions")


def test_full_access_gate() -> None:
    assert requires_full_access_approval("full_access", None) is True
    assert requires_full_access_approval("full_access", "APR-009") is False
    assert requires_full_access_approval("workspace_only", None) is False
    print("[PASS] full-access approval gate")


def test_policy_parity_key_is_runner_agnostic() -> None:
    codex = evaluate_policy(
        PolicyContext(
            project_id="cockpit",
            runner="codex",
            action_scope="full_access",
            requested_skills=["openai-docs"],
            approval_ref="APR-010",
        )
    )
    antigravity = evaluate_policy(
        PolicyContext(
            project_id="cockpit",
            runner="antigravity",
            action_scope="full_access",
            requested_skills=["openai-docs"],
            approval_ref="APR-010",
        )
    )
    assert codex.allowed is True
    assert antigravity.allowed is True
    assert codex.reason_code == antigravity.reason_code
    assert codex.parity_key == antigravity.parity_key
    print("[PASS] policy parity key consistent across runners")


def test_revoke_and_quarantine_pipeline() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        lock_path = Path(tmp) / "skills.lock.json"
        entry = _sample_entry()
        lock_path.write_text(
            json.dumps({"schema_version": 1, "skills": [asdict(entry)], "audit": []}, indent=2),
            encoding="utf-8",
        )

        ok_revoke, reason_revoke = revoke_skill(lock_path, "openai-docs", approval_ref="APR-020")
        assert ok_revoke is True
        assert reason_revoke == "status_updated"
        payload_revoke = json.loads(lock_path.read_text(encoding="utf-8"))
        assert payload_revoke["skills"][0]["status"] == "revoked"

        ok_quarantine, reason_quarantine = quarantine_skill(lock_path, "openai-docs", approval_ref="APR-021")
        assert ok_quarantine is True
        assert reason_quarantine == "status_updated"
        payload_quarantine = json.loads(lock_path.read_text(encoding="utf-8"))
        assert payload_quarantine["skills"][0]["status"] == "quarantined"
        assert len(payload_quarantine.get("audit") or []) >= 2
    print("[PASS] revoke/quarantine pipeline")


def main() -> int:
    tests = [
        test_lock_schema_and_signature_valid,
        test_signature_tamper_rejected,
        test_provenance_contract_rejected_when_missing,
        test_trust_tier_upgrade_policy,
        test_lifecycle_transitions,
        test_full_access_gate,
        test_policy_parity_key_is_runner_agnostic,
        test_revoke_and_quarantine_pipeline,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as exc:
            print(f"[FAIL] {test.__name__}: {exc}")
            failed += 1

    print(f"\n--- Results: {passed} passed, {failed} failed ---")
    if failed:
        return 1
    print("OK: skills governance verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
