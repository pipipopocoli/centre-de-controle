#!/usr/bin/env python3
"""
Cockpit MCP Server
==================
MCP server for Antigravity ⇄ Cockpit integration.

Implements 5 core tools:
- cockpit.post_message
- cockpit.read_state
- cockpit.update_agent_state
- cockpit.request_run
- cockpit.get_quotas
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.model import AgentState, ProjectData  # noqa: E402
from app.data.store import get_project, list_projects, save_project  # noqa: E402

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Create mock classes for testing without MCP SDK
    class Tool:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class TextContent:
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text
    
    class Server:
        def __init__(self, name: str):
            self.name = name
        def list_tools(self):
            def decorator(func):
                return func
            return decorator
        def call_tool(self):
            def decorator(func):
                return func
            return decorator
    
    def stdio_server():
        """Mock stdio_server for testing."""
        class MockContext:
            async def __aenter__(self):
                return (None, None)
            async def __aexit__(self, *args):
                pass
        return MockContext()



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("mcp_server.log"), logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("cockpit-mcp")

# Log MCP availability
if not MCP_AVAILABLE:
    logger.warning("MCP SDK not installed - running in mock mode for testing")
    logger.warning("Install with: pip install mcp")

# Initialize MCP server
server = Server("cockpit")

# Tool definitions based on specification
TOOL_DEFINITIONS = [
    Tool(
        name="cockpit.post_message",
        description="Post messages to Cockpit chatroom (global channel or specific threads)",
        inputSchema={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Message content (markdown supported)",
                    "maxLength": 4000
                },
                "thread_id": {
                    "type": "string",
                    "description": "Optional thread ID. If null, posts to global channel",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high", "urgent"],
                    "default": "normal",
                    "description": "Message priority level"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tags for filtering/organization",
                    "maxItems": 5
                },
                "agent_id": {
                    "type": "string",
                    "description": "Antigravity agent identifier"
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional structured metadata",
                }
            },
            "required": ["content", "agent_id"]
        }
    ),
    Tool(
        name="cockpit.read_state",
        description="Read current project state and roadmap information",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier. If null, returns all accessible projects",
                },
                "scope": {
                    "type": "string",
                    "enum": ["summary", "roadmap", "agents", "metrics", "full"],
                    "default": "summary",
                    "description": "Data scope to retrieve"
                },
                "agent_id": {
                    "type": "string",
                    "description": "Requesting agent identifier"
                }
            },
            "required": ["agent_id"]
        }
    ),
    Tool(
        name="cockpit.update_agent_state",
        description="Signal agent progression (%, phase, ETA) to update the Cockpit grid",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Antigravity agent identifier"
                },
                "project_id": {
                    "type": "string",
                    "description": "Associated project"
                },
                "status": {
                    "type": "string",
                    "enum": ["idle", "planning", "executing", "verifying", "blocked", "error", "completed"],
                    "description": "Current agent status"
                },
                "progress": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Completion percentage of current task"
                },
                "current_phase": {
                    "type": "string",
                    "description": "Current work phase"
                },
                "current_task": {
                    "type": "string",
                    "description": "Brief description of current task",
                    "maxLength": 200
                },
                "eta": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Estimated completion time"
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metrics",
                },
                "heartbeat": {
                    "type": "boolean",
                    "default": False,
                    "description": "True if this is a periodic heartbeat update"
                }
            },
            "required": ["agent_id", "project_id", "status"]
        }
    ),
    Tool(
        name="cockpit.request_run",
        description="Trigger runs with user confirmation",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Requesting agent identifier"
                },
                "run_type": {
                    "type": "string",
                    "enum": ["test", "build", "deploy", "analysis", "migration", "custom"],
                    "description": "Type of run to execute"
                },
                "project_id": {
                    "type": "string",
                    "description": "Target project"
                },
                "description": {
                    "type": "string",
                    "description": "Human-readable description",
                    "maxLength": 500
                },
                "parameters": {
                    "type": "object",
                    "description": "Run-specific parameters",
                },
                "estimated_duration": {
                    "type": "integer",
                    "description": "Estimated duration in seconds",
                },
                "risk_level": {
                    "type": "string",
                    "enum": ["safe", "low", "medium", "high"],
                    "default": "low",
                    "description": "Risk assessment"
                },
                "requires_confirmation": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether user confirmation is required"
                }
            },
            "required": ["agent_id", "run_type", "project_id", "description"]
        }
    ),
    Tool(
        name="cockpit.get_quotas",
        description="Report quota and rate limit status",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent identifier"
                },
                "scope": {
                    "type": "string",
                    "enum": ["agent", "project", "global"],
                    "default": "agent",
                    "description": "Quota scope to check"
                }
            },
            "required": ["agent_id"]
        }
    )
]


# Tool implementations
async def handle_post_message(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle cockpit.post_message tool call."""
    try:
        content = arguments["content"]
        agent_id = arguments["agent_id"]
        thread_id = arguments.get("thread_id")
        priority = arguments.get("priority", "normal")
        tags = arguments.get("tags", [])
        metadata = arguments.get("metadata", {})

        # TODO: Implement actual message storage/broadcasting
        # For now, log to file and return success
        message_id = f"msg_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{agent_id[:8]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        message_data = {
            "message_id": message_id,
            "content": content,
            "agent_id": agent_id,
            "thread_id": thread_id,
            "priority": priority,
            "tags": tags,
            "metadata": metadata,
            "timestamp": timestamp
        }

        logger.info(f"Message posted: {message_id} from {agent_id} (priority: {priority})")
        
        # Store message in project data
        project_id = metadata.get("project_id")
        if project_id:
            try:
                project = get_project(project_id)
                if "messages" not in project.settings:
                    project.settings["messages"] = []
                project.settings["messages"].append(message_data)
                save_project(project)
            except Exception as e:
                logger.warning(f"Could not save message to project: {e}")

        result = {
            "message_id": message_id,
            "timestamp": timestamp,
            "status": "posted",
            "thread_url": f"cockpit://messages/{message_id}"
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in post_message: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def handle_read_state(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle cockpit.read_state tool call."""
    try:
        agent_id = arguments["agent_id"]
        project_id = arguments.get("project_id")
        scope = arguments.get("scope", "summary")

        logger.info(f"Reading state: agent={agent_id}, project={project_id}, scope={scope}")

        if project_id:
            # Get specific project
            project = get_project(project_id)
            projects_data = [_serialize_project(project, scope)]
        else:
            # Get all projects
            projects = list_projects()
            projects_data = [_serialize_project(p, scope) for p in projects]

        result = {
            "projects": projects_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in read_state: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def handle_update_agent_state(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle cockpit.update_agent_state tool call."""
    try:
        agent_id = arguments["agent_id"]
        project_id = arguments["project_id"]
        status = arguments["status"]
        progress = arguments.get("progress", 0)
        current_phase = arguments.get("current_phase", "")
        current_task = arguments.get("current_task", "")
        eta = arguments.get("eta")
        metadata = arguments.get("metadata", {})
        is_heartbeat = arguments.get("heartbeat", False)

        logger.info(f"Updating agent state: {agent_id} @ {project_id} - {status} ({progress}%)")

        # Load project
        project = get_project(project_id)

        # Find or create agent
        agent_idx = next((i for i, a in enumerate(project.agents) if a.agent_id == agent_id), None)
        
        # Calculate ETA in minutes
        eta_minutes = None
        if eta:
            try:
                eta_dt = datetime.fromisoformat(eta.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                eta_minutes = int((eta_dt - now).total_seconds() / 60)
            except Exception as e:
                logger.warning(f"Could not parse ETA: {e}")

        if agent_idx is not None:
            # Update existing agent
            agent = project.agents[agent_idx]
            agent.status = status
            agent.progress = int(progress)
            agent.phase = current_phase or agent.phase
            agent.eta_minutes = eta_minutes
            agent.heartbeat = datetime.now(timezone.utc).isoformat()
        else:
            # Create new agent
            agent = AgentState(
                agent_id=agent_id,
                name=metadata.get("name", agent_id),
                source=metadata.get("source", "antigravity"),
                phase=current_phase,
                progress=int(progress),
                eta_minutes=eta_minutes,
                heartbeat=datetime.now(timezone.utc).isoformat(),
                status=status
            )
            project.agents.append(agent)

        # Store current task in settings
        if not is_heartbeat:
            if "agent_tasks" not in project.settings:
                project.settings["agent_tasks"] = {}
            project.settings["agent_tasks"][agent_id] = {
                "current_task": current_task,
                "current_phase": current_phase,
                "metadata": metadata,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

        save_project(project)

        update_id = f"update_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{agent_id[:8]}"
        result = {
            "update_id": update_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "acknowledged": True,
            "dashboard_url": f"cockpit://projects/{project_id}/agents/{agent_id}"
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in update_agent_state: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def handle_request_run(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle cockpit.request_run tool call."""
    try:
        agent_id = arguments["agent_id"]
        run_type = arguments["run_type"]
        project_id = arguments["project_id"]
        description = arguments["description"]
        parameters = arguments.get("parameters", {})
        estimated_duration = arguments.get("estimated_duration")
        risk_level = arguments.get("risk_level", "low")
        requires_confirmation = arguments.get("requires_confirmation", True)

        logger.info(f"Run request: {run_type} from {agent_id} (risk: {risk_level})")

        # Generate request ID
        request_id = f"run_req_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{agent_id[:8]}"

        # Auto-approve safe test runs
        auto_approved = (risk_level == "safe" and run_type == "test" and not requires_confirmation)
        
        status = "approved" if auto_approved else "pending_approval"
        run_id = f"run_{run_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}" if auto_approved else None

        # Store run request in project
        project = get_project(project_id)
        if "run_requests" not in project.settings:
            project.settings["run_requests"] = []
        
        run_request = {
            "request_id": request_id,
            "run_id": run_id,
            "agent_id": agent_id,
            "run_type": run_type,
            "description": description,
            "parameters": parameters,
            "estimated_duration": estimated_duration,
            "risk_level": risk_level,
            "status": status,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "auto_approved": auto_approved
        }
        project.settings["run_requests"].append(run_request)
        save_project(project)

        result = {
            "request_id": request_id,
            "status": status,
            "run_id": run_id,
            "confirmation_url": f"cockpit://projects/{project_id}/runs/{request_id}",
            "estimated_approval_time": 300 if not auto_approved else 0,
            "message": "Auto-approved" if auto_approved else "Pending user confirmation"
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in request_run: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def handle_get_quotas(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle cockpit.get_quotas tool call."""
    try:
        agent_id = arguments["agent_id"]
        scope = arguments.get("scope", "agent")

        logger.info(f"Checking quotas: agent={agent_id}, scope={scope}")

        # TODO: Implement actual quota tracking
        # For now, return mock "OK" status
        result = {
            "quotas": {
                "api_calls": {
                    "limit": 10000,
                    "used": 150,
                    "remaining": 9850,
                    "reset_at": (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()),
                    "status": "OK"
                },
                "messages": {
                    "limit": 1000,
                    "used": 45,
                    "remaining": 955,
                    "reset_at": (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()),
                    "status": "OK"
                },
                "runs": {
                    "concurrent_limit": 5,
                    "active_runs": 0,
                    "queued_runs": 0,
                    "status": "OK"
                },
                "storage": {
                    "limit_bytes": 10737418240,  # 10 GB
                    "used_bytes": 1073741824,     # 1 GB
                    "remaining_bytes": 9663676416,
                    "status": "OK"
                }
            },
            "plan": "developer",
            "warnings": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in get_quotas: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


def _serialize_project(project: ProjectData, scope: str) -> dict[str, Any]:
    """Serialize project data based on scope."""
    data = {
        "project_id": project.project_id,
        "name": project.name,
        "status": project.settings.get("status", "active")
    }

    if scope in ["roadmap", "full"]:
        data["roadmap"] = {
            "phases": [
                {
                    "phase_id": phase,
                    "name": phase,
                    "status": "active" if i < 2 else "pending",
                    "progress": 75 if i == 0 else 30 if i == 1 else 0,
                    "eta": None
                }
                for i, phase in enumerate(project.roadmap.keys())
            ],
            "current_phase": list(project.roadmap.keys())[0] if project.roadmap else None
        }

    if scope in ["agents", "full"]:
        data["agents"] = [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "status": agent.status or "idle",
                "current_task": project.settings.get("agent_tasks", {}).get(agent.agent_id, {}).get("current_task")
            }
            for agent in project.agents
        ]

    if scope in ["metrics", "full"]:
        total_tasks = sum(len(tasks) for tasks in project.roadmap.values())
        data["metrics"] = {
            "total_tasks": total_tasks,
            "completed_tasks": int(total_tasks * 0.3),  # Mock
            "active_runs": len([r for r in project.settings.get("run_requests", []) if r.get("status") == "running"]),
            "last_update": datetime.now(timezone.utc).isoformat()
        }

    return data


# MCP Server handlers
@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return TOOL_DEFINITIONS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {name}")
    
    if name == "cockpit.post_message":
        return await handle_post_message(arguments)
    elif name == "cockpit.read_state":
        return await handle_read_state(arguments)
    elif name == "cockpit.update_agent_state":
        return await handle_update_agent_state(arguments)
    elif name == "cockpit.request_run":
        return await handle_request_run(arguments)
    elif name == "cockpit.get_quotas":
        return await handle_get_quotas(arguments)
    else:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    """Run MCP server."""
    logger.info("Starting Cockpit MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
