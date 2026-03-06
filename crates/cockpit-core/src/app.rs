use std::{
    collections::{HashMap, HashSet},
    path::PathBuf,
};

use axum::{
    Json, Router,
    extract::{
        Path, Query, State, WebSocketUpgrade,
        ws::{Message, WebSocket},
    },
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::{delete, get, post},
};
use chrono::Utc;
use serde::Deserialize;
use serde_json::{Value, json};
use tower_http::cors::CorsLayer;
use uuid::Uuid;

use crate::{
    chat,
    models::{
        AgentRecord, ApprovalDecisionRequest, ApprovalStatus, ChatApprovalsResponse,
        ChatHistoryResponse, ChatMessage, CreateAgentRequest, CreateAgentResponse,
        CreateTaskRequest, DeliveryMode, LiveTurnRequest, LiveTurnResponse, LlmProfileResponse,
        MessageVisibility, PixelAgentStatus, PixelFeedResponse, RoadmapDraftRequest,
        RoadmapDraftResponse, TasksResponse, TerminalOpenRequest, TerminalSendRequest,
        TerminalSession, UpdateLlmProfileRequest, UpdateTaskRequest, WsEventEnvelope,
    },
    openrouter, orchestrator,
    state::AppState,
    storage,
};

pub fn build_router(state: AppState) -> Router {
    Router::new()
        .route("/healthz", get(healthz))
        .route(
            "/v1/projects/{id}/agents",
            post(create_agent).get(list_agents),
        )
        .route("/v1/projects/{id}/agents/{agent_id}", delete(delete_agent))
        .route(
            "/v1/projects/{id}/agents/{agent_id}/terminal/open",
            post(open_terminal),
        )
        .route(
            "/v1/projects/{id}/agents/{agent_id}/terminal/send",
            post(send_terminal_input),
        )
        .route(
            "/v1/projects/{id}/agents/{agent_id}/terminal/restart",
            post(restart_terminal),
        )
        .route("/v1/projects/{id}/chat/live-turn", post(live_turn))
        .route("/v1/projects/{id}/chat", get(chat_history))
        .route("/v1/projects/{id}/chat/reset", post(reset_chat))
        .route("/v1/projects/{id}/chat/approvals", get(chat_approvals))
        .route(
            "/v1/projects/{id}/chat/approvals/{request_id}/approve",
            post(approve_approval),
        )
        .route(
            "/v1/projects/{id}/chat/approvals/{request_id}/reject",
            post(reject_approval),
        )
        .route("/v1/projects/{id}/pixel-feed", get(pixel_feed))
        .route("/v1/projects/{id}/tasks", get(get_tasks).post(post_task))
        .route("/v1/projects/{id}/tasks/{task_id}", axum::routing::patch(patch_task))
        .route("/v1/projects/{id}/layout", get(get_layout).put(put_layout))
        .route("/v1/projects/{id}/events", get(ws_events))
        .route(
            "/v1/projects/{id}/llm-profile",
            get(get_llm_profile).put(put_llm_profile),
        )
        .route(
            "/v1/projects/{id}/roadmap/clems-draft",
            post(post_roadmap_clems_draft),
        )
        .layer(CorsLayer::permissive())
        .with_state(state)
}

async fn healthz() -> Json<Value> {
    let build = crate::build_info::runtime_build_info();
    Json(json!({
        "status": "ok",
        "mode": "owner_local",
        "date_ref": "2026-03-03",
        "time": Utc::now().to_rfc3339(),
        "build_sha": build.build_sha,
        "build_time": build.build_time,
        "app_mode": build.app_mode,
    }))
}

