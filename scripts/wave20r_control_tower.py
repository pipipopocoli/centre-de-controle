#!/usr/bin/env python3
"""
Wave20R control tower snapshot and preflight checker.

This script is the L0 orchestration helper for Wave20R. It reads the canonical
Wave20R artifacts under docs/swarm_results and produces a machine-readable and
human-readable snapshot of lane status and quality gate compliance.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_DEFER_REASONS = {"non_repro", "stale", "policy", "intentional_contract"}
EXPECTED_MODEL_LOCK = "Model: moonshotai/kimi-k2.5"
EXPECTED_REASONING_LOCK = "Reasoning: enabled=true; preserve reasoning_details unchanged across follow-up calls."
LANES = [f"A{i}" for i in range(1, 21)]


@dataclass
class LaneStatus:
    lane: str
    branch: str
    backlog_path: str
    prompt_path: str
    report_path: str
    rows_total: int
    rows_done: int
    rows_defer: int
    rows_open: int
    invalid_action_count: int
    defer_missing_reason: int
    defer_invalid_reason: int
    defer_missing_evidence: int
    model_lock_ok: bool
    reasoning_lock_ok: bool
    branch_exists: bool
    report_has_now: bool
    report_has_next: bool
    report_has_blockers: bool
    report_placeholder_count: int
    backlog_exists: bool
    prompt_exists: bool
    report_exists: bool


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wave20R control tower status snapshot.")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root path.",
    )
    parser.add_argument(
        "--swarm-dir",
        default="docs/swarm_results",
        help="Path to swarm results directory relative to repo root.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write snapshot markdown/json files under swarm results.",
    )
    parser.add_argument(
        "--json-out",
        default="wave20r_control_tower_snapshot.json",
        help="JSON output filename inside swarm dir.",
    )
    parser.add_argument(
        "--md-out",
        default="wave20r_control_tower_snapshot.md",
        help="Markdown output filename inside swarm dir.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero on control-critical violations.",
    )
    parser.add_argument(
        "--strict-open",
        action="store_true",
        help="Return non-zero if any backlog row is still open.",
    )
    return parser.parse_args()


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _branch_exists(repo_root: Path, branch: str) -> bool:
    command = ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"]
    proc = subprocess.run(command, cwd=repo_root, check=False)
    return proc.returncode == 0


def _parse_markdown_table_row(line: str) -> list[str]:
    if not line.startswith("|"):
        return []
    parts = [part.strip() for part in line.strip().strip("|").split("|")]
    return parts


def _parse_backlog_rows(backlog_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw_line in backlog_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("| `ISSUE-"):
            continue
        cols = _parse_markdown_table_row(line)
        if len(cols) < 10:
            continue
        row = {
            "issue_id": cols[0].strip("` "),
            "source": cols[1].strip("` "),
            "severity": cols[2].strip("` "),
            "file": cols[3].strip("` "),
            "status_before": cols[4].strip("` "),
            "action": cols[5].strip("` ").lower(),
            "evidence_command": cols[6].strip("` "),
            "evidence_result": cols[7].strip("` "),
            "reason_code": cols[8].strip("` "),
            "note": cols[9],
        }
        rows.append(row)
    return rows


def _parse_coverage_metrics(coverage_text: str) -> dict[str, int]:
    metrics = {"total_rows": -1, "assigned_rows": -1, "unassigned_rows": -1, "overlap_rows": -1}
    patterns = {
        "total_rows": r"- total_rows:\s+(\d+)",
        "assigned_rows": r"- assigned_rows:\s+(\d+)",
        "unassigned_rows": r"- unassigned_rows:\s+(\d+)",
        "overlap_rows": r"- overlap_rows:\s+(\d+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, coverage_text)
        if match:
            metrics[key] = int(match.group(1))
    return metrics


def _collect_prompt_required_skills(prompt_text: str) -> list[str]:
    skills: list[str] = []
    in_skills = False
    for raw_line in prompt_text.splitlines():
        line = raw_line.strip()
        if line.startswith("2) Required skills"):
            in_skills = True
            continue
        if in_skills and line.startswith("3) File scope"):
            break
        if in_skills and line.startswith("- "):
            skills.append(line[2:].strip())
    return skills


def _parse_skills_manifest(skills_manifest_text: str) -> dict[str, bool]:
    status: dict[str, bool] = {}
    for raw_line in skills_manifest_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("| `"):
            continue
        cols = _parse_markdown_table_row(line)
        if len(cols) < 4:
            continue
        skill_name = cols[0].strip("` ")
        installed = cols[2].strip("` ").lower() == "yes"
        status[skill_name] = installed
    return status


def _lane_status(repo_root: Path, swarm_dir: Path, lane: str) -> LaneStatus:
    lane_num = lane[1:]
    branch = f"codex/wave20r-a{lane_num}"
    backlog = swarm_dir / f"wave20r_a{lane_num}_backlog.md"
    prompt = swarm_dir / f"wave20r_agent{lane_num}_prompt.md"
    report = swarm_dir / f"wave20r_agent{lane_num}_report.md"

    backlog_text = _read_text(backlog)
    prompt_text = _read_text(prompt)
    report_text = _read_text(report)
    rows = _parse_backlog_rows(backlog_text)

    rows_done = 0
    rows_defer = 0
    rows_open = 0
    invalid_action_count = 0
    defer_missing_reason = 0
    defer_invalid_reason = 0
    defer_missing_evidence = 0

    for row in rows:
        action = row["action"]
        if action == "done":
            rows_done += 1
        elif action == "defer":
            rows_defer += 1
            reason = row["reason_code"].strip()
            if not reason:
                defer_missing_reason += 1
            elif reason not in ALLOWED_DEFER_REASONS:
                defer_invalid_reason += 1
            evidence_cmd = row["evidence_command"].strip()
            evidence_result = row["evidence_result"].strip()
            if not evidence_cmd or not evidence_result:
                defer_missing_evidence += 1
        elif action == "":
            rows_open += 1
        else:
            invalid_action_count += 1

    report_has_now = "## Now" in report_text
    report_has_next = "## Next" in report_text
    report_has_blockers = "## Blockers" in report_text
    report_placeholder_count = report_text.count("(fill)")

    return LaneStatus(
        lane=lane,
        branch=branch,
        backlog_path=str(backlog),
        prompt_path=str(prompt),
        report_path=str(report),
        rows_total=len(rows),
        rows_done=rows_done,
        rows_defer=rows_defer,
        rows_open=rows_open,
        invalid_action_count=invalid_action_count,
        defer_missing_reason=defer_missing_reason,
        defer_invalid_reason=defer_invalid_reason,
        defer_missing_evidence=defer_missing_evidence,
        model_lock_ok=EXPECTED_MODEL_LOCK in prompt_text,
        reasoning_lock_ok=EXPECTED_REASONING_LOCK in prompt_text,
        branch_exists=_branch_exists(repo_root, branch),
        report_has_now=report_has_now,
        report_has_next=report_has_next,
        report_has_blockers=report_has_blockers,
        report_placeholder_count=report_placeholder_count,
        backlog_exists=backlog.exists(),
        prompt_exists=prompt.exists(),
        report_exists=report.exists(),
    )


def _findings(snapshot: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    coverage = snapshot["coverage"]
    if coverage["unassigned_rows"] != 0:
        findings.append(f"coverage_unassigned_rows={coverage['unassigned_rows']}")
    if coverage["overlap_rows"] != 0:
        findings.append(f"coverage_overlap_rows={coverage['overlap_rows']}")

    for lane in snapshot["lanes"]:
        lane_name = lane["lane"]
        if not lane["branch_exists"]:
            findings.append(f"{lane_name}:missing_branch")
        if not lane["model_lock_ok"]:
            findings.append(f"{lane_name}:model_lock_missing")
        if not lane["reasoning_lock_ok"]:
            findings.append(f"{lane_name}:reasoning_lock_missing")
        if lane["invalid_action_count"] > 0:
            findings.append(f"{lane_name}:invalid_action_count={lane['invalid_action_count']}")
        if lane["defer_missing_reason"] > 0:
            findings.append(f"{lane_name}:defer_missing_reason={lane['defer_missing_reason']}")
        if lane["defer_invalid_reason"] > 0:
            findings.append(f"{lane_name}:defer_invalid_reason={lane['defer_invalid_reason']}")
        if lane["defer_missing_evidence"] > 0:
            findings.append(f"{lane_name}:defer_missing_evidence={lane['defer_missing_evidence']}")
    return findings


def _build_snapshot(repo_root: Path, swarm_dir: Path) -> dict[str, Any]:
    coverage_path = swarm_dir / "wave20r_split_coverage_check.md"
    skills_manifest_path = swarm_dir / "wave20r_skills_manifest.md"
    coverage = _parse_coverage_metrics(_read_text(coverage_path))
    skills_manifest = _parse_skills_manifest(_read_text(skills_manifest_path))

    lane_statuses = [asdict(_lane_status(repo_root, swarm_dir, lane)) for lane in LANES]

    required_skills: set[str] = set()
    for lane in LANES:
        prompt_path = swarm_dir / f"wave20r_agent{lane[1:]}_prompt.md"
        required_skills.update(_collect_prompt_required_skills(_read_text(prompt_path)))

    missing_skills = sorted(skill for skill in required_skills if not skills_manifest.get(skill, False))

    summary = {
        "rows_total": sum(lane["rows_total"] for lane in lane_statuses),
        "rows_done": sum(lane["rows_done"] for lane in lane_statuses),
        "rows_defer": sum(lane["rows_defer"] for lane in lane_statuses),
        "rows_open": sum(lane["rows_open"] for lane in lane_statuses),
        "invalid_action_count": sum(lane["invalid_action_count"] for lane in lane_statuses),
        "defer_missing_reason": sum(lane["defer_missing_reason"] for lane in lane_statuses),
        "defer_invalid_reason": sum(lane["defer_invalid_reason"] for lane in lane_statuses),
        "defer_missing_evidence": sum(lane["defer_missing_evidence"] for lane in lane_statuses),
        "missing_skills_count": len(missing_skills),
    }

    snapshot = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repo_root": str(repo_root),
        "swarm_dir": str(swarm_dir),
        "coverage": coverage,
        "summary": summary,
        "missing_skills": missing_skills,
        "lanes": lane_statuses,
    }
    snapshot["findings"] = _findings(snapshot)
    return snapshot


def _snapshot_markdown(snapshot: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Wave20R Control Tower Snapshot")
    lines.append("")
    lines.append(f"- generated_at_utc: `{snapshot['generated_at_utc']}`")
    lines.append(f"- repo_root: `{snapshot['repo_root']}`")
    lines.append("")
    lines.append("## Coverage")
    lines.append(f"- total_rows: `{snapshot['coverage']['total_rows']}`")
    lines.append(f"- assigned_rows: `{snapshot['coverage']['assigned_rows']}`")
    lines.append(f"- unassigned_rows: `{snapshot['coverage']['unassigned_rows']}`")
    lines.append(f"- overlap_rows: `{snapshot['coverage']['overlap_rows']}`")
    lines.append("")
    lines.append("## Summary")
    summary = snapshot["summary"]
    lines.append(f"- rows_total: `{summary['rows_total']}`")
    lines.append(f"- rows_done: `{summary['rows_done']}`")
    lines.append(f"- rows_defer: `{summary['rows_defer']}`")
    lines.append(f"- rows_open: `{summary['rows_open']}`")
    lines.append(f"- invalid_action_count: `{summary['invalid_action_count']}`")
    lines.append(f"- defer_missing_reason: `{summary['defer_missing_reason']}`")
    lines.append(f"- defer_invalid_reason: `{summary['defer_invalid_reason']}`")
    lines.append(f"- defer_missing_evidence: `{summary['defer_missing_evidence']}`")
    lines.append(f"- missing_skills_count: `{summary['missing_skills_count']}`")
    lines.append("")
    lines.append("## Lane Table")
    lines.append("| lane | rows | done | defer | open | invalid_action | defer_missing_reason | defer_invalid_reason | defer_missing_evidence | branch | model_lock | reasoning_lock | report_placeholders |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---:|")
    for lane in snapshot["lanes"]:
        lines.append(
            f"| `{lane['lane']}` | {lane['rows_total']} | {lane['rows_done']} | {lane['rows_defer']} | {lane['rows_open']} | "
            f"{lane['invalid_action_count']} | {lane['defer_missing_reason']} | {lane['defer_invalid_reason']} | {lane['defer_missing_evidence']} | "
            f"{'ok' if lane['branch_exists'] else 'missing'} | "
            f"{'ok' if lane['model_lock_ok'] else 'missing'} | "
            f"{'ok' if lane['reasoning_lock_ok'] else 'missing'} | {lane['report_placeholder_count']} |"
        )

    lines.append("")
    lines.append("## Findings")
    if snapshot["findings"]:
        for finding in snapshot["findings"]:
            lines.append(f"- {finding}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## Missing Skills")
    if snapshot["missing_skills"]:
        for skill in snapshot["missing_skills"]:
            lines.append(f"- {skill}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _write_outputs(snapshot: dict[str, Any], json_path: Path, md_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    md_path.write_text(_snapshot_markdown(snapshot), encoding="utf-8")


def _is_strict_failure(snapshot: dict[str, Any], strict_open: bool) -> bool:
    coverage = snapshot["coverage"]
    summary = snapshot["summary"]
    if coverage["unassigned_rows"] != 0 or coverage["overlap_rows"] != 0:
        return True
    if summary["invalid_action_count"] > 0:
        return True
    if summary["defer_missing_reason"] > 0 or summary["defer_invalid_reason"] > 0:
        return True
    if summary["defer_missing_evidence"] > 0:
        return True
    if summary["missing_skills_count"] > 0:
        return True
    for lane in snapshot["lanes"]:
        if not lane["branch_exists"]:
            return True
        if not lane["model_lock_ok"] or not lane["reasoning_lock_ok"]:
            return True
    if strict_open and summary["rows_open"] > 0:
        return True
    return False


def main() -> int:
    args = _parse_args()
    repo_root = Path(args.repo_root).resolve()
    swarm_dir = (repo_root / args.swarm_dir).resolve()

    snapshot = _build_snapshot(repo_root, swarm_dir)
    markdown = _snapshot_markdown(snapshot)
    print(markdown)

    if args.write:
        json_path = swarm_dir / args.json_out
        md_path = swarm_dir / args.md_out
        _write_outputs(snapshot, json_path, md_path)
        print(f"\nWrote: {json_path}")
        print(f"Wrote: {md_path}")

    if args.strict and _is_strict_failure(snapshot, strict_open=args.strict_open):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

