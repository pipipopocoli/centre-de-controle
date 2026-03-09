use std::path::Path;

use anyhow::Result;
use chrono::Utc;
use serde_json::{Value, json};
use tokio::task::JoinSet;
use tokio::time::{Duration, sleep, timeout};
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
const ROOM_AGENT_LLM_TIMEOUT_SECONDS: u64 = 12;
const ROOM_SUMMARY_TIMEOUT_SECONDS: u64 = 18;
const DIRECT_LLM_TIMEOUT_SECONDS: u64 = 12;
const DIRECT_LLM_RETRY_DELAY_SECONDS: u64 = 1;
const DIRECT_RESCUE_TIMEOUT_SECONDS: u64 = 8;
const ROOM_SUMMARY_RETRY_DELAY_SECONDS: u64 = 2;
const DIRECT_CHAT_MAX_TOKENS: u32 = 220;
const DIRECT_CHAT_TEMPERATURE: f32 = 0.25;
const DIRECT_RESCUE_MAX_TOKENS: u32 = 120;
const DIRECT_RESCUE_TEMPERATURE: f32 = 0.15;
const DIRECT_RESCUE_MODEL: &str = "anthropic/claude-sonnet-4.6";

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

#[derive(Debug, Clone)]
struct AgentReply {
    text: String,
    reply_source: &'static str,
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
    match mode {
        ChatMode::Direct => match agent_id {
            "clems" => "You are @clems, Cockpit L0 orchestrator in a direct operator chat. Reply in natural french, ascii only, human, and genuinely conversational. Answer with 1 to 3 short sentences max. Final answer only. No chain of thought. Suggest next actions only when helpful. Do not emit a TASKS block unless the operator explicitly asks for official tasks.".to_string(),
            "victor" => "You are @victor, backend lead L1 in a direct operator chat. Reply in natural french, ascii only, conversational, and concrete. Answer with 1 to 3 short sentences max. Final answer only. Do not emit a TASKS block unless the operator explicitly asks for official tasks.".to_string(),
            "leo" => "You are @leo, UI lead L1 in a direct operator chat. Reply in natural french, ascii only, conversational, and concrete. Answer with 1 to 3 short sentences max. Final answer only. Do not emit a TASKS block unless the operator explicitly asks for official tasks.".to_string(),
            "nova" => "You are @nova, creative science lead L1 in a direct operator chat. Reply in natural french, ascii only, evidence aware, and conversational. Answer with 1 to 3 short sentences max. Final answer only. Do not emit a TASKS block unless the operator explicitly asks for official tasks.".to_string(),
            "vulgarisation" => "You are @vulgarisation, simplification lead L1 in a direct operator chat. Reply in simple french, ascii only, very clear, and conversational. Answer with 1 to 3 short sentences max. Final answer only. Do not emit a TASKS block unless the operator explicitly asks for official tasks.".to_string(),
            _ => format!(
                "You are @{agent_id}, specialist L2 in a direct operator chat. Reply in natural french, ascii only, execution focused, and conversational. Answer with 1 to 3 short sentences max. Final answer only. Do not create roadmap, strategy, or TASKS blocks unless explicitly asked."
            ),
        },
        ChatMode::ConcealRoom => {
            let mode_hint = "conceal_room";
            match agent_id {
                "clems" => format!(
                    "You are @clems, Cockpit L0 orchestrator. mode={mode_hint}. Reply in concise french, ascii only, action oriented. Keep the visible answer short: 2 to 4 short lines max. Final answer only. If operator asks for a task list or roadmap, append a TASKS: block with bullet lines '- title | owner=agent-id | done=definition'."
                ),
                "victor" => format!(
                    "You are @victor, backend lead L1. mode={mode_hint}. Reply in concise french with implementation actions. Keep it under 80 words. Final answer only. If you are defining official tasks, append a TASKS: block with bullet lines '- title | owner=agent-id | done=definition'."
                ),
                "leo" => format!(
                    "You are @leo, UI lead L1. mode={mode_hint}. Reply in concise french with UX and frontend actions. Keep it under 80 words. Final answer only. If you are defining official tasks, append a TASKS: block with bullet lines '- title | owner=agent-id | done=definition'."
                ),
                "nova" => format!(
                    "You are @nova, creative science lead L1. mode={mode_hint}. Reply concise with evidence path and decision tag. Keep it under 80 words. Final answer only. If you define official tasks, append a TASKS: block with bullet lines '- title | owner=agent-id | done=definition'."
                ),
                "vulgarisation" => format!(
                    "You are @vulgarisation, simplification lead L1. mode={mode_hint}. Reply in simple french for operator. Keep it under 70 words. Final answer only. If you define official tasks, append a TASKS: block with bullet lines '- title | owner=agent-id | done=definition'."
                ),
                _ => format!(
                    "You are @{agent_id}, specialist L2. mode={mode_hint}. Reply concise with one execution next step. Keep it under 60 words. Final answer only. Never create roadmap, strategy, or TASKS block."
                ),
            }
        }
    }
}

