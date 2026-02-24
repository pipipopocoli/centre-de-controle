# ISSUE-CP-0056 - Wave16 Codex-Only Outage Mode

- Owner: victor
- Phase: Ship
- Status: Done

## Objective
Run the active lane in codex-only outage mode while Antigravity is unavailable.

## Scope (In)
- `app/services/auto_mode.py`
- `control/projects/cockpit/agents/registry.json`
- `control/projects/cockpit/settings.json`
- `tests/verify_wave16_codex_only_outage_mode.py`

## Done (Definition)
- [x] `nova` is routed to Codex for this wave.
- [x] AG-targeted dispatch is blocked under outage mode policy.
- [x] Deterministic test proves codex-only behavior.

## Constraints
- no tournament activation
- no UI redesign in this lane

## Closeout
- Closed at: 2026-02-24T00:00:00Z
- Proof:
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/agents/registry.json`
  - `/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/settings.json`
  - `/Users/oliviercloutier/Desktop/Cockpit/tests/verify_wave16_codex_only_outage_mode.py`
