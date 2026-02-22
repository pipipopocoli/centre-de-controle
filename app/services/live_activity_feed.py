from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.data.model import AgentState, ProjectData

OPEN_REQUEST_STATUSES = {"queued", "dispatched", "reminded"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in _read_text(path).splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _parse_state_items(path: Path) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in _read_text(path).splitlines():
        line = raw.strip()
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
            continue
        if current and line.startswith("- "):
            sections[current].append(line[2:].strip())
    return sections


def _resolve_repo_path(project: ProjectData) -> tuple[Path, str]:
    settings = project.settings if isinstance(project.settings, dict) else {}
    candidates = [
        str(settings.get("linked_repo_path") or "").strip(),
        str(settings.get("repo_path") or "").strip(),
    ]
    for raw in candidates:
        if not raw:
            continue
        candidate = Path(raw).expanduser()
        if candidate.exists() and candidate.is_dir():
            return candidate.resolve(), "linked_repo"
    workspace = Path(__file__).resolve().parents[2]
    return workspace, "workspace_fallback"


def _run_git(repo_path: Path, args: list[str]) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_path), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _collect_code_lane(repo_path: Path, *, limit: int) -> dict[str, Any]:
    branch = _run_git(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"
    status_output = _run_git(repo_path, ["status", "--porcelain"])
    log_output = _run_git(
        repo_path,
        ["log", "--date=iso-strict", "--pretty=format:%H|%ad|%an|%s", "-n", str(max(limit, 1))],
    )

    changed_files: list[str] = []
    if status_output:
        for row in status_output.splitlines():
            line = row.rstrip()
            if not line:
                continue
            path = line[3:].strip() if len(line) >= 4 else line
            if path:
                changed_files.append(path)

    commits: list[dict[str, str]] = []
    if log_output:
        for row in log_output.splitlines():
            parts = row.split("|", 3)
            if len(parts) != 4:
                continue
            commits.append(
                {
                    "sha": parts[0].strip(),
                    "timestamp": parts[1].strip(),
                    "author": parts[2].strip(),
                    "message": parts[3].strip(),
                }
            )

    return {
        "repo_path": str(repo_path),
        "available": bool(commits or changed_files or branch != "unknown"),
        "branch": branch,
        "commits": commits[: max(limit, 1)],
        "changed_files": changed_files[: max(limit, 1)],
    }


def _issue_summary(issues_dir: Path) -> dict[str, int]:
    counts = {
        "total": 0,
        "open_like": 0,
        "done": 0,
        "deferred": 0,
    }
    if not issues_dir.exists():
        return counts

    for path in sorted(issues_dir.glob("ISSUE-*.md")):
        counts["total"] += 1
        text = _read_text(path)
        status = "open"
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("- status:"):
                status = stripped.split(":", 1)[1].strip().lower()
                break
        if status in {"done", "closed"}:
            counts["done"] += 1
        elif status in {"deferred", "backlog deferred"}:
            counts["deferred"] += 1
        else:
            counts["open_like"] += 1

    return counts


def _collect_task_lane(project: ProjectData, *, limit: int) -> dict[str, Any]:
    project_dir = project.path
    state = _parse_state_items(project_dir / "STATE.md")
    now_items = state.get("Now", [])
    next_items = state.get("Next", [])
    blockers = state.get("Blockers", [])

    requests = _read_ndjson(project_dir / "runs" / "requests.ndjson")
    open_requests = 0
    latest_requests: list[dict[str, str]] = []
    for payload in requests:
        status = str(payload.get("status") or "").strip().lower()
        if status in OPEN_REQUEST_STATUSES:
            open_requests += 1
        latest_requests.append(
            {
                "request_id": str(payload.get("request_id") or ""),
                "agent_id": str(payload.get("agent_id") or ""),
                "status": status or "unknown",
                "updated_at": str(payload.get("updated_at") or payload.get("created_at") or ""),
            }
        )
    latest_requests.sort(key=lambda row: row.get("updated_at") or "", reverse=True)

    return {
        "phase": (state.get("Phase") or ["Plan"])[0],
        "now": now_items[: max(limit, 1)],
        "next": next_items[: max(limit, 1)],
        "blockers": blockers[: max(limit, 1)],
        "open_requests": open_requests,
        "issues": _issue_summary(project_dir / "issues"),
        "latest_requests": latest_requests[: max(limit, 1)],
    }


def _status_bucket(agent: AgentState) -> str:
    status = (agent.status or "").strip().lower()
    blockers = [item for item in agent.blockers if str(item).strip()]
    if blockers and status in {"", "idle", "completed", "replied", "closed"}:
        return "blocked"
    if status in {"blocked", "error"}:
        return "blocked"
    if status in {"planning", "executing", "verifying"}:
        return "action"
    if status in {"pinged", "queued", "dispatched", "reminded", "waiting_reconfirm"}:
        return "waiting"
    return "rest"


def _collect_agent_lane(project: ProjectData) -> dict[str, Any]:
    levels: dict[int, dict[str, Any]] = {
        0: {"count": 0, "action": 0, "waiting": 0, "blocked": 0, "rest": 0},
        1: {"count": 0, "action": 0, "waiting": 0, "blocked": 0, "rest": 0},
        2: {"count": 0, "action": 0, "waiting": 0, "blocked": 0, "rest": 0},
    }
    active_agents: list[dict[str, Any]] = []
    for agent in project.agents:
        try:
            parsed_level = int(agent.level)
        except (TypeError, ValueError):
            parsed_level = 2
        level = parsed_level if parsed_level in {0, 1, 2} else 2
        bucket = _status_bucket(agent)
        levels[level]["count"] += 1
        levels[level][bucket] += 1
        if bucket in {"action", "waiting", "blocked"}:
            active_agents.append(
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "level": level,
                    "bucket": bucket,
                    "status": agent.status or "",
                }
            )
    active_agents.sort(key=lambda item: (int(item.get("level") or 2), str(item.get("name") or "").lower()))
    return {
        "levels": levels,
        "active_agents": active_agents[:12],
    }


def build_live_activity_feed(
    project: ProjectData,
    limit: int = 30,
    *,
    include_code: bool = True,
) -> dict[str, Any]:
    bounded_limit = max(5, min(int(limit), 100))
    repo_path, repo_source = _resolve_repo_path(project)
    code_payload: dict[str, Any]
    if include_code:
        code_payload = _collect_code_lane(repo_path, limit=bounded_limit)
    else:
        code_payload = {
            "repo_path": str(repo_path),
            "available": True,
            "branch": "cached",
            "commits": [],
            "changed_files": [],
            "cached_only": True,
        }

    return {
        "generated_at": _utc_now_iso(),
        "project_id": project.project_id,
        "repo_source": repo_source,
        "code": code_payload,
        "tasks": _collect_task_lane(project, limit=bounded_limit),
        "agents": _collect_agent_lane(project),
    }
