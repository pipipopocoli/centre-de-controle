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
import os
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.auto_mode import emit_kpi_snapshot  # noqa: E402
from scripts.auto_mode_core import (  # noqa: E402
    DEFAULT_PROJECT,
    dispatch_once,
    load_config,
    resolve_projects_root,
)

NO_DISPATCH_LOG_EVERY = 12
KPI_EMIT_INTERVAL_SECONDS = 1800


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
    args = parser.parse_args()

    project_id = args.project or os.environ.get("COCKPIT_PROJECT_ID") or DEFAULT_PROJECT
    projects_root = resolve_projects_root(args.data_dir)

    do_open = not args.no_open
    do_clipboard = not args.no_clipboard
    do_notify = not args.no_notify

    config_path = Path(args.config).expanduser() if args.config else None
    config, resolved = load_config(config_path, projects_root, project_id)
    max_actions = args.max_actions if args.max_actions is not None else int(config.get("max_actions", 1))

    config_hint = str(resolved) if resolved else "(default config)"
    print(f"Auto-mode using projects root: {projects_root}")
    print(f"Config: {config_hint}")
    print(f"Max actions per cycle: {max_actions}")

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
            "Dispatched: "
            f"{stats['dispatched']} | "
            f"Skipped: {stats['skipped']} "
            f"(invalid={stats['skipped_invalid']}, reminder={stats['skipped_reminder']}, "
            f"old={stats['skipped_old']}, wrong_project={stats['skipped_wrong_project']}, duplicate={stats['skipped_duplicate']}) | "
            f"Actions: {stats['actions_used']} "
            f"(sent={stats.get('sent_actions', 0)}, fallback={stats.get('fallback_actions', 0)}) | "
            f"State: {stats.get('state_path', '')}"
        )
        return 0

    tick_count = 0
    next_kpi_emit_at = time.monotonic()
    while True:
        tick_count += 1
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
        should_log = bool(stats["dispatched"]) or (tick_count % NO_DISPATCH_LOG_EVERY == 0)
        if should_log:
            print(
                "Dispatched: "
                f"{stats['dispatched']} | "
                f"Skipped: {stats['skipped']} "
                f"(invalid={stats['skipped_invalid']}, reminder={stats['skipped_reminder']}, "
                f"old={stats['skipped_old']}, wrong_project={stats['skipped_wrong_project']}, duplicate={stats['skipped_duplicate']}) | "
                f"Actions: {stats['actions_used']} "
                f"(sent={stats.get('sent_actions', 0)}, fallback={stats.get('fallback_actions', 0)}) | "
                f"State: {stats.get('state_path', '')}"
            )
        now_mono = time.monotonic()
        if now_mono >= next_kpi_emit_at:
            snapshot = emit_kpi_snapshot(
                projects_root,
                project_id,
                post_chat=True,
                min_interval_minutes=25,
            )
            if snapshot.get("emitted"):
                print(f"KPI snapshot emitted: {snapshot.get('snapshot_path', '')}")
            next_kpi_emit_at = now_mono + KPI_EMIT_INTERVAL_SECONDS
        time.sleep(max(args.interval, 0.5))


if __name__ == "__main__":
    raise SystemExit(main())
