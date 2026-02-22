from app.services.project_bible import build_project_bible_html
from app.data.model import ProjectData
from pathlib import Path
import tempfile
import os

def test_bible_expansion():
    # Setup: Create a temp project dir with a STATE.md containing Skills and Gates
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        state_path = tmp_path / "STATE.md"
        state_path.write_text("""
## Phase
Plan

## Objective
Test Expansion

## Risks
- Risk 1

## Skills
- Python
- Docker
- AWS

## Gates
- [x] Intake
- [ ] Transition
""", encoding="utf-8")
        
        # Create dummy project data
        project = ProjectData(
            project_id="test-proj",
            name="Test Project",
            path=tmp_path,
            agents=[],
            roadmap={},
            settings={}
        )
        
        # Build HTML
        html = build_project_bible_html(project)
        
        # Verify
        print("Verifying HTML content...")
        if "Skills Needed" not in html:
            raise AssertionError("Missing 'Skills Needed' header")
        if "Active Gates" not in html:
            raise AssertionError("Missing 'Active Gates' header")
        if "<li>Python</li>" not in html:
            raise AssertionError("Missing Skill: Python")
        if "<li>[x] Intake</li>" not in html:
            raise AssertionError("Missing Gate: Intake")
            
        print("Bible verification passed!")

if __name__ == "__main__":
    try:
        test_bible_expansion()
        print("\nAll bible tests passed.")
    except Exception as e:
        print(f"\nTest failed: {e}")
        exit(1)
