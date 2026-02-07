from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
BRAINF_DIR = ROOT_DIR / "brainfs"
SKILLS_PATH = BRAINF_DIR / "skills" / "skills.json"
POLICIES_PATH = BRAINF_DIR / "policies" / "default.json"
PROFILES_DIR = BRAINF_DIR / "profiles"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_skills() -> list[dict[str, Any]]:
    if not SKILLS_PATH.exists():
        return []
    try:
        payload = json.loads(SKILLS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []
    skills = payload.get("skills")
    if not isinstance(skills, list):
        return []
    return [s for s in skills if isinstance(s, dict)]


def load_policies() -> dict[str, Any]:
    if not POLICIES_PATH.exists():
        return {}
    try:
        payload = json.loads(POLICIES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _default_profile(project_id: str, stack: list[str]) -> dict[str, Any]:
    # Simple default: enable skills based on stack
    skills = []
    stack_lower = {s.lower() for s in stack}
    if "python" in stack_lower:
        skills.append("python")
    if "node" in stack_lower or "javascript" in stack_lower or "typescript" in stack_lower:
        skills.append("node")
    # Always include UI + MCP for Cockpit
    skills.extend(["ui", "mcp"])

    return {
        "project_id": project_id,
        "stack": stack,
        "skills": sorted(set(skills)),
        "created_at": _utc_now_iso(),
    }


def load_profile(project_id: str) -> dict[str, Any] | None:
    path = PROFILES_DIR / f"{project_id}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def ensure_profile(project_id: str, stack: list[str]) -> dict[str, Any]:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    profile = load_profile(project_id)
    if profile:
        return profile
    profile = _default_profile(project_id, stack)
    (PROFILES_DIR / f"{project_id}.json").write_text(
        json.dumps(profile, indent=2),
        encoding="utf-8",
    )
    return profile
