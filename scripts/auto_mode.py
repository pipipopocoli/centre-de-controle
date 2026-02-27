#!/usr/bin/env python3
"""
Auto-mode runner (local-first).

Reads run requests from a project's data dir and:
- writes per-agent inbox NDJSON files
- copies a prompt to clipboard
- opens the target app (Codex/Antigravity) based on agent mapping

Default data dir (projects root) is macOS App Support:
  ~/Library/Application Support/Cockpit/projects
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import (  # noqa: E402
    CONTROL_CADENCE_KPI_MIN_INTERVAL_MINUTES,
    _dispatch_config,
    _load_project_settings,
    emit_control_cadence_kpi_snapshot,
)
from scripts.auto_mode_healthcheck import evaluate_healthcheck  # noqa: E402
from scripts.auto_mode_core import (  # noqa: E402
    DEFAULT_PROJECT,
    dispatch_once,
    load_config,
    resolve_projects_root,
)


def _dispatch_audit_snapshot(projects_root: Path, project_id: str, max_actions_requested: int) -> dict[str, Any]:
    settings = _load_project_settings(projects_root / project_id)
    dispatch_cfg = _dispatch_config(settings)
    requested = max(0, int(max_actions_requested))
    effective = requested
    reason = "credit_guard_disabled"

    if bool(dispatch_cfg["credit_guard_enabled"]):
        configured_cap = int(dispatch_cfg["max_actions_effective"])
        if configured_cap > 0:
            if requested > configured_cap:
                effective = configured_cap
                reason = "credit_guard_cap_applied"
            else:
                reason = "credit_guard_enabled_no_cap"
        else:
            reason = "credit_guard_enabled_no_cap"

    return {
        "max_actions_requested": requested,
        "max_actions_effective": effective,
        "credit_guard_enabled": bool(dispatch_cfg["credit_guard_enabled"]),
        "codex_only_enabled": bool(dispatch_cfg["codex_only_enabled"]),
        "allowed_platforms": list(dispatch_cfg["allowed_platforms"]),
        "allowed_agents": sorted(str(item) for item in dispatch_cfg["allowed_agents"]),
        "credit_guard_reason": reason,
    }


def _print_dispatch_audit_line(audit: dict[str, Any]) -> None:
    allowed_platforms = ",".join(str(item) for item in audit.get("allowed_platforms", []))
    allowed_agents = ",".join(str(item) for item in audit.get("allowed_agents", []))
    print(
        "DispatchAudit "
        f"codex_only_enabled={str(bool(audit.get('codex_only_enabled'))).lower()} "
        f"credit_guard_enabled={str(bool(audit.get('credit_guard_enabled'))).lower()} "
        f"max_actions_requested={int(audit.get('max_actions_requested') or 0)} "
        f"max_actions_effective={int(audit.get('max_actions_effective') or 0)} "
        f"credit_guard_reason={str(audit.get('credit_guard_reason') or '')} "
        f"allowed_platforms={allowed_platforms} "
        f"allowed_agents={allowed_agents}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-mode runner for Cockpit run requests.")
    parser.add_argument("--project", default=None, help="Project id (default: COCKPIT_PROJECT_ID or cockpit)")
    parser.add_argument(
        "--data-dir",
        default=None,
        help=(
            "Projects root (default: App Support). Special values: repo, app. "
            "If you pass the Cockpit base dir, /projects will be appended."
        ),
    )
    parser.add_argument("--interval", type=float, default=5.0, help="Polling interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--no-open", action="store_true", help="Do not open apps")
    parser.add_argument("--no-clipboard", action="store_true", help="Do not copy to clipboard")
    parser.add_argument("--no-notify", action="store_true", help="Do not send macOS notifications")
    parser.add_argument("--config", default=None, help="Path to auto-mode config JSON")
    parser.add_argument(
        "--max-actions",
        type=int,
        default=None,
        help="Override max clipboard/open/notify actions per cycle",
    )
    parser.add_argument(
        "--print-prompt",
        action="store_true",
        help="Print the prompt to stdout when actions are triggered",
    )
    parser.add_argument(
        "--no-kpi-snapshot",
        action="store_true",
        help="Disable control-cadence KPI snapshot emission",
    )
    parser.add_argument(
        "--kpi-min-interval-minutes",
        type=int,
        default=CONTROL_CADENCE_KPI_MIN_INTERVAL_MINUTES,
        help="Minimum interval between KPI snapshots for cadence mode",
    )
    parser.add_argument(
        "--pulse-only",
        action="store_true",
        help=(
            "Run one pulse cycle with no dispatch side effects "
            "(equivalent to --once --max-actions 0 --no-open --no-clipboard --no-notify)."
        ),
    )
    parser.add_argument(
        "--dual-root-checkpoint",
        action="store_true",
        help="Run pulse+health checkpoint for both repo and app roots and emit combined JSON summary.",
    )
    parser.add_argument(
        "--dual-root-repo-data-dir",
        default="repo",
        help="Projects root selector/path for repo checkpoint leg (default: repo).",
    )
    parser.add_argument(
        "--dual-root-app-data-dir",
        default="app",
        help="Projects root selector/path for app checkpoint leg (default: app).",
    )
    args = parser.parse_args()

    project_id = args.project or os.environ.get("COCKPIT_PROJECT_ID") or DEFAULT_PROJECT
    projects_root = resolve_projects_root(args.data_dir)

    if args.pulse_only:
        args.once = True
        args.max_actions = 0
        args.no_open = True
        args.no_clipboard = True
        args.no_notify = True

    if args.dual_root_checkpoint:
        checkpoint_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        summary: dict[str, Any] = {
            "checkpoint_at": checkpoint_at,
            "project_id": project_id,
        }
        overall_status = "healthy"
        root_specs = (
            ("repo", resolve_projects_root(args.dual_root_repo_data_dir)),
            ("app", resolve_projects_root(args.dual_root_app_data_dir)),
        )

        for label, root in root_specs:
            root_config, _ = load_config(None, root, project_id)
            pulse_stats = dispatch_once(
                root,
                project_id,
                do_open=False,
                do_clipboard=False,
                do_notify=False,
                max_actions=0,
                print_prompt=False,
                config=root_config,
            )
            pulse_snapshot = emit_control_cadence_kpi_snapshot(
                root,
                project_id,
                min_interval_minutes=max(int(args.kpi_min_interval_minutes), 1),
            )
            health = evaluate_healthcheck(
                project=project_id,
                data_dir=str(root),
                stale_seconds=3600,
                max_open=3,
                max_snapshot_age_seconds=2100,
                autopulse_guard=True,
                autopulse_min_interval_minutes=max(int(args.kpi_min_interval_minutes), 1),
            )
            if str(health.get("status")) != "healthy":
                overall_status = "degraded"

            summary[label] = {
                "projects_root": str(root),
                "pulse": {
                    "dispatched": int(pulse_stats.get("dispatched") or 0),
                    "skipped": int(pulse_stats.get("skipped") or 0),
                    "actions_used": int(pulse_stats.get("actions_used") or 0),
                    "gate_blocked": int(pulse_stats.get("gate_blocked") or 0),
                    "state_path": str(pulse_stats.get("state_path") or ""),
                    "snapshot": pulse_snapshot,
                },
                "dispatch_audit": _dispatch_audit_snapshot(root, project_id, 0),
                "health": health,
                "status": str(health.get("status") or "degraded"),
            }

        summary["overall_status"] = overall_status
        print(json.dumps(summary, indent=2))
        return 0 if overall_status == "healthy" else 1

    do_open = not args.no_open
    do_clipboard = not args.no_clipboard
    do_notify = not args.no_notify

    config_path = Path(args.config).expanduser() if args.config else None
    config, resolved = load_config(config_path, projects_root, project_id)
    max_actions = args.max_actions if args.max_actions is not None else int(config.get("max_actions", 1))
    dispatch_audit = _dispatch_audit_snapshot(projects_root, project_id, max_actions)

    config_hint = str(resolved) if resolved else "(default config)"
    print(f"Auto-mode using projects root: {projects_root}")
    print(f"Config: {config_hint}")
    print(f"Max actions per cycle: {max_actions}")

    def emit_snapshot_line() -> None:
        if args.no_kpi_snapshot:
            print("KPI snapshot emitted=false reason=disabled snapshot_path=")
            return
        snapshot = emit_control_cadence_kpi_snapshot(
            projects_root,
            project_id,
            min_interval_minutes=max(int(args.kpi_min_interval_minutes), 1),
        )
        emitted = bool(snapshot.get("emitted"))
        reason = str(snapshot.get("reason") or ("emitted" if emitted else "unknown"))
        snapshot_path = str(snapshot.get("snapshot_path") or "")
        generated_at = str(snapshot.get("generated_at") or "")
        print(
            "KPI snapshot "
            f"emitted={str(emitted).lower()} "
            f"reason={reason} "
            f"snapshot_path={snapshot_path} "
            f"generated_at={generated_at}"
        )

    if args.once:
        stats = dispatch_once(
            projects_root,
            project_id,
            do_open=do_open,
            do_clipboard=do_clipboard,
            do_notify=do_notify,
            max_actions=max(0, max_actions),
            print_prompt=args.print_prompt,
            config=config,
        )
        print(
            f"Dispatched: {stats['dispatched']} | Skipped: {stats['skipped']} | "
            f"Actions: {stats['actions_used']} (sent={stats.get('sent_actions', 0)}, "
            f"fallback={stats.get('fallback_actions', 0)}) | "
            f"GateBlocked: {stats.get('gate_blocked', 0)} | "
            f"GateReport: {stats.get('gate_report_path', '')} | "
            f"State: {stats.get('state_path', '')}"
        )
        _print_dispatch_audit_line(dispatch_audit)
        emit_snapshot_line()
        return 0

    while True:
        stats = dispatch_once(
            projects_root,
            project_id,
            do_open=do_open,
            do_clipboard=do_clipboard,
            do_notify=do_notify,
            max_actions=max(0, max_actions),
            print_prompt=args.print_prompt,
            config=config,
        )
        if stats["dispatched"]:
            print(
                f"Dispatched: {stats['dispatched']} | Skipped: {stats['skipped']} | "
                f"Actions: {stats['actions_used']} (sent={stats.get('sent_actions', 0)}, "
                f"fallback={stats.get('fallback_actions', 0)}) | "
                f"GateBlocked: {stats.get('gate_blocked', 0)} | "
                f"GateReport: {stats.get('gate_report_path', '')} | "
                f"State: {stats.get('state_path', '')}"
            )
        _print_dispatch_audit_line(dispatch_audit)
        emit_snapshot_line()
        time.sleep(max(args.interval, 0.5))


if __name__ == "__main__":
    raise SystemExit(main())
