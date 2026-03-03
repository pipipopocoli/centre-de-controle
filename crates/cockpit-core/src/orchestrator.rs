use std::{env, path::Path};

use anyhow::Result;
use chrono::Utc;
use serde_json::{Value, json};
use uuid::Uuid;

use crate::{
    chat,
    models::{
        ApprovalRequest, ApprovalStatus, ChatMessage, ChatMode, ExecutionMode, LiveTurnRequest,
        MessageVisibility,
    },
    openrouter,
    storage,
};

const DEFAULT_MODEL_CLEMS: &str = "openai/gpt-4o-mini";
const DEFAULT_MODEL_L1: &str = "liquid/lfm-2.5-1.2b-thinking:free";
const DEFAULT_MODEL_L2: &str = "arcee-ai/trinity-large-preview:free";
const OVERLAP_WINDOW_MINUTES: i64 = 30;

#[derive(Debug)]
pub struct OrchestrationResult {
    pub messages: Vec<ChatMessage>,
    pub clems_summary: String,
    pub approval_requests: Vec<ApprovalRequest>,
    pub spawned_agents: Vec<String>,
    pub model_usage: Value,
    pub error: Option<String>,
}

fn model_for_key(key: &str, fallback: &str) -> String {
    env::var(key).unwrap_or_else(|_| fallback.to_string())
}

fn model_for_agent(agent_id: &str) -> String {
    if agent_id == "clems" {
        model_for_key("COCKPIT_MODEL_CLEMS", DEFAULT_MODEL_CLEMS)
    } else if agent_id.starts_with("agent-") {
        model_for_key("COCKPIT_MODEL_L2", DEFAULT_MODEL_L2)
    } else {
        model_for_key("COCKPIT_MODEL_L1", DEFAULT_MODEL_L1)
    }
}

fn actor_prompt(agent_id: &str, mode: &ChatMode) -> String {
    let mode_hint = match mode {
        ChatMode::Direct => "direct",
        ChatMode::ConcealRoom => "conceal_room",
    };
    match agent_id {
        "clems" => format!(
            "You are @clems, Cockpit L0 orchestrator. mode={mode_hint}. Reply in concise french, ascii only, action oriented."
        ),
        "victor" => format!(
            "You are @victor, backend lead L1. mode={mode_hint}. Reply in concise french with implementation actions."
        ),
        "leo" => format!(
            "You are @leo, UI lead L1. mode={mode_hint}. Reply in concise french with UX and frontend actions."
        ),
        "nova" => format!(
            "You are @nova, creative science lead L1. mode={mode_hint}. Reply concise with evidence path and decision tag."
        ),
        "vulgarisation" => format!(
            "You are @vulgarisation, simplification lead L1. mode={mode_hint}. Reply in simple french for operator."
        ),
        _ => format!(
            "You are @{agent_id}, specialist L2. mode={mode_hint}. Reply concise with execution next step."
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
    author: &str,
    mode: ChatMode,
    user_text: &str,
    context_ref: Option<&Value>,
    usage_calls: &mut Vec<Value>,
) -> String {
    let model = model_for_agent(author);
    let system = actor_prompt(author, &mode);
    let mut user_prompt = format!("Operator message:\n{}\n", user_text.trim());
    if let Some(context_ref) = context_ref {
        user_prompt.push_str(&format!("Context ref:\n{}\n", context_ref));
    }
    let result = openrouter::chat_completion(&model, &system, &user_prompt).await;
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
    user_text: &str,
    context_snippets: &[String],
    usage_calls: &mut Vec<Value>,
) -> String {
    let model = model_for_agent("clems");
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
    let result = openrouter::chat_completion(&model, system, &joined).await;
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
            let target = chat::resolve_direct_target(mentions);
            let target_reply = llm_reply(
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
                let summary_text = clems_summary(&payload.text, std::slice::from_ref(&target_reply), &mut usage_calls).await;
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
            let targets = chat::conceal_targets(mentions);
            let mut snippets = Vec::new();
            for target in &targets {
                let text = llm_reply(
                    target,
                    ChatMode::ConcealRoom,
                    &payload.text,
                    payload.context_ref.as_ref(),
                    &mut usage_calls,
                )
                .await;
                snippets.push(format!("@{} {}", target, text));
                messages.push(message_with_meta(
                    target,
                    text,
                    thread_id.clone(),
                    run_id,
                    ChatMode::ConcealRoom,
                    execution_mode.clone(),
                    "conceal_reply",
                    MessageVisibility::Internal,
                ));
            }

            let summary = clems_summary(&payload.text, &snippets, &mut usage_calls).await;
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

                let overlap =
                    storage::has_section_overlap_risk(control_root, project_id, &section_tag, OVERLAP_WINDOW_MINUTES)?;
                if !overlap {
                    approval.status = ApprovalStatus::Approved;
                    approval.decided_by = Some("clems".to_string());
                    approval.decided_at = Some(Utc::now().to_rfc3339());
                    approval.decision_note = Some("auto-approved: free models and no overlap risk".to_string());
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
                            &agent_id,
                            ChatMode::ConcealRoom,
                            &format!("Spawned for section {}. Task: {}", section_tag, payload.text),
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

            if usage_calls.iter().any(|call| call.get("status") != Some(&Value::String("ok".to_string()))) {
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
