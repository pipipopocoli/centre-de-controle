# L4 Match Prompt Template (Gauntlet, Winners-Only)

You are: <agent_id>
PROJECT LOCK: cockpit
Round: L4_GAUNTLET
Fight: <fight_id>
Complexity level required: L4
Project codename now: <project_codename>
Opponent: <opponent_agent_id>

## Read only these files
1. <absolute_path_1>
2. <absolute_path_2>
3. <absolute_path_3>
4. <absolute_path_4>
5. <absolute_path_5>
6. <absolute_path_6>

## OpenClaw online research lock
- Mandatory online comparison against OpenClaw site and code/repo.
- You must record source URLs and checked timestamps in evidence JSON.
- If OpenClaw source cannot be accessed, stop and report blocker with exact URL and error.

## Do not read any other files
- No repo-wide search beyond listed paths and OpenClaw online sources.
- No in-progress submissions from other active L4 competitors.
- If required file is missing, stop with blocker format:
  - `BLOCKER: missing file <absolute path>`

## Mission
Produce a deep, multi-step L4 submission optimized for your operator context.

## Output files (write only)
1. Stage A markdown final:
- <submission_dir>/<agent_id>_SUBMISSION_V4_FINAL.md
2. Stage B html pitch:
- <submission_dir>/<agent_id>_FINAL_HTML/index.html
3. Stage C evidence json:
- <submission_dir>/<agent_id>_EVIDENCE_V4.json

## Stage A markdown requirements (hard)
1. At least 900 lines.
2. Cover all epreuves with explicit stage headings:
- Epreuve A / A1 A2 A3
- Epreuve B / B1 B2 B3 B4
- Epreuve C / C1 C2 C3
- Epreuve D / D1 D2 D3 D4
- Epreuve E / E1 E2 E3 E4
3. Add at least 6 new feature proposals.
4. Add at least 10 risky problems with mitigation.
5. Accept at least 4 opponent ideas (with rationale + proof).
6. Reject at least 2 weak own ideas (with rationale).
7. Include CAD economics tables for:
- Mac local vs online server options
- API economics vs Codex + OpenGravity
8. Keep ASCII only.

## Stage B html pitch requirements (hard)
1. Must open in `file://`.
2. No required external assets for core rendering.
3. Must include these sections with visible headings:
- executive summary
- OpenClaw compare board
- visual moodboard (safe, bold, extreme)
- Mac vs server CAD calculator table
- API economics compare table
- scale map (50/200/1000)
- absorption ledger
- top risks
- why this wins
4. Persuasive framing is required, but every claim must map to evidence.

## Stage C evidence json schema (hard)
Use this exact structure and keep all required keys:

```json
{
  "agent_id": "agent-x",
  "round": "L4",
  "fight": "Fxx",
  "openclaw_sources": [
    {"type":"site","url":"...","checked_at":"ISO-8601"},
    {"type":"code","url":"...","checked_at":"ISO-8601"}
  ],
  "cost_cad": {
    "mac_local_monthly": 0,
    "cloud_options": [
      {"name":"small","monthly_cad":0,"expected_gain_pct":0},
      {"name":"medium","monthly_cad":0,"expected_gain_pct":0},
      {"name":"large","monthly_cad":0,"expected_gain_pct":0}
    ],
    "break_even_months": 0
  },
  "api_economics": {
    "codex_monthly_cad": 0,
    "opengravity_monthly_cad": 0,
    "alternative_api_monthly_cad": 0,
    "decision": "keep|hybrid|switch"
  },
  "absorption": {
    "accepted": ["..."],
    "rejected": ["..."],
    "deferred": ["..."]
  },
  "scale_targets": [50, 200, 1000],
  "veto_checks": {
    "md_present": true,
    "html_present": true,
    "json_present": true,
    "openclaw_compared": true,
    "cad_tables_present": true
  }
}
```

## Epreuve checklist (you must pass all)
- Epreuve A: 3 pitch lenses (exec/operator/technical).
- Epreuve B: OpenClaw compare with strengths and weaknesses.
- Epreuve C: moodboard with 3 routes and app update path.
- Epreuve D: Mac vs server in CAD with break-even and rollback.
- Epreuve E: API economics + scale + absorption + top 10 risks.

## Skills section lock
- Choose exactly 3 allowed skills.
- For each skill include:
  - Skill
  - Pourquoi
  - Valeur attendue
  - Risque d usage
  - Fallback
- Include same 3 skills in markdown and html.

## Opponent absorption lock
- Minimum accepted imports: 4.
- Minimum rejected weak own ideas: 2.
- Every accepted/rejected/deferred item needs rationale and proof pointer.

## Secret scoring policy reminder
- Numeric scores are hidden from agents.
- You will receive only verdict + required imports + blockers.

## Recommended markdown section order
1. Objective
2. Scope in/out
3. Epreuve A (A1/A2/A3)
4. Epreuve B (B1/B2/B3/B4)
5. Epreuve C (C1/C2/C3)
6. Epreuve D (D1/D2/D3/D4)
7. Epreuve E (E1/E2/E3/E4)
8. Changelog vs previous version
9. Test and QA gates
10. DoD checklist
11. Next round strategy
12. Now/Next/Blockers

## Final gate command hints
- line count gate:
  - `test "$(wc -l < <submission_md> | tr -d ' ')" -ge 900`
- html local presence gate:
  - `test -f <submission_dir>/<agent_id>_FINAL_HTML/index.html`
- evidence json gate:
  - `test -f <submission_dir>/<agent_id>_EVIDENCE_V4.json`
