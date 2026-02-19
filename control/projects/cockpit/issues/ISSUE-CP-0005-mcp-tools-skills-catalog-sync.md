# ISSUE-CP-0005 - MCP tools for skills catalog and sync

- Owner: victor
- Phase: Implement
- Status: Done

## Objective
- Add MCP tools `list_skills_catalog` and `sync_skills` with dry_run support.

## Scope (In)
- Tool schemas and handlers.
- Dry-run response payload.
- Error handling and logging.

## Scope (Out)
- UI controls and UX copy.
- Full production auth layer.

## Now
- MCP tools implemented and wired:
  - `cockpit.list_skills_catalog`
  - `cockpit.sync_skills`

## Next
- Monitor payload compatibility for existing MCP clients.
- Keep fail-open policy visible in response warnings/events.

## Blockers
- None.

## Done (Definition)
- Both tools callable and return structured payload.
- `sync_skills` supports dry_run true/false.
- No crash on missing catalog; clear error returned.

## Links
- STATE.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- DECISIONS.md: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/DECISIONS.md
- Server: /Users/oliviercloutier/Desktop/Cockpit/control/mcp_server.py
- Catalog: /Users/oliviercloutier/Desktop/Cockpit/app/services/skills_catalog.py
- Installer: /Users/oliviercloutier/Desktop/Cockpit/app/services/skills_installer.py
- Policy: /Users/oliviercloutier/Desktop/Cockpit/app/services/skills_policy.py
- Test: /Users/oliviercloutier/Desktop/Cockpit/tests/verify_mcp_skills_tools.py
- PR: main (V2-WAVE-03)

## Risks
- Tool contract drift with existing MCP clients.

## Proof
- `cd /Users/oliviercloutier/Desktop/Cockpit && .venv/bin/python tests/verify_mcp_skills_tools.py`
- Result: both MCP tools callable with structured payloads and dry_run support.
