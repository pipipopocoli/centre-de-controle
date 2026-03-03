#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{
    env,
    net::{SocketAddr, TcpStream},
    path::PathBuf,
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
    TcpStream::connect_timeout(&backend_addr(), Duration::from_millis(140)).is_ok()
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

    if let Some(control_root) = resolve_control_root() {
        command.env("COCKPIT_CONTROL_ROOT", control_root);
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
