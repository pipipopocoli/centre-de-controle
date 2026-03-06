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

fn main() {
    let manifest_dir = std::env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".to_string());

    let build_sha = run_capture("git", &["-C", &manifest_dir, "rev-parse", "--short", "HEAD"])
        .unwrap_or_else(|| "unknown".to_string());
    let build_time = run_capture("date", &["-u", "+%Y-%m-%dT%H:%M:%SZ"])
        .unwrap_or_else(|| "unknown".to_string());

    println!("cargo:rustc-env=COCKPIT_BUILD_SHA={build_sha}");
    println!("cargo:rustc-env=COCKPIT_BUILD_TIME={build_time}");
    println!("cargo:rustc-env=COCKPIT_APP_MODE=cockpit_local");
}
