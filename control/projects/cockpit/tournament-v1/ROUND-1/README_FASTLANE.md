# ROUND-1 FASTLANE RUNBOOK

Goal
- Run R16 with zero ambiguity.

Do this only
1. Open dispatch list:
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/PROMPTS/03_ROUND1_PROMPTS_READY.md

2. Send each prompt file to matching agent.

3. Collect outputs only in:
- /Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1/ROUND-1/FIGHT-XX/SUBMISSIONS/

4. After each fight final submissions are in, send one TOURNAMENT_UPDATE_V1 packet to Clems.

Important
- If a submission file already exists from a previous test, overwrite it for this run.
- Do not create alternative filenames.
- Do not move files outside fight folders.
