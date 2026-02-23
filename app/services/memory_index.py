from __future__ import annotations

import gzip
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from app.data import store as data_store


APP_SUPPORT_PROJECTS_ROOT = Path.home() / "Library" / "Application Support" / "Cockpit" / "projects"
MAX_JOURNAL_LINES = 200
MAX_GLOBAL_CHAT_LINES = 120

RETENTION_POLICY_VERSION = "wave14-7-30-90-permanent-v1"
RETENTION_NEXT_COMPACTION_HOURS = 2
RETENTION_TIERS = ("hot_7d", "warm_30d", "cool_90d", "archive_permanent")
RETENTION_INDEX_LINE_LIMITS = {
    "hot_7d": 240,
    "warm_30d": 180,
    "cool_90d": 120,
}
RETENTION_TEXT_CHAR_LIMITS = {
    "hot_7d": 420,
    "warm_30d": 240,
    "cool_90d": 160,
}


@dataclass(frozen=True)
class MemoryHit:
    path: str
    source_type: str
    snippet: str
    score: float


@dataclass(frozen=True)
class IndexReport:
    project_id: str
    projects_root: str
    db_path: str
    docs_indexed: int
    indexed_sources: list[str]
    built_at: str


@dataclass(frozen=True)
class AgentMemoryIndexReport:
    project_id: str
    projects_root: str
    agent_indexes: list[str]
    indexed_agents: list[str]
    generated_count: int


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _resolve_projects_root(projects_root: Path | None) -> Path:
    if projects_root is None:
        return APP_SUPPORT_PROJECTS_ROOT
    return projects_root.expanduser().resolve()


def _index_path(projects_root: Path, project_id: str) -> Path:
    return projects_root / project_id / "runs" / "memory_index.sqlite3"


