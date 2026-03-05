use std::{
    collections::HashMap,
    fs::{self, File, OpenOptions},
    io::{BufRead, BufReader, Write},
    path::{Path, PathBuf},
};

use anyhow::{Context, Result};
use chrono::{Duration, Utc};
use rusqlite::{Connection, params};
use serde_json::{Value, json};

use crate::models::{
    AgentRecord, ApprovalRequest, ApprovalStatus, ChatMessage, MessageVisibility, WsEventEnvelope,
};

pub fn project_root(control_root: &Path, project_id: &str) -> PathBuf {
    control_root.join(project_id)
}

pub fn ensure_project_scaffold(control_root: &Path, project_id: &str) -> Result<PathBuf> {
    let root = project_root(control_root, project_id);
    fs::create_dir_all(root.join("agents"))?;
    fs::create_dir_all(root.join("chat/threads"))?;
    fs::create_dir_all(root.join("runs"))?;
    fs::create_dir_all(root.join("pixel"))?;

    let registry_path = root.join("agents/registry.json");
    if !registry_path.exists() {
        fs::write(&registry_path, "{}\n")?;
    }

    let chat_path = root.join("chat/global.ndjson");
    if !chat_path.exists() {
        File::create(&chat_path)?;
    }

    let approvals_path = root.join("chat/approvals.ndjson");
    if !approvals_path.exists() {
        File::create(&approvals_path)?;
    }

    let layout_path = root.join("pixel/layout.json");
    if !layout_path.exists() {
        fs::write(layout_path, serde_json::to_string_pretty(&default_layout())?)?;
    }

    let state_path = root.join("STATE.md");
    if !state_path.exists() {
        fs::write(
            state_path,
            "# State\n\n## Phase\n- Implement\n\n## Objective\n- Cockpit Next rewrite\n\n## Now\n- Bootstrap\n\n## Next\n- Pixel Home + chat live\n\n## In Progress\n- none\n\n## Blockers\n- none\n\n## Risks\n- rewrite scope\n\n## Links\n- none\n",
        )?;
    }

    let roadmap_path = root.join("ROADMAP.md");
    if !roadmap_path.exists() {
        fs::write(roadmap_path, "# Roadmap\n\n- Build Cockpit Next\n")?;
    }

    let decisions_path = root.join("DECISIONS.md");
    if !decisions_path.exists() {
        fs::write(decisions_path, "# Decisions\n")?;
    }

    ensure_runtime_db(control_root, project_id)?;
    Ok(root)
}

pub fn load_agents(control_root: &Path, project_id: &str) -> Result<HashMap<String, AgentRecord>> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let path = root.join("agents/registry.json");
    let raw = fs::read_to_string(&path)?;
    if raw.trim().is_empty() {
        return Ok(HashMap::new());
    }
    let parsed: HashMap<String, AgentRecord> =
        serde_json::from_str(&raw).with_context(|| format!("invalid json in {}", path.display()))?;
    Ok(parsed)
}

pub fn save_agents(
    control_root: &Path,
    project_id: &str,
    agents: &HashMap<String, AgentRecord>,
) -> Result<()> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let path = root.join("agents/registry.json");
    fs::write(path, serde_json::to_string_pretty(agents)?)?;
    Ok(())
}

pub fn ensure_agent_files(control_root: &Path, project_id: &str, agent_id: &str) -> Result<()> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let dir = root.join("agents").join(agent_id);
    fs::create_dir_all(&dir)?;

    let state_path = dir.join("state.json");
    if !state_path.exists() {
        let payload = json!({
            "agent_id": agent_id,
            "phase": "Implement",
            "status": "idle",
            "heartbeat": Utc::now().to_rfc3339(),
        });
        fs::write(state_path, serde_json::to_string_pretty(&payload)?)?;
    }

    let memory_path = dir.join("memory.md");
    if !memory_path.exists() {
        fs::write(memory_path, format!("# Memory - {agent_id}\n\n- Initialized\n"))?;
    }

    let journal_path = dir.join("journal.ndjson");
    if !journal_path.exists() {
        File::create(journal_path)?;
    }

    Ok(())
}

