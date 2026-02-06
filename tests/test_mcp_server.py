#!/usr/bin/env python3
"""
MCP Server Test Suite
=====================
Tests the Cockpit MCP server implementation.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.store import ensure_demo_project, get_project  # noqa: E402


def test_post_message():
    """Test post_message tool."""
    print("Testing: cockpit.post_message")
    
    arguments = {
        "agent_id": "test_agent_123",
        "content": "🧪 Test message from unit test",
        "priority": "normal",
        "tags": ["#test"],
        "metadata": {"project_id": "demo"}
    }
    
    # Simulate tool call
    from control.mcp_server import handle_post_message
    result = asyncio.run(handle_post_message(arguments))
    
    data = json.loads(result[0].text)
    assert "message_id" in data
    assert data["status"] == "posted"
    print(f"  ✅ Message posted: {data['message_id']}")


def test_read_state():
    """Test read_state tool."""
    print("Testing: cockpit.read_state")
    
    ensure_demo_project()
    
    arguments = {
        "agent_id": "test_agent_123",
        "project_id": "demo",
        "scope": "full"
    }
    
    from control.mcp_server import handle_read_state
    result = asyncio.run(handle_read_state(arguments))
    
    data = json.loads(result[0].text)
    assert "projects" in data
    assert len(data["projects"]) > 0
    assert data["projects"][0]["project_id"] == "demo"
    print(f"  ✅ State read: {data['projects'][0]['name']}")


def test_update_agent_state():
    """Test update_agent_state tool."""
    print("Testing: cockpit.update_agent_state")
    
    ensure_demo_project()
    
    arguments = {
        "agent_id": "test_agent_xyz",
        "project_id": "demo",
        "status": "executing",
        "progress": 75,
        "current_phase": "Testing",
        "current_task": "Running MCP tests",
        "metadata": {"source": "test_suite"}
    }
    
    from control.mcp_server import handle_update_agent_state
    result = asyncio.run(handle_update_agent_state(arguments))
    
    data = json.loads(result[0].text)
    assert data["acknowledged"] == True
    assert "update_id" in data
    
    # Verify agent was added/updated
    project = get_project("demo")
    agent = next((a for a in project.agents if a.agent_id == "test_agent_xyz"), None)
    assert agent is not None
    assert agent.status == "executing"
    assert agent.percent == 75
    assert agent.phase == "Test"
    print(f"  ✅ Agent state updated: {agent.name} @ {agent.percent}% ({agent.phase})")


def test_request_run():
    """Test request_run tool."""
    print("Testing: cockpit.request_run")
    
    ensure_demo_project()
    
    # Test auto-approval
    arguments = {
        "agent_id": "test_agent_123",
        "run_type": "test",
        "project_id": "demo",
        "description": "Test run with auto-approval",
        "risk_level": "safe",
        "requires_confirmation": False
    }
    
    from control.mcp_server import handle_request_run
    result = asyncio.run(handle_request_run(arguments))
    
    data = json.loads(result[0].text)
    assert data["status"] == "approved"
    assert data["run_id"] is not None
    print(f"  ✅ Run auto-approved: {data['run_id']}")
    
    # Test pending approval
    arguments["risk_level"] = "medium"
    arguments["requires_confirmation"] = True
    
    result = asyncio.run(handle_request_run(arguments))
    data = json.loads(result[0].text)
    assert data["status"] == "pending_approval"
    assert data["run_id"] is None
    print(f"  ✅ Run pending approval: {data['request_id']}")


def test_get_quotas():
    """Test get_quotas tool."""
    print("Testing: cockpit.get_quotas")
    
    arguments = {
        "agent_id": "test_agent_123",
        "scope": "agent"
    }
    
    from control.mcp_server import handle_get_quotas
    result = asyncio.run(handle_get_quotas(arguments))
    
    data = json.loads(result[0].text)
    assert "quotas" in data
    assert "api_calls" in data["quotas"]
    assert data["quotas"]["api_calls"]["status"] == "OK"
    print(f"  ✅ Quotas retrieved: {data['plan']} plan")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Cockpit MCP Server Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        test_post_message,
        test_read_state,
        test_update_agent_state,
        test_request_run,
        test_get_quotas
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
            print()
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1
            print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
