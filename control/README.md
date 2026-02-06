# Cockpit MCP Server

MCP (Model Context Protocol) server for integrating Antigravity agents with Cockpit mission control.

## Features

- ✅ **5 Core Tools**: `post_message`, `read_state`, `update_agent_state`, `request_run`, `get_quotas`
- ✅ **Real-time Updates**: Agent state synchronization with Cockpit UI
- ✅ **Run Management**: User-approved run requests with auto-approval for safe operations
- ✅ **Quota Tracking**: Monitor API limits and resource usage
- ✅ **Chat Integration**: Post messages to global channel or threads

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure MCP Client** (in Antigravity):
   
   Add to your MCP client configuration (e.g., `~/.config/antigravity/mcp_config.json`):
   
   ```json
   {
     "mcpServers": {
       "cockpit": {
         "command": "python3",
         "args": ["/Users/oliviercloutier/Desktop/Cockpit/control/mcp_server.py"],
         "env": {
           "COCKPIT_PROJECT_ID": "your_project_id"
         }
       }
     }
   }
   ```

## Usage

### From Antigravity Agent

The MCP server exposes 5 tools that Antigravity agents can call:

#### 1. Post Message
```python
await use_mcp_tool("cockpit.post_message", {
    "agent_id": "ag_motherload_miner_a7f3c12b",
    "content": "🚀 Started mining PDFs from university repository",
    "priority": "normal",
    "tags": ["#milestone", "#mining"]
})
```

#### 2. Read Project State
```python
state = await use_mcp_tool("cockpit.read_state", {
    "agent_id": "ag_motherload_miner_a7f3c12b",
    "scope": "full"  # or "summary", "roadmap", "agents", "metrics"
})
```

#### 3. Update Agent State
```python
await use_mcp_tool("cockpit.update_agent_state", {
    "agent_id": "ag_motherload_miner_a7f3c12b",
    "project_id": "proj_motherload_3d9a821c",
    "status": "executing",
    "progress": 45,
    "current_phase": "PDF Extraction",
    "current_task": "Processing batch 3/10"
})
```

#### 4. Request Run
```python
run = await use_mcp_tool("cockpit.request_run", {
    "agent_id": "ag_motherload_deployer_xyz",
    "run_type": "test",
    "project_id": "proj_motherload_3d9a821c",
    "description": "Run pytest suite on new features",
    "risk_level": "safe",  # Auto-approves
    "estimated_duration": 120
})
```

#### 5. Check Quotas
```python
quotas = await use_mcp_tool("cockpit.get_quotas", {
    "agent_id": "ag_motherload_miner_a7f3c12b",
    "scope": "agent"
})

if quotas["quotas"]["api_calls"]["status"] == "LOW":
    print("⚠️ API quota running low!")
```

## Architecture

```
┌─────────────────────────────────────┐
│     Antigravity Agent Manager        │
│  (Mission Control / Agent Platform)  │
└──────────────┬──────────────────────┘
               │ MCP Protocol
               │ (stdio/JSON-RPC)
               ▼
┌─────────────────────────────────────┐
│      Cockpit MCP Server              │
│      (control/mcp_server.py)         │
├─────────────────────────────────────┤
│  Tools:                              │
│   • post_message                     │
│   • read_state                       │
│   • update_agent_state               │
│   • request_run                      │
│   • get_quotas                       │
└──────────────┬──────────────────────┘
               │ Python API
               ▼
┌─────────────────────────────────────┐
│     Cockpit Data Layer               │
│     (app/data/store.py)              │
├─────────────────────────────────────┤
│  • Projects                          │
│  • Agent States                      │
│  • Messages                          │
│  • Run Requests                      │
└─────────────────────────────────────┘
```

## Protocol Conventions

### Agent IDs
Format: `ag_{project}_{role}_{uuid8}`  
Example: `ag_motherload_miner_a7f3c12b`

### Project IDs
Format: `proj_{slug}_{uuid8}`  
Example: `proj_motherload_3d9a821c`

### Status Values
- `idle` - No active work
- `planning` - Research/design phase
- `executing` - Implementation
- `verifying` - Testing/validation
- `blocked` - Waiting on user/external dependency
- `error` - Encountered error
- `completed` - Task finished

### Heartbeat Protocol
- **Frequency**: Every 60 seconds during active work
- **Timeout**: 90 seconds → "unresponsive", 5 minutes → "idle"
- **Format**: Call `update_agent_state` with `heartbeat: true`

### Tags
Standard tags: `#milestone`, `#blocker`, `#question`, `#review`, `#deploy`, `#test`, `#research`

## Logging

Server logs are written to:
- **File**: `mcp_server.log` (in server directory)
- **stderr**: Real-time console output

Log format:
```
2026-02-06 17:44:20 [INFO] Tool called: cockpit.update_agent_state
2026-02-06 17:44:20 [INFO] Updating agent state: ag_test_abc @ proj_test_xyz - executing (45%)
```

## Error Handling

All tools return JSON responses. Errors follow this format:

```json
{
  "error": "Human-readable error message"
}
```

Common error scenarios:
- **Project not found**: Check `project_id` is valid
- **Agent not registered**: Call `update_agent_state` first to register
- **Invalid parameters**: Check tool schema requirements

## Testing

Test the MCP server manually:

```bash
# Run server in test mode
python3 control/mcp_server.py

# In another terminal, send test JSON-RPC request
echo '{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "cockpit.get_quotas",
    "arguments": {"agent_id": "test_agent"}
  },
  "id": 1
}' | python3 control/mcp_server.py
```

## Next Steps

- [ ] Implement persistent message storage (database)
- [ ] Add WebSocket support for real-time UI updates
- [ ] Build run approval UI in Cockpit frontend
- [ ] Implement actual quota tracking system
- [ ] Add authentication/authorization layer
- [ ] Create comprehensive test suite

## See Also

- [MCP Integration Specification](../brain/*/mcp_integration_spec.md) - Full protocol reference
- [Cockpit UI Components](../app/ui/) - Frontend implementation
- [Data Models](../app/data/model.py) - Core data structures

---

**Version**: 1.0.0  
**Last Updated**: 2026-02-06
