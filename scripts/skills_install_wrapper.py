#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.skills_installer import summary_to_dict, sync_skills  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Skills installer wrapper (idempotent + dry_run).",
    )
    parser.add_argument("--project-id", required=True, help="Target project id")
    parser.add_argument(
        "--skill",
        action="append",
        default=[],
        help="Skill id to sync (repeatable)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report actions without mutating install_state.json",
    )
    parser.add_argument(
        "--projects-root",
        default=None,
        help="Optional projects root override",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    projects_root = Path(args.projects_root).expanduser() if args.projects_root else None
    try:
        summary = sync_skills(
            args.project_id,
            args.skill or [],
            projects_root=projects_root,
            dry_run=bool(args.dry_run),
        )
    except Exception as exc:  # noqa: BLE001 - wrapper fatal error
        print(json.dumps({"error": f"wrapper_failed:{exc}"}))
        return 1

    print(json.dumps(summary_to_dict(summary), indent=2))
    if summary.error:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
