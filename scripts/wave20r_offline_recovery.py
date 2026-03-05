#!/usr/bin/env python3
"""
Wave20R offline recovery runner.

Goal:
- Reuse already-paid run artifacts from wave20r_kimi_runs.
- Select best candidate diff per lane (offline-only).
- Sanitize/repair patch text and apply on a clean integration worktree.
- Emit recovery matrix + apply log for evidence-first closeout.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


WILDCARD_CHARS = {"*", "?", "["}
DIFF_FILE_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)$", re.MULTILINE)
HUNK_HEADER_RE = re.compile(r"^@@ -(?P<a>\d+)(?:,(?P<b>\d+))? \+(?P<c>\d+)(?:,(?P<d>\d+))? @@(?P<tail>.*)$")
DEFAULT_RUNS = [
    "20260305_152618",
    "20260305_150113",
    "20260305_144439",
]


@dataclass
class LaneAttempt:
    lane: str
    run_id: str
    source_diff: str
    priority: int
    variant: str
    changed_files: list[str]
    allowed_ok: bool
    violations: list[str]
    status: str
    reason: str


@dataclass
class LaneOutcome:
    lane: str
    status: str
    selected_run: str
    selected_diff: str
    priority: int
    apply_variant: str
    changed_files: list[str]
    reason: str
    attempts: list[LaneAttempt]


def _die(message: str, code: int = 1) -> None:
    print(f"Error: {message}")
    raise SystemExit(code)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wave20R offline-first recovery from existing run artifacts.")
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Target integration worktree (clean) where diffs will be applied.",
    )
    parser.add_argument(
        "--source-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Source repo containing run artifacts and lane manifests.",
    )
    parser.add_argument(
        "--runs",
        default=",".join(DEFAULT_RUNS),
        help="Comma-separated run ids in priority order (best first).",
    )
    parser.add_argument(
        "--tasks-file",
        default="docs/swarm_results/wave20r_kimi_tasks.json",
        help="Task manifest path relative to source root (or absolute).",
    )
    parser.add_argument(
        "--swarm-dir",
        default="docs/swarm_results",
        help="Swarm results directory relative to source root.",
    )
    parser.add_argument(
        "--output-prefix",
        default="wave20r_offline_recovery",
        help="Output prefix for matrix/json/log files.",
    )
    parser.add_argument(
        "--allow-dirty-target",
        action="store_true",
        help="Skip clean-tree enforcement on target worktree.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not apply; only build matrix and candidate selection.",
    )
    parser.add_argument(
        "--only-lanes",
        default="",
        help="Optional comma-separated lane list (A1,A2,..) to limit processing.",
    )
    return parser.parse_args()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(_read_text(path))


def _resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def _lane_sort_key(task_id: str) -> int:
    m = re.match(r"^wave20r-a(\d+)$", task_id.strip())
    if not m:
        return 10_000
    return int(m.group(1))


def _normalize_rule(rule: str) -> str:
    return rule.strip().lstrip("./")


def _normalize_path(path: str) -> str:
    return path.strip().lstrip("./")


def _is_wildcard_rule(rule: str) -> bool:
    return any(ch in rule for ch in WILDCARD_CHARS)


def _path_matches_rule(path: str, rule: str) -> bool:
    from fnmatch import fnmatch

    target = _normalize_path(path)
    candidate = _normalize_rule(rule)
    if not candidate:
        return False
    if candidate.endswith("/**"):
        return target.startswith(candidate[:-3])
    if candidate.endswith("/"):
        return target.startswith(candidate)
    if _is_wildcard_rule(candidate):
        return fnmatch(target, candidate)
    return target == candidate


def _validate_allowed_files(changed_files: list[str], allowed_rules: list[str]) -> tuple[bool, list[str]]:
    violations: list[str] = []
    for path in changed_files:
        if not any(_path_matches_rule(path, rule) for rule in allowed_rules):
            violations.append(path)
    return (len(violations) == 0, violations)


def _ensure_clean_repo(repo_root: Path) -> None:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        _die(f"Cannot read git status for target repo: {repo_root}")
    if proc.stdout.strip():
        _die(f"Target worktree is not clean: {repo_root}")


def _clean_patch_path(path: str) -> str:
    clean = path.strip()
    if clean == "/dev/null":
        return clean
    clean = clean.lstrip("/")
    if clean.startswith("a/") or clean.startswith("b/"):
        clean = clean[2:]
    return clean


def _sanitize_diff_headers(diff_text: str) -> str:
    lines = diff_text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    out: list[str] = []
    for raw in lines:
        if raw.startswith("index "):
            # Generated diffs often use fake sha values and break git apply.
            continue
        if raw.startswith("diff --git "):
            m = re.match(r"^diff --git a/(.+?) b/(.+?)$", raw)
            if m:
                a_path = _clean_patch_path(m.group(1))
                b_path = _clean_patch_path(m.group(2))
                out.append(f"diff --git a/{a_path} b/{b_path}")
                continue
        if raw.startswith("--- "):
            old = raw[4:].strip()
            if old == "/dev/null":
                out.append("--- /dev/null")
            else:
                p = _clean_patch_path(old)
                out.append(f"--- a/{p}")
            continue
        if raw.startswith("+++ "):
            new = raw[4:].strip()
            if new == "/dev/null":
                out.append("+++ /dev/null")
            else:
                p = _clean_patch_path(new)
                out.append(f"+++ b/{p}")
            continue
        out.append(raw)
    return "\n".join(out).strip() + "\n"


def _normalize_unified_diff(diff_text: str) -> str:
    lines = diff_text.splitlines()
    output: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = HUNK_HEADER_RE.match(line)
        if not match:
            output.append(line)
            i += 1
            continue

        old_start = int(match.group("a"))
        new_start = int(match.group("c"))
        tail = match.group("tail")
        i += 1
        hunk_lines: list[str] = []
        while i < len(lines):
            nxt = lines[i]
            if nxt.startswith("diff --git ") or nxt.startswith("@@ "):
                break
            hunk_lines.append(nxt)
            i += 1

        old_count = 0
        new_count = 0
        for hunk in hunk_lines:
            if not hunk:
                continue
            prefix = hunk[0]
            if prefix == " ":
                old_count += 1
                new_count += 1
            elif prefix == "-":
                old_count += 1
            elif prefix == "+":
                new_count += 1
            elif prefix == "\\":
                continue
            else:
                old_count += 1
                new_count += 1

        output.append(f"@@ -{old_start},{old_count} +{new_start},{new_count} @@{tail}")
        output.extend(hunk_lines)
    return "\n".join(output).strip() + "\n"


def _extract_changed_files(diff_text: str) -> list[str]:
    files = set()
    for _, b_path in DIFF_FILE_RE.findall(diff_text):
        files.add(_normalize_path(_clean_patch_path(b_path)))
    return sorted(item for item in files if item)


def _split_diff_blocks(diff_text: str) -> list[tuple[str, str, str]]:
    blocks: list[tuple[str, str, str]] = []
    lines = diff_text.splitlines()
    current: list[str] = []
    current_a = ""
    current_b = ""
    for raw in lines:
        if raw.startswith("diff --git "):
            if current:
                blocks.append((current_a, current_b, "\n".join(current).strip() + "\n"))
                current = []
            m = re.match(r"^diff --git a/(.+?) b/(.+?)$", raw)
            if m:
                current_a = _clean_patch_path(m.group(1))
                current_b = _clean_patch_path(m.group(2))
            else:
                current_a = ""
                current_b = ""
            current.append(raw)
        elif current:
            current.append(raw)
    if current:
        blocks.append((current_a, current_b, "\n".join(current).strip() + "\n"))
    return blocks


def _strip_docs_swarm_blocks(diff_text: str) -> tuple[str, bool]:
    blocks = _split_diff_blocks(diff_text)
    if not blocks:
        return (diff_text, False)
    kept: list[str] = []
    stripped = False
    for _, b_path, block in blocks:
        rel = _normalize_path(_clean_patch_path(b_path))
        if rel.startswith("docs/swarm_results/"):
            stripped = True
            continue
        kept.append(block.rstrip("\n"))
    if not kept:
        return ("", stripped)
    return ("\n".join(kept).strip() + "\n", stripped)


def _keep_docs_swarm_blocks(diff_text: str) -> tuple[str, bool]:
    blocks = _split_diff_blocks(diff_text)
    if not blocks:
        return ("", False)
    kept: list[str] = []
    found = False
    for _, b_path, block in blocks:
        rel = _normalize_path(_clean_patch_path(b_path))
        if rel.startswith("docs/swarm_results/"):
            found = True
            kept.append(block.rstrip("\n"))
    if not kept:
        return ("", found)
    return ("\n".join(kept).strip() + "\n", found)


def _parse_diff_file_meta(diff_text: str) -> list[dict[str, Any]]:
    metas: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in diff_text.splitlines():
        if raw.startswith("diff --git "):
            m = re.match(r"^diff --git a/(.+?) b/(.+?)$", raw)
            if m:
                current = {"a": _clean_patch_path(m.group(1)), "b": _clean_patch_path(m.group(2)), "new_file": False}
                metas.append(current)
            else:
                current = None
            continue
        if current is None:
            continue
        if raw.startswith("new file mode "):
            current["new_file"] = True
    return metas


def _seed_file_from_source_or_placeholder(
    target_repo: Path,
    source_repo: Path,
    relative_path: str,
    task_backlog_full: str,
) -> None:
    target = target_repo / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)

    source = source_repo / relative_path
    if source.exists():
        target.write_text(source.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        return

    if relative_path.startswith("docs/swarm_results/wave20r_a") and relative_path.endswith("_backlog.md"):
        target.write_text(task_backlog_full, encoding="utf-8")
        return

    if relative_path.startswith("docs/swarm_results/wave20r_agent") and relative_path.endswith("_report.md"):
        target.write_text(
            "\n".join(
                [
                    "# Wave20R Agent Report",
                    "",
                    "## Summary Table",
                    "(fill)",
                    "",
                    "## Evidence List",
                    "(fill)",
                    "",
                    "## Residual Risks",
                    "(fill)",
                    "",
                    "## Now",
                    "(fill)",
                    "",
                    "## Next",
                    "(fill)",
                    "",
                    "## Blockers",
                    "(fill)",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return

    target.write_text("", encoding="utf-8")


def _prepare_docs_targets_for_diff(target_repo: Path, source_repo: Path, task: dict[str, Any], diff_text: str) -> None:
    meta = _parse_diff_file_meta(diff_text)
    context = task.get("context_pack", {})
    backlog_full = str(context.get("backlog_full", ""))
    for file_meta in meta:
        target_rel = _normalize_path(str(file_meta.get("b", "")))
        if not target_rel.startswith("docs/swarm_results/wave20r_"):
            continue
        target = target_repo / target_rel
        is_new = bool(file_meta.get("new_file"))
        if is_new:
            if target.exists():
                target.unlink()
            continue
        if not target.exists():
            _seed_file_from_source_or_placeholder(
                target_repo=target_repo,
                source_repo=source_repo,
                relative_path=target_rel,
                task_backlog_full=backlog_full,
            )


def _run_apply(target_repo: Path, diff_path: Path) -> tuple[bool, str]:
    check_proc = subprocess.run(
        ["git", "apply", "--check", str(diff_path)],
        cwd=target_repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if check_proc.returncode == 0:
        apply_proc = subprocess.run(
            ["git", "apply", str(diff_path)],
            cwd=target_repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if apply_proc.returncode == 0:
            return (True, "applied")
        reason = (apply_proc.stderr or apply_proc.stdout).strip() or "git apply failed"
        return (False, reason)

    check_3way = subprocess.run(
        ["git", "apply", "--3way", "--check", str(diff_path)],
        cwd=target_repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if check_3way.returncode != 0:
        reason = (check_3way.stderr or check_3way.stdout or check_proc.stderr or check_proc.stdout).strip()
        return (False, reason or "git apply --check failed")

    apply_3way = subprocess.run(
        ["git", "apply", "--3way", str(diff_path)],
        cwd=target_repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if apply_3way.returncode == 0:
        return (True, "applied-3way")
    reason = (apply_3way.stderr or apply_3way.stdout).strip() or "git apply --3way failed"
    return (False, reason)


def _load_tasks(tasks_file: Path) -> dict[str, dict[str, Any]]:
    manifest = _read_json(tasks_file)
    tasks_raw = manifest.get("tasks")
    if not isinstance(tasks_raw, list):
        _die(f"Invalid tasks manifest: {tasks_file}")
    tasks: dict[str, dict[str, Any]] = {}
    for task in tasks_raw:
        if not isinstance(task, dict):
            continue
        task_id = str(task.get("id", "")).strip()
        if task_id:
            tasks[task_id] = task
    if not tasks:
        _die(f"No tasks found in: {tasks_file}")
    return tasks


def _load_run_reports(source_root: Path, swarm_dir: Path, run_ids: list[str]) -> dict[str, dict[str, Any]]:
    runs_root = swarm_dir / "wave20r_kimi_runs"
    reports: dict[str, dict[str, Any]] = {}
    for run_id in run_ids:
        report_path = runs_root / run_id / "run_report.json"
        if not report_path.exists():
            _die(f"Missing run_report.json for run: {run_id}")
        reports[run_id] = _read_json(report_path)
    return reports


def _candidate_priority(result: dict[str, Any], has_diff: bool) -> int:
    if not has_diff:
        return 3
    if "error" in result:
        return 3
    if (
        bool(result.get("ready_for_apply"))
        and bool(result.get("format_ok"))
        and bool(result.get("diff_structure_ok"))
        and bool(result.get("allowed_ok"))
        and not bool(result.get("blocked"))
    ):
        return 1
    return 2


def _collect_candidates_for_lane(
    lane_id: str,
    run_ids: list[str],
    run_reports: dict[str, dict[str, Any]],
    source_root: Path,
    swarm_dir: Path,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    runs_root = swarm_dir / "wave20r_kimi_runs"
    for run_order, run_id in enumerate(run_ids):
        report = run_reports[run_id]
        result = None
        for item in report.get("results", []):
            if str(item.get("task_id")) == lane_id:
                result = item
                break
        if result is None:
            continue

        apply_status = ""
        apply_reason = ""
        for entry in report.get("apply_report", []):
            if str(entry.get("task_id")) == lane_id:
                apply_status = str(entry.get("status", ""))
                apply_reason = str(entry.get("reason", ""))
                break

        diff_dir = runs_root / run_id / "diffs"
        variants: list[Path] = []
        normalized = diff_dir / f"{lane_id}.normalized.diff"
        regular = diff_dir / f"{lane_id}.diff"
        if normalized.exists():
            variants.append(normalized)
        if regular.exists():
            variants.append(regular)

        if not variants and isinstance(result.get("diff"), str) and result.get("diff", "").strip():
            fallback_path = diff_dir / f"{lane_id}.from_report.diff"
            fallback_path.write_text(str(result.get("diff")), encoding="utf-8")
            variants.append(fallback_path)

        if not variants:
            candidates.append(
                {
                    "lane": lane_id,
                    "run_id": run_id,
                    "run_order": run_order,
                    "diff_path": "",
                    "priority": 3,
                    "apply_status": apply_status,
                    "apply_reason": apply_reason,
                    "result": result,
                }
            )
            continue

        for idx, variant in enumerate(variants):
            candidates.append(
                {
                    "lane": lane_id,
                    "run_id": run_id,
                    "run_order": run_order,
                    "variant_order": idx,
                    "diff_path": str(variant.relative_to(source_root)),
                    "priority": _candidate_priority(result, has_diff=True),
                    "apply_status": apply_status,
                    "apply_reason": apply_reason,
                    "result": result,
                }
            )

    candidates.sort(key=lambda c: (int(c.get("priority", 3)), int(c.get("run_order", 99)), int(c.get("variant_order", 9))))
    return candidates


def _try_apply_candidate(
    *,
    target_repo: Path,
    source_repo: Path,
    lane_id: str,
    task: dict[str, Any],
    candidate: dict[str, Any],
    artifacts_tmp: Path,
    dry_run: bool,
) -> tuple[bool, str, str, list[str], list[str]]:
    source_diff_rel = str(candidate.get("diff_path", ""))
    if not source_diff_rel:
        return (False, "no_diff", "none", [], [])

    source_diff_path = source_repo / source_diff_rel
    if not source_diff_path.exists():
        return (False, f"missing_diff:{source_diff_rel}", "none", [], [])

    raw = _read_text(source_diff_path)
    if not raw.strip():
        return (False, "empty_diff", "none", [], [])

    sanitized = _normalize_unified_diff(_sanitize_diff_headers(raw))
    changed_files = _extract_changed_files(sanitized)
    if not changed_files:
        return (False, "no_changed_files_after_sanitize", "none", [], [])

    allowed_rules = [str(x) for x in task.get("allowed_files", [])]
    allowed_ok, violations = _validate_allowed_files(changed_files, allowed_rules)
    if not allowed_ok:
        return (False, f"out_of_scope:{','.join(violations)}", "none", changed_files, violations)

    if dry_run:
        return (True, "dry_run_ready", "full", changed_files, [])

    _prepare_docs_targets_for_diff(target_repo, source_repo, task, sanitized)
    full_diff_path = artifacts_tmp / f"{lane_id}.{candidate['run_id']}.full.diff"
    full_diff_path.write_text(sanitized, encoding="utf-8")

    ok, reason = _run_apply(target_repo, full_diff_path)
    if ok:
        return (True, reason, "full", changed_files, [])

    docs_only_diff, has_docs = _keep_docs_swarm_blocks(sanitized)
    if has_docs and docs_only_diff.strip():
        docs_changed = _extract_changed_files(docs_only_diff)
        docs_ok, docs_violations = _validate_allowed_files(docs_changed, allowed_rules)
        if docs_ok:
            _prepare_docs_targets_for_diff(target_repo, source_repo, task, docs_only_diff)
            docs_only_path = artifacts_tmp / f"{lane_id}.{candidate['run_id']}.docsonly.diff"
            docs_only_path.write_text(docs_only_diff, encoding="utf-8")
            ok_docs, reason_docs = _run_apply(target_repo, docs_only_path)
            if ok_docs:
                return (True, reason_docs, "docs_only", docs_changed, [])
            reason = f"{reason}; docs_only:{reason_docs}"
        else:
            reason = f"{reason}; docs_only_out_of_scope:{','.join(docs_violations)}"

    stripped_diff, stripped_any = _strip_docs_swarm_blocks(sanitized)
    if stripped_any and stripped_diff.strip():
        stripped_changed = _extract_changed_files(stripped_diff)
        stripped_ok, stripped_violations = _validate_allowed_files(stripped_changed, allowed_rules)
        if stripped_ok:
            _prepare_docs_targets_for_diff(target_repo, source_repo, task, stripped_diff)
            stripped_diff_path = artifacts_tmp / f"{lane_id}.{candidate['run_id']}.stripdocs.diff"
            stripped_diff_path.write_text(stripped_diff, encoding="utf-8")
            ok2, reason2 = _run_apply(target_repo, stripped_diff_path)
            if ok2:
                return (True, reason2, "strip_docs_swarm", stripped_changed, [])
            return (False, f"{reason}; strip_docs:{reason2}", "strip_docs_swarm", stripped_changed, stripped_violations)
        return (False, f"{reason}; strip_docs_out_of_scope:{','.join(stripped_violations)}", "strip_docs_swarm", stripped_changed, stripped_violations)

    return (False, reason, "full", changed_files, [])


def _write_matrix_md(path: Path, outcomes: list[LaneOutcome]) -> None:
    lines: list[str] = []
    lines.append("# Wave20R Offline Recovery Matrix")
    lines.append("")
    lines.append(f"- generated_at_utc: `{dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()}`")
    lines.append("")
    lines.append("| lane | status | selected_run | selected_diff | priority | apply_variant | changed_files | reason |")
    lines.append("|---|---|---|---|---:|---|---:|---|")
    for out in outcomes:
        lines.append(
            f"| `{out.lane}` | `{out.status}` | `{out.selected_run}` | `{out.selected_diff}` | "
            f"{out.priority} | `{out.apply_variant}` | {len(out.changed_files)} | {out.reason.replace('|', '/')} |"
        )
    lines.append("")
    lines.append("## Attempt Log")
    lines.append("")
    for out in outcomes:
        lines.append(f"### {out.lane}")
        if not out.attempts:
            lines.append("- no attempts")
            lines.append("")
            continue
        for att in out.attempts:
            lines.append(
                f"- run `{att.run_id}` | diff `{att.source_diff}` | priority `{att.priority}` | "
                f"variant `{att.variant}` | status `{att.status}` | reason `{att.reason}`"
            )
        lines.append("")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main() -> None:
    args = _parse_args()
    target_repo = Path(args.repo_root).resolve()
    source_root = Path(args.source_root).resolve()
    if not target_repo.exists():
        _die(f"Target repo does not exist: {target_repo}")
    if not source_root.exists():
        _die(f"Source root does not exist: {source_root}")

    if not args.allow_dirty_target and not args.dry_run:
        _ensure_clean_repo(target_repo)

    run_ids = [item.strip() for item in str(args.runs).split(",") if item.strip()]
    if not run_ids:
        _die("No run ids provided.")

    swarm_dir = _resolve_path(source_root, args.swarm_dir)
    if not swarm_dir.exists():
        _die(f"Swarm dir missing: {swarm_dir}")

    tasks_file = _resolve_path(source_root, args.tasks_file)
    tasks = _load_tasks(tasks_file)
    run_reports = _load_run_reports(source_root, swarm_dir, run_ids)

    only_lanes: set[str] = set()
    if args.only_lanes.strip():
        for raw in args.only_lanes.split(","):
            lane = raw.strip().upper()
            if not lane:
                continue
            if lane.startswith("A") and lane[1:].isdigit():
                only_lanes.add(f"wave20r-a{int(lane[1:])}")
            elif lane.startswith("WAVE20R-A") and lane.split("-")[-1].isdigit():
                only_lanes.add(f"wave20r-a{int(lane.split('-')[-1])}")

    all_lane_ids = sorted([k for k in tasks.keys() if re.match(r"^wave20r-a\d+$", k)], key=_lane_sort_key)
    if only_lanes:
        lane_ids = [lane for lane in all_lane_ids if lane in only_lanes]
    else:
        lane_ids = all_lane_ids
    if not lane_ids:
        _die("No lanes selected for recovery.")

    output_dir = _resolve_path(source_root, "docs/swarm_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    artifacts_tmp = output_dir / f"{args.output_prefix}_tmp_{stamp}"
    artifacts_tmp.mkdir(parents=True, exist_ok=True)

    outcomes: list[LaneOutcome] = []
    for lane_id in lane_ids:
        task = tasks[lane_id]
        candidates = _collect_candidates_for_lane(
            lane_id=lane_id,
            run_ids=run_ids,
            run_reports=run_reports,
            source_root=source_root,
            swarm_dir=swarm_dir,
        )
        attempts: list[LaneAttempt] = []
        applied = False
        selected_run = ""
        selected_diff = ""
        priority = 3
        apply_variant = "none"
        changed_files: list[str] = []
        reason = "no_candidate"

        for cand in candidates:
            run_id = str(cand.get("run_id", ""))
            source_diff = str(cand.get("diff_path", ""))
            cand_priority = int(cand.get("priority", 3))
            ok, attempt_reason, variant, changed, violations = _try_apply_candidate(
                target_repo=target_repo,
                source_repo=source_root,
                lane_id=lane_id,
                task=task,
                candidate=cand,
                artifacts_tmp=artifacts_tmp,
                dry_run=args.dry_run,
            )
            attempts.append(
                LaneAttempt(
                    lane=lane_id,
                    run_id=run_id,
                    source_diff=source_diff,
                    priority=cand_priority,
                    variant=variant,
                    changed_files=changed,
                    allowed_ok=(len(violations) == 0),
                    violations=violations,
                    status="applied" if ok else "failed",
                    reason=attempt_reason,
                )
            )
            if ok:
                applied = True
                selected_run = run_id
                selected_diff = source_diff
                priority = cand_priority
                apply_variant = variant
                changed_files = changed
                reason = attempt_reason
                break
            if not selected_run:
                selected_run = run_id
                selected_diff = source_diff
                priority = cand_priority
                apply_variant = variant
                changed_files = changed
                reason = attempt_reason

        outcomes.append(
            LaneOutcome(
                lane=lane_id.replace("wave20r-", "").upper(),
                status="applied" if applied else "defer",
                selected_run=selected_run,
                selected_diff=selected_diff,
                priority=priority,
                apply_variant=apply_variant,
                changed_files=changed_files,
                reason=reason,
                attempts=attempts,
            )
        )
        print(
            f"{lane_id}: status={'applied' if applied else 'defer'} "
            f"run={selected_run or '-'} diff={selected_diff or '-'} reason={reason}"
        )

    applied_count = sum(1 for out in outcomes if out.status == "applied")
    defer_count = len(outcomes) - applied_count
    summary = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "target_repo": str(target_repo),
        "source_root": str(source_root),
        "runs": run_ids,
        "dry_run": bool(args.dry_run),
        "lanes_total": len(outcomes),
        "lanes_applied": applied_count,
        "lanes_defer": defer_count,
        "outcomes": [asdict(out) for out in outcomes],
    }

    json_out = output_dir / f"{args.output_prefix}_matrix.json"
    md_out = output_dir / f"{args.output_prefix}_matrix.md"
    log_out = output_dir / f"{args.output_prefix}_apply_log.md"
    json_out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_matrix_md(md_out, outcomes)

    log_lines = [
        "# Wave20R Offline Recovery Apply Log",
        "",
        f"- generated_at_utc: `{summary['generated_at_utc']}`",
        f"- target_repo: `{target_repo}`",
        f"- source_root: `{source_root}`",
        f"- runs: `{', '.join(run_ids)}`",
        f"- lanes_applied: `{applied_count}`",
        f"- lanes_defer: `{defer_count}`",
        "",
    ]
    for out in outcomes:
        log_lines.append(f"## {out.lane}")
        log_lines.append(f"- status: `{out.status}`")
        log_lines.append(f"- selected_run: `{out.selected_run}`")
        log_lines.append(f"- selected_diff: `{out.selected_diff}`")
        log_lines.append(f"- reason: `{out.reason}`")
        for att in out.attempts:
            log_lines.append(
                f"  - attempt run={att.run_id} diff={att.source_diff} priority={att.priority} "
                f"variant={att.variant} status={att.status} reason={att.reason}"
            )
        log_lines.append("")
    log_out.write_text("\n".join(log_lines).strip() + "\n", encoding="utf-8")

    print(f"Wrote: {json_out}")
    print(f"Wrote: {md_out}")
    print(f"Wrote: {log_out}")
    print(f"Summary: lanes_total={len(outcomes)} applied={applied_count} defer={defer_count}")


if __name__ == "__main__":
    main()