def _agent_index_path(projects_root: Path, project_id: str, agent_id: str) -> Path:
    return projects_root / project_id / "agents" / agent_id / "memory.index.json"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _read_ndjson_tail(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    if limit > 0:
        lines = lines[-limit:]
    rows: list[dict[str, Any]] = []
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _read_ndjson_all(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    rows: list[dict[str, Any]] = []
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _parse_iso_timestamp(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalize_inline_text(text: Any) -> str:
    return " ".join(str(text or "").strip().split())


def _truncate(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[: max_chars - 3] + "..."


def _timestamp_text(payload: dict[str, Any]) -> str:
    return str(payload.get("timestamp") or payload.get("created_at") or payload.get("updated_at") or "").strip()


def _row_author(payload: dict[str, Any]) -> str:
    return str(payload.get("author") or payload.get("from") or payload.get("agent_id") or "agent").strip()


def _row_text(payload: dict[str, Any]) -> str:
    value = payload.get("text") or payload.get("event") or payload.get("content") or ""
    return _normalize_inline_text(value)


def _retention_tier(timestamp: datetime | None, now: datetime) -> str:
    if timestamp is None:
        return "archive_permanent"
    age_days = max(0.0, (now - timestamp).total_seconds() / 86400.0)
    if age_days <= 7:
        return "hot_7d"
    if age_days <= 30:
        return "warm_30d"
    if age_days <= 90:
        return "cool_90d"
    return "archive_permanent"


def _render_retention_line(payload: dict[str, Any], tier: str) -> str:
    text = _row_text(payload)
    if not text:
        return ""

    limit = RETENTION_TEXT_CHAR_LIMITS.get(tier, 160)
    if tier == "hot_7d":
        body = _truncate(text, limit)
    elif tier == "warm_30d":
        body = _truncate(text, limit)
    else:
        body = _truncate(text, limit)

    timestamp = _timestamp_text(payload)
    author = _row_author(payload)
    prefix = f"[{timestamp}] " if timestamp else ""
    return f"{prefix}{author}: {body}".strip()


def _collect_root_markdown(project_dir: Path) -> Iterable[tuple[str, str, str]]:
    files = [
        ("STATE.md", "state"),
        ("ROADMAP.md", "roadmap"),
        ("DECISIONS.md", "decisions"),
    ]
    for filename, source_type in files:
        path = project_dir / filename
        if not path.exists():
            continue
        text = _read_text(path)
        if not text:
            continue
        yield (filename, source_type, text)


def _journal_to_text(rows: list[dict[str, Any]]) -> str:
    rendered: list[str] = []
    for payload in rows:
        ts = _timestamp_text(payload)
        author = _row_author(payload)
        text = _row_text(payload)
        if not text:
            continue
        prefix = f"[{ts}] " if ts else ""
        rendered.append(f"{prefix}{author}: {text}")
    return "\n".join(rendered).strip()


def _dedupe_sorted(values: list[str], *, limit: int) -> list[str]:
    normalized = {str(item).strip() for item in values if str(item).strip()}
    return sorted(normalized, key=lambda item: item.lower())[: max(0, limit)]


def _parse_markdown_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("## "):
            current = line[3:].strip().lower()
            sections.setdefault(current, [])
            continue
        if current is None:
            continue
        if line.startswith("- "):
            sections[current].append(line[2:].strip())
            continue
        if line and not line.startswith("#"):
            sections[current].append(line)
    return sections


def _extract_decisions(decisions_text: str, *, limit: int = 8) -> list[str]:
    items: list[str] = []
    for raw in decisions_text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            items.append(line[3:].strip())
            continue
        if line.lower().startswith("- decision:"):
            items.append(line.split(":", 1)[1].strip())
    return _dedupe_sorted(items, limit=limit)


def _extract_agent_signals(rows: list[dict[str, Any]], *, limit: int = 10) -> list[str]:
    rendered: list[str] = []
    for payload in rows:
        timestamp = _timestamp_text(payload)
        text = _row_text(payload)
        if not text:
            continue
        if timestamp:
            rendered.append(f"{timestamp} | {text}")
        else:
            rendered.append(text)
    return _dedupe_sorted(rendered, limit=limit)


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _slugify(value: str) -> str:
    normalized = "".join(ch if ch.isalnum() else "_" for ch in str(value))
    collapsed = "_".join(part for part in normalized.split("_") if part)
    return collapsed.lower() or "source"


def _collect_agent_memory_docs(project_dir: Path) -> list[tuple[str, str, str]]:
    agents_dir = project_dir / "agents"
    if not agents_dir.exists():
        return []

    docs: list[tuple[str, str, str]] = []
    for agent_dir in sorted([p for p in agents_dir.iterdir() if p.is_dir()], key=lambda p: p.name):
        agent_id = agent_dir.name
        for filename, source_type in (
            ("memory.md", "memory"),
            ("memory.proposed.md", "memory_proposed"),
        ):
            path = agent_dir / filename
            if not path.exists():
                continue
            text = _read_text(path)
            if not text:
                continue
            docs.append((f"agents/{agent_id}/{filename}", source_type, text))
    return docs


def _collect_retention_source_docs(
    rows: list[dict[str, Any]],
    *,
    source_path: str,
    doc_path_prefix: str,
    source_type_prefix: str,
    now: datetime,
) -> tuple[list[tuple[str, str, str]], dict[str, Any], list[dict[str, Any]]]:
    counts = {tier: 0 for tier in RETENTION_TIERS}
    indexed_lines: dict[str, int] = {"hot_7d": 0, "warm_30d": 0, "cool_90d": 0}
    tier_lines: dict[str, list[str]] = {"hot_7d": [], "warm_30d": [], "cool_90d": []}
    archive_rows: list[dict[str, Any]] = []

    valid_timestamps = 0
    invalid_or_missing_timestamps = 0

    for payload in rows:
        timestamp = _parse_iso_timestamp(_timestamp_text(payload))
        if timestamp is None:
            invalid_or_missing_timestamps += 1
        else:
            valid_timestamps += 1

        tier = _retention_tier(timestamp, now)
        counts[tier] += 1

        if tier == "archive_permanent":
            archive_rows.append(payload)
            continue

        line = _render_retention_line(payload, tier)
        if line:
            tier_lines[tier].append(line)

    docs: list[tuple[str, str, str]] = []
    for tier in ("hot_7d", "warm_30d", "cool_90d"):
        limit = RETENTION_INDEX_LINE_LIMITS.get(tier, 0)
        lines = tier_lines[tier][-limit:] if limit > 0 else []
        indexed_lines[tier] = len(lines)
        text = "\n".join(lines).strip()
        if text:
            docs.append(
                (
                    f"{doc_path_prefix}.{tier}",
                    f"{source_type_prefix}_{tier}",
                    text,
                )
            )

    total_rows = sum(counts.values())
    timestamp_valid_ratio = 0.0
    if total_rows > 0:
        timestamp_valid_ratio = round(valid_timestamps / total_rows, 4)

    metadata: dict[str, Any] = {
        "counts": counts,
        "indexed_lines": indexed_lines,
        "total_rows": total_rows,
        "timestamp_quality": {
            "valid": valid_timestamps,
            "invalid_or_missing": invalid_or_missing_timestamps,
            "valid_ratio": timestamp_valid_ratio,
        },
    }

    return docs, metadata, archive_rows


def _collect_retention_docs(
    project_dir: Path,
    *,
    now: datetime,
) -> tuple[list[tuple[str, str, str]], dict[str, dict[str, Any]], dict[str, int], dict[str, list[dict[str, Any]]]]:
    docs: list[tuple[str, str, str]] = []
    source_metadata: dict[str, dict[str, Any]] = {}
    totals = {tier: 0 for tier in RETENTION_TIERS}
    archive_rows_by_source: dict[str, list[dict[str, Any]]] = {}

    agents_dir = project_dir / "agents"
    if agents_dir.exists():
        for agent_dir in sorted([p for p in agents_dir.iterdir() if p.is_dir()], key=lambda p: p.name):
            agent_id = agent_dir.name
            source_rel = f"agents/{agent_id}/journal.ndjson"
            rows = _read_ndjson_all(agent_dir / "journal.ndjson")
            source_docs, metadata, archive_rows = _collect_retention_source_docs(
                rows,
                source_path=source_rel,
                doc_path_prefix=f"agents/{agent_id}/journal",
                source_type_prefix="journal",
                now=now,
            )
            docs.extend(source_docs)
            source_metadata[source_rel] = metadata
            for tier in RETENTION_TIERS:
                totals[tier] += int(metadata["counts"].get(tier, 0))
            if archive_rows:
                archive_rows_by_source[source_rel] = archive_rows

    chat_source_rel = "chat/global.ndjson"
    chat_rows = _read_ndjson_all(project_dir / "chat" / "global.ndjson")
    chat_docs, chat_metadata, chat_archive_rows = _collect_retention_source_docs(
        chat_rows,
        source_path=chat_source_rel,
        doc_path_prefix="chat/global",
        source_type_prefix="chat",
        now=now,
    )
    docs.extend(chat_docs)
    source_metadata[chat_source_rel] = chat_metadata
    for tier in RETENTION_TIERS:
        totals[tier] += int(chat_metadata["counts"].get(tier, 0))
    if chat_archive_rows:
        archive_rows_by_source[chat_source_rel] = chat_archive_rows

    return docs, source_metadata, totals, archive_rows_by_source


def _write_archive_artifacts(
    project_id: str,
    projects_root: Path,
    archive_rows_by_source: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    archive_dir = data_store.retention_archive_dir(project_id, projects_root=projects_root)
    archive_dir.mkdir(parents=True, exist_ok=True)

    artifacts: list[dict[str, Any]] = []
    for source_path in sorted(archive_rows_by_source.keys()):
        rows = archive_rows_by_source.get(source_path) or []
        if not rows:
            continue

        encoded_lines = [json.dumps(row, sort_keys=True, ensure_ascii=True) for row in rows]
        payload_bytes = ("\n".join(encoded_lines) + "\n").encode("utf-8")
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()

        filename = f"{_slugify(source_path)}_{payload_hash[:16]}.ndjson.gz"
        artifact_path = archive_dir / filename
        if not artifact_path.exists():
            artifact_path.write_bytes(gzip.compress(payload_bytes, mtime=0))

        artifacts.append(
            {
                "source_path": source_path,
                "path": str(artifact_path),
                "hash": payload_hash,
                "row_count": len(rows),
            }
        )

    return artifacts


def _collect_documents(
    project_dir: Path,
    *,
    now: datetime,
) -> tuple[list[tuple[str, str, str]], dict[str, dict[str, Any]], dict[str, int], dict[str, list[dict[str, Any]]]]:
    docs: list[tuple[str, str, str]] = []
    docs.extend(_collect_root_markdown(project_dir))
    docs.extend(_collect_agent_memory_docs(project_dir))

    retention_docs, source_metadata, totals, archive_rows_by_source = _collect_retention_docs(
        project_dir,
        now=now,
    )
    docs.extend(retention_docs)

    # deterministic ordering
    return sorted(docs, key=lambda item: (item[0], item[1])), source_metadata, totals, archive_rows_by_source


def build_agent_memory_indexes(
    project_id: str,
    projects_root: Path | None = None,
    *,
    core_agents: tuple[str, ...] | None = None,
) -> AgentMemoryIndexReport:
    """
    Generate deterministic agents/*/memory.index.json for core roles.

    Output intentionally excludes timestamps to keep byte-identical output
    when source files do not change.
    """
    root = _resolve_projects_root(projects_root)
    project_dir = root / project_id
    if not project_dir.exists():
        raise FileNotFoundError(f"Project not found: {project_dir}")

    resolved_core_agents: tuple[str, ...]
    if core_agents is None:
        from app.services.agent_registry import load_agent_registry

        registry = load_agent_registry(project_id, root)
        preferred = ["clems", "victor", "leo", "nova"]
        # Always consider canonical core first, even with partial/missing registry.
        selected: list[str] = list(preferred)

        for agent_id in sorted(registry.keys()):
            meta = registry.get(agent_id)
            if meta is None:
                continue
            if int(meta.level) <= 1 and agent_id not in selected:
                selected.append(agent_id)

        if not selected:
            selected = list(preferred)
        resolved_core_agents = tuple(selected)
    else:
        resolved_core_agents = tuple(core_agents)

    decisions_text = _read_text(project_dir / "DECISIONS.md")
    decisions = _extract_decisions(decisions_text, limit=8)

    indexed_paths: list[str] = []
    indexed_agents: list[str] = []

    for agent_id in resolved_core_agents:
        agent_dir = project_dir / "agents" / agent_id
        if not agent_dir.exists():
            continue

        memory_text = _read_text(agent_dir / "memory.md")
        sections = _parse_markdown_sections(memory_text)
        facts = _dedupe_sorted(
            sections.get("facts / constraints", []) + sections.get("facts", []),
            limit=12,
        )
        open_loops = _dedupe_sorted(
            sections.get("open loops", []) + sections.get("blockers", []) + sections.get("next", []),
            limit=12,
        )

        journal_rows = _read_ndjson_tail(agent_dir / "journal.ndjson", 120)
        chat_rows = _read_ndjson_tail(project_dir / "chat" / "global.ndjson", 40)
        signals = _extract_agent_signals(journal_rows + chat_rows, limit=10)

        payload = {
            "schema_version": 1,
            "project_id": project_id,
            "agent_id": agent_id,
            "facts": facts,
            "decisions": decisions,
            "open_loops": open_loops,
            "signals": signals,
            "source_files": sorted(
                [
                    str(project_dir / "DECISIONS.md"),
                    str(agent_dir / "memory.md"),
                    str(agent_dir / "journal.ndjson"),
                    str(project_dir / "chat" / "global.ndjson"),
                ]
            ),
        }

        output_path = _agent_index_path(root, project_id, agent_id)
        _write_json_atomic(output_path, payload)
        indexed_paths.append(str(output_path))
        indexed_agents.append(agent_id)

    return AgentMemoryIndexReport(
        project_id=project_id,
        projects_root=str(root),
        agent_indexes=sorted(indexed_paths),
        indexed_agents=sorted(indexed_agents),
        generated_count=len(indexed_paths),
    )


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS memory_fts")
    conn.execute(
        "CREATE VIRTUAL TABLE memory_fts USING fts5("
        "path UNINDEXED, "
        "source_type UNINDEXED, "
        "content, "
        "tokenize='unicode61'"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS memory_meta ("
        "key TEXT PRIMARY KEY, "
        "value TEXT NOT NULL"
        ")"
    )


def build_index(project_id: str, projects_root: Path | None = None) -> IndexReport:
    root = _resolve_projects_root(projects_root)
    project_dir = root / project_id
    if not project_dir.exists():
        raise FileNotFoundError(f"Project not found: {project_dir}")

    now = _utc_now()
    built_at = now.isoformat()

    db_path = _index_path(root, project_id)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    docs, source_metadata, totals, archive_rows_by_source = _collect_documents(project_dir, now=now)

    with sqlite3.connect(db_path) as conn:
        _ensure_schema(conn)
        conn.executemany(
            "INSERT INTO memory_fts(path, source_type, content) VALUES (?, ?, ?)",
            docs,
        )
        conn.execute("DELETE FROM memory_meta")
        conn.executemany(
            "INSERT INTO memory_meta(key, value) VALUES (?, ?)",
            [
                ("project_id", project_id),
                ("built_at", built_at),
                ("docs_indexed", str(len(docs))),
            ],
        )
        conn.commit()

    archive_artifacts = _write_archive_artifacts(
        project_id,
        root,
        archive_rows_by_source,
    )

    retention_root = data_store.retention_dir(project_id, projects_root=root)
    canonical_project_id = retention_root.parent.parent.name
    next_compaction_at = (now + timedelta(hours=RETENTION_NEXT_COMPACTION_HOURS)).isoformat()

    retention_status: dict[str, Any] = {
        "policy_version": RETENTION_POLICY_VERSION,
        "project_id": project_id,
        "generated_at": built_at,
        "next_compaction_at": next_compaction_at,
        "sources": source_metadata,
        "totals": totals,
        "archive_artifacts": sorted(archive_artifacts, key=lambda item: str(item.get("path") or "")),
        "isolation_check": {
            "canonical_project_id": canonical_project_id,
            "projects_root": str(root),
        },
    }
    data_store.write_retention_status(project_id, retention_status, projects_root=root)

    return IndexReport(
        project_id=project_id,
        projects_root=str(root),
        db_path=str(db_path),
        docs_indexed=len(docs),
        indexed_sources=[path for path, _source, _content in docs],
        built_at=built_at,
    )


def _normalize_query(query: str) -> str:
    tokens: list[str] = []
    for raw in str(query or "").strip().split():
        cleaned = "".join(ch for ch in raw.lower() if ch.isalnum() or ch in {"_", "-"})
        if cleaned:
            tokens.append(cleaned)
    return " AND ".join(tokens)


def search_memory(
    project_id: str,
    query: str,
    limit: int = 5,
    projects_root: Path | None = None,
) -> list[MemoryHit]:
    root = _resolve_projects_root(projects_root)
    db_path = _index_path(root, project_id)
    if not db_path.exists():
        return []

    normalized_query = _normalize_query(query)
    if not normalized_query:
        return []

    safe_limit = max(1, min(int(limit), 50))
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT path, source_type, snippet(memory_fts, 2, '[', ']', ' ... ', 18), bm25(memory_fts) AS score "
            "FROM memory_fts "
            "WHERE memory_fts MATCH ? "
            "ORDER BY score ASC, path ASC "
            "LIMIT ?",
            (normalized_query, safe_limit),
        )
        rows = cursor.fetchall()

    hits: list[MemoryHit] = []
    for path, source_type, snippet, score in rows:
        try:
            normalized_score = float(score)
        except (TypeError, ValueError):
            normalized_score = 0.0
        hits.append(
            MemoryHit(
                path=str(path),
                source_type=str(source_type),
                snippet=str(snippet or ""),
                score=normalized_score,
            )
        )
    return hits
