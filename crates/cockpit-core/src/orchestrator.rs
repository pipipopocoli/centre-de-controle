use std::path::Path;

use anyhow::Result;
use chrono::Utc;
use serde_json::{Value, json};
use tokio::task::JoinSet;
use tokio::time::{Duration, timeout};
use uuid::Uuid;

use crate::{
    chat,
    models::{
        ApprovalRequest, ApprovalStatus, ChatMessage, ChatMode, ExecutionMode, LiveTurnRequest,
        LlmProfile, MessageVisibility,
    },
    openrouter, storage,
};

const OVERLAP_WINDOW_MINUTES: i64 = 30;
const LLM_CALL_TIMEOUT_SECONDS: u64 = 5;

// Hierarchical delegation metadata and policy guards
// ISSUE-W20R-A9-004: L0->L1/L1->L2 enforcement
const L0_AGENTS: &[&str] = &["clems"];
const L1_AGENTS: &[&str] = &["victor", "leo", "nova", "vulgarisation"];
const L2_PREFIX: &str = "agent-";

/// Returns the delegation level (0, 1, or 2) for an agent ID
pub fn delegation_level(agent_id: &str) -> u8 {
    if L0_AGENTS.contains(&agent_id) {
        0
    } else if L1_AGENTS.contains(&agent_id) {
        1
    } else if agent_id.starts_with(L2_PREFIX) {
        2
    } else {
        2 // Unknown agents default to L2 specialist
    }
}

/// Validates delegation per hierarchical policy: L0->L1/L2 OK, L1->L2 OK, no lateral/upward
pub fn validate_delegation(from: &str, to: &str) -> Result<(), String> {
    let from_level = delegation_level(from);
    let to_level = delegation_level(to);

    match (from_level, to_level) {
        (0, 1) => Ok(()), // L0 -> L1 OK
        (0, 2) => Ok(()), // L0 -> L2 OK
        (1, 2) => Ok(()), // L1 -> L2 OK
        (0, 0) => Err(format!("L0 cannot delegate to L0: {} -> {}", from, to)),
        (1, 0) => Err(format!("L1 cannot delegate to L0: {} -> {}", from, to)),
        (1, 1) => Err(format!("L1 cannot delegate to L1: {} -> {}", from, to)),
        (2, _) => Err(format!("L2 cannot delegate: {} -> {}", from, to)),
        _ => Err(format!(
            "Invalid delegation: {} (L{}) -> {} (L{})",
            from, from_level, to, to_level
        )),
    }
}

#[derive(Debug)]
pub struct OrchestrationResult {
    pub messages: Vec<ChatMessage>,
    pub clems_summary: String,
    pub approval_requests: Vec<ApprovalRequest>,
    pub spawned_agents: Vec<String>,
    pub model_usage: Value,
    pub error: Option<String>,
}

fn model_for_agent(profile: &LlmProfile, agent_id: &str) -> String {
    if agent_id == "clems" {
        return profile.clems_model.clone();
    }
    if agent_id.starts_with("agent-") {
        return profile.l2_default_model.clone();
    }
    profile
        .l1_models
        .get(agent_id)
        .cloned()
        .unwrap_or_else(|| profile.clems_model.clone())
}

fn actor_prompt(agent_id: &str, mode: &ChatMode) -> String {
    let mode_hint = match mode {
        ChatMode::Direct => "direct",
        ChatMode::ConcealRoom => "conceal_room",
    };
    match agent_id {
        "clems" => format!(
            "You are @clems, Cockpit L0 orchestrator. mode={mode_hint}. Reply in concise french, ascii only, action oriented. If operator asks for a task list or roadmap, append a TASKS: block with bullet lines '- title | owner=agent-id | done=definition'."
        ),
        "victor" => format!(
            "You are @victor, backend lead L1. mode={mode_hint}. Reply in concise french with implementation actions. If you are defining official tasks, append a TASKS: block with bullet lines '- title | owner=agent-id | done=definition'."
        ),
        "leo" => format!(
            "You are @leo, UI lead L1. mode={mode_hint}. Reply in concise french with UX and frontend actions. If you are defining official tasks, append a TASKS: block with bullet lines '- title | owner=agent-id | done=definition'."
        ),
        "nova" => format!(
            "You are @nova, creative science lead L1. mode={mode_hint}. Reply concise with evidence path and decision tag. If you define official tasks, append a TASKS: block with bullet lines '- title | owner=agent-id | done=definition'."
        ),
        "vulgarisation" => format!(
            "You are @vulgarisation, simplification lead L1. mode={mode_hint}. Reply in simple french for operator. If you define official tasks, append a TASKS: block with bullet lines '- title | owner=agent-id | done=definition'."
        ),
        _ => format!(
            "You are @{agent_id}, specialist L2. mode={mode_hint}. Reply concise with execution next step. Never create roadmap, strategy, or TASKS block."
        ),
    }
}

