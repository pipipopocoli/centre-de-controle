from __future__ import annotations

from typing import Any


def build_plan(intake: dict[str, Any], answers: dict[str, Any] | None = None) -> dict[str, Any]:
    stack = intake.get("stack") or []
    stack_text = ", ".join(stack)
    project_name = intake.get("project_name", "Project")
    answers = answers or {}

    plan = {
        "summary": f"Plan for {project_name} ({stack_text})",
        "tasks": [
            {
                "agent_id": "clems",
                "objective": "Orchestration + questions + roadmap updates",
                "scope": "Clarify goals, maintain state/decisions, integrate findings",
                "done": "Project plan finalized + issues assigned",
            },
            {
                "agent_id": "victor",
                "objective": "Backend architecture + setup audit",
                "scope": "Dependencies, entrypoints, tests, data paths",
                "done": "Backend summary + risks + recommended fixes",
            },
            {
                "agent_id": "leo",
                "objective": "UI/UX clarity review",
                "scope": "Timeline, chat, agent cards, usability gaps",
                "done": "UI clarity checklist + recommendations",
            },
        ],
    }

    if "python" in stack:
        plan["tasks"].append(
            {
                "agent_id": "agent-1",
                "objective": "Python tooling audit",
                "scope": "venv, packaging, scripts, entrypoints",
                "done": "Setup commands + risks documented",
            }
        )
    if "node" in stack:
        plan["tasks"].append(
            {
                "agent_id": "agent-2",
                "objective": "Node tooling audit",
                "scope": "package.json scripts, build, tests",
                "done": "Run commands + risks documented",
            }
        )

    # Operator answers can influence tasks (placeholder for V5.1)
    if answers:
        plan["summary"] += " (answers incorporated)"

    return plan
