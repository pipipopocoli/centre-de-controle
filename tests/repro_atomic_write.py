import json
import os
import tempfile
from pathlib import Path
from app.services.session_state import save_ui_session, load_ui_session

def test_atomic_write():
    # Setup
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "test_session.json"
        
        # Test 1: Basic Write
        print("Testing basic write...")
        save_ui_session(
            last_project_id="test_project",
            path=tmp_path
        )
        
        data = load_ui_session(tmp_path)
        assert data.get("last_project_id") == "test_project"
        print("Basic basic write passed!")
        
        # Test 2: Update Existing
        print("Testing update...")
        save_ui_session(
            last_app_stamp="v2",
            path=tmp_path
        )
        
        data = load_ui_session(tmp_path)
        assert data.get("last_project_id") == "test_project"
        assert data.get("last_app_stamp") == "v2"
        print("Update passed!")
        
        # Test 3: Temp file cleanup check
        # We can't easily mock the crash inside the function without mocking, but we can check no temp files exist
        temp_files = list(Path(tmp_dir).glob("tmp*"))
        assert len(temp_files) == 0
        print("Cleanup passed (no temp files left)!")

if __name__ == "__main__":
    try:
        test_atomic_write()
        print("\nAll atomic write tests passed.")
    except Exception as e:
        print(f"\nTest failed: {e}")
        exit(1)
