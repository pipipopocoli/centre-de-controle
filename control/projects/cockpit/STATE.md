# State

## Phase
- Review

## Objective
- Keep `cockpit` as the only live project, harden the runtime DB, and close CP-0063 to CP-0066 without regressing direct chat or Le Conseil.

## Now
- Runtime DB opens through one hardened SQLite path with WAL pragmas and indexes.
- `flappycock` has been archived to Drive and removed from the live repo tree.
- Tablet and WCAG first-pass fixes are shipped in the desktop shell.
- CP-0063 to CP-0066 are closed at code level with evidence in local issues and release docs.

## Next
- Manual QA on Pixel Home, Le Conseil, Docs > Project, and tablet breakpoints.
- Manual VoiceOver pass on the installed app.
- Close the remaining room degradation follow-ups only if real operator QA reopens CP-0061 or CP-0062.

## In Progress
- none

## Blockers
- none

## Risks
- Room contributor fanout can still degrade when all active L1 lanes stay on Kimi and OpenRouter is slow.
- Full VoiceOver validation still requires manual operator testing on the installed app.

## Links
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0061-fix-z-index-overlay-chat-pixel-home.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0062-impl-menter-pagination-messages-concierge-room.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0063-finaliser-hardening-db.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0064-d-ployer-backup-automatique.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0065-responsive-tablette.md
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/issues/ISSUE-CP-0066-audit-accessibilit-wcag.md
- /Users/oliviercloutier/Desktop/Cockpit/docs/COCKPIT_RUNBOOK.md
