
import sys
import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.timeline_feed import build_project_timeline_feed, _read_text
from app.data.model import ProjectData

# Temp dir for test files
TEST_DIR = Path(__file__).parent / "temp_hybrid_timeline"

def setup_test_project():
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir()
    (TEST_DIR / "issues").mkdir()
    (TEST_DIR / "runs").mkdir()
    (TEST_DIR / "missions").mkdir()
    
    project = MagicMock(spec=ProjectData)
    project.project_id = "test-proj"
    project.path = TEST_DIR
    return project

def cleanup():
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)

def test_hybrid_timeline():
    print("\n=== Testing Hybrid Timeline Feed ===")
    project = setup_test_project()

    try:
        # HT-001: State Update
        print("Running HT-001: State Update ...", end=" ")
        (TEST_DIR / "STATE.md").write_text("# State\n\n## Next\n- Verify hybrid timeline", encoding="utf-8")
        feed = build_project_timeline_feed(project)
        events = feed["events"]
        assert any(e["title"] == "STATE updated" for e in events)
        print("PASS")

        # HT-002: New Issue (Todo)
        print("Running HT-002: New Issue ...", end=" ")
        (TEST_DIR / "issues" / "ISSUE-999.md").write_text("# ISSUE-999 - Test Issue\n- Status: Todo", encoding="utf-8")
        feed = build_project_timeline_feed(project)
        events = feed["events"]
        issue_event = next((e for e in events if "ISSUE-999" in e["title"]), None)
        assert issue_event is not None
        assert issue_event["lane"] == "delivery"
        assert issue_event["severity"] == "info"
        print("PASS")

        # HT-003: Active Issue
        print("Running HT-003: Active Issue ...", end=" ")
        (TEST_DIR / "issues" / "ISSUE-999.md").write_text("# ISSUE-999 - Test Issue\n- Status: In Progress", encoding="utf-8")
        feed = build_project_timeline_feed(project)
        events = feed["events"]
        issue_event = next((e for e in events if "ISSUE-999" in e["title"]), None)
        assert issue_event is not None
        assert issue_event["severity"] == "warn"  # In Progress -> Warn
        print("PASS")

        # HT-004: Runtime Request Failed
        print("Running HT-004: Runtime Request Failed ...", end=" ")
        request_line = json.dumps({
            "request_id": "req-1",
            "status": "failed",
            "agent_id": "agent-x",
            "created_at": "2023-01-01T12:00:00Z"
        })
        (TEST_DIR / "runs" / "requests.ndjson").write_text(request_line + "\n", encoding="utf-8")
        feed = build_project_timeline_feed(project)
        events = feed["events"]
        req_event = next((e for e in events if "req-1" in e["title"]), None)
        assert req_event is not None
        assert req_event["lane"] == "runtime"
        assert req_event["severity"] == "critical"
        print("PASS")

        # HT-005: Decisions
        print("Running HT-005: New Decision ...", end=" ")
        (TEST_DIR / "DECISIONS.md").write_text("# Decisions\n- ADR-001", encoding="utf-8")
        feed = build_project_timeline_feed(project)
        events = feed["events"]
        assert any(e["title"] == "DECISIONS updated" for e in events)
        assert any(e["lane"] == "decision" for e in events if "DECISIONS" in e["title"])
        print("PASS")
        
        # HT-006: Mission
        print("Running HT-006: Mission Start ...", end=" ")
        (TEST_DIR / "missions" / "mission-alpha.md").write_text("# Mission Alpha", encoding="utf-8")
        feed = build_project_timeline_feed(project)
        events = feed["events"]
        assert any(e["title"] == "mission mission-alpha" for e in events)
        assert any(e["lane"] == "mission" for e in events if "mission-alpha" in e["title"])
        print("PASS")
        
        # HT-007: Risk Log
        print("Running HT-007: Risk Log ...", end=" ")
        (TEST_DIR / "STATE.md").write_text("# State\n\n## Risks\n- High latency risk", encoding="utf-8")
        feed = build_project_timeline_feed(project)
        events = feed["events"]
        risk_event = next((e for e in events if "risk 1" in e["title"]), None)
        assert risk_event is not None
        assert risk_event["lane"] == "risk"
        assert risk_event["severity"] == "warn"
        print("PASS")

        # HT-PF-002: Empty Project (Edge Case)
        print("Running HT-PF-002: Empty Project ...", end=" ")
        # Clear all files
        shutil.rmtree(TEST_DIR)
        TEST_DIR.mkdir()
        (TEST_DIR / "issues").mkdir() # Recreate empty dirs to prevent errors if code expects them, though model mocks might need more care
        (TEST_DIR / "runs").mkdir() 
        # Actually proper empty project simulation
        empty_project = MagicMock(spec=ProjectData)
        empty_project.project_id = "empty-proj"
        empty_project.path = TEST_DIR
        
        feed = build_project_timeline_feed(empty_project)
        events = feed["events"]
        # Fallback event expected
        assert len(events) == 1
        assert events[0]["title"] == "no timeline events"
        print("PASS")

    finally:
        cleanup()

if __name__ == "__main__":
    try:
        test_hybrid_timeline()
        print("\nAll automated verification checks PASSED.")
    except AssertionError as e:
        print(f"\nFAILED: {e}")
        cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        cleanup()
        sys.exit(1)
