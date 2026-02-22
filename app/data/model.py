from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PHASES = ["Plan", "Implement", "Test", "Review", "Ship"]


@dataclass
class AgentState:
    agent_id: str
    name: str
    engine: str
    phase: str
    percent: int
    eta_minutes: int | None
    heartbeat: str | None
    status: str | None
    blockers: list[str]
    current_task: str | None = None
    level: int = 2
    lead_id: str | None = None
    role: str = "specialist"
    platform: str | None = None
    skills: list[str] = field(default_factory=list)


@dataclass
class ProjectData:
    project_id: str
    name: str
    path: Path
    agents: list[AgentState]
    roadmap: dict[str, list[str]]
    settings: dict[str, Any]
