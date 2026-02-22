from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ALLOWED_SUITES = {"B0", "B1", "B2", "B3"}


@dataclass(frozen=True)
class ScenarioEntry:
    scenario_id: str
    suite_id: str
    risk_tags: list[str]
    active: bool
    owner_role: str


@dataclass(frozen=True)
class ReplayManifest:
    run_id: str
    project_id: str
    git_sha: str
    scenario_profile: str
    toolchain_hash: str
    policy_version: str
    created_at: str
    seed: int | str | None = None
    trace_id: str | None = None


def load_scenario_registry(path: Path) -> dict[str, Any]:
    """Load a scenario registry JSON file and return parsed payload."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("scenario registry must be a JSON object")
    return payload


def validate_scenario_registry(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if not isinstance(payload, dict):
        return ["payload must be a dictionary"]

    version = payload.get("version")
    if not isinstance(version, str) or not version.strip():
        errors.append("version is required and must be a non-empty string")

    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list):
        errors.append("scenarios must be a list")
        return errors

    ids: list[str] = []
    seen: set[str] = set()
    for idx, item in enumerate(scenarios):
        prefix = f"scenarios[{idx}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue

        scenario_id = item.get("scenario_id")
        suite_id = item.get("suite_id")
        risk_tags = item.get("risk_tags")
        active = item.get("active")
        owner_role = item.get("owner_role")

        if not isinstance(scenario_id, str) or not scenario_id.strip():
            errors.append(f"{prefix}.scenario_id must be a non-empty string")
        else:
            sid = scenario_id.strip()
            ids.append(sid)
            if sid in seen:
                errors.append(f"duplicate scenario_id: {sid}")
            seen.add(sid)

        if not isinstance(suite_id, str) or suite_id not in ALLOWED_SUITES:
            errors.append(f"{prefix}.suite_id must be one of {sorted(ALLOWED_SUITES)}")

        if not isinstance(risk_tags, list) or not all(isinstance(tag, str) and tag.strip() for tag in risk_tags):
            errors.append(f"{prefix}.risk_tags must be a list of non-empty strings")

        if not isinstance(active, bool):
            errors.append(f"{prefix}.active must be a boolean")

        if not isinstance(owner_role, str) or not owner_role.strip():
            errors.append(f"{prefix}.owner_role must be a non-empty string")

    if ids != sorted(ids):
        errors.append("scenarios must be sorted by scenario_id for deterministic hashing")

    return errors


def validate_replay_manifest(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if not isinstance(payload, dict):
        return ["payload must be a dictionary"]

    required_fields = [
        "run_id",
        "project_id",
        "git_sha",
        "scenario_profile",
        "toolchain_hash",
        "policy_version",
        "created_at",
    ]

    for field in required_fields:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} is required and must be a non-empty string")

    created_at = payload.get("created_at")
    if isinstance(created_at, str) and created_at.strip():
        try:
            datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append("created_at must be ISO-8601")

    seed = payload.get("seed")
    if seed is not None and not isinstance(seed, (int, str)):
        errors.append("seed must be int, string, or null")

    trace_id = payload.get("trace_id")
    if trace_id is not None and (not isinstance(trace_id, str) or not trace_id.strip()):
        errors.append("trace_id must be a non-empty string when present")

    return errors
