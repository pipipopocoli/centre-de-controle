#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import resolve_projects_root  # noqa: E402
from app.services.reliability_core import append_wal_record, recover_from_wal, verify_wal_integrity  # noqa: E402


def _inject_crash(projects_root: Path, project_id: str, run_id: str) -> dict[str, str]:
    tx_id = f"{run_id}:inject_crash"
    wal = append_wal_record(
        projects_root,
        project_id,
        tx_id=tx_id,
        record_type="begin",
        payload={
            "run_id": run_id,
            "reason": "crash_injected",
            "note": "simulated interruption between wal begin and commit",
        },
    )
    return {
        "status": "crash_injected",
        "project_id": project_id,
        "run_id": run_id,
        "tx_id": tx_id,
        "wal_id": wal.wal_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Reliability recovery CLI (CAP-L1-006)")
    parser.add_argument("--project", default=None, help="Project id")
    parser.add_argument("--data-dir", default=None, help="Projects root (repo/app/or absolute path)")

    sub = parser.add_subparsers(dest="command", required=True)

    inject = sub.add_parser("inject-crash", help="Inject crash between WAL begin and commit")
    inject.add_argument("--project", default=None, help="Project id")
    inject.add_argument("--data-dir", default=None, help="Projects root (repo/app/or absolute path)")
    inject.add_argument("--run-id", required=True, help="Run id")

    verify = sub.add_parser("verify", help="Verify WAL checksums and quarantine corrupted records")
    verify.add_argument("--project", default=None, help="Project id")
    verify.add_argument("--data-dir", default=None, help="Projects root (repo/app/or absolute path)")

    recover = sub.add_parser("recover", help="Recover incomplete transactions from WAL")
    recover.add_argument("--project", default=None, help="Project id")
    recover.add_argument("--data-dir", default=None, help="Projects root (repo/app/or absolute path)")
    recover.add_argument("--run-id", default=None, help="Optional run id for targeted bundle rebuild")

    args = parser.parse_args()
    project_id = str(getattr(args, "project", None) or "cockpit").strip() or "cockpit"
    data_dir = getattr(args, "data_dir", None)
    projects_root = resolve_projects_root(data_dir, env={})

    if args.command == "inject-crash":
        payload = _inject_crash(projects_root, project_id, args.run_id)
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "verify":
        payload = verify_wal_integrity(projects_root, project_id)
        print(json.dumps(payload, indent=2))
        if int(payload.get("quarantined_records") or 0) > 0:
            return 2
        return 0

    if args.command == "recover":
        try:
            payload = recover_from_wal(projects_root, project_id, run_id=args.run_id)
        except Exception as exc:
            print(json.dumps({"status": "recovery_failed", "error": str(exc)}, indent=2))
            return 3
        print(json.dumps(payload, indent=2))
        return 0

    return 3


if __name__ == "__main__":
    raise SystemExit(main())
