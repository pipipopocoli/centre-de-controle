#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUND1_DIR = ROOT / "ROUND-1"
ROUND2_DIR = ROOT / "ROUND-2"
ROUND3_DIR = ROOT / "ROUND-3"
ACTIVE_L3_DIR = ROUND3_DIR / "ACTIVE_L3"
FINAL_DIR = ROOT / "FINAL"
DATA_DIR = ROOT / "data"
DATA_JSON = DATA_DIR / "arena_state.json"
DATA_JS = DATA_DIR / "arena_state.js"

AGENT_PROJECTS = {
    "agent-1": "Rogue",
    "agent-2": "Pulse",
    "agent-3": "Atlas",
    "agent-4": "Nova",
    "agent-5": "Titan",
    "agent-6": "Vortex",
    "agent-7": "Cipher",
    "agent-8": "Astra",
    "agent-9": "Blaze",
    "agent-10": "Orbit",
    "agent-11": "Drift",
    "agent-12": "Echo",
    "agent-13": "Flux",
    "agent-14": "Shard",
    "agent-15": "Zenith",
    "agent-16": "Aegis",
}

FIGHTS_R16 = {
    "F01": ("agent-1", "agent-16"),
    "F02": ("agent-8", "agent-9"),
    "F03": ("agent-5", "agent-12"),
    "F04": ("agent-4", "agent-13"),
    "F05": ("agent-6", "agent-11"),
    "F06": ("agent-3", "agent-14"),
    "F07": ("agent-7", "agent-10"),
    "F08": ("agent-2", "agent-15"),
}

FIGHTS_QF = {
    "F09": ("winner:F01", "winner:F02"),
    "F10": ("winner:F03", "winner:F04"),
    "F11": ("winner:F05", "winner:F06"),
    "F12": ("winner:F07", "winner:F08"),
}

FIGHTS_SF = {
    "F13": ("winner:F09", "winner:F10"),
    "F14": ("winner:F11", "winner:F12"),
}

FIGHTS_FINAL = {
    "F15": ("winner:F13", "winner:F14"),
}

ROUND_META = {
    "F01": ("R16", "L1"),
    "F02": ("R16", "L1"),
    "F03": ("R16", "L1"),
    "F04": ("R16", "L1"),
    "F05": ("R16", "L1"),
    "F06": ("R16", "L1"),
    "F07": ("R16", "L1"),
    "F08": ("R16", "L1"),
    "F09": ("QF", "L2"),
    "F10": ("QF", "L2"),
    "F11": ("QF", "L2"),
    "F12": ("QF", "L2"),
    "F13": ("SF", "L3"),
    "F14": ("SF", "L3"),
    "F15": ("FINAL", "L4"),
}

ROUND_ORDER = ["R16", "QF", "SF", "FINAL"]
ROUND_DIR_BY_ID = {
    "R16": ROUND1_DIR,
    "QF": ROUND2_DIR,
    "SF": ROUND3_DIR,
    "FINAL": FINAL_DIR,
}
VERSION_TAG_BY_ROUND = {
    "R16": "V1",
    "QF": "V2",
    "SF": "V3",
    "FINAL": "V4",
}

FIGHT_ORDER = {
    "R16": ["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08"],
    "QF": ["F09", "F10", "F11", "F12"],
    "SF": ["F13", "F14"],
    "FINAL": ["F15"],
}

ALL_FIGHTS = {}
ALL_FIGHTS.update(FIGHTS_R16)
ALL_FIGHTS.update(FIGHTS_QF)
ALL_FIGHTS.update(FIGHTS_SF)
ALL_FIGHTS.update(FIGHTS_FINAL)

LEAD_IDS = {"leo", "victor"}


def agent_stage(has_bootstrap: bool, has_final: bool) -> str:
    if has_final and has_bootstrap:
        return "final"
    if has_final and not has_bootstrap:
        return "final_only"
    if has_bootstrap and not has_final:
        return "bootstrap"
    return "none"


