#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{
    collections::HashMap,
    env,
    fs,
    io::{Read, Write},
    net::{SocketAddr, TcpStream},
    path::{Path, PathBuf},
    process::{Command, Stdio},
    thread,
    time::Duration,
};

const BACKEND_HOST: &str = "127.0.0.1";
const BACKEND_PORT: u16 = 8787;

fn backend_addr() -> SocketAddr {
    format!("{BACKEND_HOST}:{BACKEND_PORT}")
        .parse()
        .expect("invalid backend socket")
}

fn backend_is_running() -> bool {
    let mut stream = match TcpStream::connect_timeout(&backend_addr(), Duration::from_millis(300)) {
        Ok(stream) => stream,
        Err(_) => return false,
    };
    let _ = stream.set_read_timeout(Some(Duration::from_millis(500)));
    let _ = stream.set_write_timeout(Some(Duration::from_millis(500)));

    if stream
        .write_all(b"GET /healthz HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n")
        .is_err()
    {
        return false;
    }

    let mut buffer = [0_u8; 256];
    let read = match stream.read(&mut buffer) {
        Ok(read) if read > 0 => read,
        _ => return false,
    };

    let response_head = String::from_utf8_lossy(&buffer[..read]);
    response_head.starts_with("HTTP/1.1 200") || response_head.starts_with("HTTP/1.0 200")
}

fn control_root_candidates() -> Vec<PathBuf> {
    let mut candidates = Vec::new();

    if let Ok(from_env) = env::var("COCKPIT_CONTROL_ROOT") {
        candidates.push(PathBuf::from(from_env));
    }

    if let Ok(cwd) = env::current_dir() {
        candidates.push(cwd.join("control/projects"));
        candidates.push(cwd.join("../../control/projects"));
    }

    if let Ok(home) = env::var("HOME") {
        let home = PathBuf::from(home);
        candidates.push(home.join("Desktop/Cockpit/control/projects"));
        candidates.push(home.join("Cockpit/control/projects"));
    }

    candidates
}

fn resolve_control_root() -> Option<PathBuf> {
    control_root_candidates()
        .into_iter()
        .find(|path| path.exists())
}

fn dotenv_candidates(control_root: Option<&Path>) -> Vec<PathBuf> {
    let mut candidates = Vec::new();

    if let Ok(cwd) = env::current_dir() {
        candidates.push(cwd.join(".env"));
    }

    if let Some(control_root) = control_root {
        if let Some(repo_root) = control_root.parent().and_then(|value| value.parent()) {
            candidates.push(repo_root.join(".env"));
        }
    }

    if let Ok(home) = env::var("HOME") {
        let home = PathBuf::from(home);
        candidates.push(home.join("Desktop/Cockpit/.env"));
        candidates.push(home.join("Library/Application Support/Cockpit/.env"));
        candidates.push(home.join(".cockpit/.env"));
    }

    candidates
}

fn parse_dotenv(path: &Path) -> HashMap<String, String> {
    let Ok(raw) = fs::read_to_string(path) else {
        return HashMap::new();
    };

    let mut values = HashMap::new();
    for line in raw.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('#') {
            continue;
        }

        let normalized = trimmed.strip_prefix("export ").unwrap_or(trimmed);
        let Some((key, value)) = normalized.split_once('=') else {
            continue;
        };

        let key = key.trim();
        if key.is_empty() {
            continue;
        }

        let mut value = value.trim().to_string();
        if value.len() >= 2 {
            let quoted = (value.starts_with('"') && value.ends_with('"'))
                || (value.starts_with('\'') && value.ends_with('\''));
            if quoted {
                value = value[1..value.len() - 1].to_string();
            }
        }

        values.insert(key.to_string(), value);
    }

    values
}

