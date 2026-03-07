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
    AgentRecord, ApprovalRequest, ApprovalStatus, ChatMessage, LlmProfile, MessageVisibility,
    TaskRecord, TaskStatus, WsEventEnvelope,
};

const LEGACY_RUNTIME_PLATFORMS: &[&str] = &["codex", "antigravity", "ollama"];
const LEGACY_SYSTEM_AGENT_IDS: &[&str] = &["codex", "antigravity", "ollama"];

pub fn project_root(control_root: &Path, project_id: &str) -> PathBuf {
    control_root.join(project_id)
}

fn normalize_platform(platform: &str) -> String {
    let trimmed = platform.trim();
    if trimmed.is_empty() {
        return "openrouter".to_string();
    }

    let lowered = trimmed.to_ascii_lowercase();
    if lowered == "openrouter" || LEGACY_RUNTIME_PLATFORMS.contains(&lowered.as_str()) {
        return "openrouter".to_string();
    }

    trimmed.to_string()
}

fn is_hidden_legacy_system_agent(agent_id: &str) -> bool {
    LEGACY_SYSTEM_AGENT_IDS.contains(&agent_id)
}

fn normalize_agent_record(mut agent: AgentRecord) -> Option<AgentRecord> {
    agent.platform = normalize_platform(&agent.platform);
    if is_hidden_legacy_system_agent(&agent.agent_id) {
        return None;
    }
    Some(agent)
}

pub fn ensure_project_scaffold(control_root: &Path, project_id: &str) -> Result<PathBuf> {
    let root = project_root(control_root, project_id);
    fs::create_dir_all(root.join("agents"))?;
    fs::create_dir_all(root.join("chat/threads"))?;
    fs::create_dir_all(root.join("issues"))?;
    fs::create_dir_all(root.join("runs"))?;
    fs::create_dir_all(root.join("pixel"))?;

    let registry_path = root.join("agents/registry.json");
    if !registry_path.exists() {
        fs::write(&registry_path, "{}\n")?;
    }

    let settings_path = root.join("settings.json");
    if !settings_path.exists() {
        fs::write(
            &settings_path,
            serde_json::to_string_pretty(&json!({
                "project_id": project_id,
                "project_name": project_id,
                "linked_repo_path": "",
                "updated_at": Utc::now().to_rfc3339(),
            }))?,
        )?;
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
        fs::write(
            layout_path,
            serde_json::to_string_pretty(&default_layout())?,
        )?;
    }

    let state_path = root.join("STATE.md");
    if !state_path.exists() {
        fs::write(
            state_path,
            "# State\n\n## Phase\n- Implement\n\n## Objective\n- Cockpit rewrite\n\n## Now\n- Bootstrap\n\n## Next\n- Pixel Home + chat live\n\n## In Progress\n- none\n\n## Blockers\n- none\n\n## Risks\n- rewrite scope\n\n## Links\n- none\n",
        )?;
    }

    let roadmap_path = root.join("ROADMAP.md");
    if !roadmap_path.exists() {
        fs::write(roadmap_path, "# Roadmap\n\n- Build Cockpit\n")?;
    }

    let decisions_path = root.join("DECISIONS.md");
    if !decisions_path.exists() {
        fs::write(decisions_path, "# Decisions\n")?;
    }

    ensure_runtime_db(control_root, project_id)?;
    Ok(root)
}

pub fn load_settings(control_root: &Path, project_id: &str) -> Result<Value> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let path = root.join("settings.json");
    let raw = fs::read_to_string(path)?;
    let value = serde_json::from_str::<Value>(&raw)?;
    Ok(value)
}

pub fn save_settings(control_root: &Path, project_id: &str, settings: &Value) -> Result<Value> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let path = root.join("settings.json");
    let mut payload = settings.clone();
    if let Some(object) = payload.as_object_mut() {
        object.insert("project_id".to_string(), json!(project_id));
        if object
            .get("project_name")
            .and_then(Value::as_str)
            .map(str::trim)
            .unwrap_or("")
            .is_empty()
        {
            object.insert("project_name".to_string(), json!(project_id));
        }
        object.insert("updated_at".to_string(), json!(Utc::now().to_rfc3339()));
    }
    fs::write(path, serde_json::to_string_pretty(&payload)?)?;
    Ok(payload)
}

pub fn linked_repo_path(control_root: &Path, project_id: &str) -> Result<Option<String>> {
    let settings = load_settings(control_root, project_id)?;
    let value = settings
        .get("linked_repo_path")
        .and_then(Value::as_str)
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(ToString::to_string);
    Ok(value)
}

pub fn read_project_text(control_root: &Path, project_id: &str, file_name: &str) -> Result<String> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    Ok(fs::read_to_string(root.join(file_name)).unwrap_or_default())
}