fn direct_chat_options(profile: &LlmProfile) -> openrouter::ChatCompletionOptions {
    openrouter::ChatCompletionOptions {
        max_tokens: Some(profile.max_tokens.unwrap_or(DIRECT_CHAT_MAX_TOKENS).min(DIRECT_CHAT_MAX_TOKENS)),
        temperature: Some(profile.temperature.unwrap_or(DIRECT_CHAT_TEMPERATURE).min(DIRECT_CHAT_TEMPERATURE)),
    }
}

fn direct_rescue_options() -> openrouter::ChatCompletionOptions {
    openrouter::ChatCompletionOptions {
        max_tokens: Some(DIRECT_RESCUE_MAX_TOKENS),
        temperature: Some(DIRECT_RESCUE_TEMPERATURE),
    }
}

fn direct_rescue_prompt(agent_id: &str) -> String {
    match agent_id {
        "clems" => "You are @clems in a direct operator chat. Reply in natural french, ascii only, with 1 or 2 short sentences max. Be helpful, human, and concrete. Final answer only.".to_string(),
        "victor" => "You are @victor in a direct operator chat. Reply in natural french, ascii only, with 1 or 2 short sentences max. Be concrete and helpful. Final answer only.".to_string(),
        "leo" => "You are @leo in a direct operator chat. Reply in natural french, ascii only, with 1 or 2 short sentences max. Be concrete and helpful. Final answer only.".to_string(),
        "nova" => "You are @nova in a direct operator chat. Reply in natural french, ascii only, with 1 or 2 short sentences max. Be clear, evidence aware, and helpful. Final answer only.".to_string(),
        "vulgarisation" => "You are @vulgarisation in a direct operator chat. Reply in simple french, ascii only, with 1 or 2 short sentences max. Final answer only.".to_string(),
        _ => format!(
            "You are @{agent_id} in a direct operator chat. Reply in natural french, ascii only, with 1 or 2 short sentences max. Be concrete and helpful. Final answer only."
        ),
    }
}

fn direct_rescue_models(primary_model: &str) -> Vec<String> {
    let mut models = vec![primary_model.to_string()];
    if primary_model != DIRECT_RESCUE_MODEL {
        models.push(DIRECT_RESCUE_MODEL.to_string());
    }
    models
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
    reply_source: Option<&str>,
) -> ChatMessage {
    let mut message = ChatMessage::new(author, text, thread_id).with_visibility(visibility);
    let mut metadata = json!({
        "run_id": run_id,
        "mode": mode_to_str(&chat_mode),
        "execution_mode": execution_mode_to_str(&execution_mode),
        "kind": kind,
    });
    if let Some(reply_source) = reply_source {
        metadata["reply_source"] = Value::String(reply_source.to_string());
    }
    message.metadata = metadata;
    message
}

