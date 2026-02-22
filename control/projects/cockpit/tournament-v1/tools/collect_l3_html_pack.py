#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_L3 = ROOT / "ROUND-3" / "ACTIVE_L3"
PACK_DIR = ACTIVE_L3 / "HTML_REVIEW_PACK"
MANIFEST_JSON = PACK_DIR / "manifest.json"
INDEX_MD = PACK_DIR / "INDEX.md"


def file_url(path: Path) -> str:
    return "file://" + str(path)


def collect_sources() -> list[dict]:
    out = []
    for fight_dir in sorted(ACTIVE_L3.glob("FIGHT-*")):
        submissions = fight_dir / "SUBMISSIONS"
        if not submissions.exists():
            continue
        for html_dir in sorted(submissions.glob("*_FINAL_HTML")):
            index_html = html_dir / "index.html"
            if not index_html.exists():
                continue
            folder = html_dir.name
            agent_id = folder[: -len("_FINAL_HTML")]
            out.append(
                {
                    "fight": fight_dir.name.replace("FIGHT-", "F"),
                    "agent_id": agent_id,
                    "source_dir": str(html_dir),
                    "source_index": str(index_html),
                }
            )
    return out


def main() -> int:
    PACK_DIR.mkdir(parents=True, exist_ok=True)

    sources = collect_sources()
    copied = []

    for item in sources:
        fight = item["fight"]
        agent_id = item["agent_id"]
        src_dir = Path(item["source_dir"])

        dst_dir = PACK_DIR / fight / f"{agent_id}_FINAL_HTML"
        dst_dir.parent.mkdir(parents=True, exist_ok=True)
        if dst_dir.exists():
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)

        copied.append(
            {
                "fight": fight,
                "agent_id": agent_id,
                "copied_dir": str(dst_dir),
                "copied_index": str(dst_dir / "index.html"),
                "copied_index_url": file_url(dst_dir / "index.html"),
            }
        )

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources_found": len(sources),
        "copied": copied,
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# L3 HTML Review Pack",
        "",
        f"Generated at: {manifest['generated_at']}",
        f"Total pages: {len(copied)}",
        "",
    ]
    if not copied:
        lines.append("- No html pitch pages found yet.")
    else:
        for item in copied:
            lines.append(
                f"- {item['fight']} | {item['agent_id']} | {item['copied_index']} | {item['copied_index_url']}"
            )
    lines.append("")
    INDEX_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {MANIFEST_JSON}")
    print(f"Wrote {INDEX_MD}")
    print(f"Copied html pages: {len(copied)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