pub fn load_roadmap_sections(control_root: &Path, project_id: &str) -> Result<Value> {
    let raw = read_project_text(control_root, project_id, "ROADMAP.md")?;
    Ok(json!({
        "now": extract_markdown_section_bullets(&raw, "Now"),
        "next": extract_markdown_section_bullets(&raw, "Next"),
        "risks": extract_markdown_section_bullets(&raw, "Risks"),
    }))
}

pub fn save_roadmap_sections(
    control_root: &Path,
    project_id: &str,
    now: &[String],
    next: &[String],
    risks: &[String],
) -> Result<String> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let path = root.join("ROADMAP.md");
    let content = render_roadmap_markdown(now, next, risks);
    fs::write(&path, &content)?;
    Ok(content)
}

pub fn load_agents(control_root: &Path, project_id: &str) -> Result<HashMap<String, AgentRecord>> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let path = root.join("agents/registry.json");
    let raw = fs::read_to_string(&path)?;
    if raw.trim().is_empty() {
        return Ok(HashMap::new());
    }
    let parsed: HashMap<String, AgentRecord> = serde_json::from_str(&raw)
        .with_context(|| format!("invalid json in {}", path.display()))?;
    Ok(parsed
        .into_iter()
        .filter_map(|(agent_id, agent)| {
            normalize_agent_record(agent).map(|agent| (agent_id, agent))
        })
        .collect())
}

pub fn save_agents(
    control_root: &Path,
    project_id: &str,
    agents: &HashMap<String, AgentRecord>,
) -> Result<()> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let path = root.join("agents/registry.json");
    let normalized: HashMap<String, AgentRecord> = agents
        .iter()
        .filter_map(|(agent_id, agent)| {
            normalize_agent_record(agent.clone()).map(|agent| (agent_id.clone(), agent))
        })
        .collect();
    fs::write(path, serde_json::to_string_pretty(&normalized)?)?;
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
        fs::write(
            memory_path,
            format!("# Memory - {agent_id}\n\n- Initialized\n"),
        )?;
    }

    let journal_path = dir.join("journal.ndjson");
    if !journal_path.exists() {
        File::create(journal_path)?;
    }

    Ok(())
}

pub fn remove_agent_files(control_root: &Path, project_id: &str, agent_id: &str) -> Result<()> {
    let dir = project_root(control_root, project_id)
        .join("agents")
        .join(agent_id);
    if dir.exists() {
        fs::remove_dir_all(dir)?;
    }
    Ok(())
}

pub fn append_chat_message(
    control_root: &Path,
    project_id: &str,
    message: &ChatMessage,
) -> Result<()> {
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

    Ok((
        existing_messages,
        existing_approvals,
        chat_deleted + approvals_deleted,
    ))
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

pub fn append_runtime_event(
    control_root: &Path,
    project_id: &str,
    event: &WsEventEnvelope,
) -> Result<()> {
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
    let mut stmt =
        conn.prepare("SELECT payload_json FROM approval_requests WHERE request_id = ?1 LIMIT 1")?;

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

pub fn load_llm_profile(control_root: &Path, project_id: &str) -> Result<LlmProfile> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let cockpit_dir = root.join(".cockpit");
    let profile_path = cockpit_dir.join("llm-profile.json");

    let profile = if profile_path.exists() {
        let content = fs::read_to_string(&profile_path)?;
        serde_json::from_str::<LlmProfile>(&content)?
    } else {
        LlmProfile::default()
    };

    Ok(normalize_llm_profile(profile))
}

pub fn save_llm_profile(control_root: &Path, project_id: &str, profile: &LlmProfile) -> Result<LlmProfile> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let cockpit_dir = root.join(".cockpit");
    fs::create_dir_all(&cockpit_dir)?;

    let normalized = validate_llm_profile(normalize_llm_profile(profile.clone()))?;
    let profile_path = cockpit_dir.join("llm-profile.json");
    fs::write(profile_path, serde_json::to_string_pretty(&normalized)?)?;
    Ok(normalized)
}

pub fn list_tasks(control_root: &Path, project_id: &str) -> Result<Vec<TaskRecord>> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let issues_dir = root.join("issues");
    let mut tasks = Vec::new();

    for entry in fs::read_dir(issues_dir)? {
        let entry = entry?;
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let Some(name) = path.file_name().and_then(|value| value.to_str()) else {
            continue;
        };
        if !name.starts_with("ISSUE-") || !name.ends_with(".md") {
            continue;
        }
        if let Some(task) = parse_issue_task(&path)? {
            tasks.push(task);
        }
    }

    tasks.sort_by(|a, b| {
        let status_rank = |status: TaskStatus| match status {
            TaskStatus::Todo => 0_u8,
            TaskStatus::InProgress => 1_u8,
            TaskStatus::Blocked => 2_u8,
            TaskStatus::Done => 3_u8,
        };
        status_rank(a.status)
            .cmp(&status_rank(b.status))
            .then_with(|| a.title.to_lowercase().cmp(&b.title.to_lowercase()))
            .then_with(|| a.task_id.cmp(&b.task_id))
    });
    Ok(tasks)
}

