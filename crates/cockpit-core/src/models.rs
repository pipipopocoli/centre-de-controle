use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::collections::HashMap;
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
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub phase: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub status: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub current_task: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub heartbeat: Option<String>,
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
    pub target_agent_id: Option<String>,
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
    pub fn new(
        author: impl Into<String>,
        text: impl Into<String>,
        thread_id: Option<String>,
    ) -> Self {
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
    pub chat_targetable: bool,
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

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum TaskStatus {
    Todo,
    InProgress,
    Blocked,
    Done,
}

impl TaskStatus {
    pub fn as_label(self) -> &'static str {
        match self {
            Self::Todo => "Todo",
            Self::InProgress => "In Progress",
            Self::Blocked => "Blocked",
            Self::Done => "Done",
        }
    }
}

impl Default for TaskStatus {
    fn default() -> Self {
        Self::Todo
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskRecord {
    pub task_id: String,
    pub title: String,
    pub owner: String,
    pub phase: String,
    pub status: TaskStatus,
    pub source: String,
    pub objective: String,
    pub done_definition: String,
    #[serde(default)]
    pub links: Vec<String>,
    #[serde(default)]
    pub risks: Vec<String>,
    pub path: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TasksResponse {
    pub project_id: String,
    pub generated_at: String,
    pub tasks: Vec<TaskRecord>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillLibraryEntry {
    pub skill_id: String,
    pub name: String,
    pub description: String,
    pub source_path: String,
    pub project_locked: bool,
    pub project_status: Option<String>,
    #[serde(default)]
    pub assigned_agents: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillsLibraryResponse {
    pub project_id: String,
    pub generated_at: String,
    pub skills: Vec<SkillLibraryEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateTaskRequest {
    pub title: String,
    pub owner: Option<String>,
    pub phase: Option<String>,
    pub status: Option<TaskStatus>,
    pub source: Option<String>,
    pub objective: Option<String>,
    pub done_definition: Option<String>,
    #[serde(default)]
    pub links: Vec<String>,
    #[serde(default)]
    pub risks: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateTaskRequest {
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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WsEventEnvelope {
    pub project_id: String,
    pub timestamp: String,
    #[serde(rename = "type")]
    pub event_type: String,
    pub payload: Value,
}

impl WsEventEnvelope {
    pub fn new(
        project_id: impl Into<String>,
        event_type: impl Into<String>,
        payload: Value,
    ) -> Self {
        Self {
            project_id: project_id.into(),
            timestamp: Utc::now().to_rfc3339(),
            event_type: event_type.into(),
            payload,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LlmProfile {
    #[serde(default = "default_provider")]
    pub provider: String,
    #[serde(default = "default_voice_stt_model")]
    pub voice_stt_model: String,
    #[serde(default = "default_clems_model")]
    pub clems_model: String,
    #[serde(default = "default_clems_catalog")]
    pub clems_catalog: Vec<String>,
    #[serde(default)]
    pub l1_models: HashMap<String, String>,
    #[serde(default = "default_l1_catalog")]
    pub l1_catalog: Vec<String>,
    #[serde(default = "default_l2_default_model")]
    pub l2_default_model: String,
    #[serde(default = "default_l2_pool")]
    pub l2_pool: Vec<String>,
    #[serde(default = "default_l2_selection_mode")]
    pub l2_selection_mode: String,
    #[serde(default = "default_stream_enabled")]
    pub stream_enabled: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub fallback_model: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub legacy_mapping: Option<HashMap<String, String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_tokens: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub temperature: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub default_model: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub l1_model: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub l2_scene_model: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub lfm_spawn_max: Option<u8>,
}

fn default_provider() -> String {
    "openrouter".to_string()
}

fn default_voice_stt_model() -> String {
    "google/gemini-2.5-flash".to_string()
}

fn default_clems_model() -> String {
    "moonshotai/kimi-k2.5".to_string()
}

fn default_clems_catalog() -> Vec<String> {
    vec![
        "moonshotai/kimi-k2.5".to_string(),
        "anthropic/claude-sonnet-4.6".to_string(),
        "anthropic/claude-opus-4.6".to_string(),
    ]
}

fn default_l1_catalog() -> Vec<String> {
    vec![
        "moonshotai/kimi-k2.5".to_string(),
        "anthropic/claude-sonnet-4.6".to_string(),
        "anthropic/claude-opus-4.6".to_string(),
        "openai/gpt-5.4".to_string(),
        "google/gemini-3.1-pro-preview".to_string(),
        "x-ai/grok-4".to_string(),
    ]
}

fn default_l2_default_model() -> String {
    "minimax/minimax-m2.5".to_string()
}

fn default_l2_pool() -> Vec<String> {
    vec![
        "minimax/minimax-m2.5".to_string(),
        "moonshotai/kimi-k2.5".to_string(),
        "deepseek/deepseek-chat-v3.1".to_string(),
    ]
}

fn default_l2_selection_mode() -> String {
    "manual_primary".to_string()
}

fn default_stream_enabled() -> bool {
    true
}

impl Default for LlmProfile {
    fn default() -> Self {
        let mut l1_models = HashMap::new();
        for agent_id in ["victor", "leo", "nova", "vulgarisation"] {
            l1_models.insert(agent_id.to_string(), default_clems_model());
        }
        Self {
            provider: default_provider(),
            voice_stt_model: default_voice_stt_model(),
            clems_model: default_clems_model(),
            clems_catalog: default_clems_catalog(),
            l1_models,
            l1_catalog: default_l1_catalog(),
            l2_default_model: default_l2_default_model(),
            l2_pool: default_l2_pool(),
            l2_selection_mode: default_l2_selection_mode(),
            stream_enabled: default_stream_enabled(),
            fallback_model: Some("liquid/lfm-2.5-1.2b-thinking:free".to_string()),
            legacy_mapping: Some(HashMap::new()),
            max_tokens: Some(4096),
            temperature: Some(0.7),
            default_model: None,
            l1_model: None,
            l2_scene_model: None,
            lfm_spawn_max: Some(10),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LlmProfileResponse {
    pub project_id: String,
    pub profile: LlmProfile,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectSettings {
    pub project_id: String,
    pub project_name: String,
    pub linked_repo_path: Option<String>,
    pub updated_at: String,
    pub raw: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectSettingsResponse {
    pub project_id: String,
    pub settings: ProjectSettings,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateProjectRequest {
    pub project_id: String,
    pub project_name: Option<String>,
    pub linked_repo_path: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectCatalogEntry {
    pub project_id: String,
    pub project_name: String,
    pub linked_repo_path: Option<String>,
    pub phase: String,
    pub objective: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectCatalogResponse {
    pub generated_at: String,
    #[serde(default)]
    pub projects: Vec<ProjectCatalogEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectTaskCounts {
    pub todo: usize,
    pub in_progress: usize,
    pub blocked: usize,
    pub done: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectModelUsageEntry {
    pub model: String,
    pub cost_cad: f64,
    pub events: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectSummaryResponse {
    pub project_id: String,
    pub linked_repo_path: Option<String>,
    pub phase: String,
    pub objective: String,
    #[serde(default)]
    pub roadmap_now: Vec<String>,
    #[serde(default)]
    pub roadmap_next: Vec<String>,
    #[serde(default)]
    pub roadmap_risks: Vec<String>,
    #[serde(default)]
    pub latest_decisions: Vec<String>,
    pub open_task_counts: ProjectTaskCounts,
    pub monthly_cost_estimate_cad: Option<f64>,
    pub cost_events_this_month: usize,
    #[serde(default)]
    pub model_usage_summary: Vec<ProjectModelUsageEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateProjectSettingsRequest {
    pub project_name: Option<String>,
    pub linked_repo_path: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateLlmProfileRequest {
    pub voice_stt_model: Option<String>,
    pub clems_model: Option<String>,
    pub clems_catalog: Option<Vec<String>>,
    pub l1_models: Option<HashMap<String, String>>,
    pub l1_catalog: Option<Vec<String>>,
    pub l2_default_model: Option<String>,
    pub l2_pool: Option<Vec<String>>,
    pub l2_selection_mode: Option<String>,
    pub stream_enabled: Option<bool>,
    pub default_model: Option<String>,
    pub fallback_model: Option<String>,
    pub l1_model: Option<String>,
    pub l2_scene_model: Option<String>,
    pub lfm_spawn_max: Option<u8>,
    pub max_tokens: Option<u32>,
    pub temperature: Option<f32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoadmapSections {
    #[serde(default)]
    pub now: Vec<String>,
    #[serde(default)]
    pub next: Vec<String>,
    #[serde(default)]
    pub risks: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoadmapResponse {
    pub project_id: String,
    pub sections: RoadmapSections,
    pub raw_md: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateRoadmapRequest {
    #[serde(default)]
    pub now: Vec<String>,
    #[serde(default)]
    pub next: Vec<String>,
    #[serde(default)]
    pub risks: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoadmapDraftRequest {
    pub prompt: String,
    #[serde(default)]
    pub context: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoadmapDraftResponse {
    pub run_id: String,
    pub draft: Value,
    pub model_usage: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TakeoverStartRequest {
    pub linked_repo_path: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TakeoverSuggestedTask {
    pub title: String,
    pub owner: String,
    pub objective: String,
    pub done_definition: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TakeoverSuggestedSkill {
    pub skill_id: String,
    pub owner: String,
    pub reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TakeoverStartResponse {
    pub run_id: String,
    pub project_id: String,
    pub linked_repo_path: Option<String>,
    pub summary_human: String,
    #[serde(default)]
    pub summary_tech: Vec<String>,
    pub roadmap_sections: RoadmapSections,
    #[serde(default)]
    pub suggested_tasks: Vec<TakeoverSuggestedTask>,
    #[serde(default)]
    pub suggested_skills: Vec<TakeoverSuggestedSkill>,
    pub repo_findings: Value,
    pub model_usage: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VoiceTranscribeRequest {
    pub audio_base64: String,
    pub format: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VoiceTranscribeResponse {
    pub project_id: String,
    pub text: String,
    pub model: String,
    pub duration_ms: i64,
    pub status: String,
    pub usage: Value,
    pub error: Option<String>,
}