pub fn remove_agent_files(control_root: &Path, project_id: &str, agent_id: &str) -> Result<()> {
    let dir = project_root(control_root, project_id).join("agents").join(agent_id);
    if dir.exists() {
        fs::remove_dir_all(dir)?;
    }
    Ok(())
}

pub fn append_chat_message(control_root: &Path, project_id: &str, message: &ChatMessage) -> Result<()> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let path = root.join("chat/global.ndjson");
    let mut file = OpenOptions::new().append(true).create(true).open(&path)?;
    let raw = serde_json::to_string(message)?;
    writeln!(file, "{raw}")?;

    let db_path = ensure_runtime_db(control_root, project_id)?;
    let conn = Connection::open(db_path)?;
    conn.execute(
        "INSERT INTO chat_messages (timestamp, author, text, payload_json) VALUES (?1, ?2, ?3, ?4)",
        params![message.timestamp, message.author, message.text, raw],
    )?;

    Ok(())
}

pub fn read_chat(
    control_root: &Path,
    project_id: &str,
    limit: usize,
    visibility: Option<MessageVisibility>,
) -> Result<Vec<ChatMessage>> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let path = root.join("chat/global.ndjson");
    if !path.exists() {
        return Ok(Vec::new());
    }

    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut rows = Vec::new();
    for line in reader.lines() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }
        if let Ok(value) = serde_json::from_str::<ChatMessage>(&line) {
            if let Some(filter) = visibility {
                if value.visibility != filter {
                    continue;
                }
            }
            rows.push(value);
        }
    }

    if rows.len() > limit {
        let start = rows.len() - limit;
        Ok(rows[start..].to_vec())
    } else {
        Ok(rows)
    }
}

pub fn clear_chat_data(control_root: &Path, project_id: &str) -> Result<(usize, usize, usize)> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let chat_path = root.join("chat/global.ndjson");
    let approvals_path = root.join("chat/approvals.ndjson");

    let existing_messages = count_lines(&chat_path)?;
    let existing_approvals = count_lines(&approvals_path)?;

    fs::write(&chat_path, "")?;
    fs::write(&approvals_path, "")?;

    let db_path = ensure_runtime_db(control_root, project_id)?;
    let conn = Connection::open(db_path)?;

    let chat_deleted = conn.execute("DELETE FROM chat_messages", [])?;
    let approvals_deleted = conn.execute("DELETE FROM approval_requests", [])?;

    Ok((existing_messages, existing_approvals, chat_deleted + approvals_deleted))
}

pub fn load_layout(control_root: &Path, project_id: &str) -> Result<Value> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let path = root.join("pixel/layout.json");
    let raw = fs::read_to_string(path)?;
    let value = serde_json::from_str::<Value>(&raw)?;
    Ok(value)
}

pub fn save_layout(control_root: &Path, project_id: &str, layout: &Value) -> Result<()> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let path = root.join("pixel/layout.json");
    fs::write(path, serde_json::to_string_pretty(layout)?)?;
    Ok(())
}

pub fn append_runtime_event(control_root: &Path, project_id: &str, event: &WsEventEnvelope) -> Result<()> {
    let db_path = ensure_runtime_db(control_root, project_id)?;
    let conn = Connection::open(db_path)?;
    conn.execute(
        "INSERT INTO events (timestamp, event_type, payload_json) VALUES (?1, ?2, ?3)",
        params![
            event.timestamp,
            event.event_type,
            serde_json::to_string(&event.payload)?
        ],
    )?;
    Ok(())
}