pub fn create_task(
    control_root: &Path,
    project_id: &str,
    title: &str,
    owner: Option<&str>,
    phase: Option<&str>,
    status: TaskStatus,
    source: Option<&str>,
    objective: Option<&str>,
    done_definition: Option<&str>,
    links: &[String],
    risks: &[String],
) -> Result<TaskRecord> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let issues_dir = root.join("issues");
    let task_id = next_issue_id(&issues_dir)?;
    let slug = slugify(title);
    let path = issues_dir.join(format!("{task_id}-{slug}.md"));

    let task = TaskRecord {
        task_id: task_id.clone(),
        title: title.trim().to_string(),
        owner: owner.unwrap_or("clems").trim().to_string(),
        phase: phase.unwrap_or("Implement").trim().to_string(),
        status,
        source: source.unwrap_or("manual").trim().to_string(),
        objective: normalize_multiline(objective.unwrap_or("TBD")),
        done_definition: normalize_multiline(done_definition.unwrap_or("Define verifiable done criteria.")),
        links: normalize_lines(links.to_vec()),
        risks: normalize_lines(risks.to_vec()),
        path: path.display().to_string(),
        updated_at: Utc::now().to_rfc3339(),
    };

    fs::write(&path, render_task_markdown(&task))?;
    Ok(task)
}

pub fn update_task(
    control_root: &Path,
    project_id: &str,
    task_id: &str,
    patch: &TaskRecordPatch,
) -> Result<Option<TaskRecord>> {
    let root = ensure_project_scaffold(control_root, project_id)?;
    let Some(path) = find_issue_path(root.join("issues").as_path(), task_id)? else {
        return Ok(None);
    };

    let raw = fs::read_to_string(&path)?;
    let mut task = parse_issue_task(&path)?.ok_or_else(|| anyhow::anyhow!("invalid task file"))?;

    if let Some(title) = &patch.title {
        task.title = title.trim().to_string();
    }
    if let Some(owner) = &patch.owner {
        task.owner = owner.trim().to_string();
    }
    if let Some(phase) = &patch.phase {
        task.phase = phase.trim().to_string();
    }
    if let Some(status) = patch.status {
        task.status = status;
    }
    if let Some(source) = &patch.source {
        task.source = source.trim().to_string();
    }
    if let Some(objective) = &patch.objective {
        task.objective = normalize_multiline(objective);
    }
    if let Some(done_definition) = &patch.done_definition {
        task.done_definition = normalize_multiline(done_definition);
    }
    if let Some(links) = &patch.links {
        task.links = normalize_lines(links.clone());
    }
    if let Some(risks) = &patch.risks {
        task.risks = normalize_lines(risks.clone());
    }

    task.updated_at = Utc::now().to_rfc3339();
    task.path = path.display().to_string();

    let updated = rewrite_issue_markdown(&raw, &task);
    fs::write(&path, updated)?;
    Ok(Some(task))
}

pub fn create_tasks_from_ai_message(
    control_root: &Path,
    project_id: &str,
    author: &str,
    text: &str,
) -> Result<Vec<TaskRecord>> {
    if !matches!(author, "clems" | "victor" | "leo" | "nova" | "vulgarisation") {
        return Ok(Vec::new());
    }

    let specs = extract_ai_task_specs(author, text);
    let mut out = Vec::new();
    for spec in specs {
        out.push(create_task(
            control_root,
            project_id,
            &spec.title,
            Some(spec.owner.as_deref().unwrap_or(author)),
            Some("Implement"),
            TaskStatus::Todo,
            Some("ai_auto"),
            Some(spec.objective.as_deref().unwrap_or(&spec.title)),
            Some(
                spec.done_definition
                    .as_deref()
                    .unwrap_or("Task completed with verifiable output and tests or logs."),
            ),
            &Vec::new(),
            &Vec::new(),
        )?);
    }
    Ok(out)
}

#[derive(Debug, Default)]
pub struct TaskRecordPatch {
    pub title: Option<String>,
    pub owner: Option<String>,
    pub phase: Option<String>,
    pub status: Option<TaskStatus>,
    pub source: Option<String>,
    pub objective: Option<String>,
    pub done_definition: Option<String>,
    pub links: Option<Vec<String>>,
    pub risks: Option<Vec<String>>,
}

