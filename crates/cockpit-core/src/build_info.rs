pub struct BuildInfo {
    pub build_sha: &'static str,
    pub build_time: &'static str,
    pub app_mode: &'static str,
}

pub fn runtime_build_info() -> BuildInfo {
    BuildInfo {
        build_sha: option_env!("COCKPIT_BUILD_SHA").unwrap_or("unknown"),
        build_time: option_env!("COCKPIT_BUILD_TIME").unwrap_or("unknown"),
        app_mode: option_env!("COCKPIT_APP_MODE").unwrap_or("cockpit_local"),
    }
}