pub fn append_approval_request(
    control_root: &Path,
    project_id: &str,
    approval: &ApprovalRequest,
) -> Result<()> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let path = root.join("chat/approvals.ndjson");
    let mut file = OpenOptions::new().append(true).create(true).open(&path)?;
    let raw = serde_json::to_string(approval)?;
    writeln!(file, "{raw}")?;

    let db_path = ensure_runtime_db(control_root, project_id)?;
    let conn = Connection::open(db_path)?;
    conn.execute(
        "INSERT INTO approval_requests (
            request_id,
            run_id,
            requester,
            section_tag,
            reason,
            status,
            requested_at,
            decided_by,
            decided_at,
            decision_note,
            payload_json
        ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)
        ON CONFLICT(request_id) DO UPDATE SET
            run_id=excluded.run_id,
            requester=excluded.requester,
            section_tag=excluded.section_tag,
            reason=excluded.reason,
            status=excluded.status,
            requested_at=excluded.requested_at,
            decided_by=excluded.decided_by,
            decided_at=excluded.decided_at,
            decision_note=excluded.decision_note,
            payload_json=excluded.payload_json",
        params![
            approval.request_id,
            approval.run_id,
            approval.requester,
            approval.section_tag,
            approval.reason,
            approval_status_to_str(&approval.status),
            approval.requested_at,
            approval.decided_by,
            approval.decided_at,
            approval.decision_note,
            raw,
        ],
    )?;

    Ok(())
}

pub fn list_approvals(
    control_root: &Path,
    project_id: &str,
    status: Option<ApprovalStatus>,
) -> Result<Vec<ApprovalRequest>> {
    let db_path = ensure_runtime_db(control_root, project_id)?;
    let conn = Connection::open(db_path)?;

    let mut out = Vec::new();
    if let Some(status) = status {
        let status = approval_status_to_str(&status);
        let mut stmt = conn.prepare(
            "SELECT payload_json
             FROM approval_requests
             WHERE status = ?1
             ORDER BY requested_at DESC, request_id DESC",
        )?;
        let rows = stmt.query_map(params![status], |row| row.get::<_, String>(0))?;
        for row in rows {
            let raw = row?;
            if let Ok(parsed) = serde_json::from_str::<ApprovalRequest>(&raw) {
                out.push(parsed);
            }
        }
    } else {
        let mut stmt = conn.prepare(
            "SELECT payload_json
             FROM approval_requests
             ORDER BY requested_at DESC, request_id DESC",
        )?;
        let rows = stmt.query_map([], |row| row.get::<_, String>(0))?;
        for row in rows {
            let raw = row?;
            if let Ok(parsed) = serde_json::from_str::<ApprovalRequest>(&raw) {
                out.push(parsed);
            }
        }
    }

    Ok(out)
}

pub fn get_approval(
    control_root: &Path,
    project_id: &str,
    request_id: &str,
) -> Result<Option<ApprovalRequest>> {
    let db_path = ensure_runtime_db(control_root, project_id)?;
    let conn = Connection::open(db_path)?;
    let mut stmt = conn.prepare(
        "SELECT payload_json FROM approval_requests WHERE request_id = ?1 LIMIT 1",
    )?;

    let mut rows = stmt.query(params![request_id])?;
    if let Some(row) = rows.next()? {
        let raw: String = row.get(0)?;
        if let Ok(parsed) = serde_json::from_str::<ApprovalRequest>(&raw) {
            return Ok(Some(parsed));
        }
    }

    Ok(None)
}

pub fn update_approval_decision(
    control_root: &Path,
    project_id: &str,
    request_id: &str,
    status: ApprovalStatus,
    decided_by: &str,
    note: Option<String>,
) -> Result<Option<ApprovalRequest>> {
    let mut approval = if let Some(found) = get_approval(control_root, project_id, request_id)? {
        found
    } else {
        return Ok(None);
    };

    approval.status = status;
    approval.decided_by = Some(decided_by.to_string());
    approval.decided_at = Some(Utc::now().to_rfc3339());
    approval.decision_note = note;

    append_approval_request(control_root, project_id, &approval)?;
    Ok(Some(approval))
}