fn is_retryable_error(error: &str) -> bool {
    error.starts_with("openrouter_unreachable:") || error.starts_with("openrouter_timeout_after_")
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
) -> AgentReply {
    let context_owned = context_ref.cloned();
    let model = model_for_agent(profile, author);
    let system = actor_prompt(author, &mode);
    let mut user_prompt = format!("Operator message:\n{}\n", user_text.trim());
    if let Some(context_ref) = context_ref {
        user_prompt.push_str(&format!("Context ref:\n{}\n", context_ref));
    }
    let timeout_seconds = match mode {
        ChatMode::Direct => DIRECT_LLM_TIMEOUT_SECONDS,
        ChatMode::ConcealRoom => ROOM_AGENT_LLM_TIMEOUT_SECONDS,
    };
    let max_attempts = match mode {
        ChatMode::Direct => 2usize,
        ChatMode::ConcealRoom => 1usize,
    };

    for attempt in 1..=max_attempts {
        let options = if matches!(mode, ChatMode::Direct) {
            direct_chat_options(profile)
        } else {
            openrouter::ChatCompletionOptions::default()
        };
        let result = match timeout(
            Duration::from_secs(timeout_seconds),
            openrouter::chat_completion_with_options(&model, &system, &user_prompt, &options),
        )
        .await
        {
            Ok(result) => result,
            Err(_) => openrouter::LlmCallResult {
                status: "failed".to_string(),
                text: String::new(),
                model: model.clone(),
                usage: json!({}),
                error: Some(format!("openrouter_timeout_after_{}s", timeout_seconds)),
            },
        };

        usage_calls.push(json!({
            "agent_id": author,
            "model": result.model,
            "status": result.status,
            "usage": result.usage,
            "error": result.error,
            "attempt": attempt,
            "context_ref": context_owned,
            "reply_mode": mode_to_str(&mode),
        }));

        if result.status == "ok" && !result.text.trim().is_empty() {
            return AgentReply {
                text: result.text.trim().to_string(),
                reply_source: "llm",
            };
        }

        let error = result
            .error
            .clone()
            .unwrap_or_else(|| "openrouter_empty_response".to_string());

        if matches!(mode, ChatMode::Direct) && attempt < max_attempts && is_retryable_error(&error)
        {
            sleep(Duration::from_secs(DIRECT_LLM_RETRY_DELAY_SECONDS)).await;
            continue;
        }

        break;
    }

    if matches!(mode, ChatMode::Direct) {
        let rescue_prompt = direct_rescue_prompt(author);
        for rescue_model in direct_rescue_models(&model) {
            let rescue_result = match timeout(
                Duration::from_secs(DIRECT_RESCUE_TIMEOUT_SECONDS),
                openrouter::chat_completion_with_options(
                    &rescue_model,
                    &rescue_prompt,
                    user_text.trim(),
                    &direct_rescue_options(),
                ),
            )
            .await
            {
                Ok(result) => result,
                Err(_) => openrouter::LlmCallResult {
                    status: "failed".to_string(),
                    text: String::new(),
                    model: rescue_model.clone(),
                    usage: json!({}),
                    error: Some(format!(
                        "openrouter_timeout_after_{}s",
                        DIRECT_RESCUE_TIMEOUT_SECONDS
                    )),
                },
            };

            usage_calls.push(json!({
                "agent_id": author,
                "model": rescue_result.model,
                "status": rescue_result.status,
                "usage": rescue_result.usage,
                "error": rescue_result.error,
                "attempt": format!("rescue:{rescue_model}"),
                "context_ref": context_owned,
                "reply_mode": mode_to_str(&mode),
            }));

            if rescue_result.status == "ok" && !rescue_result.text.trim().is_empty() {
                return AgentReply {
                    text: rescue_result.text.trim().to_string(),
                    reply_source: "llm",
                };
            }
        }
    }

    AgentReply {
        text: chat::generate_agent_reply(author, user_text, mode),
        reply_source: "fallback",
    }
}

