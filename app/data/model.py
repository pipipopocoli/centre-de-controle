from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


PHASES = ["Plan", "Implement", "Test", "Review", "Ship"]


@dataclass
class AgentState:
    agent_id: str
    name: str
    source: str
    phase: str
    progress: int
    eta_minutes: int | None
    heartbeat: str | None
    status: str | None


@dataclass
class ProjectData:
    project_id: str
    name: str
    path: Path
    agents: list[AgentState]
    roadmap: dict[str, list[str]]
    settings: dict[str, Any]