#[derive(Debug)]
struct AiTaskSpec {
    title: String,
    owner: Option<String>,
    objective: Option<String>,
    done_definition: Option<String>,
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

fn normalize_llm_profile(mut profile: LlmProfile) -> LlmProfile {
    profile.provider = "openrouter".to_string();

    if profile.voice_stt_model.trim().is_empty() {
        profile.voice_stt_model = LlmProfile::default().voice_stt_model;
    }

    if profile.clems_catalog.is_empty() {
        profile.clems_catalog = LlmProfile::default().clems_catalog;
    }
    if profile.l1_catalog.is_empty() {
        profile.l1_catalog = LlmProfile::default().l1_catalog;
    }
    if profile.l2_pool.is_empty() {
        profile.l2_pool = LlmProfile::default().l2_pool;
    }
    if profile.l2_selection_mode.trim().is_empty() {
        profile.l2_selection_mode = LlmProfile::default().l2_selection_mode;
    }

    if profile.clems_model.trim().is_empty()
        || (profile.default_model.is_some() && profile.clems_model == LlmProfile::default().clems_model)
    {
        profile.clems_model = profile
            .default_model
            .clone()
            .filter(|value| !value.trim().is_empty())
            .unwrap_or_else(|| LlmProfile::default().clems_model);
    }

    let l1_seed = profile
        .l1_model
        .clone()
        .filter(|value| !value.trim().is_empty())
        .or_else(|| {
            profile
                .default_model
                .clone()
                .filter(|value| !value.trim().is_empty())
        })
        .unwrap_or_else(|| LlmProfile::default().clems_model);

    for agent_id in ["victor", "leo", "nova", "vulgarisation"] {
        profile
            .l1_models
            .entry(agent_id.to_string())
            .or_insert_with(|| l1_seed.clone());
    }
    for agent_id in ["victor", "leo", "nova", "vulgarisation"] {
        if let Some(current) = profile.l1_models.get_mut(agent_id) {
            if current.trim().is_empty()
                || (profile.l1_model.is_some() && *current == LlmProfile::default().clems_model)
            {
                *current = l1_seed.clone();
            }
        }
    }
    profile
        .l1_models
        .retain(|_, value| !value.trim().is_empty());

    if profile.l2_default_model.trim().is_empty()
        || (profile.l2_scene_model.is_some()
            && profile.l2_default_model == LlmProfile::default().l2_default_model)
    {
        profile.l2_default_model = profile
            .l2_scene_model
            .clone()
            .filter(|value| !value.trim().is_empty())
            .unwrap_or_else(|| LlmProfile::default().l2_default_model);
    }

    dedup_in_place(&mut profile.clems_catalog);
    dedup_in_place(&mut profile.l1_catalog);
    dedup_in_place(&mut profile.l2_pool);
    if !profile.l2_pool.contains(&profile.l2_default_model) {
        profile.l2_pool.insert(0, profile.l2_default_model.clone());
        dedup_in_place(&mut profile.l2_pool);
    }

    if profile.lfm_spawn_max.is_none() {
        profile.lfm_spawn_max = Some(10);
    }

    profile
}

fn validate_llm_profile(mut profile: LlmProfile) -> Result<LlmProfile> {
    if !profile.clems_catalog.contains(&profile.clems_model) {
        anyhow::bail!("clems_model must exist in clems_catalog");
    }
    for (agent_id, model_id) in &profile.l1_models {
        if !profile.l1_catalog.contains(model_id) {
            anyhow::bail!("l1 model for {agent_id} must exist in l1_catalog");
        }
    }
    for model_id in &profile.l2_pool {
        if !default_l2_models().contains(&model_id.as_str()) && !model_id.eq(&profile.l2_default_model) {
            anyhow::bail!("l2_pool contains unsupported model: {model_id}");
        }
    }
    if !profile.l2_pool.contains(&profile.l2_default_model) {
        anyhow::bail!("l2_default_model must exist in l2_pool");
    }
    if profile.l2_selection_mode != "manual_primary" {
        anyhow::bail!("unsupported l2_selection_mode: {}", profile.l2_selection_mode);
    }

    profile.default_model = Some(profile.clems_model.clone());
    profile.l1_model = profile.l1_models.get("victor").cloned();
    profile.l2_scene_model = Some(profile.l2_default_model.clone());
    profile.lfm_spawn_max = Some(10);
    Ok(profile)
}

fn extract_markdown_section_bullets(markdown: &str, section: &str) -> Vec<String> {
    let target = format!("## {section}");
    let mut out = Vec::new();
    let mut in_section = false;
    for raw_line in markdown.lines() {
        let line = raw_line.trim();
        if line.starts_with("## ") {
            in_section = line == target;
            continue;
        }
        if !in_section {
            continue;
        }
        if let Some(value) = line.strip_prefix("- ").map(str::trim).filter(|value| !value.is_empty()) {
            out.push(value.to_string());
        }
    }
    out
}

fn render_roadmap_markdown(now: &[String], next: &[String], risks: &[String]) -> String {
    let mut lines = vec!["# Roadmap".to_string(), String::new()];
    for (title, values) in [("Now", now), ("Next", next), ("Risks", risks)] {
        lines.push(format!("## {title}"));
        if values.is_empty() {
            lines.push("- none".to_string());
        } else {
            for value in values {
                let normalized = value.trim();
                if !normalized.is_empty() {
                    lines.push(format!("- {normalized}"));
                }
            }
        }
        lines.push(String::new());
    }
    lines.join("\n")
}

fn default_l2_models() -> [&'static str; 3] {
    [
        "minimax/minimax-m2.5",
        "moonshotai/kimi-k2.5",
        "deepseek/deepseek-chat-v3.1",
    ]
}

fn dedup_in_place(values: &mut Vec<String>) {
    let mut seen = std::collections::BTreeSet::new();
    values.retain(|value| seen.insert(value.clone()));
}

fn parse_issue_task(path: &Path) -> Result<Option<TaskRecord>> {
    let raw = fs::read_to_string(path)?;
    let lines: Vec<&str> = raw.lines().collect();
    if lines.is_empty() {
        return Ok(None);
    }

    let heading = lines
        .iter()
        .find_map(|line| line.trim().strip_prefix("# "))
        .unwrap_or(path.file_stem().and_then(|value| value.to_str()).unwrap_or("ISSUE-UNKNOWN"));
    let (task_id, title) = parse_heading(heading, path);

    let owner = find_metadata_value(&lines, "Owner").unwrap_or_else(|| "unassigned".to_string());
    let phase = find_metadata_value(&lines, "Phase").unwrap_or_else(|| "Implement".to_string());
    let status = parse_task_status(find_metadata_value(&lines, "Status").as_deref());
    let source = find_metadata_value(&lines, "Source").unwrap_or_else(|| "manual".to_string());
    let objective = section_to_text(&lines, "Objective").unwrap_or_else(|| "TBD".to_string());
    let done_definition = section_to_text(&lines, "Done (Definition)")
        .or_else(|| section_to_text(&lines, "Done"))
        .unwrap_or_else(|| "Define verifiable done criteria.".to_string());
    let links = section_to_list(&lines, "Links");
    let risks = section_to_list(&lines, "Risks");
    let updated_at = fs::metadata(path)
        .ok()
        .and_then(|meta| meta.modified().ok())
        .map(|stamp| chrono::DateTime::<Utc>::from(stamp).to_rfc3339())
        .unwrap_or_else(|| Utc::now().to_rfc3339());

    Ok(Some(TaskRecord {
        task_id,
        title,
        owner,
        phase,
        status,
        source,
        objective,
        done_definition,
        links,
        risks,
        path: path.display().to_string(),
        updated_at,
    }))
}

fn parse_heading(heading: &str, path: &Path) -> (String, String) {
    let normalized = heading.trim();
    let fallback_id = path
        .file_stem()
        .and_then(|value| value.to_str())
        .unwrap_or("ISSUE-UNKNOWN")
        .split('-')
        .take(3)
        .collect::<Vec<_>>()
        .join("-");

    if let Some((id, rest)) = normalized.split_once(" - ") {
        return (id.trim().to_string(), rest.trim().to_string());
    }

    let task_id = normalized
        .split_whitespace()
        .next()
        .filter(|value| value.starts_with("ISSUE-"))
        .map(ToString::to_string)
        .unwrap_or(fallback_id);
    let title = normalized
        .strip_prefix(&task_id)
        .map(|value| value.trim_start_matches('-').trim().to_string())
        .filter(|value| !value.is_empty())
        .unwrap_or_else(|| task_id.clone());
    (task_id, title)
}

fn find_metadata_value(lines: &[&str], key: &str) -> Option<String> {
    let prefix = format!("- {key}:");
    lines.iter().find_map(|line| {
        let trimmed = line.trim();
        trimmed
            .strip_prefix(&prefix)
            .map(|value| value.trim().to_string())
            .filter(|value| !value.is_empty())
    })
}

fn parse_task_status(value: Option<&str>) -> TaskStatus {
    match value.unwrap_or("todo").trim().to_ascii_lowercase().as_str() {
        "done" => TaskStatus::Done,
        "blocked" => TaskStatus::Blocked,
        "in progress" | "in_progress" => TaskStatus::InProgress,
        _ => TaskStatus::Todo,
    }
}

fn section_to_list(lines: &[&str], section: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut in_section = false;
    let target = format!("## {section}");
    for line in lines {
        let trimmed = line.trim();
        if trimmed.starts_with("## ") {
            in_section = trimmed == target;
            continue;
        }
        if !in_section {
            continue;
        }
        if let Some(value) = trimmed.strip_prefix("- [x] ") {
            if !value.trim().is_empty() {
                out.push(value.trim().to_string());
            }
            continue;
        }
        if let Some(value) = trimmed.strip_prefix("- [ ] ") {
            if !value.trim().is_empty() {
                out.push(value.trim().to_string());
            }
            continue;
        }
        if let Some(value) = trimmed.strip_prefix("- ") {
            if !value.trim().is_empty() {
                out.push(value.trim().to_string());
            }
        }
    }
    out
}

fn section_to_text(lines: &[&str], section: &str) -> Option<String> {
    let items = section_to_list(lines, section);
    if items.is_empty() {
        None
    } else {
        Some(items.join("\n"))
    }
}

fn normalize_multiline(value: &str) -> String {
    value
        .lines()
        .map(str::trim)
        .filter(|line| !line.is_empty())
        .collect::<Vec<_>>()
        .join("\n")
}

fn normalize_lines(values: Vec<String>) -> Vec<String> {
    values
        .into_iter()
        .map(|line| line.trim().to_string())
        .filter(|line| !line.is_empty())
        .collect()
}

fn slugify(title: &str) -> String {
    let mut out = String::new();
    let mut prev_dash = false;
    for ch in title.trim().chars() {
        let next = if ch.is_ascii_alphanumeric() {
            ch.to_ascii_lowercase()
        } else {
            '-'
        };
        if next == '-' {
            if prev_dash {
                continue;
            }
            prev_dash = true;
        } else {
            prev_dash = false;
        }
        out.push(next);
    }
    out.trim_matches('-').to_string().chars().take(64).collect::<String>()
}

fn next_issue_id(issues_dir: &Path) -> Result<String> {
    let mut max_n = 0_u32;
    for entry in fs::read_dir(issues_dir)? {
        let entry = entry?;
        let Some(name) = entry.file_name().to_str().map(ToString::to_string) else {
            continue;
        };
        let Some(rest) = name.strip_prefix("ISSUE-CP-") else {
            continue;
        };
        let digits = rest
            .chars()
            .take_while(|ch| ch.is_ascii_digit())
            .collect::<String>();
        if let Ok(value) = digits.parse::<u32>() {
            max_n = max_n.max(value);
        }
    }
    Ok(format!("ISSUE-CP-{:04}", max_n + 1))
}

fn render_task_markdown(task: &TaskRecord) -> String {
    let mut lines = vec![
        format!("# {} - {}", task.task_id, task.title),
        String::new(),
        format!("- Owner: {}", task.owner),
        format!("- Phase: {}", task.phase),
        format!("- Status: {}", task.status.as_label()),
        format!("- Source: {}", task.source),
        String::new(),
        "## Objective".to_string(),
    ];
    lines.extend(as_bullets(&task.objective));
    lines.extend([
        String::new(),
        "## Done (Definition)".to_string(),
    ]);
    lines.extend(as_checkbox_bullets(&task.done_definition));
    lines.extend([String::new(), "## Links".to_string()]);
    lines.extend(as_bullets_from_list(&task.links));
    lines.extend([String::new(), "## Risks".to_string()]);
    lines.extend(as_bullets_from_list(&task.risks));
    lines.push(String::new());
    lines.join("\n")
}

fn as_bullets(value: &str) -> Vec<String> {
    let rows = normalize_multiline(value);
    if rows.is_empty() {
        return vec!["- TBD".to_string()];
    }
    rows.lines().map(|line| format!("- {line}")).collect()
}

fn as_checkbox_bullets(value: &str) -> Vec<String> {
    let rows = normalize_multiline(value);
    if rows.is_empty() {
        return vec!["- [ ] Define verifiable done criteria.".to_string()];
    }
    rows.lines().map(|line| format!("- [ ] {line}")).collect()
}

fn as_bullets_from_list(values: &[String]) -> Vec<String> {
    if values.is_empty() {
        return vec!["- none".to_string()];
    }
    values.iter().map(|line| format!("- {line}")).collect()
}

fn rewrite_issue_markdown(raw: &str, task: &TaskRecord) -> String {
    let lines: Vec<String> = raw.lines().map(ToString::to_string).collect();
    let lines = replace_heading(lines, task);
    let lines = replace_metadata(lines, "Owner", &task.owner);
    let lines = replace_metadata(lines, "Phase", &task.phase);
    let lines = replace_metadata(lines, "Status", task.status.as_label());
    let lines = replace_metadata(lines, "Source", &task.source);
    let lines = replace_section(lines, "Objective", &as_bullets(&task.objective));
    let lines = replace_section(lines, "Done (Definition)", &as_checkbox_bullets(&task.done_definition));
    let lines = replace_section(lines, "Links", &as_bullets_from_list(&task.links));
    let mut lines = replace_section(lines, "Risks", &as_bullets_from_list(&task.risks));
    if !lines.last().is_some_and(|line| line.is_empty()) {
        lines.push(String::new());
    }
    lines.join("\n")
}

fn replace_heading(mut lines: Vec<String>, task: &TaskRecord) -> Vec<String> {
    for line in &mut lines {
        if line.trim().starts_with("# ") {
            *line = format!("# {} - {}", task.task_id, task.title);
            return lines;
        }
    }
    lines.insert(0, format!("# {} - {}", task.task_id, task.title));
    lines.insert(1, String::new());
    lines
}

fn replace_metadata(mut lines: Vec<String>, key: &str, value: &str) -> Vec<String> {
    let prefix = format!("- {key}:");
    for line in &mut lines {
        if line.trim().starts_with(&prefix) {
            *line = format!("{prefix} {value}");
            return lines;
        }
    }

    let insert_at = lines
        .iter()
        .position(|line| line.trim().starts_with("## "))
        .unwrap_or(lines.len());
    lines.insert(insert_at, format!("{prefix} {value}"));
    lines
}

fn replace_section(mut lines: Vec<String>, section: &str, contents: &[String]) -> Vec<String> {
    let header = format!("## {section}");
    let mut start = None;
    let mut end = None;
    for (index, line) in lines.iter().enumerate() {
        if line.trim() == header {
            start = Some(index);
            continue;
        }
        if start.is_some() && line.trim().starts_with("## ") {
            end = Some(index);
            break;
        }
    }

    let mut block = vec![header];
    block.extend(contents.iter().cloned());
    block.push(String::new());

    match (start, end) {
        (Some(start), Some(end)) => {
            lines.splice(start..end, block);
        }
        (Some(start), None) => {
            lines.splice(start..lines.len(), block);
        }
        (None, _) => {
            if !lines.last().is_some_and(|line| line.is_empty()) {
                lines.push(String::new());
            }
            lines.extend(block);
        }
    }
    lines
}

fn find_issue_path(issues_dir: &Path, task_id: &str) -> Result<Option<PathBuf>> {
    for entry in fs::read_dir(issues_dir)? {
        let entry = entry?;
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let Some(name) = path.file_name().and_then(|value| value.to_str()) else {
            continue;
        };
        if name.starts_with(task_id) && name.ends_with(".md") {
            return Ok(Some(path));
        }
    }
    Ok(None)
}

fn extract_ai_task_specs(author: &str, text: &str) -> Vec<AiTaskSpec> {
    let lines: Vec<&str> = text.lines().collect();
    let mut in_block = false;
    let mut out = Vec::new();

    for raw in lines {
        let trimmed = raw.trim();
        let lowered = trimmed.to_ascii_lowercase();
        if matches!(lowered.as_str(), "tasks:" | "task list:" | "todo:" | "to do:") {
            in_block = true;
            continue;
        }
        if !in_block {
            continue;
        }
        if trimmed.is_empty() {
            break;
        }
        if !trimmed.starts_with("- ") {
            break;
        }
        let item = trimmed.trim_start_matches("- ").trim();
        if let Some(spec) = parse_ai_task_line(author, item) {
            out.push(spec);
        }
    }
    out
}

fn parse_ai_task_line(author: &str, line: &str) -> Option<AiTaskSpec> {
    let mut title = line.to_string();
    let mut owner = Some(author.to_string());
    let mut objective = None;
    let mut done_definition = None;

    let segments = line.split('|').map(str::trim).collect::<Vec<_>>();
    if let Some(first) = segments.first() {
        title = (*first).to_string();
    }
    for segment in segments.iter().skip(1) {
        if let Some(value) = segment.strip_prefix("owner=") {
            owner = Some(value.trim().trim_start_matches('@').to_string());
        } else if let Some(value) = segment.strip_prefix("objective=") {
            objective = Some(value.trim().to_string());
        } else if let Some(value) = segment.strip_prefix("done=") {
            done_definition = Some(value.trim().to_string());
        }
    }

    let title = title.trim().trim_start_matches("[ ]").trim();
    if title.is_empty() {
        return None;
    }

    Some(AiTaskSpec {
        title: title.to_string(),
        owner,
        objective,
        done_definition,
    })
}

#[cfg(test)]
mod tests {
    use super::{
        TaskRecordPatch, create_task, create_tasks_from_ai_message, load_agents, load_llm_profile,
        list_tasks, save_agents, save_llm_profile, update_task,
    };
    use crate::models::{AgentRecord, LlmProfile, TaskStatus};
    use std::{collections::HashMap, fs};
    use uuid::Uuid;

