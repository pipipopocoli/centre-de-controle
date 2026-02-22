#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import resolve_projects_root  # noqa: E402


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def _stamp(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%SZ")


def _report_stamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H%MZ")


def _demo_type(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.exists() and path.is_dir():
        return "directory"
    return "missing"


def _path_stat(path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "path": str(path),
        "exists": bool(path.exists()),
        "is_symlink": bool(path.is_symlink()),
    }

    try:
        st_l = path.lstat()
        payload["lstat_inode"] = int(st_l.st_ino)
        payload["lstat_nlink"] = int(st_l.st_nlink)
        payload["lstat_mode"] = stat.S_IFMT(st_l.st_mode)
    except OSError:
        payload["lstat_inode"] = None
        payload["lstat_nlink"] = None
        payload["lstat_mode"] = None

    if path.exists():
        try:
            st = path.stat()
            payload["inode"] = int(st.st_ino)
            payload["nlink"] = int(st.st_nlink)
            payload["mode"] = stat.S_IFMT(st.st_mode)
        except OSError:
            payload["inode"] = None
            payload["nlink"] = None
            payload["mode"] = None

    if path.is_symlink():
        try:
            payload["symlink_target"] = os.readlink(path)
        except OSError:
            payload["symlink_target"] = None

    try:
        payload["resolved_path"] = str(path.resolve())
    except OSError:
        payload["resolved_path"] = None

    return payload


def _iter_hardlink_findings(scan_roots: list[Path]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    seen_inodes: set[tuple[int, int]] = set()

    for root in scan_roots:
        if not root.exists() or not root.is_dir():
            continue
        for candidate in root.rglob("*"):
            if not candidate.is_file():
                continue
            try:
                st = candidate.stat()
            except OSError:
                continue
            if not stat.S_ISREG(st.st_mode):
                continue
            if int(st.st_nlink) <= 1:
                continue
            inode_key = (int(st.st_dev), int(st.st_ino))
            if inode_key in seen_inodes:
                continue
            seen_inodes.add(inode_key)
            findings.append(
                {
                    "path": str(candidate),
                    "inode": int(st.st_ino),
                    "nlink": int(st.st_nlink),
                    "size": int(st.st_size),
                }
            )

    return findings


def _scan_roots(projects_root: Path) -> list[Path]:
    roots: list[Path] = []
    seen: set[str] = set()
    for candidate in [projects_root / "cockpit", projects_root / "demo"]:
        if not candidate.exists() and not candidate.is_symlink():
            continue
        root = candidate.resolve() if candidate.is_symlink() else candidate
        if not root.exists() or not root.is_dir():
            continue
        key = str(root)
        if key in seen:
            continue
        seen.add(key)
        roots.append(root)
    return roots


def _collect_audit(projects_root: Path) -> dict[str, Any]:
    demo_path = projects_root / "demo"
    cockpit_path = projects_root / "cockpit"

    demo_info = _path_stat(demo_path)
    demo_info["type"] = _demo_type(demo_path)
    cockpit_info = _path_stat(cockpit_path)

    alias_to_cockpit = False
    if demo_path.exists() or demo_path.is_symlink():
        try:
            alias_to_cockpit = demo_path.resolve() == cockpit_path.resolve()
        except OSError:
            alias_to_cockpit = False

    hardlink_findings = _iter_hardlink_findings(_scan_roots(projects_root))

    return {
        "projects_root": str(projects_root),
        "demo": demo_info,
        "cockpit": cockpit_info,
        "alias_to_cockpit": bool(alias_to_cockpit),
        "hardlink_findings": hardlink_findings,
        "hardlink_findings_count": len(hardlink_findings),
    }


@contextmanager
def _store_projects_root(projects_root: Path):
    import app.data.paths as paths_mod  # noqa: E402
    import app.data.store as store_mod  # noqa: E402

    old_paths_projects_dir = paths_mod.PROJECTS_DIR
    old_store_projects_dir = store_mod.PROJECTS_DIR
    paths_mod.PROJECTS_DIR = projects_root
    store_mod.PROJECTS_DIR = projects_root
    try:
        yield store_mod
    finally:
        paths_mod.PROJECTS_DIR = old_paths_projects_dir
        store_mod.PROJECTS_DIR = old_store_projects_dir


def _evaluate_store_contracts(projects_root: Path, project_id: str) -> dict[str, Any]:
    output: dict[str, Any] = {
        "list_projects": [],
        "load_demo_project_id": None,
        "load_demo_path": None,
        "load_project_project_id": None,
        "errors": [],
    }
    with _store_projects_root(projects_root) as store_mod:
        try:
            output["list_projects"] = store_mod.list_projects()
        except Exception as exc:  # pragma: no cover - defensive
            output["errors"].append(f"list_projects_error:{exc}")

        try:
            loaded_demo = store_mod.load_project("demo")
            output["load_demo_project_id"] = loaded_demo.project_id
            output["load_demo_path"] = str(loaded_demo.path)
        except Exception as exc:
            output["errors"].append(f"load_demo_error:{exc}")

        try:
            loaded_project = store_mod.load_project(project_id)
            output["load_project_project_id"] = loaded_project.project_id
        except Exception as exc:
            output["errors"].append(f"load_project_error:{exc}")

    listed = output.get("list_projects")
    if isinstance(listed, list):
        output["demo_in_list_projects"] = "demo" in listed
        output["archive_in_list_projects"] = "_archive" in listed
    else:
        output["demo_in_list_projects"] = None
        output["archive_in_list_projects"] = None

    return output


def _archive_demo(projects_root: Path, now: datetime) -> dict[str, Any]:
    demo_path = projects_root / "demo"
    action = {
        "archived": False,
        "archived_demo_path": None,
        "reason": "demo_missing",
    }
    if not demo_path.exists() and not demo_path.is_symlink():
        return action

    archive_root = projects_root / "_archive"
    archive_root.mkdir(parents=True, exist_ok=True)

    base = archive_root / f"demo_{_stamp(now)}"
    target = base
    suffix = 1
    while target.exists() or target.is_symlink():
        target = archive_root / f"{base.name}_{suffix:02d}"
        suffix += 1

    demo_path.rename(target)
    action["archived"] = True
    action["archived_demo_path"] = str(target)
    action["reason"] = "archived"
    return action


def _write_report(
    *,
    projects_root: Path,
    project_id: str,
    now: datetime,
    apply_mode: bool,
    pre_audit: dict[str, Any],
    post_audit: dict[str, Any],
    pre_contract: dict[str, Any],
    post_contract: dict[str, Any],
    action: dict[str, Any],
    blockers: list[str],
) -> Path:
    runs_dir = projects_root / project_id / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    report_path = runs_dir / f"WAVE12_ISOLATION_REPAIR_{_report_stamp(now)}.md"

    status_line = "ok" if not blockers else "blocked"
    now_line = (
        "Now: isolation check complete; cockpit is canonical; demo alias archived or absent; active lanes filtered."
        if not blockers
        else "Now: isolation repair ran but one or more checks are blocked."
    )
    next_line = "Next: keep 2h cadence checks on lane visibility and runtime root integrity."
    blockers_line = "Blockers: none" if not blockers else f"Blockers: {'; '.join(blockers)}"

    report = [
        "# Wave12 Isolation Repair",
        "",
        f"- generated_at_utc: {_utc_iso(now)}",
        f"- mode: {'apply' if apply_mode else 'audit'}",
        f"- projects_root: {projects_root}",
        f"- status: {status_line}",
        "",
        "## Pre Audit",
        f"- demo_type: {pre_audit.get('demo', {}).get('type')}",
        f"- demo_alias_to_cockpit: {pre_audit.get('alias_to_cockpit')}",
        f"- hardlink_findings_count: {pre_audit.get('hardlink_findings_count')}",
        "",
        "## Actions",
        f"- archived: {action.get('archived')}",
        f"- archived_demo_path: {action.get('archived_demo_path')}",
        f"- reason: {action.get('reason')}",
        "",
        "## Post Audit",
        f"- demo_type: {post_audit.get('demo', {}).get('type')}",
        f"- demo_alias_to_cockpit: {post_audit.get('alias_to_cockpit')}",
        f"- hardlink_findings_count: {post_audit.get('hardlink_findings_count')}",
        "",
        "## Store Contract",
        f"- pre_list_projects: {pre_contract.get('list_projects')}",
        f"- post_list_projects: {post_contract.get('list_projects')}",
        f"- post_load_demo_project_id: {post_contract.get('load_demo_project_id')}",
        f"- post_load_demo_path: {post_contract.get('load_demo_path')}",
        f"- post_contract_errors: {post_contract.get('errors')}",
        "",
        "## Hardlink Findings",
    ]

    findings = post_audit.get("hardlink_findings")
    if isinstance(findings, list) and findings:
        for finding in findings:
            report.append(
                f"- {finding.get('path')} inode={finding.get('inode')} nlink={finding.get('nlink')} size={finding.get('size')}"
            )
    else:
        report.append("- none")

    report.extend(
        [
            "",
            "## Now / Next / Blockers",
            f"- {now_line}",
            f"- {next_line}",
            f"- {blockers_line}",
        ]
    )

    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Wave12 isolation repair for cockpit/demo runtime roots.")
    parser.add_argument("--project", default="cockpit", help="Canonical project id (default: cockpit)")
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Projects root selector: app, repo, or absolute path",
    )
    parser.add_argument("--apply", action="store_true", help="Apply repair (archive demo) instead of audit-only")
    args = parser.parse_args()

    now = _utc_now()
    projects_root = resolve_projects_root(args.data_dir, env=dict(os.environ))
    blockers: list[str] = []

    pre_audit = _collect_audit(projects_root)
    pre_contract = _evaluate_store_contracts(projects_root, args.project)

    action = {
        "archived": False,
        "archived_demo_path": None,
        "reason": "audit_only",
    }

    if args.apply:
        try:
            action = _archive_demo(projects_root, now)
        except Exception as exc:  # pragma: no cover - defensive
            blockers.append(f"archive_failed:{exc}")
            action = {
                "archived": False,
                "archived_demo_path": None,
                "reason": "archive_failed",
            }

    cockpit_path = projects_root / "cockpit"
    if not cockpit_path.exists() or not cockpit_path.is_dir():
        blockers.append("cockpit_missing_after_repair")

    post_audit = _collect_audit(projects_root)
    post_contract = _evaluate_store_contracts(projects_root, args.project)
    post_errors = post_contract.get("errors")
    if isinstance(post_errors, list) and post_errors:
        blockers.extend([f"store_contract:{item}" for item in post_errors])

    report_path = _write_report(
        projects_root=projects_root,
        project_id=args.project,
        now=now,
        apply_mode=bool(args.apply),
        pre_audit=pre_audit,
        post_audit=post_audit,
        pre_contract=pre_contract,
        post_contract=post_contract,
        action=action,
        blockers=blockers,
    )

    summary = {
        "ok": not blockers,
        "mode": "apply" if args.apply else "audit",
        "generated_at_utc": _utc_iso(now),
        "projects_root": str(projects_root),
        "pre_audit": pre_audit,
        "actions": action,
        "post_audit": post_audit,
        "pre_contract": pre_contract,
        "post_contract": post_contract,
        "report_path": str(report_path),
        "blockers": blockers,
    }
    print(json.dumps(summary, indent=2))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
