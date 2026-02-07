#!/usr/bin/env python3
"""
Auto-mode core utilities (local-first).

Intended for reuse by scripts/auto_mode.py and tests.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_PROJECT = "demo"
MAX_PROCESSED_IDS = 5000
ROOT_DIR = Path(__file__).resolve().parents[1]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _default_projects_root() -> Path:
    return Path.home() / "Library" / "Application Support" / "Cockpit" / "projects"


def _normalize_projects_root(path: Path) -> Path:
    if path.name == "Cockpit":
        return path / "projects"
    if path.name != "projects" and (path / "projects").exists():
        return path / "projects"
    return path


def resolve_projects_root(data_dir: str | None) -> Path:
    if data_dir:
        lowered = data_dir.lower().strip()
        if lowered in {"repo", "dev"}:
            return ROOT_DIR / "control" / "projects"
        if lowered in {"appsupport", "app"}:
            return _default_projects_root()
        return _normalize_projects_root(Path(data_dir).expanduser())

    env_value = os.environ.get("COCKPIT_DATA_DIR")
    if env_value:
        return _normalize_projects_root(Path(env_value).expanduser())

    return _default_projects_root()


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


def _default_config() -> dict[str, Any]:
    return {
        "app_map": {
            "codex": "Codex",
            "antigravity": "Antigravity",
        },
        "agent_map": {
            "leo": "antigravity",
            "victor": "codex",
        },
        "max_actions": 1,
    }


def _merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in {"app_map", "agent_map"} and isinstance(value, dict):
            merged_map = dict(base.get(key, {}))
            merged_map.update(value)
            merged[key] = merged_map
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


def _agent_platform(agent_id: str, config: dict[str, Any]) -> str:
    agent_map = config.get("agent_map") or {}
    if isinstance(agent_map, dict):
        mapped = agent_map.get(agent_id)
        if isinstance(mapped, str) and mapped.strip():
            return mapped.strip().lower()

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
    subprocess.run(["pbcopy"], input=text, text=True, check=False)


def _open_app(app_name: str) -> None:
    subprocess.run(["open", "-a", app_name], check=False)


def _notify(title: str, message: str) -> None:
    script = f'display notification \"{message}\" with title \"{title}\"'
    subprocess.run(["osascript", "-e", script], check=False)


def _paths(projects_root: Path, project_id: str) -> tuple[Path, Path, Path]:
    project_dir = projects_root / project_id
    requests_path = project_dir / "runs" / "requests.ndjson"
    inbox_dir = project_dir / "runs" / "inbox"
    state_path = project_dir / "runs" / "auto_mode_state.json"
    return requests_path, inbox_dir, state_path


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
    requests_path, inbox_dir, state_path = _paths(projects_root, project_id)

    processed = _load_state(state_path)
    processed_set = set(processed)

    dispatched = 0
    skipped = 0
    actions_used = 0

    app_map = config.get("app_map") or {}
    if not isinstance(app_map, dict):
        app_map = {}
    codex_app = str(app_map.get("codex") or "Codex")
    ag_app = str(app_map.get("antigravity") or "Antigravity")

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

        inbox_path = inbox_dir / f"{agent_id}.ndjson"
        _append_ndjson(inbox_path, payload)

        prompt = _format_prompt(project_id, payload)
        platform = _agent_platform(agent_id, config)
        app_to_open = codex_app if platform == "codex" else ag_app

        if max_actions > 0 and actions_used < max_actions:
            if do_clipboard:
                _copy_to_clipboard(prompt)
            if do_open:
                _open_app(app_to_open)
            if do_notify:
                _notify(
                    "Cockpit auto-mode",
                    f"Copied task for @{agent_id} and opened {app_to_open}",
                )
            if print_prompt:
                print(prompt)
            actions_used += 1

        processed.append(request_id)
        processed_set.add(request_id)
        dispatched += 1

    _save_state(state_path, processed)
    return {"dispatched": dispatched, "skipped": skipped, "actions_used": actions_used}
