use std::{collections::HashSet, path::PathBuf, sync::{Arc, Mutex}};

use anyhow::Result;
use serde_json::Value;
use tokio::sync::broadcast;

use crate::{models::WsEventEnvelope, storage, terminal::TerminalManager};

#[derive(Clone)]
pub struct AppState {
    pub control_root: Arc<PathBuf>,
    pub event_tx: broadcast::Sender<WsEventEnvelope>,
    pub terminal_manager: TerminalManager,
    pub clems_session_acks: Arc<Mutex<HashSet<String>>>,
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
}
