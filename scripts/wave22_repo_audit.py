#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ACTIVE_SURFACES = {
    "desktop_tauri": "apps/cockpit-desktop",
    "rust_core": "crates/cockpit-core",
    "python_app": "app",
    "python_server": "server",
    "android": "android",
    "scripts": "scripts",
    "docs_active": "docs",
    "control_project": "control/projects/cockpit",
}

EXCLUDED_PARTS = {
    ".git",
    "node_modules",
    "target",
    "dist",
    "build",
    ".venv",
    "venv",
    ".pytest_cache",
    "site/.vercel",
    "docs/releases",
    "docs/swarm",
    "control/projects/cockpit/tournament-v1",
    "control/projects/cockpit/tournament-v2",
    "control/projects/cockpit/MEGA_MERGE",
    "repo/cockpit",
    "_cleanup_archive",
}

PATTERNS = {
    "legacy_naming": re.compile(r"Cockpit Next|Centre de controle|launch_cockpit_legacy|legacy Python", re.I),
    "demo_refs": re.compile(r"\bdemo\b|wizard-demo|ws-demo|rbac-demo|proj_demo", re.I),
    "stale_api_refs": re.compile(r"chat/agentic-turn|wizard-live/start|wizard-live/run|wizard-live/stop", re.I),
    "debt_markers": re.compile(r"\b(?:TODO|FIXME|HACK)\b"),
    "legacy_runtime": re.compile(r"legacy_|legacy\b", re.I),
}

DOC_ROOTS = [
    Path("README.md"),
    Path("QUICKSTART.md"),
    Path("GUIDE_INSTALLATION.md"),
    Path("docs"),
    Path("control/projects/cockpit"),
]

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def is_excluded(path: Path) -> bool:
    text = path.as_posix()
    for part in EXCLUDED_PARTS:
        if part in text:
            return True
    return False


def iter_files(root: Path, base: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(base)
        if is_excluded(rel):
            continue
        if rel.name in {"package-lock.json", "snapshot.json"}:
            continue
        yield path, rel


def scan_surface(base: Path, rel_root: str):
    root = base / rel_root
    files = []
    findings = defaultdict(list)
    if not root.exists():
        return {"root": rel_root, "files": 0, "findings": {}}
    for path, rel in iter_files(root, base):
        files.append(rel.as_posix())
        if path.suffix.lower() not in {".md", ".py", ".rs", ".ts", ".tsx", ".css", ".json", ".yml", ".yaml", ".sh", ".kt", ".html"}:
            continue
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for key, pattern in PATTERNS.items():
            for match in pattern.finditer(raw):
                line_no = raw[: match.start()].count("\n") + 1
                line = raw.splitlines()[line_no - 1][:220] if raw.splitlines() else ""
                findings[key].append({
                    "file": rel.as_posix(),
                    "line": line_no,
                    "snippet": line.strip(),
                })
    return {
        "root": rel_root,
        "files": len(files),
        "findings": {k: v[:80] for k, v in findings.items() if v},
    }


def iter_doc_files(base: Path):
    for root in DOC_ROOTS:
        target = base / root
        if not target.exists():
            continue
        if target.is_file():
            rel = target.relative_to(base)
            if not is_excluded(rel):
                yield target, rel
            continue
        for path, rel in iter_files(target, base):
            if path.suffix.lower() == ".md":
                yield path, rel


def check_links(base: Path):
    broken = []
    for path, rel in iter_doc_files(base):
        raw = path.read_text(encoding="utf-8", errors="ignore")
        for match in MARKDOWN_LINK_RE.finditer(raw):
            target = match.group(1).strip()
            if not target or target.startswith("http://") or target.startswith("https://") or target.startswith("#") or target.startswith("mailto:"):
                continue
            if target.startswith("/"):
                resolved = Path(target)
            else:
                resolved = (path.parent / target).resolve()
            if not resolved.exists():
                broken.append({
                    "file": rel.as_posix(),
                    "target": target,
                    "resolved": str(resolved),
                })
    return broken


def top_findings(summary):
    rows = []
    for surface, info in summary.items():
        for key, matches in info.get("findings", {}).items():
            rows.append((len(matches), surface, key, matches[:5]))
    return sorted(rows, reverse=True)


def write_truth_md(out_path: Path, summary):
    lines = ["# Wave22 Repo Truth Scan", "", "## Live Surfaces", "", "| Surface | Root | Files | Key Findings |", "|---|---|---:|---:|"]
    for surface, info in summary.items():
        findings_count = sum(len(v) for v in info.get("findings", {}).values())
        lines.append(f"| `{surface}` | `{info['root']}` | {info['files']} | {findings_count} |")
    lines.extend(["", "## Notes", ""])
    for count, surface, key, matches in top_findings(summary)[:20]:
        lines.append(f"- `{surface}` / `{key}`: {count} hit(s)")
        for match in matches:
            lines.append(f"  - `{match['file']}:{match['line']}` - {match['snippet']}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_hygiene_md(out_path: Path, summary, broken_links):
    lines = ["# Wave22 Repo Hygiene Findings", "", "## Top Debt Buckets", ""]
    for count, surface, key, matches in top_findings(summary)[:25]:
        lines.append(f"### {surface} / {key} ({count})")
        for match in matches:
            lines.append(f"- `{match['file']}:{match['line']}` - {match['snippet']}")
        lines.append("")
    lines.append("## Broken Local Markdown Links")
    lines.append("")
    if not broken_links:
        lines.append("- none")
    else:
        for item in broken_links[:120]:
            lines.append(f"- `{item['file']}` -> `{item['target']}`")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    base = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {name: scan_surface(base, rel_root) for name, rel_root in ACTIVE_SURFACES.items()}
    broken_links = check_links(base)

    (out_dir / "repo_audit.json").write_text(
        json.dumps({"surfaces": summary, "broken_links": broken_links}, indent=2),
        encoding="utf-8",
    )
    write_truth_md(out_dir / "01_repo_truth_scan.md", summary)
    write_hygiene_md(out_dir / "02_repo_hygiene_findings.md", summary, broken_links)


if __name__ == "__main__":
    main()