fn mode_to_str(mode: &ChatMode) -> &'static str {
    match mode {
        ChatMode::Direct => "direct",
        ChatMode::ConcealRoom => "conceal_room",
    }
}

fn execution_mode_to_str(mode: &ExecutionMode) -> &'static str {
    match mode {
        ExecutionMode::Chat => "chat",
        ExecutionMode::Scene => "scene",
    }
}

fn message_with_meta(
    author: &str,
    text: String,
    thread_id: Option<String>,
    run_id: &str,
    chat_mode: ChatMode,
    execution_mode: ExecutionMode,
    kind: &str,
    visibility: MessageVisibility,
) -> ChatMessage {
    let mut message = ChatMessage::new(author, text, thread_id).with_visibility(visibility);
    message.metadata = json!({
        "run_id": run_id,
        "mode": mode_to_str(&chat_mode),
        "execution_mode": execution_mode_to_str(&execution_mode),
        "kind": kind,
    });
    message
}

fn should_request_l2(payload: &LiveTurnRequest, l1_outputs: &[String]) -> bool {
    if matches!(payload.execution_mode, ExecutionMode::Scene) {
        return true;
    }
    let text = payload.text.to_lowercase();
    let mut combined = text;
    for out in l1_outputs {
        combined.push(' ');
        combined.push_str(&out.to_lowercase());
    }
    let cues = [
        "l2",
        "specialist",
        "agent-",
        "scene",
        "decompose",
        "breakdown",
        "parallel",
    ];
    cues.iter().any(|cue| combined.contains(cue))
}

async fn llm_reply(
    profile: &LlmProfile,
    author: &str,
    mode: ChatMode,
    user_text: &str,
    context_ref: Option<&Value>,
    usage_calls: &mut Vec<Value>,
) -> String {
    let context_owned = context_ref.cloned();
    let model = model_for_agent(profile, author);
    let system = actor_prompt(author, &mode);
    let mut user_prompt = format!("Operator message:\n{}\n", user_text.trim());
    if let Some(context_ref) = context_ref {
        user_prompt.push_str(&format!("Context ref:\n{}\n", context_ref));
    }
    let result = match timeout(
        Duration::from_secs(LLM_CALL_TIMEOUT_SECONDS),
        openrouter::chat_completion(&model, &system, &user_prompt),
    )
    .await
    {
        Ok(result) => result,
        Err(_) => {
            let fallback = chat::generate_agent_reply(author, user_text, mode.clone());
            usage_calls.push(json!({
                "agent_id": author,
                "model": model,
                "status": "failed",
                "usage": json!({}),
                "error": format!("openrouter_timeout_after_{}s", LLM_CALL_TIMEOUT_SECONDS),
                "context_ref": context_owned,
            }));
            return fallback;
        }
    };
    usage_calls.push(json!({
        "agent_id": author,
        "model": result.model,
        "status": result.status,
        "usage": result.usage,
        "error": result.error,
    }));

    if result.status == "ok" && !result.text.trim().is_empty() {
        return result.text.trim().to_string();
    }
    chat::generate_agent_reply(author, user_text, mode)
}

async fn clems_summary(
    profile: &LlmProfile,
    user_text: &str,
    context_snippets: &[String],
    usage_calls: &mut Vec<Value>,
) -> String {
    let model = model_for_agent(profile, "clems");
    let system = "You are @clems. Create a short synthesis in french with next immediate action.";
    let joined = if context_snippets.is_empty() {
        user_text.to_string()
    } else {
        format!(
            "Operator:\n{}\n\nContributions:\n- {}",
            user_text.trim(),
            context_snippets.join("\n- ")
        )
    };
    let result = match timeout(
        Duration::from_secs(LLM_CALL_TIMEOUT_SECONDS),
        openrouter::chat_completion(&model, system, &joined),
    )
    .await
    {
        Ok(result) => result,
        Err(_) => {
            usage_calls.push(json!({
                "agent_id": "clems",
                "model": model,
                "status": "failed",
                "usage": json!({}),
                "error": format!("openrouter_timeout_after_{}s", LLM_CALL_TIMEOUT_SECONDS),
                "purpose": "summary",
            }));
            return chat::clems_summary(user_text, context_snippets.len().max(1));
        }
    };
    usage_calls.push(json!({
        "agent_id": "clems",
        "model": result.model,
        "status": result.status,
        "usage": result.usage,
        "error": result.error,
        "purpose": "summary",
    }));

    if result.status == "ok" && !result.text.trim().is_empty() {
        return result.text.trim().to_string();
    }
    chat::clems_summary(user_text, context_snippets.len().max(1))
}

