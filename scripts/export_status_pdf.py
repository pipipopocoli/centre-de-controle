#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.status_report import build_status_html, collect_status_snapshot, render_pdf_from_html  # noqa: E402


def _default_out_path() -> Path:
    today = datetime.now().astimezone().strftime("%Y-%m-%d")
    return Path.home() / "Desktop" / f"COCKPIT_STATUS_{today}.pdf"


def _resolve_project_roots(project_id: str, scope: str) -> tuple[Path, Path]:
    repo_project_root = ROOT_DIR / "control" / "projects" / project_id
    appsupport_project_root = (
        Path.home() / "Library" / "Application Support" / "Cockpit" / "projects" / project_id
    )
    if scope == "repo":
        return repo_project_root, repo_project_root
    if scope == "appsupport":
        return appsupport_project_root, appsupport_project_root
    return repo_project_root, appsupport_project_root


def _resolve_output(path: Path) -> Path:
    candidate = path.expanduser().resolve()
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix or ".pdf"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    return candidate.with_name(f"{stem}_{stamp}{suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Cockpit dual-root status report to PDF.")
    parser.add_argument("--project-id", default="cockpit", help="Project id (default: cockpit).")
    parser.add_argument(
        "--scope",
        default="dual-root",
        choices=["dual-root", "repo", "appsupport"],
        help="Data scope: dual-root (default), repo, or appsupport.",
    )
    parser.add_argument(
        "--out",
        default=str(_default_out_path()),
        help="PDF output path (default: ~/Desktop/COCKPIT_STATUS_<date>.pdf).",
    )
    parser.add_argument("--language", default="fr", help="Report language (default: fr).")
    parser.add_argument("--json", action="store_true", help="Print JSON payload in addition to summary line.")
    args = parser.parse_args()

    project_id = str(args.project_id).strip() or "cockpit"
    repo_root, appsupport_root = _resolve_project_roots(project_id, str(args.scope))

    snapshot = collect_status_snapshot(
        project_id=project_id,
        repo_root=repo_root,
        appsupport_root=appsupport_root,
    )
    html_content = build_status_html(snapshot, language=args.language)

    output_path = _resolve_output(Path(args.out))
    final_pdf = render_pdf_from_html(html_content, output_path)

    payload = {
        "project_id": project_id,
        "scope": str(args.scope),
        "overall_status": snapshot.get("overall_status", "unknown"),
        "bugs": len(snapshot.get("bugs", [])),
        "missing": len(snapshot.get("missing", [])),
        "out": str(final_pdf),
        "size_bytes": final_pdf.stat().st_size if final_pdf.exists() else 0,
    }

    if args.json:
        print(json.dumps(payload, indent=2))

    print(f"out={payload['out']}")
    print(f"size_bytes={payload['size_bytes']}")
    print(f"overall_status={payload['overall_status']}")
    print(f"bugs={payload['bugs']}")
    print(f"missing={payload['missing']}")
    print(
        "StatusPdfSummary "
        f"project_id={payload['project_id']} "
        f"scope={payload['scope']} "
        f"overall={payload['overall_status']} "
        f"bugs={payload['bugs']} "
        f"missing={payload['missing']} "
        f"out={payload['out']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
