#!/usr/bin/env python3
"""
Pack Context Basic Verification
==============================
Verifies pack context generator output shape and limits.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import ensure_demo_project  # noqa: E402
from app.services.pack_context import build_pack_context  # noqa: E402


def main() -> int:
    ensure_demo_project()

    light = build_pack_context("demo", "light", None)
    full = build_pack_context("demo", "full", None)

    assert light.strip()
    assert full.strip()

    light_lines = light.strip().splitlines()
    assert len(light_lines) <= 30

    full_lines = full.strip().splitlines()
    assert len(full_lines) <= 120

    required_sections = [
        "Objectif",
        "Etat",
        "Decisions",
        "Taches ouvertes",
        "Chat",
        "Risques",
    ]
    for section in required_sections:
        assert any(line.startswith(section) for line in light_lines), f"Missing section: {section}"

    print("✅ Pack Context checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
