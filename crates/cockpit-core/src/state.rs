use std::{
    collections::HashSet,
    path::PathBuf,
    sync::{Arc, Mutex},
};

use anyhow::Result;
use chrono::Utc;
use serde_json::Value;
use tokio::sync::broadcast;

use crate::{models::WsEventEnvelope, openrouter, storage, terminal::TerminalManager};

#[derive(Clone, Debug)]
pub struct OpenRouterStatusSnapshot {
    pub status: String,
    pub base_url: String,
    pub api_key_present: bool,
    pub last_ok_at: Option<String>,
    pub last_error: Option<String>,
    pub last_error_kind: Option<String>,
    pub last_http_status: Option<u16>,
    pub last_request_id: Option<String>,
    pub last_body_preview: Option<String>,
}

#[derive(Clone, Debug)]
struct OpenRouterRuntimeState {
    base_url: String,
    api_key_present: bool,
    last_ok_at: Option<String>,
    last_error: Option<String>,
    last_error_kind: Option<String>,
    last_http_status: Option<u16>,
    last_request_id: Option<String>,
    last_body_preview: Option<String>,
}

impl OpenRouterRuntimeState {
    fn new() -> Self {
        Self {
            base_url: openrouter::health_base_url(),
            api_key_present: openrouter::health_api_key_present(),
            last_ok_at: None,
            last_error: None,
            last_error_kind: None,
            last_http_status: None,
            last_request_id: None,
            last_body_preview: None,
        }
    }

    fn snapshot(&self) -> OpenRouterStatusSnapshot {
        let status = if !self.api_key_present {
            "missing_key"
        } else if self.base_url.trim().is_empty() {
            "missing_base_url"
        } else if self.last_error.is_some() {
            "degraded"
        } else {
            "ready"
        };

        OpenRouterStatusSnapshot {
            status: status.to_string(),
            base_url: self.base_url.clone(),
            api_key_present: self.api_key_present,
            last_ok_at: self.last_ok_at.clone(),
            last_error: self.last_error.clone(),
            last_error_kind: self.last_error_kind.clone(),
            last_http_status: self.last_http_status,
            last_request_id: self.last_request_id.clone(),
            last_body_preview: self.last_body_preview.clone(),
        }
    }
}

#[derive(Clone)]
pub struct AppState {
    pub control_root: Arc<PathBuf>,
    pub event_tx: broadcast::Sender<WsEventEnvelope>,
    pub terminal_manager: TerminalManager,
    pub clems_session_acks: Arc<Mutex<HashSet<String>>>,
    openrouter_state: Arc<Mutex<OpenRouterRuntimeState>>,
}

impl AppState {
    pub fn new(control_root: PathBuf) -> Result<Self> {
        std::fs::create_dir_all(&control_root)?;
        let (event_tx, _) = broadcast::channel(4096);
        let terminal_manager = TerminalManager::new(event_tx.clone());
        Ok(Self {
            control_root: Arc::new(control_root),
            event_tx,
            terminal_manager,
            clems_session_acks: Arc::new(Mutex::new(HashSet::new())),
            openrouter_state: Arc::new(Mutex::new(OpenRouterRuntimeState::new())),
        })
    }

    pub fn emit_event(&self, project_id: &str, event_type: &str, payload: Value) {
        let event = WsEventEnvelope::new(project_id, event_type, payload);
        let _ = self.event_tx.send(event.clone());
        let _ = storage::append_runtime_event(self.control_root.as_ref(), project_id, &event);
    }

    pub fn mark_clems_session_ack(&self, session_id: &str) -> bool {
        if let Ok(mut acks) = self.clems_session_acks.lock() {
            return acks.insert(session_id.to_string());
        }
        false
    }

    pub fn mark_openrouter_ok(&self) {
        self.mark_openrouter_ok_with_diagnostics(None);
    }

    pub fn mark_openrouter_ok_with_diagnostics(
        &self,
        diagnostics: Option<&openrouter::OpenRouterCallDiagnostics>,
    ) {
        if let Ok(mut state) = self.openrouter_state.lock() {
            state.last_ok_at = Some(Utc::now().to_rfc3339());
            state.last_error = None;
            state.last_error_kind = None;
            state.last_http_status = None;
            state.last_body_preview = None;
            state.last_request_id = diagnostics.and_then(|value| value.request_id.clone());
        }
    }

    pub fn mark_openrouter_error(&self, error: impl Into<String>) {
        self.mark_openrouter_error_with_diagnostics(error, None);
    }

    pub fn mark_openrouter_error_with_diagnostics(
        &self,
        error: impl Into<String>,
        diagnostics: Option<&openrouter::OpenRouterCallDiagnostics>,
    ) {
        if let Ok(mut state) = self.openrouter_state.lock() {
            state.last_error = Some(error.into());
            state.last_error_kind = diagnostics.and_then(|value| value.error_kind.clone());
            state.last_http_status = diagnostics.and_then(|value| value.http_status);
            state.last_request_id = diagnostics.and_then(|value| value.request_id.clone());
            state.last_body_preview = diagnostics.and_then(|value| value.body_preview.clone());
        }
    }

    pub fn openrouter_status(&self) -> OpenRouterStatusSnapshot {
        match self.openrouter_state.lock() {
            Ok(state) => state.snapshot(),
            Err(_) => OpenRouterRuntimeState::new().snapshot(),
        }
    }
}