    fn temp_root() -> std::path::PathBuf {
        let root =
            std::env::temp_dir().join(format!("cockpit-core-storage-{}", Uuid::new_v4().simple()));
        fs::create_dir_all(&root).expect("create temp root");
        root
    }

    fn sample_agent(agent_id: &str, platform: &str) -> AgentRecord {
        AgentRecord {
            agent_id: agent_id.to_string(),
            name: agent_id.to_string(),
            engine: "CDX".to_string(),
            platform: platform.to_string(),
            level: 2,
            lead_id: Some("victor".to_string()),
            role: "specialist".to_string(),
            skills: Vec::new(),
        }
    }

    #[test]
    fn load_agents_normalizes_legacy_platforms_and_hides_legacy_system_agents() {
        let root = temp_root();
        let project_id = "demo";
        let project_root = root.join(project_id).join("agents");
        fs::create_dir_all(&project_root).expect("create agent dir");
        fs::write(
            project_root.join("registry.json"),
            serde_json::to_string_pretty(&HashMap::from([
                ("agent-1".to_string(), sample_agent("agent-1", "codex")),
                (
                    "antigravity".to_string(),
                    sample_agent("antigravity", "antigravity"),
                ),
            ]))
            .expect("serialize registry"),
        )
        .expect("write registry");

        let agents = load_agents(&root, project_id).expect("load agents");
        assert_eq!(agents.len(), 1);
        assert_eq!(agents["agent-1"].platform, "openrouter");
        assert!(!agents.contains_key("antigravity"));
    }

