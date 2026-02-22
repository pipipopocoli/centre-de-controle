# OpenClaw Sources (Operator Managed)

Purpose
- Define approved online OpenClaw references for L4 benchmark work.
- Agents must compare against both site and code/repo sources.

Status
- REQUIRED BEFORE DISPATCH: set at least 1 site URL and 1 code/repo URL.

Approved online sources

Site URLs
1. <fill_me_openclaw_site_url_1>
2. <fill_me_openclaw_site_url_2_optional>

Code/Repo URLs
1. <fill_me_openclaw_code_or_repo_url_1>
2. <fill_me_openclaw_code_or_repo_url_2_optional>

Agent evidence requirements
- In `<agent_id>_EVIDENCE_V4.json`, include:
  - one `type: site` URL from this file
  - one `type: code` URL from this file
  - `checked_at` timestamp in ISO-8601 for each URL

Blocker rule
- If this file is not filled with valid URLs at dispatch time, agents must stop with:
  - `BLOCKER: missing OpenClaw source URLs in /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/PROMPTS/15_OPENCLAW_SOURCES.md`
