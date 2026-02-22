import sys
from pathlib import Path
from app.data.model import ProjectData
from app.services.timeline_feed import build_project_timeline_feed

# Mock Project
project_root = Path("/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit")
project = ProjectData(
    project_id="cockpit",
    path=project_root,
    name="Cockpit",
    description="Test",
    repo_url="",
    created_at=""
)

def verify_feed():
    print("Generating feed run 1...")
    feed1 = build_project_timeline_feed(project, limit=50)
    events1 = feed1["events"]
    
    print("Generating feed run 2...")
    feed2 = build_project_timeline_feed(project, limit=50)
    events2 = feed2["events"]
    
    # Check Length
    if len(events1) != len(events2):
        print(f"FAIL: Length mismatch {len(events1)} vs {len(events2)}")
        sys.exit(1)
        
    # Check Order
    for i, (e1, e2) in enumerate(zip(events1, events2)):
        id1 = e1["event_id"]
        id2 = e2["event_id"]
        if id1 != id2:
             print(f"FAIL: Mismatch at index {i}: {id1} vs {id2}")
             sys.exit(1)
             
    print(f"OK: Verified {len(events1)} events are deterministic.")

if __name__ == "__main__":
    verify_feed()
