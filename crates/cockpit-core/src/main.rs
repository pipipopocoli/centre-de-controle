use std::{env, net::SocketAddr, path::PathBuf};

use anyhow::Context;
use cockpit_core::{app::build_router, state::AppState};
use tracing::info;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "cockpit_core=info,tower_http=info,axum=info".into()),
        )
        .init();

    let root = env::var("COCKPIT_CONTROL_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|_| default_control_root());

    let host = env::var("COCKPIT_HOST")
        .or_else(|_| env::var("COCKPIT_NEXT_HOST"))
        .unwrap_or_else(|_| "127.0.0.1".to_string());
    let port: u16 = env::var("COCKPIT_PORT")
        .or_else(|_| env::var("COCKPIT_NEXT_PORT"))
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(8787);

    let addr: SocketAddr = format!("{host}:{port}")
        .parse()
        .with_context(|| format!("invalid bind address {host}:{port}"))?;

    let state = AppState::new(root)?;
    let app = build_router(state);

    info!("cockpit-core listening on http://{addr}");

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;
    Ok(())
}

fn default_control_root() -> PathBuf {
    let cwd = env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    let candidate_direct = cwd.join("control/projects");
    if candidate_direct.exists() {
        return candidate_direct;
    }

    let candidate_repo = cwd.join("../../control/projects");
    if candidate_repo.exists() {
        return candidate_repo;
    }

    candidate_direct
}
