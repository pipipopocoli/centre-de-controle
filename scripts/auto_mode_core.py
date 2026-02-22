#!/usr/bin/env python3
"""
Auto-mode core utilities (local-first).

This module is a thin wrapper around app/services/auto_mode.py so:
- scripts/auto_mode.py stays small
- in-app auto-mode and CLI share the same dispatch logic
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from app.services.auto_mode import agent_platform
from app.services.auto_mode import dispatch_once as dispatch_once_core
from app.services.auto_mode import resolve_projects_root as resolve_projects_root_core
from app.services.auto_send import SendRoute
from app.services.auto_send import send_action as auto_send_action

DEFAULT_PROJECT = "cockpit"


def resolve_projects_root(data_dir: str | None) -> Path:
    return resolve_projects_root_core(data_dir, env=dict(os.environ))


def _default_config() -> dict[str, Any]:
    return {
        "app_map": {
            "codex": "Codex",
            "antigravity": "Antigravity",
        },
        "max_actions": 1,
    }


def _merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key == "app_map" and isinstance(value, dict):
            merged_map = dict(base.get("app_map", {}))
            merged_map.update(value)
            merged["app_map"] = merged_map
        else:
            merged[key] = value
    return merged


def load_config(
    config_path: Path | None,
    projects_root: Path,
    project_id: str,
) -> tuple[dict[str, Any], Path | None]:
    default = _default_config()
    resolved_path = config_path
    if resolved_path is None:
        resolved_path = projects_root / project_id / "runs" / "auto_mode_config.json"
        if not resolved_path.exists():
            return default, None

    if not resolved_path.exists():
        return default, resolved_path

    try:
        payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default, resolved_path
    if not isinstance(payload, dict):
        return default, resolved_path

    return _merge_config(default, payload), resolved_path


def _copy_to_clipboard(text: str) -> None:
    subprocess.run(["pbcopy"], input=text, text=True, check=False)


def _open_app(app_name: str) -> None:
    subprocess.run(["open", "-a", app_name], check=False)


def _notify(title: str, message: str) -> None:
    script = f'display notification \"{message}\" with title \"{title}\"'
    subprocess.run(["osascript", "-e", script], check=False)


def dispatch_once(
    projects_root: Path,
    project_id: str,
    *,
    do_open: bool,
    do_clipboard: bool,
    do_notify: bool,
    max_actions: int,
    print_prompt: bool,
    config: dict[str, Any],
) -> dict[str, Any]:
    app_map = config.get("app_map") or {}
    if not isinstance(app_map, dict):
        app_map = {}
    codex_app = str(app_map.get("codex") or "Codex")
    ag_app = str(app_map.get("antigravity") or "Antigravity")

    result = dispatch_once_core(
        projects_root,
        project_id,
        max_actions=max_actions,
        codex_app=codex_app,
        ag_app=ag_app,
    )

    require_window_match = bool(config.get("require_window_match", False))
    sent_count = 0
    fallback_count = 0
    send_statuses: dict[str, int] = {}

    for action in result.actions:
        sent = False
        if do_open and do_clipboard:
            route = SendRoute(
                project_id=project_id,
                agent_id=action.agent_id,
                platform=str(action.platform or agent_platform(action.agent_id)),
                app_name=action.app_to_open,
                window_title_contains=action.app_to_open,
                require_window_match=require_window_match,
            )
            send_result = auto_send_action(action, route, dry_run=False)
            status = str(send_result.status or "")
            send_statuses[status] = send_statuses.get(status, 0) + 1
            sent = bool(send_result.sent)

        if sent:
            sent_count += 1
        else:
            fallback_count += 1
            if do_clipboard:
                _copy_to_clipboard(action.prompt_text)
            if do_open:
                _open_app(action.app_to_open)

        if do_notify:
            _notify("Cockpit auto-mode", action.notify_text)
        if print_prompt:
            print(action.prompt_text)

    state_path = projects_root / project_id / "runs" / "auto_mode_state.json"

    return {
        "dispatched": result.dispatched_count,
        "skipped": result.skipped_count,
        "actions_used": len(result.actions),
        "sent_actions": sent_count,
        "fallback_actions": fallback_count,
        "send_statuses": send_statuses,
        "state_path": str(state_path),
    }
