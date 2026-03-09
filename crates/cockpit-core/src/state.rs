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
}

#[derive(Clone, Debug)]
struct OpenRouterRuntimeState {
    base_url: String,
    api_key_present: bool,
    last_ok_at: Option<String>,
    last_error: Option<String>,
}

impl OpenRouterRuntimeState {
    fn new() -> Self {
        Self {
            base_url: openrouter::health_base_url(),
            api_key_present: openrouter::health_api_key_present(),
            last_ok_at: None,
            last_error: None,
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
        if let Ok(mut state) = self.openrouter_state.lock() {
            state.last_ok_at = Some(Utc::now().to_rfc3339());
            state.last_error = None;
        }
    }

    pub fn mark_openrouter_error(&self, error: impl Into<String>) {
        if let Ok(mut state) = self.openrouter_state.lock() {
            state.last_error = Some(error.into());
        }
    }

    pub fn openrouter_status(&self) -> OpenRouterStatusSnapshot {
        match self.openrouter_state.lock() {
            Ok(state) => state.snapshot(),
            Err(_) => OpenRouterRuntimeState::new().snapshot(),
        }
    }
}
