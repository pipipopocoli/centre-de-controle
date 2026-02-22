#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("/Users/oliviercloutier/Desktop/Cockpit/control/projects/cockpit/tournament-v1")
R2 = ROOT / "ROUND-2"

SPECS = [
    ("agent-16", "F09", "agent-8", "01", "02"),
    ("agent-8", "F09", "agent-16", "02", "01"),
    ("agent-12", "F10", "agent-4", "03", "04"),
    ("agent-4", "F10", "agent-12", "04", "03"),
    ("agent-11", "F11", "agent-3", "05", "06"),
    ("agent-3", "F11", "agent-11", "06", "05"),
    ("agent-10", "F12", "agent-15", "07", "08"),
    ("agent-15", "F12", "agent-10", "08", "07"),
]

JUDGE_FIGHTS = ["09", "10", "11", "12"]



def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""



def main() -> int:
    missing: list[str] = []
    notes: list[str] = []

    # 1) READMEs
    for agent, fight, opp, self_r1, opp_r1 in SPECS:
        fight_num = fight[1:]
        readme = R2 / "AGENT_READMES" / f"{agent}_README.md"
        prompt = R2 / f"FIGHT-{fight_num}" / "PROMPTS" / f"{agent}_PROMPT_QF.md"
        output = R2 / f"FIGHT-{fight_num}" / "SUBMISSIONS" / f"{agent}_SUBMISSION_V2_FINAL.md"
        self_final = ROOT / "ROUND-1" / f"FIGHT-{self_r1}" / "SUBMISSIONS" / f"{agent}_SUBMISSION_V1_FINAL.md"
        opp_final = ROOT / "ROUND-1" / f"FIGHT-{opp_r1}" / "SUBMISSIONS" / f"{opp}_SUBMISSION_V1_FINAL.md"

        if not readme.exists():
            missing.append(str(readme))
        if not prompt.exists():
            missing.append(str(prompt))

        if readme.exists():
            t = read_text(readme)
            for required in [str(prompt), str(output), str(self_final), str(opp_final)]:
                if required not in t:
                    missing.append(f"{readme} missing reference: {required}")

        if prompt.exists():
            t = read_text(prompt)
            if str(output) not in t:
                missing.append(f"{prompt} missing output path: {output}")

    # 2) Judge files
    for num in JUDGE_FIGHTS:
        judge = R2 / f"FIGHT-{num}" / "JUDGE_FEEDBACK.md"
        if not judge.exists():
            missing.append(str(judge))
        else:
            text = read_text(judge)
            required_fragments = [
                "Status",
                "- impact: 30",
                "- workflow: 15",
                "- integration: 10",
                "- feasibility: 20",
                "- risk: 15",
                "- cost_time: 10",
                "Winner",
            ]
            for frag in required_fragments:
                if frag not in text:
                    missing.append(f"{judge} missing fragment: {frag}")

            has_pending = "- pending" in text
            has_locked = "- winner_locked" in text
            if not (has_pending or has_locked):
                missing.append(f"{judge} missing status value: pending or winner_locked")

            has_tbd = "- TBD" in text
            has_agent = bool(re.search(r"(?m)^- agent-\d+\s*$", text))
            if not (has_tbd or has_agent):
                missing.append(f"{judge} missing winner value: TBD or agent-<n>")

    # 3) Dispatch file references
    dispatch_files = [
        ROOT / "PROMPTS" / "07_QF_PROMPTS_READY.md",
        ROOT / "PROMPTS" / "08_ROUND2_QF_DISPATCH.md",
        R2 / "DISPATCH_README_INDEX.md",
    ]
    for path in dispatch_files:
        if not path.exists():
            missing.append(str(path))

    for agent, *_ in SPECS:
        readme_path = R2 / "AGENT_READMES" / f"{agent}_README.md"
        for path in dispatch_files:
            if path.exists():
                if str(readme_path) not in read_text(path):
                    missing.append(f"{path} missing dispatch reference: {readme_path}")

    # 4) Existing draft handling
    draft = R2 / "FIGHT-09" / "SUBMISSIONS" / "agent-8_SUBMISSION_V2_FINAL.md"
    if draft.exists():
        notes.append(f"DRAFT_PREPACK_DETECTED: {draft}")

    if missing:
        print("FAIL")
        print("Missing or invalid items:")
        for item in missing:
            print(f"- {item}")
        if notes:
            print("Notes:")
            for note in notes:
                print(f"- {note}")
        return 1

    print("PASS")
    print("Round 2 QF pack is complete.")
    if notes:
        print("Notes:")
        for note in notes:
            print(f"- {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
