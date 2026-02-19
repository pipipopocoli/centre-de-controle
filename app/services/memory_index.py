from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


APP_SUPPORT_PROJECTS_ROOT = Path.home() / "Library" / "Application Support" / "Cockpit" / "projects"
MAX_JOURNAL_LINES = 200
MAX_GLOBAL_CHAT_LINES = 120


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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def _read_ndjson_tail(path: Path, limit: int) -> list[dict]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    if limit > 0:
        lines = lines[-limit:]
    rows: list[dict] = []
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


def _journal_to_text(rows: list[dict]) -> str:
    rendered: list[str] = []
    for payload in rows:
        ts = str(payload.get("timestamp") or "").strip()
        author = str(payload.get("author") or payload.get("from") or payload.get("agent_id") or "agent").strip()
        text = str(payload.get("text") or payload.get("event") or payload.get("content") or "").strip()
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


def _extract_agent_signals(rows: list[dict], *, limit: int = 10) -> list[str]:
    rendered: list[str] = []
    for payload in rows:
        timestamp = str(payload.get("timestamp") or "").strip()
        text = str(payload.get("text") or payload.get("event") or payload.get("content") or "").strip()
        if not text:
            continue
        if timestamp:
            rendered.append(f"{timestamp} | {text}")
        else:
            rendered.append(text)
    return _dedupe_sorted(rendered, limit=limit)


def _write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _collect_agent_files(project_dir: Path) -> Iterable[tuple[str, str, str]]:
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

        journal_rows = _read_ndjson_tail(agent_dir / "journal.ndjson", MAX_JOURNAL_LINES)
        journal_text = _journal_to_text(journal_rows)
        if journal_text:
            docs.append((f"agents/{agent_id}/journal.tail", "journal_tail", journal_text))
    return docs


def _collect_chat_tail(project_dir: Path) -> Iterable[tuple[str, str, str]]:
    chat_rows = _read_ndjson_tail(project_dir / "chat" / "global.ndjson", MAX_GLOBAL_CHAT_LINES)
    text = _journal_to_text(chat_rows)
    if not text:
        return []
    return [("chat/global.tail", "chat_tail", text)]


def _collect_documents(project_dir: Path) -> list[tuple[str, str, str]]:
    docs: list[tuple[str, str, str]] = []
    docs.extend(_collect_root_markdown(project_dir))
    docs.extend(_collect_agent_files(project_dir))
    docs.extend(_collect_chat_tail(project_dir))
    # deterministic ordering
    return sorted(docs, key=lambda item: (item[0], item[1]))


def build_agent_memory_indexes(
    project_id: str,
    projects_root: Path | None = None,
    *,
    core_agents: tuple[str, ...] = ("clems", "victor", "leo"),
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

    decisions_text = _read_text(project_dir / "DECISIONS.md")
    decisions = _extract_decisions(decisions_text, limit=8)

    indexed_paths: list[str] = []
    indexed_agents: list[str] = []

    for agent_id in core_agents:
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

    db_path = _index_path(root, project_id)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    docs = _collect_documents(project_dir)
    built_at = _utc_now_iso()

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
