#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import ensure_demo_project, load_project  # noqa: E402
from app.services.project_bible import run_comprehension_drill_suite, update_vulgarisation  # noqa: E402


def main() -> int:
    result = run_comprehension_drill_suite()

    assert result.get("scenario_count") == 20, "expected 20 scenarios"
    assert result.get("question_count") == 100, "expected 100 evaluated answers"

    answer_accuracy = float(result.get("answer_accuracy") or 0.0)
    scenario_pass_rate = float(result.get("scenario_pass_rate") or 0.0)

    assert answer_accuracy >= 0.85, f"answer accuracy below gate: {answer_accuracy:.3f}"
    assert scenario_pass_rate >= 0.85, f"scenario pass rate below gate: {scenario_pass_rate:.3f}"
    assert bool(result.get("passed_gate")) is True, "gate flag should be true"

    ensure_demo_project()
    project = load_project("demo")
    html_result = update_vulgarisation(project)
    html_doc = html_result.html_path.read_text(encoding="utf-8")
    assert "Brief 60s" in html_doc, "brief section missing from rendered html"
    assert "Delta refresh" in html_doc, "delta signal missing from rendered html"

    print(
        "OK: comprehension gate verified | "
        f"answer_accuracy={answer_accuracy:.3f} scenario_pass_rate={scenario_pass_rate:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
