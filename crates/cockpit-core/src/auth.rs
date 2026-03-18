use axum::{
    extract::Request,
    http::{HeaderMap, StatusCode},
    middleware::Next,
    response::{IntoResponse, Response},
};
use serde_json::json;

/// Lightweight bearer-token auth middleware.
///
/// When `COCKPIT_API_TOKEN` is set, every request (except `/healthz`) must
/// include `Authorization: Bearer <token>`.  When the env var is absent or
/// empty the middleware is a pass-through so local dev stays frictionless.
pub async fn require_token(headers: HeaderMap, request: Request, next: Next) -> Response {
    let expected = match std::env::var("COCKPIT_API_TOKEN") {
        Ok(val) if !val.trim().is_empty() => val.trim().to_string(),
        _ => return next.run(request).await, // no token configured → skip auth
    };

    // Allow healthz without auth
    if request.uri().path() == "/healthz" {
        return next.run(request).await;
    }

    let provided = headers
        .get("authorization")
        .and_then(|v| v.to_str().ok())
        .and_then(|v| v.strip_prefix("Bearer "))
        .map(|v| v.trim());

    match provided {
        Some(token) if token == expected => next.run(request).await,
        _ => (
            StatusCode::UNAUTHORIZED,
            axum::Json(json!({ "error": "missing or invalid bearer token" })),
        )
            .into_response(),
    }
}
