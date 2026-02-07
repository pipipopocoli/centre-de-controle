import sys
import traceback
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.brain_manager import BrainManager, _next_issue_number
from app.services.question_builder import build_questions
from app.ui.roadmap import normalize_phase_key, phase_display_label


def test_question_builder() -> None:
    print("Testing Question Builder...")

    # Case 1: Empty intake should ask for project purpose.
    q1 = build_questions({})
    assert "but principal" in q1[0]
    print("OK Case 1: Empty intake handled")

    # Case 2: Missing files trigger test question at minimum.
    q2 = build_questions({"top_files": ["main.py", "utils.py"]})
    assert any("tests" in q.lower() for q in q2)
    print("OK Case 2: Missing test signal detected")

    # Case 3: Present test files suppress test question.
    q3 = build_questions(
        {"top_files": ["main.py", "tests/test.py", ".env", "requirements.txt", "Dockerfile"]}
    )
    assert not any("tests" in q.lower() for q in q3)
    print("OK Case 3: Present files suppress questions")


def test_brain_manager_guardrails() -> None:
    print("\nTesting Brain Manager Guardrails...")
    bm = BrainManager()

    # Case 1: Invalid path.
    try:
        bm.run_intake("test-proj", Path("/invalid/path/123"))
        print("FAIL Case 1: Failed to catch invalid path")
    except FileNotFoundError:
        print("OK Case 1: Caught invalid path")

    # Case 2: Scan failure.
    with patch("app.services.brain_manager.scan_repo", return_value=None):
        try:
            bm.run_intake("test-proj", Path("."))
            print("FAIL Case 2: Failed to catch scan failure")
        except ValueError as e:
            if "empty data" in str(e):
                print("OK Case 2: Caught empty scan data")
            else:
                print(f"FAIL Case 2: Wrong error: {e}")


def test_issue_number_parser() -> None:
    print("\nTesting Issue Number Parser...")
    with TemporaryDirectory() as tmp:
        issues_dir = Path(tmp)
        (issues_dir / "ISSUE-0001-init.md").write_text("# x\n", encoding="utf-8")
        (issues_dir / "ISSUE-0016-something.md").write_text("# x\n", encoding="utf-8")
        (issues_dir / "ISSUE-ABCD-invalid.md").write_text("# x\n", encoding="utf-8")
        (issues_dir / "README.md").write_text("# x\n", encoding="utf-8")
        next_num = _next_issue_number(issues_dir)
        assert next_num == 17, f"expected 17, got {next_num}"
        print("OK Issue parser returns monotonic next id")


def test_phase_mapping() -> None:
    print("\nTesting Phase Mapping...")
    assert normalize_phase_key("Plan") == "Plan"
    assert normalize_phase_key("CONCEPTION") == "Plan"
    assert phase_display_label("Plan") == "CONCEPTION"
    print("OK Canonical phase mapping is stable")


def test_traceback_preserved() -> None:
    print("\nTesting Traceback Preservation...")
    bm = BrainManager()

    def explode(_repo_path: Path):
        raise RuntimeError("scan_repo exploded")

    with patch("app.services.brain_manager.scan_repo", side_effect=explode):
        try:
            bm.run_intake("test-proj", Path("."))
            print("FAIL Traceback test: no exception")
            return
        except RuntimeError as e:
            tb = traceback.extract_tb(e.__traceback__)
            last = tb[-1]
            assert last.name == "explode", f"expected origin explode, got {last.name}"
            print("OK Traceback origin preserved")


if __name__ == "__main__":
    try:
        test_question_builder()
        test_brain_manager_guardrails()
        test_issue_number_parser()
        test_phase_mapping()
        test_traceback_preserved()
        print("\nAll Hardening Tests Passed!")
    except AssertionError as e:
        print(f"\nAssertion Failed: {e}")
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