def normalize_status(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().lower()
    aliases = {
        "winner_locked": "winner_locked",
        "winner locked": "winner_locked",
        "pending": "pending",
        "scoring": "scoring",
        "scoring_requested_with_waiver": "scoring",
        "awaiting_submissions": "awaiting_submissions",
        "ready_for_prompt": "ready_for_prompt",
    }
    return aliases.get(text)


def normalize_agent(value: str | None) -> str | None:
    if value is None:
        return None
    candidate = value.strip().lower()
    if re.match(r"^agent-\d+$", candidate):
        return candidate
    if candidate in LEAD_IDS:
        return candidate
    return None


def participant_sort_key(agent_id: str) -> tuple[int, int | str]:
    if agent_id.startswith("agent-"):
        try:
            return (0, int(agent_id.split("-", 1)[1]))
        except ValueError:
            return (0, agent_id)
    if agent_id in LEAD_IDS:
        return (1, agent_id)
    return (2, agent_id)


def ensure_agent_record(agents: dict[str, dict], agent_id: str) -> None:
    if agent_id in agents:
        return
    agents[agent_id] = {
        "agent_id": agent_id,
        "project": AGENT_PROJECTS.get(agent_id, "Unknown"),
        "fight": None,
        "has_bootstrap": False,
        "has_final": False,
        "stage": "none",
        "files": [],
        "pitch": {
            "html_present": False,
            "skills_declared_count": 0,
            "html_index_path": None,
            "skills_x3_ok": False,
        },
    }


def is_winner_ref(token: str) -> bool:
    return token.startswith("winner:")


def resolve_token(token: str, winner_by_fight: dict[str, str | None]) -> str | None:
    if is_winner_ref(token):
        source = token.split(":", 1)[1]
        return winner_by_fight.get(source)
    return token


def unique_limit(items: list[str], limit: int) -> list[str]:
    out: list[str] = []
    seen = set()
    for item in items:
        if not item:
            continue
        key = item.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item.strip())
        if len(out) >= limit:
            break
    return out


def clean_item(text: str) -> str:
    cleaned = text.strip().strip("-").strip()
    cleaned = cleaned.replace("`", "")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def judge_path_for_fight(fight_id: str, round_id: str) -> Path:
    fight_dir = f"FIGHT-{fight_id[1:]}"
    candidates = []
    round_dir = ROUND_DIR_BY_ID.get(round_id)
    if round_dir is not None:
        candidates.append(round_dir / fight_dir / "JUDGE_FEEDBACK.md")
        candidates.append(round_dir / "JUDGE_FEEDBACK.md")
    if round_id != "FINAL":
        candidates.append(FINAL_DIR / fight_dir / "JUDGE_FEEDBACK.md")
    for path in candidates:
        if path.exists():
            return path
    return candidates[0] if candidates else FINAL_DIR / fight_dir / "JUDGE_FEEDBACK.md"


def submission_candidates(round_id: str, fight_id: str, agent_id: str, kind: str) -> list[Path]:
    version = VERSION_TAG_BY_ROUND[round_id]
    filename = f"{agent_id}_SUBMISSION_{version}_{kind}.md"
    fight_dir = f"FIGHT-{fight_id[1:]}"

    if round_id in {"R16", "QF"}:
        base = ROUND_DIR_BY_ID[round_id]
        return [base / fight_dir / "SUBMISSIONS" / filename]

    if round_id == "SF":
        return [
            ACTIVE_L3_DIR / fight_dir / "SUBMISSIONS" / filename,
            ROUND3_DIR / fight_dir / "SUBMISSIONS" / filename,
        ]

    return [
        ACTIVE_L3_DIR / fight_dir / "SUBMISSIONS" / filename,
        FINAL_DIR / fight_dir / "SUBMISSIONS" / filename,
        FINAL_DIR / "SUBMISSIONS" / filename,
        FINAL_DIR / filename,
    ]


