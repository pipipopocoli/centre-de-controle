use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentRecord {
    pub agent_id: String,
    pub name: String,
    pub engine: String,
    pub platform: String,
    pub level: u8,
    pub lead_id: Option<String>,
    pub role: String,
    #[serde(default)]
    pub skills: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TerminalSession {
    pub session_id: String,
    pub agent_id: String,
    pub pid: u32,
    pub state: String,
    pub cwd: String,
    pub created_at: String,
    pub last_seen_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ChatMode {
    Direct,
    ConcealRoom,
}

impl Default for ChatMode {
    fn default() -> Self {
        Self::Direct
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum MessageVisibility {
    Operator,
    Internal,
}

impl Default for MessageVisibility {
    fn default() -> Self {
        Self::Operator
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionMode {
    Chat,
    Scene,
}

impl Default for ExecutionMode {
    fn default() -> Self {
        Self::Chat
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DeliveryMode {
    Ws,
    HttpFallback,
    Hybrid,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ApprovalStatus {
    Pending,
    Approved,
    Rejected,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ApprovalDecision {
    Approved,
    Rejected,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpawnPolicy {
    pub default_auto_approve: bool,
    pub overlap_window_minutes: u32,
    pub overlap_requires_operator: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApprovalRequest {
    pub request_id: String,
    pub run_id: String,
    pub requester: String,
    pub section_tag: String,
    pub reason: String,
    pub status: ApprovalStatus,
    pub requested_at: String,
    pub decided_by: Option<String>,
    pub decided_at: Option<String>,
    pub decision_note: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiveTurnRequest {
    pub text: String,
    #[serde(default)]
    pub chat_mode: ChatMode,
    #[serde(default)]
    pub execution_mode: ExecutionMode,
    pub thread_id: Option<String>,
    #[serde(default)]
    pub mentions: Vec<String>,
    pub context_ref: Option<Value>,
    pub section_tag: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiveTurnResponse {
    pub run_id: String,
    pub status: String,
    pub messages: Vec<ChatMessage>,
    pub clems_summary: String,
    pub delivery_mode: DeliveryMode,
    #[serde(default)]
    pub approval_requests: Vec<ApprovalRequest>,
    pub spawned_agents_count: usize,
    pub model_usage: Value,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateAgentRequest {
    pub agent_id: Option<String>,
    pub name: Option<String>,
    pub engine: Option<String>,
    pub platform: Option<String>,
    pub level: Option<u8>,
    pub lead_id: Option<String>,
    pub role: Option<String>,
    pub skills: Option<Vec<String>>,
    pub cwd: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateAgentResponse {
    pub agent: AgentRecord,
    pub terminal: TerminalSession,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TerminalOpenRequest {
    pub cwd: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TerminalSendRequest {
    pub text: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApprovalDecisionRequest {
    pub decided_by: Option<String>,
    pub note: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub message_id: String,
    pub timestamp: String,
    pub author: String,
    pub text: String,
    pub thread_id: Option<String>,
    pub priority: String,
    #[serde(default)]
    pub tags: Vec<String>,
    #[serde(default)]
    pub mentions: Vec<String>,
    #[serde(default)]
    pub visibility: MessageVisibility,
    pub metadata: Value,
}

impl ChatMessage {
    pub fn new(author: impl Into<String>, text: impl Into<String>, thread_id: Option<String>) -> Self {
        Self {
            message_id: format!("msg_{}", Uuid::new_v4().simple()),
            timestamp: Utc::now().to_rfc3339(),
            author: author.into(),
            text: text.into(),
            thread_id,
            priority: "normal".to_string(),
            tags: Vec::new(),
            mentions: Vec::new(),
            visibility: MessageVisibility::Operator,
            metadata: json!({}),
        }
    }

    pub fn with_visibility(mut self, visibility: MessageVisibility) -> Self {
        self.visibility = visibility;
        self
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatHistoryResponse {
    pub project_id: String,
    pub messages: Vec<ChatMessage>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatApprovalsResponse {
    pub project_id: String,
    pub approvals: Vec<ApprovalRequest>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PixelAgentStatus {
    pub agent_id: String,
    pub name: String,
    pub level: u8,
    pub lead_id: Option<String>,
    pub role: String,
    pub terminal_state: String,
    pub terminal_session_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PixelFeedResponse {
    pub project_id: String,
    pub generated_at: String,
    pub terminals_alive: usize,
    pub queue_depth: usize,
    pub ws_connected: bool,
    pub l0_count: usize,
    pub l1_count: usize,
    pub l2_count: usize,
    pub agents: Vec<PixelAgentStatus>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WsEventEnvelope {
    pub project_id: String,
    pub timestamp: String,
    #[serde(rename = "type")]
    pub event_type: String,
    pub payload: Value,
}

impl WsEventEnvelope {
    pub fn new(project_id: impl Into<String>, event_type: impl Into<String>, payload: Value) -> Self {
        Self {
            project_id: project_id.into(),
            timestamp: Utc::now().to_rfc3339(),
            event_type: event_type.into(),
            payload,
        }
    }
}