async fn list_agents(
    Path(project_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<Value>, ApiError> {
    let agents_map = storage::load_agents(state.control_root.as_ref(), &project_id)?;
    let mut agents: Vec<AgentRecord> = agents_map.into_values().collect();
    agents.sort_by(|a, b| a.agent_id.cmp(&b.agent_id));

    Ok(Json(json!({
        "project_id": project_id,
        "agents": agents,
    })))
}

async fn create_agent(
    Path(project_id): Path<String>,
    State(state): State<AppState>,
    Json(payload): Json<CreateAgentRequest>,
) -> Result<Json<CreateAgentResponse>, ApiError> {
    storage::ensure_project_scaffold(state.control_root.as_ref(), &project_id)?;

    let mut agents = storage::load_agents(state.control_root.as_ref(), &project_id)?;
    let agent_id = payload
        .agent_id
        .clone()
        .unwrap_or_else(|| next_agent_id(&agents));

    let defaults = default_agent_profile(&agent_id);
    let agent = AgentRecord {
        agent_id: agent_id.clone(),
        name: payload.name.unwrap_or_else(|| defaults.0.clone()),
        engine: payload.engine.unwrap_or_else(|| defaults.1.to_string()),
        platform: payload.platform.unwrap_or_else(|| "openrouter".to_string()),
        level: payload.level.unwrap_or(defaults.2),
        lead_id: payload.lead_id.or(defaults.3),
        role: payload.role.unwrap_or_else(|| defaults.4.to_string()),
        skills: payload.skills.unwrap_or_default(),
    };

    agents.insert(agent_id.clone(), agent.clone());
    storage::save_agents(state.control_root.as_ref(), &project_id, &agents)?;
    storage::ensure_agent_files(state.control_root.as_ref(), &project_id, &agent_id)?;

    let project_dir = storage::project_root(state.control_root.as_ref(), &project_id);
    let cwd = payload
        .cwd
        .map(PathBuf::from)
        .unwrap_or_else(|| project_dir.clone());

    let terminal = state
        .terminal_manager
        .open_or_get(&project_id, &agent_id, cwd.clone())?;
    emit_clems_online_ack_if_needed(&state, &project_id, &agent_id, &terminal)?;

    state.emit_event(
        &project_id,
        "agent.created",
        json!({
            "agent": agent,
            "terminal": terminal,
        }),
    );
    state.emit_event(
        &project_id,
        "pixel.updated",
        json!({
            "reason": "agent.created",
            "agent_id": agent_id,
        }),
    );

    Ok(Json(CreateAgentResponse { agent, terminal }))
}

async fn delete_agent(
    Path((project_id, agent_id)): Path<(String, String)>,
    State(state): State<AppState>,
) -> Result<Json<Value>, ApiError> {
    let mut agents = storage::load_agents(state.control_root.as_ref(), &project_id)?;
    if agents.remove(&agent_id).is_none() {
        return Err(ApiError::not_found(format!("unknown agent {agent_id}")));
    }

    storage::save_agents(state.control_root.as_ref(), &project_id, &agents)?;
    storage::remove_agent_files(state.control_root.as_ref(), &project_id, &agent_id)?;
    let _ = state.terminal_manager.close(&project_id, &agent_id)?;

    state.emit_event(
        &project_id,
        "agent.updated",
        json!({
            "agent_id": agent_id,
            "action": "deleted",
        }),
    );
    state.emit_event(
        &project_id,
        "pixel.updated",
        json!({
            "reason": "agent.deleted",
            "agent_id": agent_id,
        }),
    );

    Ok(Json(json!({ "ok": true })))
}

async fn open_terminal(
    Path((project_id, agent_id)): Path<(String, String)>,
    State(state): State<AppState>,
    Json(payload): Json<TerminalOpenRequest>,
) -> Result<Json<Value>, ApiError> {
    let project_dir = storage::project_root(state.control_root.as_ref(), &project_id);
    let cwd = payload.cwd.map(PathBuf::from).unwrap_or(project_dir);

    let session = state
        .terminal_manager
        .open_or_get(&project_id, &agent_id, cwd)?;
    emit_clems_online_ack_if_needed(&state, &project_id, &agent_id, &session)?;

    Ok(Json(json!({ "session": session })))
}

async fn send_terminal_input(
    Path((project_id, agent_id)): Path<(String, String)>,
    State(state): State<AppState>,
    Json(payload): Json<TerminalSendRequest>,
) -> Result<Json<Value>, ApiError> {
    let session = state
        .terminal_manager
        .send_input(&project_id, &agent_id, &payload.text)?;

    Ok(Json(json!({ "session": session, "ok": true })))
}

async fn restart_terminal(
    Path((project_id, agent_id)): Path<(String, String)>,
    State(state): State<AppState>,
    Json(payload): Json<TerminalOpenRequest>,
) -> Result<Json<Value>, ApiError> {
    let session =
        state
            .terminal_manager
            .restart(&project_id, &agent_id, payload.cwd.map(PathBuf::from))?;
    emit_clems_online_ack_if_needed(&state, &project_id, &agent_id, &session)?;

    Ok(Json(json!({ "session": session })))
}

async fn live_turn(
    Path(project_id): Path<String>,
    State(state): State<AppState>,
    Json(payload): Json<LiveTurnRequest>,
) -> Result<Json<LiveTurnResponse>, ApiError> {
    storage::ensure_project_scaffold(state.control_root.as_ref(), &project_id)?;

    let run_id = format!("run_{}", Uuid::new_v4().simple());
    state.emit_event(
        &project_id,
        "chat.turn.started",
        json!({
            "run_id": run_id,
            "chat_mode": payload.chat_mode,
            "execution_mode": payload.execution_mode,
        }),
    );

    let mut mentions = payload.mentions.clone();
    mentions.extend(chat::extract_mentions(&payload.text));
    mentions = dedup(mentions);

    let mut operator_msg =
        ChatMessage::new("operator", payload.text.clone(), payload.thread_id.clone());
    operator_msg.mentions = mentions.clone();
    operator_msg.metadata = json!({
        "project_id": project_id,
        "chat_mode": payload.chat_mode,
        "execution_mode": payload.execution_mode,
        "run_id": run_id,
        "context_ref": payload.context_ref,
        "section_tag": payload.section_tag,
    });
    storage::append_chat_message(state.control_root.as_ref(), &project_id, &operator_msg)?;
    state.emit_event(
        &project_id,
        "chat.message.created",
        json!({ "message": operator_msg.clone() }),
    );
    state.emit_event(
        &project_id,
        "chat.delivery.confirmed",
        json!({
            "run_id": run_id,
            "message_id": operator_msg.message_id,
            "author": operator_msg.author,
        }),
    );

    let orchestration = orchestrator::run_turn(
        state.control_root.as_ref(),
        &project_id,
        &run_id,
        &payload,
        &mentions,
    )
    .await?;

    for approval in &orchestration.approval_requests {
        state.emit_event(
            &project_id,
            "approval.requested",
            json!({
                "run_id": run_id,
                "approval": approval,
            }),
        );
        if matches!(approval.status, ApprovalStatus::Approved) {
            state.emit_event(
                &project_id,
                "approval.updated",
                json!({
                    "run_id": run_id,
                    "approval": approval,
                }),
            );
        }
    }

    for agent_id in &orchestration.spawned_agents {
        state.emit_event(
            &project_id,
            "agent.spawn.requested",
            json!({
                "run_id": run_id,
                "agent_id": agent_id,
            }),
        );
        state.emit_event(
            &project_id,
            "agent.spawn.completed",
            json!({
                "run_id": run_id,
                "agent_id": agent_id,
            }),
        );
    }

    for message in &orchestration.messages {
        storage::append_chat_message(state.control_root.as_ref(), &project_id, message)?;
        state.emit_event(
            &project_id,
            "chat.message.created",
            json!({ "message": message }),
        );
        state.emit_event(
            &project_id,
            "chat.delivery.confirmed",
            json!({
                "run_id": run_id,
                "message_id": message.message_id,
                "author": message.author,
            }),
        );

        let auto_tasks = storage::create_tasks_from_ai_message(
            state.control_root.as_ref(),
            &project_id,
            &message.author,
            &message.text,
        )?;
        for task in auto_tasks {
            state.emit_event(
                &project_id,
                "task.created",
                json!({
                    "task": task,
                    "run_id": run_id,
                    "author": message.author,
                }),
            );
        }
    }

    state.emit_event(
        &project_id,
        "pixel.updated",
        json!({ "reason": "chat.turn", "run_id": run_id }),
    );
    state.emit_event(
        &project_id,
        "chat.turn.completed",
        json!({
            "run_id": run_id,
            "status": if orchestration.error.is_none() { "ok" } else { "degraded" }
        }),
    );

    let delivery_mode = if state.event_tx.receiver_count() > 0 {
        DeliveryMode::Hybrid
    } else {
        DeliveryMode::HttpFallback
    };

    let mut response_messages = Vec::with_capacity(orchestration.messages.len() + 1);
    response_messages.push(operator_msg);
    response_messages.extend(orchestration.messages.clone());

    Ok(Json(LiveTurnResponse {
        run_id,
        status: if orchestration.error.is_none() {
            "completed".to_string()
        } else {
            "degraded".to_string()
        },
        messages: response_messages,
        clems_summary: orchestration.clems_summary,
        delivery_mode,
        approval_requests: orchestration.approval_requests,
        spawned_agents_count: orchestration.spawned_agents.len(),
        model_usage: orchestration.model_usage,
        error: orchestration.error,
    }))
}

#[derive(Debug, Deserialize)]
struct ChatQuery {
    limit: Option<usize>,
    visibility: Option<String>,
}

#[derive(Debug, Deserialize)]
struct ApprovalQuery {
    status: Option<String>,
}

async fn chat_history(
    Path(project_id): Path<String>,
    State(state): State<AppState>,
    Query(query): Query<ChatQuery>,
) -> Result<Json<ChatHistoryResponse>, ApiError> {
    let limit = query.limit.unwrap_or(300).clamp(1, 5000);
    let visibility = parse_visibility_filter(query.visibility.as_deref())?;
    let messages = storage::read_chat(state.control_root.as_ref(), &project_id, limit, visibility)?;
    Ok(Json(ChatHistoryResponse {
        project_id,
        messages,
    }))
}

async fn reset_chat(
    Path(project_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<Value>, ApiError> {
    let (messages_cleared, approvals_cleared, runtime_rows_deleted) =
        storage::clear_chat_data(state.control_root.as_ref(), &project_id)?;

    state.emit_event(
        &project_id,
        "chat.reset.completed",
        json!({
            "messages_cleared": messages_cleared,
            "approvals_cleared": approvals_cleared,
            "runtime_rows_deleted": runtime_rows_deleted,
        }),
    );
    state.emit_event(
        &project_id,
        "pixel.updated",
        json!({
            "reason": "chat.reset.completed",
        }),
    );

    Ok(Json(json!({
        "ok": true,
        "messages_cleared": messages_cleared,
        "approvals_cleared": approvals_cleared,
        "runtime_rows_deleted": runtime_rows_deleted,
    })))
}

async fn chat_approvals(
    Path(project_id): Path<String>,
    State(state): State<AppState>,
    Query(query): Query<ApprovalQuery>,
) -> Result<Json<ChatApprovalsResponse>, ApiError> {
    let status = parse_approval_status(query.status.as_deref())?;
    let approvals = storage::list_approvals(state.control_root.as_ref(), &project_id, status)?;
    Ok(Json(ChatApprovalsResponse {
        project_id,
        approvals,
    }))
}

async fn approve_approval(
    Path((project_id, request_id)): Path<(String, String)>,
    State(state): State<AppState>,
    Json(payload): Json<ApprovalDecisionRequest>,
) -> Result<Json<Value>, ApiError> {
    let decided_by = normalize_decider(payload.decided_by)?;
    let approval = storage::update_approval_decision(
        state.control_root.as_ref(),
        &project_id,
        &request_id,
        ApprovalStatus::Approved,
        &decided_by,
        payload.note.clone(),
    )?
    .ok_or_else(|| ApiError::not_found(format!("unknown approval request {request_id}")))?;

    state.emit_event(
        &project_id,
        "approval.updated",
        json!({
            "approval": approval,
            "decision": "approved",
        }),
    );

    let mut spawned_agents = Vec::new();
    for idx in 0..2usize {
        let agent_id = format!("agent-{}", idx + 1);
        spawned_agents.push(agent_id.clone());
        state.emit_event(
            &project_id,
            "agent.spawn.requested",
            json!({
                "request_id": approval.request_id,
                "run_id": approval.run_id,
                "agent_id": agent_id,
                "section_tag": approval.section_tag,
            }),
        );

        let mut message = ChatMessage::new(
            agent_id.clone(),
            format!(
                "{} started on section '{}' after {} approval.",
                agent_id, approval.section_tag, decided_by
            ),
            None,
        )
        .with_visibility(MessageVisibility::Internal);
        message.metadata = json!({
            "run_id": approval.run_id,
            "request_id": approval.request_id,
            "kind": "approval_spawn",
        });
        storage::append_chat_message(state.control_root.as_ref(), &project_id, &message)?;
        state.emit_event(
            &project_id,
            "chat.message.created",
            json!({ "message": message.clone() }),
        );
        state.emit_event(
            &project_id,
            "chat.delivery.confirmed",
            json!({
                "run_id": approval.run_id,
                "message_id": message.message_id,
                "author": message.author,
            }),
        );

        state.emit_event(
            &project_id,
            "agent.spawn.completed",
            json!({
                "request_id": approval.request_id,
                "run_id": approval.run_id,
                "agent_id": agent_id,
                "section_tag": approval.section_tag,
            }),
        );
    }

    state.emit_event(
        &project_id,
        "pixel.updated",
        json!({ "reason": "approval.approved", "request_id": approval.request_id }),
    );

    Ok(Json(json!({
        "ok": true,
        "approval": approval,
        "spawned_agents_count": spawned_agents.len(),
        "spawned_agents": spawned_agents,
    })))
}

async fn reject_approval(
    Path((project_id, request_id)): Path<(String, String)>,
    State(state): State<AppState>,
    Json(payload): Json<ApprovalDecisionRequest>,
) -> Result<Json<Value>, ApiError> {
    let decided_by = normalize_decider(payload.decided_by)?;
    let approval = storage::update_approval_decision(
        state.control_root.as_ref(),
        &project_id,
        &request_id,
        ApprovalStatus::Rejected,
        &decided_by,
        payload.note.clone(),
    )?
    .ok_or_else(|| ApiError::not_found(format!("unknown approval request {request_id}")))?;

    state.emit_event(
        &project_id,
        "approval.updated",
        json!({
            "approval": approval,
            "decision": "rejected",
        }),
    );
    state.emit_event(
        &project_id,
        "pixel.updated",
        json!({ "reason": "approval.rejected", "request_id": request_id }),
    );

    Ok(Json(json!({
        "ok": true,
        "approval": approval,
    })))
}

async fn pixel_feed(
    Path(project_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<PixelFeedResponse>, ApiError> {
    let agents_map = storage::load_agents(state.control_root.as_ref(), &project_id)?;
    let alive_sessions = state.terminal_manager.sessions_for_project(&project_id);

    let mut statuses = Vec::new();
    let mut l0_count = 0usize;
    let mut l1_count = 0usize;
    let mut l2_count = 0usize;
    for (_, agent) in agents_map {
        let terminal = state
            .terminal_manager
            .session_for_agent(&project_id, &agent.agent_id);

        match agent.level {
            0 => l0_count += 1,
            1 => l1_count += 1,
            _ => l2_count += 1,
        }

        statuses.push(PixelAgentStatus {
            agent_id: agent.agent_id.clone(),
            name: agent.name,
            level: agent.level,
            lead_id: agent.lead_id,
            role: agent.role,
            chat_targetable: chat::is_directable_agent(&agent.agent_id),
            terminal_state: terminal
                .as_ref()
                .map(|s| s.state.clone())
                .unwrap_or_else(|| "offline".to_string()),
            terminal_session_id: terminal.map(|s| s.session_id),
        });
    }
    statuses.sort_by(|a, b| a.agent_id.cmp(&b.agent_id));

    Ok(Json(PixelFeedResponse {
        project_id,
        generated_at: Utc::now().to_rfc3339(),
        terminals_alive: alive_sessions.len(),
        queue_depth: 0,
        ws_connected: state.event_tx.receiver_count() > 0,
        l0_count,
        l1_count,
        l2_count,
        agents: statuses,
    }))
}

async fn get_tasks(
    Path(project_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<TasksResponse>, ApiError> {
    let tasks = storage::list_tasks(state.control_root.as_ref(), &project_id)?;
    Ok(Json(TasksResponse {
        project_id,
        generated_at: Utc::now().to_rfc3339(),
        tasks,
    }))
}

async fn post_task(
    Path(project_id): Path<String>,
    State(state): State<AppState>,
    Json(payload): Json<CreateTaskRequest>,
) -> Result<(StatusCode, Json<Value>), ApiError> {
    let title = payload.title.trim();
    if title.is_empty() {
        return Err(ApiError::bad_request("task title is required"));
    }

    let task = storage::create_task(
        state.control_root.as_ref(),
        &project_id,
        title,
        payload.owner.as_deref(),
        payload.phase.as_deref(),
        payload.status.unwrap_or_default(),
        payload.source.as_deref(),
        payload.objective.as_deref(),
        payload.done_definition.as_deref(),
        &payload.links,
        &payload.risks,
    )?;

    state.emit_event(
        &project_id,
        "task.created",
        json!({
            "task": task,
            "source": "operator",
        }),
    );

    Ok((
        StatusCode::CREATED,
        Json(json!({
            "ok": true,
            "task": task,
        })),
    ))
}

async fn patch_task(
    Path((project_id, task_id)): Path<(String, String)>,
    State(state): State<AppState>,
    Json(payload): Json<UpdateTaskRequest>,
) -> Result<Json<Value>, ApiError> {
    let patch = storage::TaskRecordPatch {
        title: payload.title,
        owner: payload.owner,
        phase: payload.phase,
        status: payload.status,
        source: payload.source,
        objective: payload.objective,
        done_definition: payload.done_definition,
        links: payload.links,
        risks: payload.risks,
    };

    let task = storage::update_task(state.control_root.as_ref(), &project_id, &task_id, &patch)?
        .ok_or_else(|| ApiError::not_found(format!("unknown task {task_id}")))?;

    state.emit_event(
        &project_id,
        "task.updated",
        json!({
            "task": task,
        }),
    );

    Ok(Json(json!({
        "ok": true,
        "task": task,
    })))
}

async fn get_layout(
    Path(project_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<Value>, ApiError> {
    let layout = storage::load_layout(state.control_root.as_ref(), &project_id)?;
    Ok(Json(layout))
}

async fn put_layout(
    Path(project_id): Path<String>,
    State(state): State<AppState>,
    Json(layout): Json<Value>,
) -> Result<Json<Value>, ApiError> {
    validate_layout(&layout)?;
    storage::save_layout(state.control_root.as_ref(), &project_id, &layout)?;

    state.emit_event(
        &project_id,
        "layout.updated",
        json!({ "layout": layout.clone() }),
    );
    state.emit_event(
        &project_id,
        "pixel.updated",
        json!({ "reason": "layout.updated" }),
    );

    Ok(Json(json!({ "ok": true })))
}

async fn ws_events(
    Path(project_id): Path<String>,
    State(state): State<AppState>,
    ws: WebSocketUpgrade,
) -> impl IntoResponse {
    ws.on_upgrade(move |socket| ws_loop(socket, state, project_id))
}

async fn ws_loop(mut socket: WebSocket, state: AppState, project_id: String) {
    let ready = WsEventEnvelope::new(
        project_id.clone(),
        "connection.ready",
        json!({ "status": "ok" }),
    );

    if send_ws_event(&mut socket, &ready).await.is_err() {
        return;
    }

    let mut rx = state.event_tx.subscribe();
    loop {
        tokio::select! {
            recv = rx.recv() => {
                match recv {
                    Ok(event) => {
                        if event.project_id == project_id && send_ws_event(&mut socket, &event).await.is_err() {
                            break;
                        }
                    }
                    Err(_) => break,
                }
            }
            incoming = socket.recv() => {
                match incoming {
                    Some(Ok(Message::Close(_))) | None => break,
                    Some(Ok(_)) => {}
                    Some(Err(_)) => break,
                }
            }
        }
    }
}

async fn send_ws_event(socket: &mut WebSocket, event: &WsEventEnvelope) -> Result<(), ()> {
    let payload = serde_json::to_string(event).map_err(|_| ())?;
    socket
        .send(Message::Text(payload.into()))
        .await
        .map_err(|_| ())
}

fn next_agent_id(agents: &HashMap<String, AgentRecord>) -> String {
    let mut max_n = 0u32;
    for key in agents.keys() {
        if let Some(n) = key
            .strip_prefix("agent-")
            .and_then(|rest| rest.parse::<u32>().ok())
        {
            max_n = max_n.max(n);
        }
    }
    format!("agent-{}", max_n + 1)
}

fn dedup(input: Vec<String>) -> Vec<String> {
    let mut seen = HashSet::new();
    let mut out = Vec::new();
    for item in input {
        let normalized = item.to_lowercase();
        if seen.insert(normalized.clone()) {
            out.push(normalized);
        }
    }
    out
}

fn emit_clems_online_ack_if_needed(
    state: &AppState,
    project_id: &str,
    agent_id: &str,
    session: &TerminalSession,
) -> Result<(), ApiError> {
    if agent_id != "clems" || session.state != "running" {
        return Ok(());
    }
    if !state.mark_clems_session_ack(&session.session_id) {
        return Ok(());
    }

    let mut message = ChatMessage::new("clems", "clems online, pret pour direct/conceal.", None)
        .with_visibility(MessageVisibility::Internal);
    message.metadata = json!({
        "kind": "terminal_online_ack",
        "agent_id": "clems",
        "session_id": session.session_id,
    });
    storage::append_chat_message(state.control_root.as_ref(), project_id, &message)?;
    state.emit_event(
        project_id,
        "chat.message.created",
        json!({ "message": message.clone() }),
    );
    state.emit_event(
        project_id,
        "chat.delivery.confirmed",
        json!({
            "message_id": message.message_id,
            "author": message.author,
            "session_id": session.session_id,
        }),
    );
    Ok(())
}

fn parse_approval_status(raw: Option<&str>) -> Result<Option<ApprovalStatus>, ApiError> {
    let Some(raw) = raw else {
        return Ok(None);
    };

    let value = raw.trim().to_lowercase();
    let status = match value.as_str() {
        "pending" => ApprovalStatus::Pending,
        "approved" => ApprovalStatus::Approved,
        "rejected" => ApprovalStatus::Rejected,
        _ => {
            return Err(ApiError::bad_request(
                "invalid approval status filter, expected pending|approved|rejected",
            ));
        }
    };
    Ok(Some(status))
}

fn parse_visibility_filter(raw: Option<&str>) -> Result<Option<MessageVisibility>, ApiError> {
    let Some(raw) = raw else {
        return Ok(Some(MessageVisibility::Operator));
    };

    let value = raw.trim().to_lowercase();
    match value.as_str() {
        "operator" => Ok(Some(MessageVisibility::Operator)),
        "all" => Ok(None),
        _ => Err(ApiError::bad_request(
            "invalid visibility filter, expected operator|all",
        )),
    }
}

fn normalize_decider(decided_by: Option<String>) -> Result<String, ApiError> {
    let normalized = decided_by
        .unwrap_or_else(|| "olivier".to_string())
        .trim()
        .to_lowercase();
    if normalized == "olivier" || normalized == "clems" {
        return Ok(normalized);
    }
    Err(ApiError::bad_request("decided_by must be olivier or clems"))
}

fn default_agent_profile(
    agent_id: &str,
) -> (String, &'static str, u8, Option<String>, &'static str) {
    match agent_id {
        "clems" => ("Clems".to_string(), "CDX", 0, None, "orchestrator"),
        "victor" => (
            "Victor".to_string(),
            "CDX",
            1,
            Some("clems".to_string()),
            "backend_lead",
        ),
        "leo" => (
            "Leo".to_string(),
            "AG",
            1,
            Some("clems".to_string()),
            "ui_lead",
        ),
        "nova" => (
            "Nova".to_string(),
            "CDX",
            1,
            Some("clems".to_string()),
            "creative_science_lead",
        ),
        "vulgarisation" => (
            "Vulgarisation".to_string(),
            "AG",
            1,
            Some("clems".to_string()),
            "vulgarisation_lead",
        ),
        _ => (
            agent_id.to_string(),
            "CDX",
            2,
            Some("victor".to_string()),
            "specialist",
        ),
    }
}

async fn get_llm_profile(
    Path(project_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<LlmProfileResponse>, ApiError> {
    let profile = storage::load_llm_profile(state.control_root.as_ref(), &project_id)?;

    Ok(Json(LlmProfileResponse {
        project_id,
        profile,
    }))
}

async fn put_llm_profile(
    Path(project_id): Path<String>,
    State(state): State<AppState>,
    Json(payload): Json<UpdateLlmProfileRequest>,
) -> Result<Json<LlmProfileResponse>, ApiError> {
    let mut profile = storage::load_llm_profile(state.control_root.as_ref(), &project_id)?;

    if let Some(model) = payload.voice_stt_model {
        profile.voice_stt_model = model;
    }
    if let Some(model) = payload.clems_model {
        profile.clems_model = model;
    }
    if let Some(catalog) = payload.clems_catalog {
        profile.clems_catalog = catalog;
    }
    if let Some(l1_models) = payload.l1_models {
        profile.l1_models = l1_models;
    }
    if let Some(catalog) = payload.l1_catalog {
        profile.l1_catalog = catalog;
    }
    if let Some(model) = payload.l2_default_model {
        profile.l2_default_model = model;
    }
    if let Some(pool) = payload.l2_pool {
        profile.l2_pool = pool;
    }
    if let Some(mode) = payload.l2_selection_mode {
        profile.l2_selection_mode = mode;
    }
    if let Some(enabled) = payload.stream_enabled {
        profile.stream_enabled = enabled;
    }
    if let Some(model) = payload.default_model {
        profile.default_model = Some(model);
    }
    if let Some(fallback) = payload.fallback_model {
        profile.fallback_model = Some(fallback);
    }
    if let Some(model) = payload.l1_model {
        profile.l1_model = Some(model);
    }
    if let Some(model) = payload.l2_scene_model {
        profile.l2_scene_model = Some(model);
    }
    if let Some(spawn_max) = payload.lfm_spawn_max {
        profile.lfm_spawn_max = Some(spawn_max);
    }
    if let Some(tokens) = payload.max_tokens {
        profile.max_tokens = Some(tokens);
    }
    if let Some(temp) = payload.temperature {
        profile.temperature = Some(temp);
    }

    let profile = storage::save_llm_profile(state.control_root.as_ref(), &project_id, &profile)?;

    Ok(Json(LlmProfileResponse {
        project_id,
        profile,
    }))
}

fn validate_layout(layout: &Value) -> Result<(), ApiError> {
    let obj = layout
        .as_object()
        .ok_or_else(|| ApiError::bad_request("layout must be an object"))?;

    for required in ["version", "cols", "rows", "tiles", "furniture"] {
        if !obj.contains_key(required) {
            return Err(ApiError::bad_request(format!(
                "missing layout field: {required}"
            )));
        }
    }

    Ok(())
}

#[derive(Debug)]
struct ApiError {
    status: StatusCode,
    message: String,
}

impl ApiError {
    fn bad_request(message: impl Into<String>) -> Self {
        Self {
            status: StatusCode::BAD_REQUEST,
            message: message.into(),
        }
    }

    fn not_found(message: impl Into<String>) -> Self {
        Self {
            status: StatusCode::NOT_FOUND,
            message: message.into(),
        }
    }
}

impl<E> From<E> for ApiError
where
    E: Into<anyhow::Error>,
{
    fn from(error: E) -> Self {
        let error: anyhow::Error = error.into();
        Self {
            status: StatusCode::INTERNAL_SERVER_ERROR,
            message: error.to_string(),
        }
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        (
            self.status,
            Json(json!({
                "error": self.message,
            })),
        )
            .into_response()
    }
}

async fn post_roadmap_clems_draft(
    Path(_project_id): Path<String>,
    State(_state): State<AppState>,
    Json(payload): Json<RoadmapDraftRequest>,
) -> Result<Json<RoadmapDraftResponse>, ApiError> {
    use chrono::Utc;

    let run_id = format!("rmp_{}", Uuid::new_v4().simple());

    let system_prompt = "You are @clems, L0 orchestrator. Generate a structured roadmap draft in JSON format with sections: summary, phases, milestones, risks, and next_actions. Respond with valid JSON only.";
    let user_prompt = format!("Context: {}\n\nPrompt: {}", payload.context, payload.prompt);

    let result =
        openrouter::chat_completion("openai/gpt-4o-mini", system_prompt, &user_prompt).await;

    if let Some(err) = &result.error {
        return Err(ApiError {
            status: StatusCode::INTERNAL_SERVER_ERROR,
            message: format!("openrouter failed: {}", err),
        });
    }

    let draft_value = serde_json::from_str(&result.text).unwrap_or_else(|_| {
        json!({
            "raw_text": result.text,
            "generated_at": Utc::now().to_rfc3339(),
            "prompt": payload.prompt
        })
    });

    Ok(Json(RoadmapDraftResponse {
        run_id,
        draft: draft_value,
        model_usage: result.usage,
    }))
}

#[cfg(test)]
mod tests {
    use super::{default_agent_profile, next_agent_id};
    use crate::models::AgentRecord;
    use std::collections::HashMap;

    #[test]
    fn agent_sequence_is_incremental() {
        let mut map = HashMap::new();
        map.insert(
            "agent-4".to_string(),
            AgentRecord {
                agent_id: "agent-4".to_string(),
                name: "agent-4".to_string(),
                engine: "CDX".to_string(),
                platform: "x".to_string(),
                level: 2,
                lead_id: None,
                role: "specialist".to_string(),
                skills: Vec::new(),
            },
        );
        assert_eq!(next_agent_id(&map), "agent-5");
    }

    #[test]
    fn default_profiles_match_l0_l1_l2_contract() {
        assert_eq!(default_agent_profile("clems").2, 0);
        assert_eq!(default_agent_profile("victor").2, 1);
        assert_eq!(default_agent_profile("leo").2, 1);
        assert_eq!(default_agent_profile("nova").2, 1);
        assert_eq!(default_agent_profile("agent-77").2, 2);
    }
}