pub fn has_section_overlap_risk(
    control_root: &Path,
    project_id: &str,
    section_tag: &str,
    overlap_window_minutes: i64,
) -> Result<bool> {
    let db_path = ensure_runtime_db(control_root, project_id)?;
    let conn = Connection::open(db_path)?;
    let cutoff = (Utc::now() - Duration::minutes(overlap_window_minutes.max(1))).to_rfc3339();
    let mut stmt = conn.prepare(
        "SELECT COUNT(1)
         FROM approval_requests
         WHERE section_tag = ?1
           AND requested_at >= ?2
           AND status IN ('pending', 'approved')",
    )?;
    let count: i64 = stmt.query_row(params![section_tag, cutoff], |row| row.get(0))?;
    Ok(count > 0)
}

fn ensure_runtime_db(control_root: &Path, project_id: &str) -> Result<PathBuf> {
    let root = ensure_runs_dir(control_root, project_id)?;
    let db_path = root.join("runtime.db");

    let conn = Connection::open(&db_path)?;
    conn.execute(
        "CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )",
        [],
    )?;
    conn.execute(
        "CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            author TEXT NOT NULL,
            text TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )",
        [],
    )?;
    conn.execute(
        "CREATE TABLE IF NOT EXISTS approval_requests (
            request_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            requester TEXT NOT NULL,
            section_tag TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL,
            requested_at TEXT NOT NULL,
            decided_by TEXT,
            decided_at TEXT,
            decision_note TEXT,
            payload_json TEXT NOT NULL
        )",
        [],
    )?;

    Ok(db_path)
}

fn count_lines(path: &Path) -> Result<usize> {
    if !path.exists() {
        return Ok(0);
    }
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut count = 0usize;
    for line in reader.lines() {
        if !line?.trim().is_empty() {
            count += 1;
        }
    }
    Ok(count)
}

fn approval_status_to_str(status: &ApprovalStatus) -> &'static str {
    match status {
        ApprovalStatus::Pending => "pending",
        ApprovalStatus::Approved => "approved",
        ApprovalStatus::Rejected => "rejected",
    }
}

fn ensure_runs_dir(control_root: &Path, project_id: &str) -> Result<PathBuf> {
    let root = project_root(control_root, project_id).join("runs");
    fs::create_dir_all(&root)?;
    Ok(root)
}

