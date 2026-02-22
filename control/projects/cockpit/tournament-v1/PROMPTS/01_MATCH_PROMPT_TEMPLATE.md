# Match Prompt Template (Zero Search, Dual Stage)

You are: <agent_id>
PROJECT LOCK: cockpit
Round: <round_id>
Fight: <fight_id>
Complexity level required: <level>
Project codename now: <project_codename>
Opponent: <opponent_agent_id>

## Read only these files
- <path_1>
- <path_2>
- <path_3>

## Do not read any other files
- If a required file is missing, stop and report blocker with exact path.

## Mission
Create your upgraded tournament submission for this round.

## Output files (write only)
- Stage 1 (technical FINAL): <final_output_path>
- Stage 2 (html pitch): <html_output_dir>/index.html

## Stage 1 FINAL rules
1. Bootstrap output is not accepted.
2. Keep same objective, increase quality.
3. Import >=3 opponent ideas.
4. Reject >=1 weak own idea with reason.
5. Keep output implementation-ready and testable.
6. Keep ASCII only.
7. FINAL markdown must be at least 500 lines.
8. Include at least 4 new feature proposals.
9. Include solutions for existing and potential problems.
10. Include at least 5 risky problems likely to occur.

## Stage 2 HTML pitch requirements
1. Build a convincing sales-style pitch page.
2. Show why the idea is novel and high-leverage.
3. Include evidence, tradeoffs, and execution path.
4. Include local assets only (no required network dependency).
5. Must open directly via `file://`.

## Skills requirement (L3 and later)
- Choose exactly 3 allowed skills.
- Explain each choice in FINAL and in HTML.
- Use this format for each selected skill:
  - Skill
  - Pourquoi
  - Valeur attendue
  - Risque d usage
  - Fallback

## Required FINAL output sections
1. Objective
2. Scope in/out
3. Architecture/workflow summary
4. Changelog vs previous version
5. Imported opponent ideas (accepted/rejected/deferred)
6. Risk register
7. Test and QA gates
8. DoD checklist
9. Next round strategy
10. Now/Next/Blockers
