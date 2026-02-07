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

from app.services.auto_mode import dispatch_once as dispatch_once_core
from app.services.auto_mode import resolve_projects_root as resolve_projects_root_core

DEFAULT_PROJECT = "demo"


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
) -> dict[str, int]:
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

    for action in result.actions:
        if do_clipboard:
            _copy_to_clipboard(action.prompt_text)
        if do_open:
            _open_app(action.app_to_open)
        if do_notify:
            _notify("Cockpit auto-mode", action.notify_text)
        if print_prompt:
            print(action.prompt_text)

    return {
        "dispatched": result.dispatched_count,
        "skipped": result.skipped_count,
        "actions_used": len(result.actions),
    }

