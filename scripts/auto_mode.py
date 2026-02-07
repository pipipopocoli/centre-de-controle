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
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_PROJECT = "demo"
MAX_PROCESSED_IDS = 5000


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _default_projects_root() -> Path:
    env_value = os.environ.get("COCKPIT_DATA_DIR")
    if env_value:
        return Path(env_value).expanduser()
    return Path.home() / "Library" / "Application Support" / "Cockpit" / "projects"


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            items.append(payload)
    return items


def _append_ndjson(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _load_state(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []
    processed = payload.get("processed")
    if not isinstance(processed, list):
        return []
    return [str(item) for item in processed if str(item).strip()]


def _save_state(path: Path, processed: list[str]) -> None:
    trimmed = processed[-MAX_PROCESSED_IDS:]
    payload = {
        "processed": trimmed,
        "updated_at": _utc_now_iso(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _agent_platform(agent_id: str) -> str:
    # Locked mapping:
    # - victor, agent-1, agent-3, ... -> Codex
    # - leo, agent-2, agent-4, ... -> Antigravity
    if agent_id == "leo":
        return "antigravity"
    if agent_id == "victor":
        return "codex"
    if agent_id.startswith("agent-"):
        try:
            n = int(agent_id.split("-", 1)[1])
        except (IndexError, ValueError):
            return "codex"
        return "codex" if (n % 2 == 1) else "antigravity"
    # default unknown to codex
    return "codex"


def _format_prompt(project_id: str, payload: dict[str, Any]) -> str:
    agent_id = str(payload.get("agent_id") or "").strip()
    created_at = str(payload.get("created_at") or "")
    source = str(payload.get("source") or "")
    msg = payload.get("message") or {}
    author = str((msg.get("author") if isinstance(msg, dict) else "") or "")
    text = str((msg.get("text") if isinstance(msg, dict) else "") or "")

    return (
        f"[Cockpit auto-mode]\\n"
        f"Project: {project_id}\\n"
        f"Target: @{agent_id}\\n"
        f"Created: {created_at} (source={source})\\n"
        f"From: {author}\\n\\n"
        f"Task:\\n{text}\\n\\n"
        "Instructions:\\n"
        "- Do the task above.\\n"
        "- Report back in Cockpit using cockpit.post_message.\\n"
        "- Update your state with cockpit.update_agent_state (phase/percent/status).\\n"
    )


def _copy_to_clipboard(text: str) -> None:
    # pbcopy exists on macOS.
    subprocess.run(["pbcopy"], input=text, text=True, check=False)


def _open_app(app_name: str) -> None:
    subprocess.run(["open", "-a", app_name], check=False)


def _notify(title: str, message: str) -> None:
    # Best-effort macOS notification.
    script = f'display notification \"{message}\" with title \"{title}\"'
    subprocess.run(["osascript", "-e", script], check=False)


def _paths(projects_root: Path, project_id: str) -> tuple[Path, Path, Path]:
    project_dir = projects_root / project_id
    requests_path = project_dir / "runs" / "requests.ndjson"
    inbox_dir = project_dir / "runs" / "inbox"
    state_path = project_dir / "runs" / "auto_mode_state.json"
    return requests_path, inbox_dir, state_path


def _dispatch_once(
    projects_root: Path,
    project_id: str,
    *,
    do_open: bool,
    do_clipboard: bool,
    do_notify: bool,
    codex_app: str,
    ag_app: str,
) -> dict[str, int]:
    requests_path, inbox_dir, state_path = _paths(projects_root, project_id)

    processed = _load_state(state_path)
    processed_set = set(processed)

    dispatched = 0
    skipped = 0

    for payload in _read_ndjson(requests_path):
        request_id = str(payload.get("request_id") or "").strip()
        agent_id = str(payload.get("agent_id") or "").strip()
        source = str(payload.get("source") or "").strip()

        if not request_id or not agent_id:
            skipped += 1
            continue
        if source == "reminder":
            skipped += 1
            continue
        if request_id in processed_set:
            skipped += 1
            continue

        # 1) write inbox
        inbox_path = inbox_dir / f"{agent_id}.ndjson"
        _append_ndjson(inbox_path, payload)

        # 2) prompt + actions
        prompt = _format_prompt(project_id, payload)
        platform = _agent_platform(agent_id)
        app_to_open = codex_app if platform == "codex" else ag_app

        if do_clipboard:
            _copy_to_clipboard(prompt)
        if do_open:
            _open_app(app_to_open)
        if do_notify:
            _notify("Cockpit auto-mode", f"Copied task for @{agent_id} and opened {app_to_open}")

        processed.append(request_id)
        processed_set.add(request_id)
        dispatched += 1

    _save_state(state_path, processed)
    return {"dispatched": dispatched, "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-mode runner for Cockpit run requests.")
    parser.add_argument("--project", default=None, help="Project id (default: COCKPIT_PROJECT_ID or demo)")
    parser.add_argument("--data-dir", default=None, help="Projects root (default: App Support)")
    parser.add_argument("--interval", type=float, default=5.0, help="Polling interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--no-open", action="store_true", help="Do not open apps")
    parser.add_argument("--no-clipboard", action="store_true", help="Do not copy to clipboard")
    parser.add_argument("--no-notify", action="store_true", help="Do not send macOS notifications")
    parser.add_argument("--codex-app", default="Codex", help="App name for Codex (open -a)")
    parser.add_argument("--ag-app", default="Antigravity", help="App name for Antigravity (open -a)")

    args = parser.parse_args()

    project_id = args.project or os.environ.get("COCKPIT_PROJECT_ID") or DEFAULT_PROJECT
    projects_root = Path(args.data_dir).expanduser() if args.data_dir else _default_projects_root()

    do_open = not args.no_open
    do_clipboard = not args.no_clipboard
    do_notify = not args.no_notify

    if args.once:
        stats = _dispatch_once(
            projects_root,
            project_id,
            do_open=do_open,
            do_clipboard=do_clipboard,
            do_notify=do_notify,
            codex_app=args.codex_app,
            ag_app=args.ag_app,
        )
        print(f"Dispatched: {stats['dispatched']} | Skipped: {stats['skipped']}")
        return 0

    while True:
        stats = _dispatch_once(
            projects_root,
            project_id,
            do_open=do_open,
            do_clipboard=do_clipboard,
            do_notify=do_notify,
            codex_app=args.codex_app,
            ag_app=args.ag_app,
        )
        if stats["dispatched"]:
            print(f"Dispatched: {stats['dispatched']} | Skipped: {stats['skipped']}")
        time.sleep(max(args.interval, 0.5))


if __name__ == "__main__":
    raise SystemExit(main())

