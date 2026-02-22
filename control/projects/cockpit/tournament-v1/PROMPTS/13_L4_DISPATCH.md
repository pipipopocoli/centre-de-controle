# L4 Dispatch (Winners-Only, Gauntlet)

Dispatch gate
- L4 dispatch is blocked until all L3 fights are `winner_locked`:
  - F13
  - F14
  - F15

Roster build rule
1. Take winners in source fight order:
   - winner(F13)
   - winner(F14)
   - winner(F15)
2. If odd count, append wildcard next free id:
   - `agent-18`, then `agent-19`, ...
3. Pair sequentially.

Expected L4 fights
- F17
- F18

Canonical dispatch line
- `Tu es agent-X. Lis ton README L4: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-4/ACTIVE_L4/AGENT_READMES/agent-X_README.md`

Pre-lock placeholders (do not send before L3 lock)
- Tu es winner-F13. Lis ton README L4: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-4/ACTIVE_L4/AGENT_READMES/winner-f13_README.md
- Tu es winner-F14. Lis ton README L4: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-4/ACTIVE_L4/AGENT_READMES/winner-f14_README.md
- Tu es winner-F15. Lis ton README L4: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-4/ACTIVE_L4/AGENT_READMES/winner-f15_README.md
- Tu es agent-18. Lis ton README L4: /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-4/ACTIVE_L4/AGENT_READMES/agent-18_README.md

Post-lock required update
- Replace `winner-f13/f14/f15` with resolved agent ids.
- Remove wildcard line if entrant count becomes even without wildcard.

Hard reminders
- L4 has 3 mandatory outputs:
  - `*_SUBMISSION_V4_FINAL.md`
  - `*_FINAL_HTML/index.html`
  - `*_EVIDENCE_V4.json`
- OpenClaw online compare is mandatory.
- Currency is CAD.
- Missing one output triggers veto risk.