async fn clems_summary(
    profile: &LlmProfile,
    user_text: &str,
    context_snippets: &[String],
    usage_calls: &mut Vec<Value>,
) -> AgentReply {
    let model = model_for_agent(profile, "clems");
    let system = "You are @clems. Create a short synthesis in french, ascii only, with Summary and Next. Keep it to 2 or 3 short lines max. Final answer only.";
    let joined = if context_snippets.is_empty() {
        user_text.to_string()
    } else {
        format!(
            "Operator:\n{}\n\nContributions:\n- {}",
            user_text.trim(),
            context_snippets.join("\n- ")
        )
    };
    for attempt in 1..=2usize {
        let result = match timeout(
            Duration::from_secs(ROOM_SUMMARY_TIMEOUT_SECONDS),
            openrouter::chat_completion(&model, system, &joined),
        )
        .await
        {
            Ok(result) => result,
            Err(_) => openrouter::LlmCallResult {
                status: "failed".to_string(),
                text: String::new(),
                model: model.clone(),
                usage: json!({}),
                error: Some(format!(
                    "openrouter_timeout_after_{}s",
                    ROOM_SUMMARY_TIMEOUT_SECONDS
                )),
            },
        };
        usage_calls.push(json!({
            "agent_id": "clems",
            "model": result.model,
            "status": result.status,
            "usage": result.usage,
            "error": result.error,
            "purpose": "summary",
            "attempt": attempt,
        }));

        if result.status == "ok" && !result.text.trim().is_empty() {
            return AgentReply {
                text: result.text.trim().to_string(),
                reply_source: "llm",
            };
        }

        let error = result
            .error
            .clone()
            .unwrap_or_else(|| "openrouter_empty_response".to_string());
        if attempt < 2 && is_retryable_error(&error) {
            sleep(Duration::from_secs(ROOM_SUMMARY_RETRY_DELAY_SECONDS)).await;
            continue;
        }
        break;
    }

    AgentReply {
        text: chat::clems_summary(user_text, context_snippets),
        reply_source: "fallback",
    }
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
            let summary = if target_reply.reply_source == "llm" {
                let target_msg = message_with_meta(
                    &target,
                    target_reply.text.clone(),
                    thread_id.clone(),
                    run_id,
                    ChatMode::Direct,
                    execution_mode.clone(),
                    "direct_reply",
                    MessageVisibility::Operator,
                    Some(target_reply.reply_source),
                );
                messages.push(target_msg);

                if target == "clems" {
                    target_reply.text.clone()
                } else {
                    let summary_reply = clems_summary(
                        &profile,
                        &payload.text,
                        std::slice::from_ref(&target_reply.text),
                        &mut usage_calls,
                    )
                    .await;
                    let summary_text = summary_reply.text.clone();
                    let summary_msg = message_with_meta(
                        "clems",
                        summary_reply.text,
                        thread_id.clone(),
                        run_id,
                        ChatMode::Direct,
                        execution_mode,
                        "direct_summary",
                        MessageVisibility::Internal,
                        Some(summary_reply.reply_source),
                    );
                    messages.push(summary_msg);
                    if summary_reply.reply_source == "fallback" {
                        error = Some("some_llm_calls_failed_using_fallback".to_string());
                    }
                    summary_text
                }
            } else {
                error = Some("some_llm_calls_failed_using_fallback".to_string());
                messages.push(message_with_meta(
                    &target,
                    format!(
                        "direct reply unavailable for @{target} after retry. keep the draft and retry.",
                    ),
                    thread_id.clone(),
                    run_id,
                    ChatMode::Direct,
                    execution_mode.clone(),
                    "direct_fallback",
                    MessageVisibility::Internal,
                    Some(target_reply.reply_source),
                ));
                String::new()
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
            let targets =
                chat::conceal_targets_from_context(payload.context_ref.as_ref(), mentions);
            let mut snippets = Vec::new();
            let mut degraded_targets = Vec::new();
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
                            Duration::from_secs(ROOM_AGENT_LLM_TIMEOUT_SECONDS),
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
                                        "error": format!(
                                            "openrouter_timeout_after_{}s",
                                            ROOM_AGENT_LLM_TIMEOUT_SECONDS
                                        ),
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
                    let reply_source = usage
                        .get("status")
                        .and_then(Value::as_str)
                        .map(|status| if status == "ok" { "llm" } else { "fallback" })
                        .unwrap_or("fallback");
                    usage_calls.push(usage);
                    if reply_source == "llm" {
                        snippets.push(format!("@{} {}", target, text));
                    } else {
                        degraded_targets.push(target.clone());
                    }
                    messages.push(message_with_meta(
                        &target,
                        text,
                        thread_id.clone(),
                        run_id,
                        ChatMode::ConcealRoom,
                        execution_mode.clone(),
                        "conceal_reply",
                        if reply_source == "llm" {
                            MessageVisibility::Operator
                        } else {
                            MessageVisibility::Internal
                        },
                        Some(reply_source),
                    ));
                }
            }

            let summary_inputs = snippets.clone();

            let summary_reply =
                clems_summary(&profile, &payload.text, &summary_inputs, &mut usage_calls).await;
            messages.push(message_with_meta(
                "clems",
                summary_reply.text.clone(),
                thread_id.clone(),
                run_id,
                ChatMode::ConcealRoom,
                execution_mode.clone(),
                "conceal_summary",
                MessageVisibility::Operator,
                Some(summary_reply.reply_source),
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
                            None,
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
                            spawn_text.text,
                            thread_id.clone(),
                            run_id,
                            ChatMode::ConcealRoom,
                            execution_mode.clone(),
                            "l2_spawn_output",
                            MessageVisibility::Internal,
                            Some(spawn_text.reply_source),
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
                clems_summary: summary_reply.text,
                approval_requests,
                spawned_agents,
                model_usage: json!({ "calls": usage_calls }),
                error,
            });
        }
    }
}