fn default_layout() -> Value {
    let cols = 30usize;
    let rows = 22usize;
    let mut tiles = vec![1u8; cols * rows];

    let mut set_tile = |col: usize, row: usize, value: u8| {
        if col < cols && row < rows {
            tiles[row * cols + col] = value;
        }
    };

    for col in 0..cols {
        set_tile(col, 0, 0);
        set_tile(col, rows - 1, 0);
    }

    for row in 0..rows {
        set_tile(0, row, 0);
        set_tile(cols - 1, row, 0);
    }

    for row in 1..rows - 1 {
        for col in 1..cols - 1 {
            if (row + col) % 2 == 0 {
                set_tile(col, row, 2);
            }
        }
    }

    for row in 1..=16 {
        if row == 8 || row == 9 {
            continue;
        }
        set_tile(17, row, 0);
    }

    for col in 17..=28 {
        if col == 20 || col == 21 {
            continue;
        }
        set_tile(col, 10, 0);
    }

    for col in 17..=28 {
        if col == 24 {
            continue;
        }
        set_tile(col, 6, 0);
    }

    for col in 1..=13 {
        if col == 6 || col == 7 {
            continue;
        }
        set_tile(col, 16, 0);
    }

    for row in 16..=20 {
        set_tile(13, row, 0);
    }

    for col in 1..=12 {
        if col == 6 || col == 7 {
            continue;
        }
        set_tile(col, 4, 0);
    }

    json!({
        "version": 1,
        "cols": cols,
        "rows": rows,
        "tiles": tiles,
        "furniture": [
            { "uid": "desk-clems", "type": "desk", "col": 4, "row": 5 },
            { "uid": "chair-clems", "type": "chair", "col": 4, "row": 6 },
            { "uid": "pc-clems", "type": "pc", "col": 4, "row": 5 },

            { "uid": "desk-victor", "type": "desk", "col": 9, "row": 5 },
            { "uid": "chair-victor", "type": "chair", "col": 9, "row": 6 },
            { "uid": "pc-victor", "type": "pc", "col": 9, "row": 5 },

            { "uid": "desk-leo", "type": "desk", "col": 4, "row": 10 },
            { "uid": "chair-leo", "type": "chair", "col": 4, "row": 11 },
            { "uid": "pc-leo", "type": "pc", "col": 4, "row": 10 },

            { "uid": "desk-nova", "type": "desk", "col": 9, "row": 10 },
            { "uid": "chair-nova", "type": "chair", "col": 9, "row": 11 },
            { "uid": "pc-nova", "type": "pc", "col": 9, "row": 10 },

            { "uid": "counter-coffee", "type": "desk-long-white", "col": 1, "row": 1 },
            { "uid": "bookshelf-top-left", "type": "bookshelf-wide", "col": 1, "row": 2 },
            { "uid": "clock-top", "type": "clock", "col": 7, "row": 1 },
            { "uid": "frame-top", "type": "frame-landscape", "col": 10, "row": 1 },
            { "uid": "cooler-main", "type": "cooler", "col": 15, "row": 2 },
            { "uid": "whiteboard-main", "type": "whiteboard", "col": 12, "row": 1 },

            { "uid": "desk-right-1", "type": "desk-long-wood", "col": 20, "row": 3 },
            { "uid": "chair-right-1", "type": "chair", "col": 21, "row": 4 },
            { "uid": "pc-right-1", "type": "pc", "col": 21, "row": 3 },
            { "uid": "bookshelf-right-1", "type": "bookshelf-wood", "col": 27, "row": 2 },
            { "uid": "clock-right", "type": "clock", "col": 24, "row": 2 },
            { "uid": "plant-right-1", "type": "plant-tall", "col": 27, "row": 5 },

            { "uid": "desk-right-2", "type": "desk-modern-gray", "col": 20, "row": 11 },
            { "uid": "chair-right-2", "type": "chair", "col": 20, "row": 12 },
            { "uid": "pc-right-2", "type": "pc", "col": 20, "row": 11 },
            { "uid": "desk-right-3", "type": "desk-modern-light", "col": 23, "row": 11 },
            { "uid": "chair-right-3", "type": "chair", "col": 23, "row": 12 },
            { "uid": "pc-right-3", "type": "pc", "col": 23, "row": 11 },
            { "uid": "table-meeting", "type": "table-meeting", "col": 20, "row": 14 },
            { "uid": "sofa-right", "type": "sofa-gray", "col": 24, "row": 15 },
            { "uid": "cabinet-right", "type": "cabinet-double", "col": 26, "row": 13 },
            { "uid": "locker-right", "type": "locker", "col": 28, "row": 13 },
            { "uid": "vending-right", "type": "vending-machine", "col": 28, "row": 3 },
            { "uid": "plant-right-2", "type": "plant", "col": 26, "row": 18 },

            { "uid": "shelf-bottom-1", "type": "bookshelf", "col": 2, "row": 17 },
            { "uid": "shelf-bottom-2", "type": "bookshelf-wide", "col": 4, "row": 17 },
            { "uid": "shelf-bottom-3", "type": "bookshelf-wood", "col": 7, "row": 17 },
            { "uid": "plant-bottom-left", "type": "plant", "col": 1, "row": 19 },
            { "uid": "frame-bottom-left", "type": "frame-portrait", "col": 11, "row": 18 },
            { "uid": "lamp-bottom-left", "type": "lamp", "col": 11, "row": 19 }
        ]
    })
}
