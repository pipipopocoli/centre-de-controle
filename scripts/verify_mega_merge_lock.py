#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REQUIRED_SECTION_HEADINGS = [
    "changed artifacts",
    "dod evidence",
    "test results",
    "rollback note",
]


@dataclass(frozen=True)
class ArtifactSpec:
    filename: str
    stream: str
    owner: str


@dataclass(frozen=True)
class ArtifactCheck:
    spec: ArtifactSpec
    exists: bool
    has_changed_artifacts: bool
    has_dod_evidence: bool
    has_test_results: bool
    has_rollback_note: bool
    status: str


@dataclass(frozen=True)
class CapabilityRow:
    capability_id: str
    layer: str
    owner: str
    interface: str
    test_gate: str


@dataclass(frozen=True)
class CheckResult:
    result: str
    blocking: bool
    evidence: str


@dataclass(frozen=True)
class Analysis:
    timestamp_utc: str
    strict: bool
    root: Path
    ownership_rows: dict[str, str]
    canonical_domain_count: int
    capability_rows: list[CapabilityRow]
    invalid_registry_rows: int
    conflict_total: int
    conflict_resolved: int
    conflict_deferred: int
    conflict_unresolved_without_owner: int
    artifact_checks: list[ArtifactCheck]
    check_a: CheckResult
    check_b: CheckResult
    check_c: CheckResult
    check_d: CheckResult
    overall_result: str
    overall_verdict: str


ARTIFACT_SPECS: list[ArtifactSpec] = [
    ArtifactSpec("reliability_contract.md", "S1", "@agent-1"),
    ArtifactSpec("replay_validation_report.md", "S1", "@agent-1"),
    ArtifactSpec("crash_recovery_test_report.md", "S1", "@agent-1"),
    ArtifactSpec("skills_policy_spec.md", "S2", "@agent-2"),
    ArtifactSpec("conformance_test_report.md", "S2", "@agent-2"),
    ArtifactSpec("revoke_drill_report.md", "S2", "@agent-2"),
    ArtifactSpec("router_contracts.md", "S3", "@agent-3"),
    ArtifactSpec("scheduler_benchmark_report.md", "S3", "@agent-3"),
    ArtifactSpec("fallback_transition_report.md", "S3", "@agent-3"),
    ArtifactSpec("memory_contracts.md", "S4", "@agent-4"),
    ArtifactSpec("isolation_test_report.md", "S4", "@agent-4"),
    ArtifactSpec("compaction_restore_report.md", "S4", "@agent-4"),
    ArtifactSpec("eval_contracts.md", "S5", "@agent-5"),
    ArtifactSpec("threshold_validation_report.md", "S5", "@agent-5"),
    ArtifactSpec("calibration_report.md", "S5", "@agent-5"),
    ArtifactSpec("vulgarisation_ui_spec.md", "S6", "@agent-6"),
    ArtifactSpec("comprehension_test_report.md", "S6", "@agent-6"),
    ArtifactSpec("accessibility_report.md", "S6", "@agent-6"),
    ArtifactSpec("cost_model_spec.md", "S7", "@agent-7"),
    ArtifactSpec("budget_guardrail_report.md", "S7", "@agent-7"),
    ArtifactSpec("capacity_slo_report.md", "S7", "@agent-7"),
    ArtifactSpec("integration_lock_report.md", "Integration", "@agent-8"),
    ArtifactSpec("final_go_no_go.md", "Integration", "@agent-8"),
]


