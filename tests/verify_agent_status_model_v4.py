#!/usr/bin/env python3
"""
Agent status model v4 verification (updated for 7-status model + blocker override).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.model import AgentState  # noqa: E402
from app.ui.agents_grid import _status_label  # noqa: E402


def _agent(agent_id: str, status: str, blockers: list[str] | None = None) -> AgentState:
    return AgentState(
        agent_id=agent_id,
        name=agent_id,
        engine="CDX",
        phase="Implement",
        percent=0,
        eta_minutes=None,
        heartbeat=None,
        status=status,
        blockers=blockers or [],
    )


def main() -> int:
    # --- Status label mapping (2-tuple: display, key) ---
    assert _status_label("queued") == ("\u23f3 Attente reponse", "waiting")
    assert _status_label("executing") == ("\u26a1 En action", "executing")
    assert _status_label("blocked") == ("\U0001f534 Bloque", "blocked")
    assert _status_label("replied") == ("\U0001f4a4 Repos", "idle")
    assert _status_label(None) == ("\U0001f4a4 Repos", "idle")
    assert _status_label("planning") == ("\U0001f9ed Planifie", "planning")
    assert _status_label("verifying") == ("\U0001f50e Verification", "verifying")
    assert _status_label("completed") == ("\u2705 Termine", "completed")
    assert _status_label("error") == ("\U0001f534 Erreur", "error")

    # --- Blocker override logic (simulates AgentCard.__init__) ---
    # idle + blockers → blocked
    _text, key = _status_label("idle")
    assert key == "idle"
    agent_with_blockers = _agent("b1", "idle", blockers=["critical issue"])
    blockers = [b.strip() for b in agent_with_blockers.blockers if b.strip()]
    if blockers and key in {"idle", "completed"}:
        key = "blocked"
    assert key == "blocked", f"Override failed: expected blocked, got {key}"

    # executing + blockers → stays executing (no override)
    _text2, key2 = _status_label("executing")
    assert key2 == "executing"
    agent_exec = _agent("b2", "executing", blockers=["minor"])
    blockers2 = [b.strip() for b in agent_exec.blockers if b.strip()]
    if blockers2 and key2 in {"idle", "completed"}:
        key2 = "blocked"
    assert key2 == "executing", f"False override: expected executing, got {key2}"

    print("OK verify_agent_status_model_v4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
