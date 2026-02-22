#!/usr/bin/env python3
"""Timeline feed contract + determinism verification."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.data.model import ProjectData  # noqa: E402
from app.services.timeline_feed import build_portfolio_timeline_feed, build_project_timeline_feed  # noqa: E402


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _seed_project(base: Path, project_id: str) -> ProjectData:
    project_dir = base / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    _write(
        project_dir / "STATE.md",
        "# State\n\n## Phase\n- Implement\n## Objective\n- Stabilize wave\n## Now\n- Dispatch active\n## Next\n- Ship packet\n## Blockers\n- none\n## Risks\n- queue drift\n",
    )
    _write(
        project_dir / "ROADMAP.md",
        "# Roadmap\n\n## Next\n- Lock gates\n## Risks\n- stale heartbeat\n",
    )
    _write(
        project_dir / "DECISIONS.md",
        "# Decisions\n\n## 2026-02-19 - ADR-X\n- Status: Accepted\n- Decision: Keep deterministic route.\n",
    )
    _write(
        project_dir / "issues" / "ISSUE-CP-0001-demo.md",
        "# ISSUE-CP-0001 - Demo issue\n- Owner: victor\n- Phase: Implement\n- Status: In Progress\n",
    )
    _write(
        project_dir / "runs" / "requests.ndjson",
        "\n".join(
            [
                json.dumps(
                    {
                        "request_id": f"runreq_{project_id}_001",
                        "agent_id": "agent-1",
                        "status": "queued",
                        "source": "mention",
                        "created_at": "2026-02-19T12:00:00+00:00",
                        "updated_at": "2026-02-19T12:05:00+00:00",
                    }
                ),
                "{invalid json line}",
            ]
        )
        + "\n",
    )
    _write(
        project_dir / "runs" / "kpi_snapshots.ndjson",
        json.dumps(
            {
                "generated_at": "2026-02-19T12:10:00+00:00",
                "close_rate_24h": 92.5,
                "stale_queued_count": 0,
                "dispatch_latency_p95": 3.1,
            }
        )
        + "\n",
    )
    _write(
        project_dir / "runs" / "slo_verdict_latest.json",
        json.dumps(
            {
                "generated_at": "2026-02-19T12:20:00+00:00",
                "verdict": "HOLD",
                "metrics": {
                    "dispatch_p95_ms": 5100,
                    "dispatch_p99_ms": 10100,
                    "success_rate": 0.94,
                },
            }
        ),
    )
    _write(project_dir / "missions" / "MISSION-DEMO.md", "# Mission\n- Demo mission update\n")
    _write(project_dir / "CHECKPOINT_DEMO.md", "# Checkpoint\n- Demo checkpoint\n")

    return ProjectData(
        project_id=project_id,
        name=project_id,
        path=project_dir,
        agents=[],
        roadmap={},
        settings={},
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "projects"
        base.mkdir(parents=True, exist_ok=True)
        p1 = _seed_project(base, "proj-a")
        p2 = _seed_project(base, "proj-b")

        feed_1 = build_project_timeline_feed(p1, limit=80)
        feed_2 = build_project_timeline_feed(p1, limit=80)

        events_1 = feed_1.get("events")
        events_2 = feed_2.get("events")
        assert isinstance(events_1, list) and events_1, "project timeline events missing"
        assert events_1 == events_2, "timeline events should be deterministic for unchanged input"

        first = events_1[0]
        required_keys = {"event_id", "ts_iso", "lane", "severity", "title", "details", "source_path", "source_uri"}
        assert required_keys <= set(first.keys()), "event schema missing keys"

        lanes = {str(item.get("lane") or "") for item in events_1 if isinstance(item, dict)}
        assert "delivery" in lanes, "expected delivery lane"
        assert "runtime" in lanes, "expected runtime lane"

        dedupe_keys = {(item.get("ts_iso"), item.get("title"), item.get("source_path")) for item in events_1 if isinstance(item, dict)}
        assert len(dedupe_keys) == len(events_1), "dedupe key collision detected"

        portfolio_12 = build_portfolio_timeline_feed([p1, p2], limit=120)
        portfolio_21 = build_portfolio_timeline_feed([p2, p1], limit=120)
        portfolio_events = portfolio_12.get("events")
        portfolio_events_rev = portfolio_21.get("events")
        assert isinstance(portfolio_events, list) and portfolio_events, "portfolio timeline events missing"
        assert isinstance(portfolio_events_rev, list) and portfolio_events_rev, "portfolio timeline events missing (reversed input)"
        assert portfolio_events == portfolio_events_rev, "portfolio events must be canonical regardless of input project order"

        ts_values = [str(item.get("ts_iso") or "") for item in portfolio_events if isinstance(item, dict)]
        assert ts_values == sorted(ts_values, reverse=True), "portfolio events must be sorted desc by ts_iso"

        grouped: dict[str, list[tuple[str, str, str]]] = {}
        for item in portfolio_events:
            if not isinstance(item, dict):
                continue
            ts = str(item.get("ts_iso") or "")
            grouped.setdefault(ts, []).append(
                (
                    str(item.get("event_id") or ""),
                    str(item.get("source_path") or ""),
                    str(item.get("title") or ""),
                )
            )
        for tie_keys in grouped.values():
            assert tie_keys == sorted(tie_keys), "equal ts_iso events must use deterministic tie-break ordering"

    print("OK: timeline feed contract + determinism verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