def html_pitch_index_candidates(round_id: str, fight_id: str, agent_id: str) -> list[Path]:
    folder = f"{agent_id}_FINAL_HTML"
    fight_dir = f"FIGHT-{fight_id[1:]}"

    if round_id == "R16":
        return [ROUND1_DIR / fight_dir / "SUBMISSIONS" / folder / "index.html"]
    if round_id == "QF":
        return [ROUND2_DIR / fight_dir / "SUBMISSIONS" / folder / "index.html"]
    if round_id == "SF":
        return [
            ACTIVE_L3_DIR / fight_dir / "SUBMISSIONS" / folder / "index.html",
            ROUND3_DIR / fight_dir / "SUBMISSIONS" / folder / "index.html",
        ]
    return [
        ACTIVE_L3_DIR / fight_dir / "SUBMISSIONS" / folder / "index.html",
        FINAL_DIR / fight_dir / "SUBMISSIONS" / folder / "index.html",
        FINAL_DIR / folder / "index.html",
    ]


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def detect_skills_declared_count(html_path: Path | None) -> int:
    if html_path is None or not html_path.exists():
        return 0
    text = read_text(html_path)
    matches = re.findall(r"(?i)\bskill(?:\s*[:#-]|\s+[1-9])", text)
    count = len(matches)
    if count == 0 and re.search(r"(?i)\bskills?\s+choisis\b", text):
        return 1
    return count


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_status_from_text(text: str) -> str | None:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.strip().lower() != "status":
            continue
        for nxt in lines[idx + 1:]:
            stripped = nxt.strip()
            if not stripped:
                continue
            if stripped.startswith("- "):
                return normalize_status(stripped[2:].strip())
            break
    return None


def parse_winner_from_text(text: str) -> str | None:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.strip().lower() != "winner":
            continue
        for nxt in lines[idx + 1:]:
            stripped = nxt.strip()
            if not stripped:
                continue
            if stripped.startswith("- "):
                winner = stripped[2:].strip()
                lowered = winner.lower()
                if lowered in {"tbd", "pending", "none", "null", "-"}:
                    return None
                return normalize_agent(winner)
            break
    return None


def parse_score_totals(text: str) -> dict[str, int]:
    scores: dict[str, int] = {}
    for m in re.finditer(r"(?mi)^-\s*(agent-\d+):.*?\btotal\s+(-?\d+)\s*$", text):
        scores[m.group(1).lower()] = int(m.group(2))
    return scores


def parse_rationale_lines(text: str) -> list[str]:
    lines = text.splitlines()
    out: list[str] = []
    for idx, line in enumerate(lines):
        if line.strip().lower() != "rationale":
            continue
        for nxt in lines[idx + 1:]:
            stripped = nxt.strip()
            if not stripped:
                if out:
                    return out
                continue
            if stripped.startswith("- "):
                out.append(clean_item(stripped[2:]))
                continue
            if out:
                return out
            break
        return out
    return out


def read_judge(fight_id: str, round_id: str) -> dict:
    path = judge_path_for_fight(fight_id, round_id)
    text = read_text(path)
    status = parse_status_from_text(text)
    if status is None and not path.exists() and round_id in {"QF", "SF", "FINAL"}:
        status = "pending"
    winner = parse_winner_from_text(text)
    scores = parse_score_totals(text)
    rationale = parse_rationale_lines(text)
    return {
        "file": str(path),
        "status": status,
        "winner": winner,
        "scores": scores,
        "rationale": rationale,
    }


def parse_sections(text: str) -> dict[str, list[str]]:
    sections = {
        "objective": [],
        "architecture": [],
        "imports": [],
        "risk": [],
    }
    current: str | None = None

    title_map = {
        "objective": "objective",
        "architecture/workflow summary": "architecture",
        "imported opponent ideas (accepted/rejected/deferred)": "imports",
        "risk register": "risk",
        "risk register (probability x impact)": "risk",
    }

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        plain = line.strip().lower()

        m = re.match(r"^\s*#{1,3}\s*(?:\d+\.\s*)?(.+?)\s*$", line)
        if m:
            title = m.group(1).strip().lower()
            if "objective" in title:
                current = "objective"
            elif "architecture/workflow summary" in title or ("architecture" in title and "workflow" in title):
                current = "architecture"
            elif "imported opponent ideas" in title:
                current = "imports"
            elif "risk register" in title:
                current = "risk"
            else:
                current = None
            continue

        if plain in title_map:
            current = title_map[plain]
            continue

        if current is not None:
            sections[current].append(line)
    return sections