fn resolved_backend_env(control_root: Option<&Path>) -> HashMap<String, String> {
    let mut resolved = HashMap::new();

    for key in [
        "COCKPIT_OPENROUTER_API_KEY",
        "OPENROUTER_API_KEY",
        "COCKPIT_OPENROUTER_BASE_URL",
    ] {
        if let Ok(value) = env::var(key) {
            let trimmed = value.trim();
            if !trimmed.is_empty() {
                resolved.insert(key.to_string(), trimmed.to_string());
            }
        }
    }

    for path in dotenv_candidates(control_root) {
        if !path.exists() {
            continue;
        }
        let values = parse_dotenv(&path);
        for key in [
            "COCKPIT_OPENROUTER_API_KEY",
            "OPENROUTER_API_KEY",
            "COCKPIT_OPENROUTER_BASE_URL",
        ] {
            if resolved.contains_key(key) {
                continue;
            }
            if let Some(value) = values.get(key).filter(|value| !value.trim().is_empty()) {
                resolved.insert(key.to_string(), value.trim().to_string());
            }
        }
    }

    if !resolved.contains_key("COCKPIT_OPENROUTER_API_KEY") {
        if let Some(value) = resolved.get("OPENROUTER_API_KEY").cloned() {
            resolved.insert("COCKPIT_OPENROUTER_API_KEY".to_string(), value);
        }
    }

    if !resolved.contains_key("OPENROUTER_API_KEY") {
        if let Some(value) = resolved.get("COCKPIT_OPENROUTER_API_KEY").cloned() {
            resolved.insert("OPENROUTER_API_KEY".to_string(), value);
        }
    }

    resolved
}

fn backend_binary_candidates() -> Vec<PathBuf> {
    let mut candidates = Vec::new();

    if let Ok(current_exe) = env::current_exe() {
        if let Some(exe_dir) = current_exe.parent() {
            candidates.push(exe_dir.join("cockpit-core"));
        }
    }

    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../");
    candidates.push(repo_root.join("crates/cockpit-core/target/release/cockpit-core"));
    candidates.push(repo_root.join("crates/cockpit-core/target/debug/cockpit-core"));

    candidates
}

fn ensure_backend_process() -> Result<(), String> {
    if backend_is_running() {
        return Ok(());
    }

    let backend_bin = backend_binary_candidates()
        .into_iter()
        .find(|path| path.exists())
        .ok_or_else(|| "cockpit-core binary not found".to_string())?;

    let mut command = Command::new(&backend_bin);
    command
        .env("COCKPIT_NEXT_HOST", BACKEND_HOST)
        .env("COCKPIT_NEXT_PORT", BACKEND_PORT.to_string())
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());

    let control_root = resolve_control_root();
    if let Some(control_root) = control_root.as_ref() {
        command.env("COCKPIT_CONTROL_ROOT", control_root);
    }

    for (key, value) in resolved_backend_env(control_root.as_deref()) {
        command.env(key, value);
    }

    command
        .spawn()
        .map_err(|err| format!("failed to spawn cockpit-core: {err}"))?;

    for _ in 0..30 {
        if backend_is_running() {
            return Ok(());
        }
        thread::sleep(Duration::from_millis(120));
    }

    Err("cockpit-core did not become healthy on 127.0.0.1:8787".to_string())
}

#[tauri::command]
fn open_os_terminal(agent_id: String, cwd: Option<String>) -> Result<(), String> {
    let target_dir = cwd
        .map(PathBuf::from)
        .unwrap_or_else(|| std::env::current_dir().unwrap_or_else(|_| PathBuf::from(".")));

    #[cfg(target_os = "macos")]
    {
        let script = format!(
            "tell application \"Terminal\" to do script \"cd '{}'; echo Agent: {}\"",
            target_dir.display(),
            agent_id
        );

        Command::new("osascript")
            .arg("-e")
            .arg(script)
            .status()
            .map_err(|err| err.to_string())?;
        return Ok(());
    }

    #[cfg(target_os = "linux")]
    {
        Command::new("x-terminal-emulator")
            .arg("--working-directory")
            .arg(target_dir)
            .status()
            .map_err(|err| err.to_string())?;
        return Ok(());
    }

    #[cfg(target_os = "windows")]
    {
        Command::new("cmd")
            .args([
                "/C",
                "start",
                "cmd",
                "/K",
                &format!("cd /d {} && echo Agent: {}", target_dir.display(), agent_id),
            ])
            .status()
            .map_err(|err| err.to_string())?;
        return Ok(());
    }

    #[allow(unreachable_code)]
    Err("unsupported platform".to_string())
}

fn main() {
    tauri::Builder::default()
        .setup(|_app| {
            if let Err(error) = ensure_backend_process() {
                eprintln!("[cockpit-next] backend startup warning: {error}");
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![open_os_terminal])
        .run(tauri::generate_context!())
        .expect("error while running tauri application")
}
