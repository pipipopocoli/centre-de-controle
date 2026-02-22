# Wave11 Operator Trust Advisory - 2026-02-23

## Brief 60s
- On est ou: Wave11 is active, Dev Live clarity is explicit, and AppSupport is the canonical runtime root for active desktop usage.
- On va ou: complete Wave11 smoke + push manifest/receipt while keeping dual-root cadence gates green.
- Pourquoi: trust fails fast when mode/root/freshness are unclear and operators cannot verify canonical cockpit quickly.
- Comment: run a strict 4-point canonical check before action, then execute with evidence-first decisions.

## Checklist - Canonical cockpit verification
- Mode: Dev Live (not stale Release app).
- Project ID: cockpit.
- Runtime root: AppSupport canonical root.
- Freshness timestamp: generated_at=2026-02-20T17:21:10+00:00 (from current vulgarisation snapshot).

## Residual risks top 3
- R1 | risk: stale release launch confusion remains possible under two-icon behavior. | owner:@leo | action: keep Dev Live anti-confusion text + visual cue in runtime panel and docs. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md
- R2 | risk: stale_tick can return if cadence pulses are skipped during active windows. | owner:@victor | action: keep cadence checks every 30-45 min while Wave11 lanes run. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md
- R3 | risk: full snapshot push has larger blast radius if smoke gate is bypassed. | owner:@clems | action: enforce Wave11 smoke suite before snapshot push + publish push receipt with refs. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md

## Deep RnD D1
- D1 | recommendation: trust-score rubric combining mode/root/freshness checks into one operator scorecard. | owner:@nova | next_action: draft the 4-signal rubric and validate it on 3 live refresh cycles. | evidence_path:/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/STATE.md;/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/ROADMAP.md | decision_tag:adopt

## Now/Next/Blockers
- Now: canonical trust check is explicit and verifiable in <=60s.
- Next: keep 2h reporting cadence and track trust-score D1 through Wave11 closeout.
- Blockers: none.