    #[test]
    fn save_agents_rewrites_platforms_to_openrouter() {
        let root = temp_root();
        let project_id = "demo";
        let mut agents = HashMap::new();
        agents.insert("agent-1".to_string(), sample_agent("agent-1", "ollama"));
        agents.insert("codex".to_string(), sample_agent("codex", "codex"));

        save_agents(&root, project_id, &agents).expect("save agents");
        let raw = fs::read_to_string(root.join(project_id).join("agents/registry.json"))
            .expect("read registry");
        assert!(raw.contains("\"openrouter\""));
        assert!(!raw.contains("\"codex\""));
        assert!(!raw.contains("\"ollama\""));
    }

    #[test]
    fn llm_profile_migrates_legacy_fields_to_role_based_schema() {
        let root = temp_root();
        let project_id = "demo";
        let project_root = root.join(project_id).join(".cockpit");
        fs::create_dir_all(&project_root).expect("create profile dir");
        fs::write(
            project_root.join("llm-profile.json"),
            serde_json::json!({
                "provider": "openrouter",
                "default_model": "moonshotai/kimi-k2.5",
                "l1_model": "anthropic/claude-sonnet-4.6",
                "l2_scene_model": "deepseek/deepseek-chat-v3.1"
            })
            .to_string(),
        )
        .expect("write profile");

        let profile = load_llm_profile(&root, project_id).expect("load profile");
        assert_eq!(profile.clems_model, "moonshotai/kimi-k2.5");
        assert_eq!(
            profile.l1_models.get("victor").map(String::as_str),
            Some("anthropic/claude-sonnet-4.6")
        );
        assert_eq!(profile.l2_default_model, "deepseek/deepseek-chat-v3.1");
    }

