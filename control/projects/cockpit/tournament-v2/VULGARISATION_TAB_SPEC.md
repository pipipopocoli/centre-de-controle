# VULGARISATION TAB SPEC - Project local HTML dashboard

## 0) Purpose
- Provide a per-project "Vulgarisation" tab in Centre de controle.
- Give fast operator understanding without external web deployment.

## 1) Product contract
- One local HTML dashboard per project.
- Dashboard source and generated output must live in project workspace.
- Dashboard must open offline.
- Operator has explicit `update` action to regenerate content.

## 2) Required sections
1. Project summary
- what the project is
- current phase
- next milestone

2. Architecture overview
- module diagram
- key interfaces
- boundaries

3. Timeline
- runs
- decisions
- approvals
- regressions

4. Progress panel
- milestones progress
- open tickets
- failing tests
- blocker count

5. Cost and usage panel
- run count
- token estimate
- API estimate (if used)

6. Skill inventory
- installed skills
- versions
- permissions
- trust tier

## 3) Required diagrams
- One high-level block diagram (kernel modules and arrows).
- One orchestration state-flow diagram.
- One timeline chart.
- One metrics bar chart.

## 4) Technical constraints
- Offline-first rendering.
- No mandatory network dependency.
- Stable rendering desktop and mobile.
- ASCII-safe text fallback for all key labels.

## 5) File contracts
Recommended per project paths:
- input config: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/<project_id>/vulgarisation/config.json`
- generated html: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/<project_id>/vulgarisation/index.html`
- generated assets: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/<project_id>/vulgarisation/assets/`
- generation log: `/Users/oliviercloutier/Desktop/Cockpit/control/projects/<project_id>/vulgarisation/update.log`

## 6) Update command contract
UI action name:
- `Update Vulgarisation`

Expected command behavior:
1. Read project state inputs.
2. Build html dashboard.
3. Write `index.html` atomically.
4. Write freshness timestamp.
5. Refresh tab view.

## 7) Freshness and traceability
Dashboard must display:
- generated_at timestamp
- source_snapshot reference
- warning if stale beyond threshold

Recommended stale thresholds:
- warning: > 24h
- critical: > 72h

## 8) Data dependencies
Minimum data inputs:
- project phase/status
- roadmap milestones
- issues/tickets summary
- run history summary
- approvals log summary
- skill lock summary
- cost telemetry summary

## 9) Acceptance tests
- Dashboard opens via local file path.
- All required sections render.
- Update action refreshes timestamp.
- Missing data gracefully degrades with explicit placeholders.
- No crash on empty project history.

## 10) Failure modes and handling
- Missing input files:
  - render fallback blocks
  - log warning
- Invalid metrics:
  - show "data unavailable"
  - keep dashboard usable
- generation error:
  - keep last good html
  - write error to update.log

## 11) Security and policy
- Dashboard generation runs workspace-only by default.
- Any access outside project scope requires @clems approval.
- No secret values rendered in html.
