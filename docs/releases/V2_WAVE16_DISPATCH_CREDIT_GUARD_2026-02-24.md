# Wave16 Dispatch Packet - Credit Guard Window (2026-02-24)

## Objective
- Keep Wave16 delivery active under codex-only outage mode, with strict credit guard and deterministic lead-first dispatch.

## Order + policy lock
1. `@victor` (runtime/backend lead)
2. `@nova` (advisory + vulgarisation + decision ledger)
3. Wait 15 minutes for lead ack (`Now / Next / Blockers`)
4. `@agent-3` only if backend load requires specialist split

Explicit pause rule:
- Do not ping `@leo` for active implementation while AG credits are unavailable.

## Gates (must stay green)
- pending stale (24h+) == 0
- stale heartbeats (1h+) <= 2
- queued runtime requests <= 3
- repo root healthcheck == healthy
- appsupport root healthcheck == healthy
- codex_only_dispatch_guard == true

## Credit guard policy
- `wave_cap <= 180`
- `reserve_floor >= 350`
- `max_actions_effective = 1`
- If reserve floor is reached, freeze new implementation prompts and keep maintenance cadence only.

## Prompt 1 - @victor (copy/paste)
```md
@victor
Objective
- Lead Wave16 runtime/backend lane in codex-only mode and keep dual-root recency healthy.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/app/services/auto_mode.py
- /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py
- /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/settings.json
- /Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave16_*.py

Scope (Out)
- AG lane reactivation
- tournament activation
- UI redesign scope

Done
- Pulse/check cadence holds both roots healthy
- Codex-only guard remains enforced
- Credit guard limits remain active and auditable
- Report in Now/Next/Blockers every checkpoint

Blocker rule
- If blocker >60 min: post 2 options + 1 recommended option, ping @clems.
```

## Prompt 2 - @nova (copy/paste)
```md
@nova
Objective
- Maintain Wave16 advisory lane with operator-first digest and evidence-backed recommendations.

Scope (In)
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/nova/memory.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/reports/
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/

Scope (Out)
- AG dispatch requests
- provider policy changes

Done
- Publish one deep research item per project phase touchpoint
- Every recommendation includes owner, next action, evidence path, decision tag
- Keep Brief 60s and operator wording short and actionable
- Report in Now/Next/Blockers every checkpoint

Blocker rule
- If blocker >60 min: post 2 options + 1 recommended option, ping @clems.
```

## Prompt 3 - @agent-3 (optional, copy/paste)
```md
@agent-3
Objective
- Support backend load only when requested by @victor after lead ack.

Scope (In)
- Deterministic tests and backend hardening files assigned by @victor

Scope (Out)
- UI lane files
- AG provider flow

Done
- Deliver assigned backend/test delta with clear proof
- Report in Now/Next/Blockers

Blocker rule
- If blocker >60 min: post 2 options + 1 recommended option, ping @victor and @clems.
```

## Cadence commands (operator)
```bash
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --data-dir repo --pulse-only
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode.py --project cockpit --pulse-only
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --data-dir repo --stale-seconds 3600 --max-open 3 --autopulse-guard
/Users/oliviercloutier/Desktop/Cockpit/.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/auto_mode_healthcheck.py --project cockpit --stale-seconds 3600 --max-open 3 --autopulse-guard
```

## Now / Next / Blockers template
- Now: <what is active now>
- Next: <next concrete step>
- Blockers: <explicit blocker or none>
