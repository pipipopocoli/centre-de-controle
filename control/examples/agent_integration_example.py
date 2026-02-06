"""
Example: Antigravity Agent Integration with Cockpit
====================================================

This example shows how an Antigravity agent initializes and communicates
with Cockpit via MCP tools.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any


class MockMCPClient:
    """Mock MCP client for demonstration."""
    
    async def use_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict:
        """Simulate calling an MCP tool."""
        print(f"📡 Calling {tool_name}...")
        print(f"   Arguments: {arguments}")
        # In real usage, this would call the actual MCP server
        return {"status": "success"}


async def initialize_agent(mcp: MockMCPClient, agent_id: str, project_id: str):
    """Initialize agent connection to Cockpit."""
    
    # Step 1: Check quotas
    quotas = await mcp.use_tool("cockpit.get_quotas", {
        "agent_id": agent_id,
        "scope": "agent"
    })
    print(f"✅ Quota check complete: {quotas}")
    
    # Step 2: Register agent with initial state
    await mcp.use_tool("cockpit.update_agent_state", {
        "agent_id": agent_id,
        "project_id": project_id,
        "status": "idle",
        "progress": 0,
        "current_phase": "Plan",
        "current_task": "Connecting to Cockpit"
    })
    print(f"✅ Agent {agent_id} registered")
    
    # Step 3: Post initialization message
    await mcp.use_tool("cockpit.post_message", {
        "agent_id": agent_id,
        "content": "🚀 Agent initialized and ready for work",
        "priority": "low",
        "tags": ["#startup"]
    })
    print(f"✅ Posted initialization message")


async def execute_task(mcp: MockMCPClient, agent_id: str, project_id: str):
    """Execute a sample task with progress updates."""
    
    # Read current project state
    state = await mcp.use_tool("cockpit.read_state", {
        "agent_id": agent_id,
        "project_id": project_id,
        "scope": "summary"
    })
    print(f"📊 Project state: {state}")
    
    # Transition to planning
    await mcp.use_tool("cockpit.update_agent_state", {
        "agent_id": agent_id,
        "project_id": project_id,
        "status": "planning",
        "progress": 10,
        "current_phase": "Plan",
        "current_task": "Analyzing requirements"
    })
    
    await mcp.use_tool("cockpit.post_message", {
        "agent_id": agent_id,
        "content": "📋 Starting planning phase for feature implementation",
        "priority": "normal",
        "tags": ["#planning"]
    })
    
    # Simulate work
    await asyncio.sleep(2)
    
    # Transition to execution
    await mcp.use_tool("cockpit.update_agent_state", {
        "agent_id": agent_id,
        "project_id": project_id,
        "status": "executing",
        "progress": 45,
        "current_phase": "Implement",
        "current_task": "Building core features"
    })
    
    await mcp.use_tool("cockpit.post_message", {
        "agent_id": agent_id,
        "content": "⚡ Executing implementation phase",
        "priority": "normal",
        "tags": ["#implementation"]
    })
    
    # Simulate more work
    await asyncio.sleep(2)
    
    # Request a test run
    run_request = await mcp.use_tool("cockpit.request_run", {
        "agent_id": agent_id,
        "run_type": "test",
        "project_id": project_id,
        "description": "Run automated test suite on new features",
        "risk_level": "safe",  # Will auto-approve
        "estimated_duration": 120,
        "parameters": {
            "test_suite": "full",
            "coverage": True
        }
    })
    print(f"🏃 Run request: {run_request}")
    
    # Complete task
    await mcp.use_tool("cockpit.update_agent_state", {
        "agent_id": agent_id,
        "project_id": project_id,
        "status": "completed",
        "progress": 100,
        "current_phase": "Ship",
        "current_task": "Feature implementation finished"
    })
    
    await mcp.use_tool("cockpit.post_message", {
        "agent_id": agent_id,
        "content": "✅ Feature implementation complete! All tests passing.",
        "priority": "high",
        "tags": ["#milestone", "#completed"]
    })


async def heartbeat_loop(mcp: MockMCPClient, agent_id: str, project_id: str, duration: int = 5):
    """Simulate heartbeat updates during active work."""
    
    for i in range(duration):
        await mcp.use_tool("cockpit.update_agent_state", {
            "agent_id": agent_id,
            "project_id": project_id,
            "status": "executing",
            "heartbeat": True
        })
        print(f"💓 Heartbeat {i+1}/{duration}")
        await asyncio.sleep(1)


async def main():
    """Main example workflow."""
    
    # Configuration
    AGENT_ID = "ag_example_worker_a7f3c12b"
    PROJECT_ID = "proj_demo_xyz123"
    
    print("=" * 60)
    print("Antigravity → Cockpit Integration Example")
    print("=" * 60)
    print()
    
    # Initialize mock MCP client
    mcp = MockMCPClient()
    
    # Initialize agent
    print("🔧 Phase 1: Initialization")
    print("-" * 60)
    await initialize_agent(mcp, AGENT_ID, PROJECT_ID)
    print()
    
    # Execute task
    print("🚀 Phase 2: Task Execution")
    print("-" * 60)
    await execute_task(mcp, AGENT_ID, PROJECT_ID)
    print()
    
    # Demonstrate heartbeat
    print("💓 Phase 3: Heartbeat Loop")
    print("-" * 60)
    await heartbeat_loop(mcp, AGENT_ID, PROJECT_ID, duration=3)
    print()
    
    print("=" * 60)
    print("✅ Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
