#!/usr/bin/env python3
"""Memory index CLI (build + search)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services.memory_index import build_agent_memory_indexes, build_index, search_memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or query Cockpit memory index")
    parser.add_argument("--project", required=True, help="Project id (ex: cockpit)")
    parser.add_argument(
        "--projects-root",
        default=None,
        help="Projects root path (default: ~/Library/Application Support/Cockpit/projects)",
    )
    parser.add_argument("--query", default=None, help="Optional query. If provided, runs search after build.")
    parser.add_argument("--limit", type=int, default=5, help="Search limit (default: 5)")
    parser.add_argument(
        "--skip-agent-json",
        action="store_true",
        help="Skip deterministic agents/*/memory.index.json generation.",
    )
    args = parser.parse_args()

    projects_root = Path(args.projects_root).expanduser() if args.projects_root else None
    report = build_index(args.project, projects_root=projects_root)
    print(f"Indexed {report.docs_indexed} docs -> {report.db_path}")

    if not args.skip_agent_json:
        agent_report = build_agent_memory_indexes(args.project, projects_root=projects_root)
        print(
            "Generated agent memory indexes:"
            f" count={agent_report.generated_count}"
            f" agents={','.join(agent_report.indexed_agents)}"
        )

    if args.query:
        hits = search_memory(args.project, args.query, limit=args.limit, projects_root=projects_root)
        print(f"Hits ({len(hits)}):")
        for hit in hits:
            print(f"- {hit.path} [{hit.source_type}] score={hit.score:.4f}")
            if hit.snippet:
                print(f"  {hit.snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
