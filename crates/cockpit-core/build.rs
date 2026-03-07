use std::path::{Path, PathBuf};
use std::process::Command;

fn run_capture(cmd: &str, args: &[&str]) -> Option<String> {
    let output = Command::new(cmd).args(args).output().ok()?;
    if !output.status.success() {
        return None;
    }
    let value = String::from_utf8(output.stdout).ok()?;
    let trimmed = value.trim();
    if trimmed.is_empty() {
        return None;
    }
    Some(trimmed.to_string())
}

fn repo_path(base: &Path, value: &str) -> PathBuf {
    let path = PathBuf::from(value);
    if path.is_absolute() {
        path
    } else {
        base.join(path)
    }
}

fn main() {
    let manifest_dir = std::env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".to_string());
    let repo_root = run_capture("git", &["-C", &manifest_dir, "rev-parse", "--show-toplevel"])
        .unwrap_or_else(|| manifest_dir.clone());
    let repo_root_path = PathBuf::from(&repo_root);

    println!("cargo:rerun-if-env-changed=COCKPIT_BUILD_SHA");
    println!("cargo:rerun-if-env-changed=COCKPIT_BUILD_TIME");
    println!("cargo:rerun-if-env-changed=COCKPIT_APP_MODE");

    if let Some(git_dir) = run_capture("git", &["-C", &repo_root, "rev-parse", "--git-dir"]) {
        let git_dir_path = repo_path(&repo_root_path, &git_dir);
        println!("cargo:rerun-if-changed={}", git_dir_path.join("HEAD").display());
        println!(
            "cargo:rerun-if-changed={}",
            git_dir_path.join("packed-refs").display()
        );
        if let Some(head_ref) = run_capture("git", &["-C", &repo_root, "symbolic-ref", "-q", "HEAD"]) {
            println!(
                "cargo:rerun-if-changed={}",
                git_dir_path.join(head_ref).display()
            );
        }
    }

    let build_sha = std::env::var("COCKPIT_BUILD_SHA")
        .ok()
        .filter(|value| !value.trim().is_empty())
        .or_else(|| run_capture("git", &["-C", &repo_root, "rev-parse", "--short", "HEAD"]))
        .unwrap_or_else(|| "unknown".to_string());
    let build_time = std::env::var("COCKPIT_BUILD_TIME")
        .ok()
        .filter(|value| !value.trim().is_empty())
        .or_else(|| run_capture("date", &["-u", "+%Y-%m-%dT%H:%M:%SZ"]))
        .unwrap_or_else(|| "unknown".to_string());
    let app_mode = std::env::var("COCKPIT_APP_MODE")
        .ok()
        .filter(|value| !value.trim().is_empty())
        .unwrap_or_else(|| "cockpit_local".to_string());

    println!("cargo:rustc-env=COCKPIT_BUILD_SHA={build_sha}");
    println!("cargo:rustc-env=COCKPIT_BUILD_TIME={build_time}");
    println!("cargo:rustc-env=COCKPIT_APP_MODE={app_mode}");
}