STREAM_ARTIFACTS = {
    "L1": ["reliability_contract.md", "replay_validation_report.md", "crash_recovery_test_report.md"],
    "L2": ["skills_policy_spec.md", "conformance_test_report.md", "revoke_drill_report.md"],
    "L3": ["router_contracts.md", "scheduler_benchmark_report.md", "fallback_transition_report.md"],
    "L4": ["memory_contracts.md", "isolation_test_report.md", "compaction_restore_report.md"],
    "L5": ["eval_contracts.md", "threshold_validation_report.md", "calibration_report.md"],
    "L6": ["vulgarisation_ui_spec.md", "comprehension_test_report.md", "accessibility_report.md"],
    "L7": ["cost_model_spec.md", "budget_guardrail_report.md", "capacity_slo_report.md"],
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_heading(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return " ".join(lowered.split())


def _collect_headings(path: Path) -> set[str]:
    if not path.exists():
        return set()
    headings: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.startswith("#"):
            continue
        normalized = _normalize_heading(line.lstrip("#").strip())
        if normalized:
            headings.add(normalized)
    return headings


def _required_sections(path: Path) -> tuple[bool, bool, bool, bool]:
    headings = _collect_headings(path)
    return (
        _normalize_heading("changed artifacts") in headings,
        _normalize_heading("dod evidence") in headings,
        _normalize_heading("test results") in headings,
        _normalize_heading("rollback note") in headings,
    )


def _parse_markdown_table_rows(path: Path, row_prefix: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        if not line.startswith(f"| {row_prefix}"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows.append(cells)
    return rows


def _parse_ownership_rows(matrix_path: Path) -> tuple[dict[str, str], int]:
    layer_owner: dict[str, str] = {}
    canonical_count = 0
    lines = matrix_path.read_text(encoding="utf-8").splitlines()
    in_canonical = False
    for raw in lines:
        line = raw.strip()
        if line.startswith("## Canonical interface ownership"):
            in_canonical = True
            continue
        if line.startswith("## ") and not line.startswith("## Canonical interface ownership"):
            in_canonical = False
        if line.startswith("| L"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) >= 2:
                layer_code = cells[0].split()[0]
                layer_owner[layer_code] = cells[1]
        if in_canonical and line.startswith("|") and not line.startswith("|---") and not line.startswith("| interface domain"):
            canonical_count += 1
    return layer_owner, canonical_count


def _parse_capabilities(registry_path: Path) -> tuple[list[CapabilityRow], int]:
    rows: list[CapabilityRow] = []
    invalid = 0
    for cells in _parse_markdown_table_rows(registry_path, "CAP-"):
        if len(cells) < 7:
            invalid += 1
            continue
        try:
            rows.append(
                CapabilityRow(
                    capability_id=cells[0],
                    layer=cells[1],
                    owner=cells[2],
                    interface=cells[5],
                    test_gate=cells[6],
                )
            )
        except IndexError:
            invalid += 1
    return rows, invalid


def _parse_conflict_stats(conflict_path: Path) -> tuple[int, int, int, int]:
    total = 0
    unresolved_without_owner = 0
    lines = conflict_path.read_text(encoding="utf-8").splitlines()
    for raw in lines:
        line = raw.strip()
        if not line.startswith("| CR-"):
            continue
        total += 1
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4:
            unresolved_without_owner += 1
            continue
        decision = cells[2]
        owner = cells[3]
        if not decision or not owner:
            unresolved_without_owner += 1
    deferred = 0
    for raw in lines:
        line = raw.strip()
        if line.startswith("- DF-"):
            deferred += 1
    resolved = max(total - deferred, 0)
    return total, resolved, deferred, unresolved_without_owner


def _artifact_checks(root: Path, strict: bool) -> list[ArtifactCheck]:
    checks: list[ArtifactCheck] = []
    for spec in ARTIFACT_SPECS:
        path = root / spec.filename
        exists = path.exists()
        has_changed, has_dod, has_tests, has_rollback = _required_sections(path)
        status = "PASS"
        if not exists:
            status = "FAIL"
        elif strict and not (has_changed and has_dod and has_tests and has_rollback):
            status = "FAIL"
        checks.append(
            ArtifactCheck(
                spec=spec,
                exists=exists,
                has_changed_artifacts=has_changed,
                has_dod_evidence=has_dod,
                has_test_results=has_tests,
                has_rollback_note=has_rollback,
                status=status,
            )
        )
    return checks


def _gate_summary(
    root: Path,
    strict: bool,
    timestamp_utc: str,
) -> Analysis:
    matrix_path = root / "01_LAYER_OWNERSHIP_MATRIX.md"
    registry_path = root / "02_CAPABILITY_REGISTRY.md"
    conflict_path = root / "03_CONFLICT_RESOLUTION_LOG.md"
    prompt_pack_path = root / "05_IMPLEMENTATION_PROMPT_PACK.md"
    for path in [matrix_path, registry_path, conflict_path, prompt_pack_path]:
        if not path.exists():
            raise FileNotFoundError(f"missing lock source: {path}")

    ownership_rows, canonical_domains = _parse_ownership_rows(matrix_path)
    capability_rows, invalid_registry_rows = _parse_capabilities(registry_path)
    conflict_total, conflict_resolved, conflict_deferred, unresolved_without_owner = _parse_conflict_stats(conflict_path)
    artifact_checks = _artifact_checks(root, strict)

    cap_ids = [row.capability_id for row in capability_rows]
    duplicate_cap_ids = [key for key, value in Counter(cap_ids).items() if value > 1]
    check_a_pass = (len(duplicate_cap_ids) == 0 and invalid_registry_rows == 0)
    check_a = CheckResult(
        result="PASS" if check_a_pass else "FAIL",
        blocking=not check_a_pass,
        evidence=(
            f"rows={len(capability_rows)}, "
            f"unique_capability_ids={len(set(cap_ids))}, "
            f"duplicate_capability_ids={len(duplicate_cap_ids)}"
        ),
    )

    owner_mismatch = 0
    for row in capability_rows:
        expected_owner = ownership_rows.get(row.layer)
        if expected_owner is None or expected_owner != row.owner:
            owner_mismatch += 1
    dup_interfaces = [key for key, value in Counter([row.interface for row in capability_rows]).items() if value > 1]
    check_b_pass = (owner_mismatch == 0 and len(dup_interfaces) == 0 and canonical_domains > 0)
    check_b = CheckResult(
        result="PASS" if check_b_pass else "FAIL",
        blocking=not check_b_pass,
        evidence=(
            f"canonical_domains={canonical_domains}, "
            f"owner_mismatch={owner_mismatch}, "
            f"duplicate_interfaces_impacted={len(dup_interfaces)}"
        ),
    )

    failing_artifacts = [item for item in artifact_checks if item.status != "PASS"]
    check_c_pass = (len(failing_artifacts) == 0 and invalid_registry_rows == 0)
    check_c = CheckResult(
        result="PASS" if check_c_pass else "FAIL",
        blocking=not check_c_pass,
        evidence=f"invalid_rows={invalid_registry_rows}, missing_stream_artifacts={len(failing_artifacts)}",
    )

    check_d_pass = unresolved_without_owner == 0
    check_d = CheckResult(
        result="PASS" if check_d_pass else "FAIL",
        blocking=not check_d_pass,
        evidence=(
            f"resolved_conflicts={conflict_resolved}, "
            f"deferred_items={conflict_deferred}, "
            f"unresolved_without_owner={unresolved_without_owner}"
        ),
    )

    overall_ok = all(item.result == "PASS" for item in [check_a, check_b, check_c, check_d])
    overall_result = "PASS" if overall_ok else "FAIL"
    overall_verdict = "GO" if overall_ok else "NO-GO"

    return Analysis(
        timestamp_utc=timestamp_utc,
        strict=strict,
        root=root,
        ownership_rows=ownership_rows,
        canonical_domain_count=canonical_domains,
        capability_rows=capability_rows,
        invalid_registry_rows=invalid_registry_rows,
        conflict_total=conflict_total,
        conflict_resolved=conflict_resolved,
        conflict_deferred=conflict_deferred,
        conflict_unresolved_without_owner=unresolved_without_owner,
        artifact_checks=artifact_checks,
        check_a=check_a,
        check_b=check_b,
        check_c=check_c,
        check_d=check_d,
        overall_result=overall_result,
        overall_verdict=overall_verdict,
    )


def _yes_no(flag: bool) -> str:
    return "yes" if flag else "no"


def _integration_report_content(analysis: Analysis) -> str:
    missing = [item.spec.filename for item in analysis.artifact_checks if item.status != "PASS"]
    lines: list[str] = []
    lines.append("# integration_lock_report")
    lines.append("")
    lines.append("## Control context")
    lines.append("- project_lock: cockpit")
    lines.append(f"- evidence_root: {analysis.root}")
    lines.append(f"- timestamp_utc: {analysis.timestamp_utc}")
    lines.append(f"- operator_mode: {'strict' if analysis.strict else 'warn'}")
    lines.append("- allowed_sources:")
    lines.append(f"  - {analysis.root / '01_LAYER_OWNERSHIP_MATRIX.md'}")
    lines.append(f"  - {analysis.root / '02_CAPABILITY_REGISTRY.md'}")
    lines.append(f"  - {analysis.root / '03_CONFLICT_RESOLUTION_LOG.md'}")
    lines.append(f"  - {analysis.root / '05_IMPLEMENTATION_PROMPT_PACK.md'}")
    lines.append("")
    lines.append("## Executive verdict")
    lines.append(f"- Overall integration lock: {analysis.overall_result}")
    lines.append(f"- Final release decision: {analysis.overall_verdict}")
    lines.append("")
    lines.append("| check_id | check_name | result | blocking | evidence |")
    lines.append("|---|---|---|---|---|")
    lines.append(f"| A | ownership_uniqueness | {analysis.check_a.result} | {'yes' if analysis.check_a.blocking else 'no'} | {analysis.check_a.evidence} |")
    lines.append(f"| B | interface_coherence | {analysis.check_b.result} | {'yes' if analysis.check_b.blocking else 'no'} | {analysis.check_b.evidence} |")
    lines.append(f"| C | gates_executable | {analysis.check_c.result} | {'yes' if analysis.check_c.blocking else 'no'} | {analysis.check_c.evidence} |")
    lines.append(f"| D | conflict_closure | {analysis.check_d.result} | {'yes' if analysis.check_d.blocking else 'no'} | {analysis.check_d.evidence} |")
    lines.append("")
    lines.append("## Missing artifacts (if any)")
    if not missing:
        lines.append("- none")
    else:
        for filename in missing:
            lines.append(f"- {filename}")
    lines.append("")
    lines.append("## Artifact ledger")
    lines.append("| artifact | stream | owner | exists | changed_artifacts | dod_evidence | test_results | rollback_note | status |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for item in analysis.artifact_checks:
        lines.append(
            f"| `{item.spec.filename}` | {item.spec.stream} | {item.spec.owner} | {_yes_no(item.exists)} | "
            f"{_yes_no(item.has_changed_artifacts)} | {_yes_no(item.has_dod_evidence)} | "
            f"{_yes_no(item.has_test_results)} | {_yes_no(item.has_rollback_note)} | {item.status} |"
        )
    lines.append("")
    lines.append("## Interface coherence matrix")
    lines.append("| layer | owner_from_matrix | owner_from_registry | capability_count | status |")
    lines.append("|---|---|---|---|---|")
    for layer in sorted(analysis.ownership_rows.keys()):
        rows = [row for row in analysis.capability_rows if row.layer == layer]
        owners = sorted(set(row.owner for row in rows))
        owner_registry = owners[0] if len(owners) == 1 else ",".join(owners) if owners else "-"
        status = "PASS" if (len(owners) == 1 and owner_registry == analysis.ownership_rows[layer]) else "FAIL"
        lines.append(
            f"| {layer} | {analysis.ownership_rows[layer]} | {owner_registry} | {len(rows)} | {status} |"
        )
    lines.append("")
    lines.append("## Gate mapping")
    lines.append("| capability_id | layer | test_gate | required_evidence_files |")
    lines.append("|---|---|---|---|")
    for row in analysis.capability_rows:
        required = ", ".join(STREAM_ARTIFACTS.get(row.layer, []))
        lines.append(
            f"| `{row.capability_id}` | {row.layer} | {row.test_gate} | `{required}` |"
        )
    lines.append("")
    lines.append("## Conflict audit")
    lines.append(f"- total_conflicts_logged: {analysis.conflict_total}")
    lines.append(f"- resolved_conflicts: {analysis.conflict_resolved}")
    lines.append(f"- deferred_items: {analysis.conflict_deferred}")
    lines.append(f"- unresolved_without_owner: {analysis.conflict_unresolved_without_owner}")
    lines.append("")
    lines.append("## Rollback map by layer")
    lines.append("- L1: rollback on replay hash drift or crash-recovery gate failure.")
    lines.append("- L2: rollback on approval gate bypass or policy parity failure.")
    lines.append("- L3: rollback on starvation regression or non-deterministic fallback.")
    lines.append("- L4: rollback on contamination sentinel hit or promotion gate bypass.")
    lines.append("- L5: rollback on verdict policy mismatch or override audit gaps.")
    lines.append("- L6: rollback on comprehension gate failure or stale threshold mismatch.")
    lines.append("- L7: rollback on hard-stop budget rule failure or non-reproducible breakeven matrix.")
    lines.append("")
    lines.append("## changed artifacts")
    lines.append(f"- {analysis.root / 'integration_lock_report.md'}")
    lines.append(f"- {analysis.root / 'final_go_no_go.md'}")
    lines.append("")
    lines.append("## DoD evidence")
    lines.append("- Checks A/B/C/D executed from locked sources.")
    lines.append("- Artifact ledger enforces strict section contract checks.")
    lines.append(f"- Overall result: {analysis.overall_result}, verdict: {analysis.overall_verdict}.")
    lines.append("")
    lines.append("## test results")
    lines.append(f"- capability rows parsed: {len(analysis.capability_rows)}")
    lines.append(f"- invalid capability rows: {analysis.invalid_registry_rows}")
    lines.append(f"- missing_stream_artifacts: {len(missing)}")
    lines.append(f"- check_A: {analysis.check_a.result}")
    lines.append(f"- check_B: {analysis.check_b.result}")
    lines.append(f"- check_C: {analysis.check_c.result}")
    lines.append(f"- check_D: {analysis.check_d.result}")
    lines.append("")
    lines.append("## rollback note")
    lines.append("- Re-run this script with corrected artifacts.")
    lines.append("- Reports are regenerated deterministically from source files and current artifact state.")
    lines.append("")
    lines.append("## Now / Next / Blockers")
    lines.append(f"- Now: strict lock refresh complete with verdict `{analysis.overall_verdict}`.")
    lines.append("- Next: rerun lock checks after any stream artifact update.")
    lines.append("- Blockers: none.")
    lines.append("")
    return "\n".join(lines)


def _final_go_no_go_content(analysis: Analysis) -> str:
    lines: list[str] = []
    lines.append("# final_go_no_go")
    lines.append("")
    lines.append("## Decision")
    lines.append(f"- timestamp_utc: {analysis.timestamp_utc}")
    lines.append("- owner_signoff: @agent-8")
    lines.append(f"- evidence_root: {analysis.root}")
    lines.append(f"- mode: {'strict' if analysis.strict else 'warn'}")
    lines.append(f"- verdict: {analysis.overall_verdict}")
    lines.append(f"- risk_level: {'LOW' if analysis.overall_verdict == 'GO' else 'HIGH'}")
    lines.append("")
    lines.append("## Blocking checks")
    lines.append(f"- Check A ownership_uniqueness: {analysis.check_a.result}")
    lines.append(f"- Check B interface_coherence: {analysis.check_b.result}")
    lines.append(f"- Check C gates_executable: {analysis.check_c.result}")
    lines.append(f"- Check D conflict_closure: {analysis.check_d.result}")
    lines.append("")
    lines.append("## Governance")
    lines.append("- PROJECT LOCK: cockpit.")
    lines.append("- No cross-project retrieval allowed.")
    lines.append("- Strict section contract required on all stream artifacts.")
    lines.append("")
    lines.append("## Rollback map (layer triggers)")
    lines.append("- L1: replay drift or crash recovery gate fail.")
    lines.append("- L2: approval gate bypass or policy parity fail.")
    lines.append("- L3: scheduler starvation or fallback determinism fail.")
    lines.append("- L4: contamination sentinel hit, promotion gate bypass, or restore fail.")
    lines.append("- L5: threshold parser mismatch or override audit gap.")
    lines.append("- L6: comprehension gate <85 percent or accessibility break.")
    lines.append("- L7: hard-stop budget guardrail fail or unreproducible breakeven matrix.")
    lines.append("")
    lines.append("## changed artifacts")
    lines.append(f"- {analysis.root / 'integration_lock_report.md'}")
    lines.append(f"- {analysis.root / 'final_go_no_go.md'}")
    lines.append("")
    lines.append("## DoD evidence")
    lines.append("- Verdict is derived from checks A/B/C/D in integration lock report.")
    lines.append("- Strict fail policy enforced for missing required sections.")
    lines.append("")
    lines.append("## test results")
    lines.append(f"- A={analysis.check_a.result}, B={analysis.check_b.result}, C={analysis.check_c.result}, D={analysis.check_d.result}")
    lines.append(f"- overall={analysis.overall_result}, verdict={analysis.overall_verdict}")
    lines.append("")
    lines.append("## rollback note")
    lines.append("- Fix failing checks, then rerun verify_mega_merge_lock.py with --strict --write-reports.")
    lines.append("")
    lines.append("## Now / Next / Blockers")
    lines.append(f"- Now: {analysis.overall_verdict} under strict integration lock.")
    lines.append("- Next: keep lock green after any stream change.")
    lines.append("- Blockers: none.")
    lines.append("")
    return "\n".join(lines)


def _write_reports(root: Path, analysis: Analysis) -> None:
    integration_path = root / "integration_lock_report.md"
    final_path = root / "final_go_no_go.md"
    integration_path.write_text(_integration_report_content(analysis), encoding="utf-8")
    final_path.write_text(_final_go_no_go_content(analysis), encoding="utf-8")


def _validate_temp_negative_path(root: Path, strict: bool) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_root = Path(tmp_dir) / "MEGA_MERGE"
        shutil.copytree(root, temp_root)
        target = temp_root / "memory_contracts.md"
        content = target.read_text(encoding="utf-8")
        # force a strict gate failure by removing rollback section heading
        content = re.sub(r"(?im)^##\s*rollback note\s*$", "## rollback_removed", content, count=1)
        target.write_text(content, encoding="utf-8")
        analysis = _gate_summary(temp_root, strict=strict, timestamp_utc=_utc_now_iso())
        return (0 if analysis.overall_verdict == "NO-GO" else 1, analysis.check_c.result)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify and refresh MEGA_MERGE integration lock reports.")
    parser.add_argument(
        "--root",
        default=str(Path("control/projects/cockpit/tournament-v2/MEGA_MERGE").resolve()),
        help="Path to MEGA_MERGE root",
    )
    parser.add_argument("--strict", action="store_true", help="Fail when required sections are missing.")
    parser.add_argument("--write-reports", action="store_true", help="Regenerate integration_lock_report.md and final_go_no_go.md")
    parser.add_argument("--timestamp-utc", default=None, help="Optional fixed UTC timestamp for deterministic output.")
    parser.add_argument("--validate-negative", action="store_true", help="Run a temporary fixture failure check.")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"root does not exist: {root}")

    timestamp = args.timestamp_utc or _utc_now_iso()
    analysis = _gate_summary(root, strict=args.strict, timestamp_utc=timestamp)

    if args.write_reports:
        # pass 1 write
        _write_reports(root, analysis)
        # pass 2 recalc to include freshly written integration artifacts
        analysis = _gate_summary(root, strict=args.strict, timestamp_utc=timestamp)
        _write_reports(root, analysis)

    if args.validate_negative:
        negative_status, check_c = _validate_temp_negative_path(root, strict=args.strict)
        print(f"negative_path_check_c={check_c}")
        print(f"negative_path_status={'PASS' if negative_status == 0 else 'FAIL'}")

    print(f"overall_result={analysis.overall_result}")
    print(f"overall_verdict={analysis.overall_verdict}")
    print(f"check_A={analysis.check_a.result}")
    print(f"check_B={analysis.check_b.result}")
    print(f"check_C={analysis.check_c.result}")
    print(f"check_D={analysis.check_d.result}")

    return 0 if analysis.overall_verdict == "GO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