    #[test]
    fn save_llm_profile_rejects_invalid_l1_model() {
        let root = temp_root();
        let project_id = "demo";
        let mut profile = LlmProfile::default();
        profile
            .l1_models
            .insert("victor".to_string(), "invalid/model".to_string());

        let result = save_llm_profile(&root, project_id, &profile);
        assert!(result.is_err());
    }

    #[test]
    fn task_crud_round_trip_uses_markdown_issue_files() {
        let root = temp_root();
        let project_id = "demo";
        let created = create_task(
            &root,
            project_id,
            "Wire To Do board",
            Some("leo"),
            Some("Implement"),
            TaskStatus::Todo,
            Some("manual"),
            Some("Ship the first To Do board UI."),
            Some("Board renders and persists."),
            &[],
            &[],
        )
        .expect("create task");

        let tasks = list_tasks(&root, project_id).expect("list tasks");
        assert_eq!(tasks.len(), 1);
        assert_eq!(tasks[0].task_id, created.task_id);

        let updated = update_task(
            &root,
            project_id,
            &created.task_id,
            &TaskRecordPatch {
                status: Some(TaskStatus::InProgress),
                owner: Some("victor".to_string()),
                ..TaskRecordPatch::default()
            },
        )
        .expect("update task")
        .expect("task exists");
        assert_eq!(updated.status, TaskStatus::InProgress);
        assert_eq!(updated.owner, "victor");
    }

    #[test]
    fn auto_task_creation_only_accepts_structured_task_blocks() {
        let root = temp_root();
        let project_id = "demo";
        let created = create_tasks_from_ai_message(
            &root,
            project_id,
            "clems",
            "Tasks:\n- Ship the To Do board | owner=leo | done=Board renders and persists\n- Tighten chat copy | owner=victor\n",
        )
        .expect("auto create tasks");
        assert_eq!(created.len(), 2);
        assert_eq!(created[0].source, "ai_auto");
    }
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