pub async fn run_turn(
    control_root: &Path,
    project_id: &str,
    run_id: &str,
    payload: &LiveTurnRequest,
    mentions: &[String],
) -> Result<OrchestrationResult> {
    let profile = storage::load_llm_profile(control_root, project_id)?;
    let mut usage_calls = Vec::new();
    let mut messages = Vec::new();
    let mut approval_requests = Vec::new();
    let mut spawned_agents = Vec::new();
    let mut error: Option<String> = None;
    let chat_mode = payload.chat_mode.clone();
    let execution_mode = payload.execution_mode.clone();
    let thread_id = payload.thread_id.clone();

    match chat_mode {
        ChatMode::Direct => {
            let target = chat::resolve_direct_target(payload.target_agent_id.as_deref(), mentions);
            let target_reply = llm_reply(
                &profile,
                &target,
                ChatMode::Direct,
                &payload.text,
                payload.context_ref.as_ref(),
                &mut usage_calls,
            )
            .await;
            let target_msg = message_with_meta(
                &target,
                target_reply.clone(),
                thread_id.clone(),
                run_id,
                ChatMode::Direct,
                execution_mode.clone(),
                "direct_reply",
                MessageVisibility::Operator,
            );
            messages.push(target_msg);

            let summary = if target == "clems" {
                target_reply
            } else {
                let summary_text = clems_summary(
                    &profile,
                    &payload.text,
                    std::slice::from_ref(&target_reply),
                    &mut usage_calls,
                )
                .await;
                let summary_msg = message_with_meta(
                    "clems",
                    summary_text.clone(),
                    thread_id.clone(),
                    run_id,
                    ChatMode::Direct,
                    execution_mode,
                    "direct_summary",
                    MessageVisibility::Internal,
                );
                messages.push(summary_msg);
                summary_text
            };

            return Ok(OrchestrationResult {
                messages,
                clems_summary: summary,
                approval_requests,
                spawned_agents,
                model_usage: json!({ "calls": usage_calls }),
                error,
            });
        }
        ChatMode::ConcealRoom => {
            let targets = chat::conceal_targets_from_context(payload.context_ref.as_ref(), mentions);
            let mut snippets = Vec::new();
            if !targets.is_empty() {
                let mut join_set = JoinSet::new();
                for target in &targets {
                    let profile = profile.clone();
                    let target_id = target.clone();
                    let user_text = payload.text.clone();
                    let context_ref = payload.context_ref.clone();
                    join_set.spawn(async move {
                        let model = model_for_agent(&profile, &target_id);
                        let system = actor_prompt(&target_id, &ChatMode::ConcealRoom);
                        let mut user_prompt = format!("Operator message:\n{}\n", user_text.trim());
                        if let Some(context_ref) = context_ref.as_ref() {
                            user_prompt.push_str(&format!("Context ref:\n{}\n", context_ref));
                        }
                        let result = match timeout(
                            Duration::from_secs(LLM_CALL_TIMEOUT_SECONDS),
                            openrouter::chat_completion(&model, &system, &user_prompt),
                        )
                        .await
                        {
                            Ok(result) => result,
                            Err(_) => {
                                return (
                                    target_id.clone(),
                                    chat::generate_agent_reply(
                                        &target_id,
                                        &user_text,
                                        ChatMode::ConcealRoom,
                                    ),
                                    json!({
                                        "agent_id": target_id,
                                        "model": model,
                                        "status": "failed",
                                        "usage": json!({}),
                                        "error": format!("openrouter_timeout_after_{}s", LLM_CALL_TIMEOUT_SECONDS),
                                    }),
                                );
                            }
                        };
                        let text = if result.status == "ok" && !result.text.trim().is_empty() {
                            result.text.trim().to_string()
                        } else {
                            chat::generate_agent_reply(
                                &target_id,
                                &user_text,
                                ChatMode::ConcealRoom,
                            )
                        };
                        (
                            target_id.clone(),
                            text,
                            json!({
                                "agent_id": target_id,
                                "model": result.model,
                                "status": result.status,
                                "usage": result.usage,
                                "error": result.error,
                            }),
                        )
                    });
                }

                let mut target_outputs = Vec::new();
                while let Some(joined) = join_set.join_next().await {
                    if let Ok((target, text, usage)) = joined {
                        target_outputs.push((target, text, usage));
                    }
                }
                target_outputs.sort_by_key(|(target, _, _)| {
                    targets
                        .iter()
                        .position(|candidate| candidate == target)
                        .unwrap_or(usize::MAX)
                });

                for (target, text, usage) in target_outputs {
                    usage_calls.push(usage);
                    snippets.push(format!("@{} {}", target, text));
                    messages.push(message_with_meta(
                        &target,
                        text,
                        thread_id.clone(),
                        run_id,
                        ChatMode::ConcealRoom,
                        execution_mode.clone(),
                        "conceal_reply",
                        MessageVisibility::Internal,
                    ));
                }
            }

            let summary = clems_summary(&profile, &payload.text, &snippets, &mut usage_calls).await;
            messages.push(message_with_meta(
                "clems",
                summary.clone(),
                thread_id.clone(),
                run_id,
                ChatMode::ConcealRoom,
                execution_mode.clone(),
                "conceal_summary",
                MessageVisibility::Operator,
            ));

            if should_request_l2(payload, &snippets) {
                let section_tag = payload
                    .section_tag
                    .clone()
                    .unwrap_or_else(|| "general".to_string());
                let requester = targets
                    .first()
                    .cloned()
                    .unwrap_or_else(|| "victor".to_string());
                let mut approval = ApprovalRequest {
                    request_id: format!("apr_{}", Uuid::new_v4().simple()),
                    run_id: run_id.to_string(),
                    requester,
                    section_tag: section_tag.clone(),
                    reason: "L1 asks Clems to trigger L2 specialists for this section.".to_string(),
                    status: ApprovalStatus::Pending,
                    requested_at: Utc::now().to_rfc3339(),
                    decided_by: None,
                    decided_at: None,
                    decision_note: None,
                };

                let overlap = storage::has_section_overlap_risk(
                    control_root,
                    project_id,
                    &section_tag,
                    OVERLAP_WINDOW_MINUTES,
                )?;
                if !overlap {
                    approval.status = ApprovalStatus::Approved;
                    approval.decided_by = Some("clems".to_string());
                    approval.decided_at = Some(Utc::now().to_rfc3339());
                    approval.decision_note =
                        Some("auto-approved: free models and no overlap risk".to_string());
                }

                storage::append_approval_request(control_root, project_id, &approval)?;
                approval_requests.push(approval.clone());

                if matches!(approval.status, ApprovalStatus::Pending) {
                    messages.push(message_with_meta(
                        "clems",
                        format!(
                            "L2 request pending on section '{}'. @olivier approve or reject this request.",
                            section_tag
                        ),
                        thread_id.clone(),
                        run_id,
                        ChatMode::ConcealRoom,
                        execution_mode.clone(),
                        "approval_pending",
                        MessageVisibility::Internal,
                    ));
                } else {
                    let spawn_count = if matches!(payload.execution_mode, ExecutionMode::Scene) {
                        3usize
                    } else {
                        2usize
                    };
                    for idx in 0..spawn_count {
                        let agent_id = format!("agent-{}", idx + 1);
                        spawned_agents.push(agent_id.clone());
                        let spawn_text = llm_reply(
                            &profile,
                            &agent_id,
                            ChatMode::ConcealRoom,
                            &format!(
                                "Spawned for section {}. Task: {}",
                                section_tag, payload.text
                            ),
                            payload.context_ref.as_ref(),
                            &mut usage_calls,
                        )
                        .await;
                        messages.push(message_with_meta(
                            &agent_id,
                            spawn_text,
                            thread_id.clone(),
                            run_id,
                            ChatMode::ConcealRoom,
                            execution_mode.clone(),
                            "l2_spawn_output",
                            MessageVisibility::Internal,
                        ));
                    }
                }
            }

            if usage_calls
                .iter()
                .any(|call| call.get("status") != Some(&Value::String("ok".to_string())))
            {
                error = Some("some_llm_calls_failed_using_fallback".to_string());
            }

            return Ok(OrchestrationResult {
                messages,
                clems_summary: summary,
                approval_requests,
                spawned_agents,
                model_usage: json!({ "calls": usage_calls }),
                error,
            });
        }
    }
}
