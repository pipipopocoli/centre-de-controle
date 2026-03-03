from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_ascii(s: Any) -> str:
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    return s.encode("ascii", "replace").decode("ascii")


SEV_ORDER = {"p0": 0, "p1": 1, "p2": 2, "p3": 3}


def _component_for_file(relpath: str) -> str:
    parts = relpath.split("/")
    if not parts:
        return "unknown"
    if parts[0] in {"apps", "crates"} and len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0]


@dataclass(frozen=True)
class Issue:
    file: str
    severity: str
    category: str
    title: str
    detail: str
    questions: tuple[str, ...]
    diff_unified: str | None

    @property
    def component(self) -> str:
        return _component_for_file(self.file)

    @property
    def key(self) -> tuple[str, str, str, str]:
        return (self.file, self.severity, self.category, self.title)


def _load_ndjson(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rows.append(json.loads(ln))
            except json.JSONDecodeError:
                rows.append(
                    {
                        "schema_version": 2,
                        "file": "(unknown)",
                        "status": "parse_error",
                        "model": "",
                        "elapsed_ms": 0,
                        "content_sha256": "",
                        "audit": {
                            "issues": [
                                {
                                    "severity": "p1",
                                    "category": "build",
                                    "title": "ndjson parse error",
                                    "detail": _to_ascii(ln)[:500],
                                }
                            ],
                            "file_questions": [],
                            "notes": "parse_error",
                        },
                    }
                )
    return rows


def _issue_from_raw(file: str, raw: dict[str, Any]) -> Issue | None:
    if not isinstance(raw, dict):
        return None
    severity = _to_ascii(raw.get("severity", "p2")).lower()
    if severity not in SEV_ORDER:
        severity = "p2"
    category = _to_ascii(raw.get("category", "bug")).lower()
    title = _to_ascii(raw.get("title", "")).strip()[:120] or "(missing title)"
    detail = _to_ascii(raw.get("detail", "")).strip()[:8000] or "(missing detail)"

    q = raw.get("questions", [])
    questions: list[str] = []
    if isinstance(q, list):
        questions = [_to_ascii(x)[:500] for x in q if x is not None][:20]

    diff = raw.get("diff_unified", None)
    diff_out = None
    if isinstance(diff, str) and diff.strip():
        diff_out = _to_ascii(diff).rstrip() + "\n"

    return Issue(
        file=_to_ascii(file),
        severity=severity,
        category=category,
        title=title,
        detail=detail,
        questions=tuple(questions),
        diff_unified=diff_out,
    )


def _classify_question(q: str, sev: str) -> str:
    # Deterministic buckets:
    # - blocking: from p0/p1 issues
    # - clarify: from p2 issues
    # - nice: from p3 issues
    if sev in {"p0", "p1"}:
        return "blocking"
    if sev == "p2":
        return "clarify"
    return "nice"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _emit_patch(out_path: Path, issues: list[Issue]) -> None:
    diffs: list[str] = []
    seen = set()
    for it in issues:
        if not it.diff_unified:
            continue
        h = hashlib.sha256(it.diff_unified.encode("utf-8", errors="replace")).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        diffs.append(it.diff_unified.rstrip() + "\n")
    _write_text(out_path, "".join(diffs))


def _git_apply_check(repo_root: Path, patch_path: Path) -> tuple[bool, str]:
    try:
        p = subprocess.run(
            ["git", "apply", "--check", str(patch_path)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
    except Exception as e:
        return False, _to_ascii(e)
    ok = p.returncode == 0
    msg = (p.stdout or "") + (p.stderr or "")
    return ok, _to_ascii(msg).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Swarm consolidator v2 (NDJSON -> reports)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input raw.ndjson path")
    parser.add_argument(
        "--out-dir",
        default=str(Path(__file__).resolve().parent.parent.parent / "docs" / "swarm"),
        help="Output directory (default: docs/swarm)",
    )
    parser.add_argument("--emit-patch-file", action="store_true", help="Write docs/swarm/latest_diffs.patch")
    parser.add_argument("--git-apply-check", action="store_true", help="Run git apply --check on combined patch")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    in_path = Path(args.in_path).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = _load_ndjson(in_path)

    status_counts = Counter()
    sev_counts = Counter()
    cat_counts = Counter()

    issues_by_key: dict[tuple[str, str, str, str], Issue] = {}
    questions_bucket: dict[str, set[str]] = {"blocking": set(), "clarify": set(), "nice": set()}

    for row in rows:
        file = _to_ascii(row.get("file", "(unknown)"))
        status = _to_ascii(row.get("status", "unknown")).lower()
        status_counts[status] += 1

        audit = row.get("audit", {}) if isinstance(row, dict) else {}
        if not isinstance(audit, dict):
            continue

        raw_issues = audit.get("issues", [])
        if isinstance(raw_issues, list):
            for raw in raw_issues:
                it = _issue_from_raw(file, raw)
                if it is None:
                    continue
                issues_by_key.setdefault(it.key, it)
                sev_counts[it.severity] += 1
                cat_counts[it.category] += 1
                for q in it.questions:
                    bucket = _classify_question(q, it.severity)
                    questions_bucket[bucket].add(_to_ascii(q))

        fq = audit.get("file_questions", [])
        if isinstance(fq, list):
            for q in fq:
                q2 = _to_ascii(q).strip()
                if q2:
                    questions_bucket["clarify"].add(q2)

    issues = list(issues_by_key.values())
    issues.sort(
        key=lambda x: (
            SEV_ORDER.get(x.severity, 9),
            x.component,
            x.category,
            x.file,
            x.title,
        )
    )

    stats = {
        "generated_at": _now_utc_iso(),
        "source_ndjson": in_path.as_posix(),
        "counts": {
            "files_total": len(rows),
            "issues_total_deduped": len(issues),
        },
        "status_counts": dict(status_counts),
        "severity_counts": {k: int(sev_counts.get(k, 0)) for k in ["p0", "p1", "p2", "p3"]},
        "category_counts": dict(cat_counts),
    }

    latest_summary = {
        "schema_version": 2,
        "stats": stats,
        "issues": [
            {
                "file": it.file,
                "component": it.component,
                "severity": it.severity,
                "category": it.category,
                "title": it.title,
                "detail": it.detail,
                "questions": list(it.questions),
                "has_diff": bool(it.diff_unified),
            }
            for it in issues
        ],
        "questions": {
            "blocking": sorted(questions_bucket["blocking"]),
            "clarify": sorted(questions_bucket["clarify"]),
            "nice": sorted(questions_bucket["nice"]),
        },
    }
    (out_dir / "latest_summary.json").write_text(
        json.dumps(latest_summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # Patch (optional) + apply check (optional).
    patch_ok = None
    patch_msg = ""
    patch_path = out_dir / "latest_diffs.patch"
    if args.emit_patch_file:
        _emit_patch(patch_path, issues)
        if args.git_apply_check:
            patch_ok, patch_msg = _git_apply_check(repo_root, patch_path)

    # Report markdown.
    md: list[str] = []
    md.append("# Swarm Audit Report (v2)\n")
    md.append(f"Generated: {stats['generated_at']}\n")
    md.append(f"Source: {stats['source_ndjson']}\n")
    md.append("")
    md.append("## Stats\n")
    md.append(f"- files_total: {stats['counts']['files_total']}")
    md.append(f"- issues_total_deduped: {stats['counts']['issues_total_deduped']}")
    md.append(f"- status_counts: {json.dumps(stats['status_counts'], sort_keys=True)}")
    md.append(f"- severity_counts: {json.dumps(stats['severity_counts'], sort_keys=True)}")
    md.append(f"- category_counts: {json.dumps(stats['category_counts'], sort_keys=True)}")
    if args.emit_patch_file:
        md.append(f"- patch_file: {patch_path.as_posix()}")
        if patch_ok is not None:
            md.append(f"- git_apply_check: {'ok' if patch_ok else 'fail'}")
            if patch_msg:
                md.append("")
                md.append("Patch apply check output:")
                md.append("```")
                md.append(_to_ascii(patch_msg)[:2000])
                md.append("```")
    md.append("")

    by_sev: dict[str, list[Issue]] = defaultdict(list)
    for it in issues:
        by_sev[it.severity].append(it)

    def render_sev(sev: str) -> None:
        items = by_sev.get(sev, [])
        md.append(f"## {sev.upper()} issues ({len(items)})\n")
        if not items:
            md.append("- (none)\n")
            return
        # Group by component then category.
        comp_cat: dict[str, dict[str, list[Issue]]] = defaultdict(lambda: defaultdict(list))
        for it in items:
            comp_cat[it.component][it.category].append(it)

        for comp in sorted(comp_cat.keys()):
            md.append(f"### {comp}\n")
            for cat in sorted(comp_cat[comp].keys()):
                md.append(f"- category: {cat}")
                for it in comp_cat[comp][cat]:
                    md.append(f"  - {it.file}: {it.title}")
                    md.append(f"    - detail: {it.detail}")
                    if it.questions:
                        md.append(f"    - questions: {json.dumps(list(it.questions))}")
                    if it.diff_unified:
                        md.append("    - diff: yes")
                md.append("")

    for sev in ["p0", "p1", "p2", "p3"]:
        render_sev(sev)

    _write_text(out_dir / "latest_report.md", "\n".join(md).rstrip() + "\n")

    # Questions markdown.
    qmd: list[str] = []
    qmd.append("# Swarm Questions (v2)\n")
    qmd.append(f"Generated: {stats['generated_at']}\n")
    qmd.append("")
    for bucket in ["blocking", "clarify", "nice"]:
        qmd.append(f"## {bucket.capitalize()}\n")
        qs = sorted(questions_bucket[bucket])
        if not qs:
            qmd.append("- (none)\n")
            continue
        for q in qs:
            qmd.append(f"- {q}")
        qmd.append("")
    _write_text(out_dir / "latest_questions.md", "\n".join(qmd).rstrip() + "\n")

    print(f"wrote {out_dir / 'latest_summary.json'}")
    print(f"wrote {out_dir / 'latest_report.md'}")
    print(f"wrote {out_dir / 'latest_questions.md'}")
    if args.emit_patch_file:
        print(f"wrote {patch_path}")


if __name__ == "__main__":
    main()
