use std::{
    collections::HashMap,
    io::{Read, Write},
    path::PathBuf,
    sync::{Arc, Mutex},
};

use anyhow::{Context, Result, anyhow};
use chrono::Utc;
use portable_pty::{CommandBuilder, PtySize, native_pty_system};
use serde_json::json;
use tokio::sync::broadcast;
use uuid::Uuid;

use crate::models::{TerminalSession, WsEventEnvelope};

struct SessionHandle {
    info: TerminalSession,
    cwd: PathBuf,
    writer: Box<dyn Write + Send>,
    child: Box<dyn portable_pty::Child + Send>,
}

#[derive(Clone)]
pub struct TerminalManager {
    sessions: Arc<Mutex<HashMap<String, SessionHandle>>>,
    event_tx: broadcast::Sender<WsEventEnvelope>,
}

impl TerminalManager {
    pub fn new(event_tx: broadcast::Sender<WsEventEnvelope>) -> Self {
        Self {
            sessions: Arc::new(Mutex::new(HashMap::new())),
            event_tx,
        }
    }

    pub fn open_or_get(
        &self,
        project_id: &str,
        agent_id: &str,
        cwd: PathBuf,
    ) -> Result<TerminalSession> {
        let key = session_key(project_id, agent_id);

        if let Some(existing) = self
            .sessions
            .lock()
            .map_err(|_| anyhow!("terminal session mutex poisoned"))?
            .get(&key)
        {
            return Ok(existing.info.clone());
        }

        let pty = native_pty_system();
        let pair = pty.openpty(PtySize {
            rows: 36,
            cols: 140,
            pixel_width: 0,
            pixel_height: 0,
        })?;

        let shell = std::env::var("SHELL").unwrap_or_else(|_| "/bin/zsh".to_string());
        let mut cmd = CommandBuilder::new(shell);
        cmd.arg("-i");
        cmd.cwd(cwd.clone());

        let child = pair
            .slave
            .spawn_command(cmd)
            .context("failed to spawn terminal child")?;

        let pid = child.process_id().unwrap_or(0);
        let mut reader = pair.master.try_clone_reader()?;
        let writer = pair.master.take_writer()?;
        let session_id = format!("ts_{}", Uuid::new_v4().simple());
        let now = Utc::now().to_rfc3339();

        let info = TerminalSession {
            session_id: session_id.clone(),
            agent_id: agent_id.to_string(),
            pid,
            state: "running".to_string(),
            cwd: cwd.to_string_lossy().to_string(),
            created_at: now.clone(),
            last_seen_at: now,
        };

        let output_project = project_id.to_string();
        let output_agent = agent_id.to_string();
        let output_session = session_id.clone();
        let output_bus = self.event_tx.clone();

        std::thread::spawn(move || {
            let mut buf = [0u8; 8192];
            loop {
                match reader.read(&mut buf) {
                    Ok(0) => {
                        let event = WsEventEnvelope::new(
                            output_project.clone(),
                            "agent.terminal.status",
                            json!({
                                "agent_id": output_agent,
                                "session_id": output_session,
                                "state": "eof"
                            }),
                        );
                        let _ = output_bus.send(event);
                        break;
                    }
                    Ok(n) => {
                        let chunk = String::from_utf8_lossy(&buf[..n]).to_string();
                        let event = WsEventEnvelope::new(
                            output_project.clone(),
                            "agent.terminal.status",
                            json!({
                                "agent_id": output_agent,
                                "session_id": output_session,
                                "state": "output",
                                "chunk": chunk
                            }),
                        );
                        let _ = output_bus.send(event);
                    }
                    Err(_) => break,
                }
            }
        });

        let mut sessions = self
            .sessions
            .lock()
            .map_err(|_| anyhow!("terminal session mutex poisoned"))?;
        sessions.insert(
            key,
            SessionHandle {
                info: info.clone(),
                cwd,
                writer,
                child,
            },
        );

        self.emit_status(project_id, agent_id, &info, "running");
        Ok(info)
    }

    pub fn send_input(
        &self,
        project_id: &str,
        agent_id: &str,
        text: &str,
    ) -> Result<TerminalSession> {
        let key = session_key(project_id, agent_id);
        let mut sessions = self
            .sessions
            .lock()
            .map_err(|_| anyhow!("terminal session mutex poisoned"))?;

        let session = sessions
            .get_mut(&key)
            .ok_or_else(|| anyhow!("terminal session not found for {agent_id}"))?;

        session.writer.write_all(text.as_bytes())?;
        if !text.ends_with('\n') {
            session.writer.write_all(b"\n")?;
        }
        session.writer.flush()?;

        session.info.last_seen_at = Utc::now().to_rfc3339();
        let cloned = session.info.clone();
        drop(sessions);

        self.emit_status(project_id, agent_id, &cloned, "input_sent");
        Ok(cloned)
    }

    pub fn restart(
        &self,
        project_id: &str,
        agent_id: &str,
        cwd: Option<PathBuf>,
    ) -> Result<TerminalSession> {
        let selected_cwd = if let Some(cwd) = cwd {
            cwd
        } else {
            self.sessions
                .lock()
                .map_err(|_| anyhow!("terminal session mutex poisoned"))?
                .get(&session_key(project_id, agent_id))
                .map(|h| h.cwd.clone())
                .unwrap_or_else(|| PathBuf::from("."))
        };

        let _ = self.close(project_id, agent_id);
        self.open_or_get(project_id, agent_id, selected_cwd)
    }

    pub fn close(&self, project_id: &str, agent_id: &str) -> Result<Option<TerminalSession>> {
        let key = session_key(project_id, agent_id);
        let mut sessions = self
            .sessions
            .lock()
            .map_err(|_| anyhow!("terminal session mutex poisoned"))?;

        let mut handle = if let Some(handle) = sessions.remove(&key) {
            handle
        } else {
            return Ok(None);
        };

        let _ = handle.child.kill();
        let _ = handle.child.wait();
        handle.info.state = "closed".to_string();
        handle.info.last_seen_at = Utc::now().to_rfc3339();
        let closed = handle.info.clone();
        drop(sessions);

        self.emit_status(project_id, agent_id, &closed, "closed");
        Ok(Some(closed))
    }

    pub fn session_for_agent(&self, project_id: &str, agent_id: &str) -> Option<TerminalSession> {
        let key = session_key(project_id, agent_id);
        self.sessions
            .lock()
            .ok()
            .and_then(|sessions| sessions.get(&key).map(|s| s.info.clone()))
    }

    pub fn sessions_for_project(&self, project_id: &str) -> Vec<TerminalSession> {
        let prefix = format!("{project_id}::");
        self.sessions
            .lock()
            .map(|sessions| {
                sessions
                    .iter()
                    .filter(|(k, _)| k.starts_with(&prefix))
                    .map(|(_, v)| v.info.clone())
                    .collect()
            })
            .unwrap_or_default()
    }

    fn emit_status(
        &self,
        project_id: &str,
        agent_id: &str,
        session: &TerminalSession,
        state: &str,
    ) {
        let event = WsEventEnvelope::new(
            project_id,
            "agent.terminal.status",
            json!({
                "agent_id": agent_id,
                "session_id": session.session_id,
                "pid": session.pid,
                "state": state,
                "cwd": session.cwd,
                "last_seen_at": session.last_seen_at,
            }),
        );
        let _ = self.event_tx.send(event);
    }
}

fn session_key(project_id: &str, agent_id: &str) -> String {
    format!("{project_id}::{agent_id}")
}