def extract_bullets(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            out.append(clean_item(stripped[2:]))
        elif stripped.startswith("* "):
            out.append(clean_item(stripped[2:]))
        elif stripped.startswith("|"):
            continue
        elif re.match(r"^(in|out|accepted|rejected|deferred)\s*:?\s*$", stripped, re.IGNORECASE):
            continue
        else:
            out.append(clean_item(stripped))
    return out


def parse_import_buckets(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    accepted: list[str] = []
    rejected: list[str] = []
    deferred: list[str] = []
    mode: str | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        content = stripped[2:].strip() if stripped.startswith("- ") else stripped
        low = content.lower()

        if low in {"accepted", "accepted:"}:
            mode = "accepted"
            continue
        if low in {"rejected", "rejected:"}:
            mode = "rejected"
            continue
        if low in {"deferred", "deferred:"}:
            mode = "deferred"
            continue

        if "decision: accepted" in low:
            accepted.append(clean_item(content))
            continue
        if "decision: rejected" in low:
            rejected.append(clean_item(content))
            continue
        if "decision: deferred" in low:
            deferred.append(clean_item(content))
            continue

        if "weak own idea" in low and "rejected" in low:
            rejected.append(clean_item(content))
            continue

        if stripped.startswith("- "):
            if mode == "accepted" and low not in {"none", "none."}:
                accepted.append(clean_item(content))
            elif mode == "rejected" and low not in {"none", "none."}:
                rejected.append(clean_item(content))
            elif mode == "deferred" and low not in {"none", "none."}:
                deferred.append(clean_item(content))

    return accepted, rejected, deferred


def extract_risks(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|") and re.search(r"\|\s*R\d+\s*\|", stripped):
            columns = [col.strip() for col in stripped.strip("|").split("|")]
            if len(columns) >= 2:
                out.append(clean_item(columns[1]))
            continue
        low = stripped.lower()
        if low.startswith("- risk:"):
            out.append(clean_item(stripped.split(":", 1)[1]))
        elif low.startswith("risk:"):
            out.append(clean_item(stripped.split(":", 1)[1]))
    return out


def infer_fight_status(
    round_id: str,
    winner: str | None,
    a_has_bootstrap: bool | None,
    a_has_final: bool | None,
    b_has_bootstrap: bool | None,
    b_has_final: bool | None,
    resolved_a: str | None,
    resolved_b: str | None,
) -> str:
    if winner:
        return "winner_locked"

    if resolved_a is None or resolved_b is None:
        return "ready_for_prompt"

    both_final = bool(a_has_final) and bool(b_has_final)
    any_submission = bool(a_has_bootstrap or a_has_final or b_has_bootstrap or b_has_final)
    if both_final:
        return "scoring"
    if any_submission:
        return "awaiting_submissions"
    if round_id in {"SF", "FINAL"}:
        return "pending"
    return "ready_for_prompt"


def stage2_for_agent(round_id: str, fight_id: str, agent_id: str | None) -> dict:
    if not agent_id:
        return {
            "md_final_received": None,
            "html_pitch_received": None,
            "html_index_path": None,
            "skills_declared_count": None,
            "skills_x3_ok": None,
        }

    md_paths = submission_candidates(round_id, fight_id, agent_id, "FINAL")
    html_paths = html_pitch_index_candidates(round_id, fight_id, agent_id)
    md_received = any(path.exists() for path in md_paths)
    html_index = first_existing(html_paths)
    html_received = html_index is not None
    skills_count = detect_skills_declared_count(html_index)

    return {
        "md_final_received": md_received,
        "html_pitch_received": html_received,
        "html_index_path": str(html_index) if html_index else None,
        "skills_declared_count": skills_count,
        "skills_x3_ok": skills_count >= 3,
    }


def extract_winner_dossier(
    winner: str,
    project: str,
    source_file: Path,
    rationale: list[str],
) -> dict:
    if not source_file.exists():
        return {
            "agent_id": winner,
            "project": project,
            "source_file": str(source_file),
            "descriptif_general": "not_extracted: winner_final_file_missing",
            "gros_avantages": ["not_extracted: winner_final_file_missing"],
            "innovations": ["not_extracted: winner_final_file_missing"],
            "faiblesses": ["not_extracted: winner_final_file_missing"],
        }

    text = read_text(source_file)
    sections = parse_sections(text)

    objective_points = unique_limit(extract_bullets(sections["objective"]), 3)
    architecture_points = unique_limit(extract_bullets(sections["architecture"]), 4)
    accepted, rejected, deferred = parse_import_buckets(sections["imports"])
    accepted = unique_limit(accepted, 6)
    rejected = unique_limit(rejected, 6)
    deferred = unique_limit(deferred, 6)
    risks = unique_limit(extract_risks(sections["risk"]), 6)

    desc_parts = unique_limit(objective_points[:2] + architecture_points[:2], 4)
    descriptif_general = "; ".join(desc_parts) if desc_parts else "not_extracted: objective_or_architecture"

    advantages = unique_limit(rationale + accepted + objective_points, 3)
    if not advantages:
        advantages = ["not_extracted: advantages"]

    innovation_keywords = (
        "lane",
        "tiered",
        "threshold",
        "deterministic",
        "sla",
        "gate",
        "escalation",
        "stoplight",
        "risk-tiered",
        "command-based",
    )
    innovation_candidates: list[str] = []
    for item in architecture_points + accepted + rationale:
        low = item.lower()
        if any(key in low for key in innovation_keywords):
            innovation_candidates.append(item)
    innovations = unique_limit(innovation_candidates + accepted, 3)
    if not innovations:
        innovations = ["not_extracted: innovations"]

    weaknesses = unique_limit(rejected + risks + deferred, 3)
    if not weaknesses:
        weaknesses = ["not_extracted: weaknesses"]

    return {
        "agent_id": winner,
        "project": project,
        "source_file": str(source_file),
        "descriptif_general": descriptif_general,
        "gros_avantages": advantages,
        "innovations": innovations,
        "faiblesses": weaknesses,
    }


def detect_active_round(fights: dict[str, dict]) -> str:
    for round_id in ROUND_ORDER:
        for fight_id in FIGHT_ORDER[round_id]:
            fight = fights[fight_id]
            if fight["status"] != "winner_locked":
                return round_id
    return "FINAL"


def next_wildcard_id(existing_ids: set[str]) -> str:
    number = 17
    while f"agent-{number}" in existing_ids:
        number += 1
    return f"agent-{number}"


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Build per-agent stage from R16 fights only.
    agents = {}
    for agent_id in sorted(AGENT_PROJECTS.keys(), key=participant_sort_key):
        agents[agent_id] = {
            "agent_id": agent_id,
            "project": AGENT_PROJECTS[agent_id],
            "fight": None,
            "has_bootstrap": False,
            "has_final": False,
            "stage": "none",
            "files": [],
            "pitch": {
                "html_present": False,
                "skills_declared_count": 0,
                "html_index_path": None,
                "skills_x3_ok": False,
            },
        }

    for fight_id, (agent_a, agent_b) in FIGHTS_R16.items():
        for agent_id in (agent_a, agent_b):
            ensure_agent_record(agents, agent_id)
            bootstrap_path = submission_candidates("R16", fight_id, agent_id, "BOOTSTRAP")[0]
            final_path = submission_candidates("R16", fight_id, agent_id, "FINAL")[0]
            has_bootstrap = bootstrap_path.exists()
            has_final = final_path.exists()
            files = []
            if has_bootstrap:
                files.append(str(bootstrap_path))
            if has_final:
                files.append(str(final_path))

            agents[agent_id].update(
                {
                    "fight": fight_id,
                    "has_bootstrap": has_bootstrap,
                    "has_final": has_final,
                    "stage": agent_stage(has_bootstrap, has_final),
                    "files": files,
                }
            )

    any_submitted = [a for a, meta in agents.items() if meta["stage"] != "none"]
    none_submitted = [a for a, meta in agents.items() if meta["stage"] == "none"]
    final_submitted = [a for a, meta in agents.items() if meta["has_final"]]
    missing_final = [a for a, meta in agents.items() if not meta["has_final"]]

    # Read judge files first so winner refs can resolve in later rounds.
    judge_by_fight: dict[str, dict] = {}
    winner_by_fight: dict[str, str | None] = {}
    for fight_id, _ in ALL_FIGHTS.items():
        round_id, _complexity = ROUND_META[fight_id]
        judge = read_judge(fight_id, round_id)
        judge_by_fight[fight_id] = judge
        winner_by_fight[fight_id] = judge["winner"]

    r16_all_finals = all(
        agents[a]["has_final"] and agents[b]["has_final"]
        for a, b in FIGHTS_R16.values()
    )
    r16_all_winners = all(winner_by_fight[fid] for fid in FIGHT_ORDER["R16"])
    r16_complete = r16_all_finals and r16_all_winners

    fights: dict[str, dict] = {}
    for fight_id, (token_a, token_b) in ALL_FIGHTS.items():
        round_id, complexity = ROUND_META[fight_id]
        judge = judge_by_fight[fight_id]

        resolved_a = resolve_token(token_a, winner_by_fight)
        resolved_b = resolve_token(token_b, winner_by_fight)
        winner = judge["winner"] or winner_by_fight.get(fight_id)

        a_has_bootstrap: bool | None = None
        a_has_final: bool | None = None
        b_has_bootstrap: bool | None = None
        b_has_final: bool | None = None

        if resolved_a is not None and normalize_agent(resolved_a):
            ensure_agent_record(agents, resolved_a)
            a_boot_paths = submission_candidates(round_id, fight_id, resolved_a, "BOOTSTRAP")
            a_final_paths = submission_candidates(round_id, fight_id, resolved_a, "FINAL")
            a_has_bootstrap = any(path.exists() for path in a_boot_paths)
            a_has_final = any(path.exists() for path in a_final_paths)

        if resolved_b is not None and normalize_agent(resolved_b):
            ensure_agent_record(agents, resolved_b)
            b_boot_paths = submission_candidates(round_id, fight_id, resolved_b, "BOOTSTRAP")
            b_final_paths = submission_candidates(round_id, fight_id, resolved_b, "FINAL")
            b_has_bootstrap = any(path.exists() for path in b_boot_paths)
            b_has_final = any(path.exists() for path in b_final_paths)

        inferred_status = infer_fight_status(
            round_id=round_id,
            winner=winner,
            a_has_bootstrap=a_has_bootstrap,
            a_has_final=a_has_final,
            b_has_bootstrap=b_has_bootstrap,
            b_has_final=b_has_final,
            resolved_a=resolved_a,
            resolved_b=resolved_b,
        )
        status = judge["status"] or inferred_status
        if winner:
            status = "winner_locked"
        elif status == "winner_locked":
            status = inferred_status

        scorecard = {
            "agent_a_total": judge["scores"].get((resolved_a or token_a).lower()) if (resolved_a or token_a) else None,
            "agent_b_total": judge["scores"].get((resolved_b or token_b).lower()) if (resolved_b or token_b) else None,
        }

        stage2_required = round_id in {"SF", "FINAL"}
        stage2_a = stage2_for_agent(round_id, fight_id, resolved_a if normalize_agent(resolved_a) else None)
        stage2_b = stage2_for_agent(round_id, fight_id, resolved_b if normalize_agent(resolved_b) else None)
        stage2_ready = (
            bool(stage2_a["md_final_received"])
            and bool(stage2_a["html_pitch_received"])
            and bool(stage2_a["skills_x3_ok"])
            and bool(stage2_b["md_final_received"])
            and bool(stage2_b["html_pitch_received"])
            and bool(stage2_b["skills_x3_ok"])
        ) if stage2_required else bool(a_has_final) and bool(b_has_final)
        stage2_veto_risk = bool(stage2_required and not stage2_ready)

        if normalize_agent(resolved_a):
            ensure_agent_record(agents, resolved_a)
            if stage2_a["html_pitch_received"]:
                agents[resolved_a]["pitch"] = {
                    "html_present": True,
                    "skills_declared_count": stage2_a["skills_declared_count"] or 0,
                    "html_index_path": stage2_a["html_index_path"],
                    "skills_x3_ok": bool(stage2_a["skills_x3_ok"]),
                }
        if normalize_agent(resolved_b):
            ensure_agent_record(agents, resolved_b)
            if stage2_b["html_pitch_received"]:
                agents[resolved_b]["pitch"] = {
                    "html_present": True,
                    "skills_declared_count": stage2_b["skills_declared_count"] or 0,
                    "html_index_path": stage2_b["html_index_path"],
                    "skills_x3_ok": bool(stage2_b["skills_x3_ok"]),
                }

        winner_dossier = None
        if winner:
            source_paths = submission_candidates(round_id, fight_id, winner, "FINAL")
            source_file = next((path for path in source_paths if path.exists()), source_paths[0])
            winner_dossier = extract_winner_dossier(
                winner=winner,
                project=AGENT_PROJECTS.get(winner, "Unknown"),
                source_file=source_file,
                rationale=judge["rationale"],
            )

        fights[fight_id] = {
            "round": round_id,
            "complexity": complexity,
            "status": status,
            "agent_a": token_a,
            "agent_b": token_b,
            "agent_a_resolved": resolved_a,
            "agent_b_resolved": resolved_b,
            "a_has_bootstrap": a_has_bootstrap,
            "a_has_final": a_has_final,
            "b_has_bootstrap": b_has_bootstrap,
            "b_has_final": b_has_final,
            "winner": winner,
            "judge": {
                "status": status,
                "winner": winner,
                "scorecard": scorecard,
                "rationale": judge["rationale"],
                "source_file": judge["file"],
            },
            "winner_dossier": winner_dossier,
            "stage2": {
                "required": stage2_required,
                "agent_a_md": stage2_a["md_final_received"],
                "agent_a_html": stage2_a["html_pitch_received"],
                "agent_b_md": stage2_b["md_final_received"],
                "agent_b_html": stage2_b["html_pitch_received"],
                "agent_a_html_index_path": stage2_a["html_index_path"],
                "agent_b_html_index_path": stage2_b["html_index_path"],
                "agent_a_skills_declared_count": stage2_a["skills_declared_count"],
                "agent_b_skills_declared_count": stage2_b["skills_declared_count"],
                "agent_a_skills_x3_ok": stage2_a["skills_x3_ok"],
                "agent_b_skills_x3_ok": stage2_b["skills_x3_ok"],
                "ready_for_scoring": stage2_ready,
                "veto_risk": stage2_veto_risk,
            },
            "blocked_until_r16_complete": round_id != "R16" and not r16_complete,
        }

    official_locked_count = sum(1 for fight in fights.values() if fight["status"] == "winner_locked")
    official_pending_count = len(fights) - official_locked_count

    l3_entries: list[str] = []
    for fight_id in FIGHT_ORDER["QF"]:
        fight = fights[fight_id]
        if fight["winner"]:
            l3_entries.append(fight["winner"])
        else:
            l3_entries.append(f"winner:{fight_id}")
    ensure_agent_record(agents, "leo")
    ensure_agent_record(agents, "victor")
    l3_entries.extend(["leo", "victor"])

    wildcard_added = None
    if len(l3_entries) % 2 != 0:
        wildcard_added = next_wildcard_id(set(agents.keys()) | set(l3_entries))
        l3_entries.append(wildcard_added)
        ensure_agent_record(agents, wildcard_added)

    l3_pairings = []
    base_fight_number = 13
    for idx in range(0, len(l3_entries), 2):
        fight_num = base_fight_number + (idx // 2)
        l3_pairings.append(
            {
                "fight": f"F{fight_num:02d}",
                "agent_a": l3_entries[idx],
                "agent_b": l3_entries[idx + 1] if idx + 1 < len(l3_entries) else None,
            }
        )

    state = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "round": detect_active_round(fights),
        "trackers": {
            "any_submitted": len(any_submitted),
            "none_submitted": len(none_submitted),
            "final_submitted": len(final_submitted),
            "missing_final_count": len(missing_final),
            "official_locked_count": official_locked_count,
            "official_pending_count": official_pending_count,
        },
        "missing_agents": {
            "none": none_submitted,
            "missing_final": missing_final,
        },
        "agents": agents,
        "fights": fights,
        "fight_order": FIGHT_ORDER,
        "l3": {
            "entries": l3_entries,
            "wildcard_added": wildcard_added,
            "pairings": l3_pairings,
            "rules": {
                "dual_stage_required": True,
                "skills_required": 3,
                "pitch_points": 25,
                "total_points": 125,
            },
        },
    }

    DATA_JSON.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    DATA_JS.write_text("window.ARENA_STATE = " + json.dumps(state, indent=2) + ";\n", encoding="utf-8")

    print(f"Wrote {DATA_JSON}")
    print(f"Wrote {DATA_JS}")
    print("Trackers:", state["trackers"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
