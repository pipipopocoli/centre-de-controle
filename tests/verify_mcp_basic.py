#!/usr/bin/env python3
"""
MCP Server Basic Verification
==============================
Verifies MCP server functions work without requiring full MCP SDK.
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import (  # noqa: E402
    ensure_demo_project,
    get_project,
    load_chat_global,
    load_chat_thread,
)


class MockTextContent:
    """Mock TextContent for testing without MCP SDK."""
    def __init__(self, text: str):
        self.text = text
        self.type = "text"


async def test_data_layer():
    """Test project creation and retrieval."""
    print("Testing: Data Layer")
    
    # Create demo project
    project = ensure_demo_project()
    assert project.project_id == "demo"
    agent_ids = {a.agent_id for a in project.agents}
    assert {"clems", "victor", "leo"} <= agent_ids
    print(f"  ✅ Demo project created: {project.name}")

    for agent_id in ("clems", "victor", "leo"):
        agent_dir = ROOT_DIR / "control" / "projects" / "demo" / "agents" / agent_id
        assert (agent_dir / "memory.md").exists()
        assert (agent_dir / "journal.ndjson").exists()
    print("  ✅ Default roster + per-agent memory scaffolded")

    # Default roster files
    for agent_id in ("clems", "victor", "leo"):
        memory_path = ROOT_DIR / "control" / "projects" / "demo" / "agents" / agent_id / "memory.md"
        assert memory_path.exists()
    print("  ✅ Default roster memory files present")
    
    # Test get_project
    project2 = get_project("demo")
    assert project2.project_id == project.project_id
    print(f"  ✅ Project retrieved: {project2.name}")

    # Legacy compat: source/progress -> engine/percent
    legacy_dir = ROOT_DIR / "control" / "projects" / "demo" / "agents" / "legacy_agent"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    legacy_state = legacy_dir / "state.json"
    legacy_state.write_text(json.dumps({
        "agent_id": "legacy_agent",
        "name": "Legacy Agent",
        "source": "antigravity",
        "phase": "Testing",
        "progress": 42,
        "eta_minutes": 5,
        "heartbeat": "2026-02-06T00:00:00+00:00",
        "status": "executing"
    }), encoding="utf-8")
    project3 = get_project("demo")
    legacy = next((a for a in project3.agents if a.agent_id == "legacy_agent"), None)
    assert legacy is not None
    assert legacy.engine == "AG"
    assert legacy.percent == 42
    assert legacy.phase == "Test"
    print("  ✅ Legacy source/progress normalized")


async def test_tool_logic():
    """Test MCP tool handler logic."""
    print("Testing: Tool Logic")
    
    ensure_demo_project()
    
    # Mock the MCP module temporarily
    sys.modules['mcp'] = type(sys)('mcp')
    sys.modules['mcp.server'] = type(sys)('mcp.server')
    sys.modules['mcp.server.stdio'] = type(sys)('mcp.server.stdio')
    sys.modules['mcp.types'] = type(sys)('mcp.types')
    
    # Create mock classes
    class MockTool:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class MockServer:
        def __init__(self, name):
            self.name = name
        def list_tools(self):
            def decorator(func):
                return func
            return decorator
        def call_tool(self):
            def decorator(func):
                return func
            return decorator
    
    sys.modules['mcp.types'].Tool = MockTool
    sys.modules['mcp.types'].TextContent = MockTextContent
    sys.modules['mcp.server'].Server = MockServer
    
    # Now import the handlers
    from control.mcp_server import (
        handle_post_message,
        handle_read_state,
        handle_update_agent_state,
        handle_request_run,
        handle_get_quotas
    )
    
    # Test post_message
    unique_text = f"Test message {datetime.now(timezone.utc).isoformat()}"
    result = await handle_post_message({
        "agent_id": "test_agent",
        "content": unique_text,
        "tags": ["#mcpwire"],
        "metadata": {"project_id": "demo"}
    })
    data = json.loads(result[0].text)
    assert data["status"] == "posted"
    messages = load_chat_global("demo")
    assert any(msg.get("text") == unique_text for msg in messages)
    thread_messages = load_chat_thread("demo", "mcpwire")
    assert any(msg.get("text") == unique_text for msg in thread_messages)
    print(f"  ✅ post_message works")
    
    # Test read_state
    result = await handle_read_state({
        "agent_id": "test_agent",
        "project_id": "demo",
        "scope": "summary"
    })
    data = json.loads(result[0].text)
    assert "projects" in data
    print(f"  ✅ read_state works")
    
    # Test update_agent_state
    result = await handle_update_agent_state({
        "agent_id": "test_agent_new",
        "project_id": "demo",
        "status": "executing",
        "progress": 50,
        "current_phase": "Testing"
    })
    data = json.loads(result[0].text)
    assert data["acknowledged"] == True
    print(f"  ✅ update_agent_state works")
    
    # Verify agent was added
    project = get_project("demo")
    agent = next((a for a in project.agents if a.agent_id == "test_agent_new"), None)
    assert agent is not None
    assert agent.percent == 50
    print(f"  ✅ Agent persisted correctly")
    
    # Test request_run
    result = await handle_request_run({
        "agent_id": "test_agent",
        "run_type": "test",
        "project_id": "demo",
        "description": "Test run",
        "risk_level": "safe"
    })
    data = json.loads(result[0].text)
    print(f"    Debug: request_run response = {data}")
    assert data["status"] == "approved" or data["status"] ==  "pending_approval"
    print(f"  ✅ request_run works (status={data['status']})")
    
    # Test get_quotas
    result = await handle_get_quotas({
        "agent_id": "test_agent",
        "scope": "agent"
    })
    data = json.loads(result[0].text)
    assert "quotas" in data
    print(f"  ✅ get_quotas works")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Cockpit MCP Server Basic Verification")
    print("=" * 60)
    print()
    
    tests = [
        test_data_layer,
        test_tool_logic
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            asyncio.run(test())
            passed += 1
            print()
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print()
        print("✅ All basic checks passed!")
        print()
        print("Next steps:")
        print("1. Install MCP SDK: pip install mcp")
        print("2. Configure Antigravity to connect to this server")
        print("3. Test end-to-end integration")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
