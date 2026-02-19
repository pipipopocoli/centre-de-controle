# Roadmap

## Vision
- Ship Cockpit V2 implementation-first with strict runtime control and optional tournament mode preserved dormant.

## Priorities
- P0: WAVE05 backend contracts (registry, scoring, backpressure, fallback).
- P1: Cost + SLO operator visibility in Pilotage/Vulgarisation.
- P2: Keep runtime hygiene green while parallel lanes run.
- P3: Keep tournament trees reusable but non-auto-executed.

## Sequence
1. Open CP-0026..CP-0032 issue set.
2. Land registry runtime source of truth and fallback-safe roster loading.
3. Land scoring + deterministic ranking + queue backpressure cap.
4. Land execution router chain `codex -> antigravity -> ollama` (flagged).
5. Emit CAD cost events + monthly estimate.
6. Emit SLO verdict artifact GO/HOLD from p95/p99/success targets.
7. Surface SLO/cost in UI and vulgarisation output.
8. Run gates at T+120 / T+240 / T+360 and close wave packet.

## Daily control gates
- pending stale (24h+) must be 0
- stale heartbeats (1h+) must be <= 2
- queued runtime requests must be <= 3
- no tournament auto-dispatch during active implementation lanes

## Active source of truth
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE_MAP_WAVE05_CP003X.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/runs/V2_WAVE05_DISPATCH_2026-02-19.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-VICTOR-WAVE05.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/missions/MISSION-LEO-WAVE05.md
