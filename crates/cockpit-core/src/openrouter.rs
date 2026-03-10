use std::{env, time::Duration};

const DEFAULT_OPENROUTER_BASE_URL: &str = "https://openrouter.ai/api/v1";

use reqwest::{
    Client,
    header::{CONTENT_TYPE, HeaderMap},
};
use serde_json::{Value, error::Category, json};

#[derive(Debug, Clone)]
pub struct LlmCallResult {
    pub status: String,
    pub text: String,
    pub model: String,
    pub usage: Value,
    pub error: Option<String>,
    pub diagnostics: Option<OpenRouterCallDiagnostics>,
}

#[derive(Debug, Clone, Default)]
pub struct ChatCompletionOptions {
    pub max_tokens: Option<u32>,
    pub temperature: Option<f32>,
}

#[derive(Debug, Clone, Default)]
pub struct OpenRouterCallDiagnostics {
    pub error_kind: Option<String>,
    pub http_status: Option<u16>,
    pub request_id: Option<String>,
    pub body_preview: Option<String>,
}

/// Maps legacy provider codes to OpenRouter model identifiers.
/// Ensures OpenRouter-only execution while preserving backward compatibility.
/// ISSUE-W20R-A9-005: Legacy provider normalization
pub fn normalize_legacy_provider(provider: &str) -> String {
    match provider.to_uppercase().as_str() {
        "CDX" => "moonshotai/kimi-k2.5".to_string(),
        "AG" => "moonshotai/kimi-k2.5".to_string(),
        "OLL" => "moonshotai/kimi-k2.5".to_string(),
        "OPENROUTER" => "moonshotai/kimi-k2.5".to_string(),
        _ => {
            // If it contains '/', assume it's already an OpenRouter model path
            if provider.contains('/') {
                provider.to_string()
            } else {
                // Default fallback for unrecognized providers
                "moonshotai/kimi-k2.5".to_string()
            }
        }
    }
}

fn api_key() -> String {
    env::var("COCKPIT_OPENROUTER_API_KEY")
        .unwrap_or_default()
        .trim()
        .to_string()
}

fn base_url() -> String {
    env::var("COCKPIT_OPENROUTER_BASE_URL")
        .unwrap_or_else(|_| DEFAULT_OPENROUTER_BASE_URL.to_string())
        .trim_end_matches('/')
        .to_string()
}

pub fn health_base_url() -> String {
    match env::var("COCKPIT_OPENROUTER_BASE_URL") {
        Ok(value) => value.trim().trim_end_matches('/').to_string(),
        Err(_) => DEFAULT_OPENROUTER_BASE_URL.to_string(),
    }
}

pub fn health_api_key_present() -> bool {
    !api_key().is_empty()
}

fn extract_text(content: &Value) -> String {
    if let Some(text) = content.as_str() {
        return text.trim().to_string();
    }

    if let Some(parts) = content.as_array() {
        let mut chunks = Vec::new();
        for part in parts {
            if let Some(text) = part.get("text").and_then(Value::as_str) {
                if !text.trim().is_empty() {
                    chunks.push(text.trim().to_string());
                }
            }
        }
        return chunks.join("\n");
    }

    String::new()
}

fn request_id(headers: &HeaderMap) -> Option<String> {
    ["x-request-id", "request-id", "x-openrouter-request-id"]
        .iter()
        .find_map(|name| headers.get(*name))
        .and_then(|value| value.to_str().ok())
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(ToString::to_string)
}

fn content_type(headers: &HeaderMap) -> Option<String> {
    headers
        .get(CONTENT_TYPE)
        .and_then(|value| value.to_str().ok())
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(ToString::to_string)
}

fn sanitize_body_preview(raw: &str) -> Option<String> {
    let compact = raw.split_whitespace().collect::<Vec<_>>().join(" ");
    if compact.is_empty() {
        return None;
    }
    let preview: String = compact.chars().take(180).collect();
    Some(preview)
}

fn classify_json_error(
    content_type: Option<&str>,
    body_text: &str,
    error: &serde_json::Error,
) -> &'static str {
    let trimmed = body_text.trim();
    let content_type = content_type.unwrap_or_default().to_ascii_lowercase();
    if trimmed.is_empty() {
        return "openrouter_empty_body";
    }
    if content_type.contains("text/html")
        || trimmed.starts_with("<!DOCTYPE")
        || trimmed.starts_with("<!doctype")
        || trimmed.starts_with("<html")
    {
        return "openrouter_html_error";
    }
    if matches!(error.classify(), Category::Eof) {
        return "openrouter_truncated_body";
    }
    "openrouter_invalid_json"
}

fn failure_result(
    model: &str,
    error: String,
    diagnostics: OpenRouterCallDiagnostics,
    usage: Value,
) -> LlmCallResult {
    LlmCallResult {
        status: "failed".to_string(),
        text: String::new(),
        model: model.to_string(),
        usage,
        error: Some(error),
        diagnostics: Some(diagnostics),
    }
}

async fn parse_response_body(model: &str, response: reqwest::Response) -> LlmCallResult {
    let status_code = response.status();
    let headers = response.headers().clone();
    let content_type = content_type(&headers);
    let request_id = request_id(&headers);
    let body_text = match response.text().await {
        Ok(body) => body,
        Err(error) => {
            return failure_result(
                model,
                format!("openrouter_unreadable_body: {error}"),
                OpenRouterCallDiagnostics {
                    error_kind: Some("openrouter_unreadable_body".to_string()),
                    http_status: Some(status_code.as_u16()),
                    request_id,
                    body_preview: None,
                },
                json!({}),
            );
        }
    };

    let preview = sanitize_body_preview(&body_text);
    let body = match serde_json::from_str::<Value>(&body_text) {
        Ok(body) => body,
        Err(error) => {
            let error_kind = classify_json_error(content_type.as_deref(), &body_text, &error);
            let detail = if error_kind == "openrouter_empty_body" {
                error_kind.to_string()
            } else {
                format!("{error_kind}: {error}")
            };
            return failure_result(
                model,
                detail,
                OpenRouterCallDiagnostics {
                    error_kind: Some(error_kind.to_string()),
                    http_status: Some(status_code.as_u16()),
                    request_id,
                    body_preview: preview,
                },
                json!({}),
            );
        }
    };

    let usage = body.get("usage").cloned().unwrap_or_else(|| json!({}));
    if !status_code.is_success() {
        let detail = body
            .get("error")
            .and_then(|value| value.get("message").or(Some(value)))
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|value| !value.is_empty())
            .or_else(|| preview.as_deref())
            .unwrap_or("openrouter_http_error");
        let error_kind = format!("openrouter_http_{}", status_code.as_u16());
        return failure_result(
            model,
            format!("{error_kind}: {detail}"),
            OpenRouterCallDiagnostics {
                error_kind: Some(error_kind),
                http_status: Some(status_code.as_u16()),
                request_id,
                body_preview: preview,
            },
            usage,
        );
    }

    let text = body
        .get("choices")
        .and_then(Value::as_array)
        .and_then(|choices| choices.first())
        .and_then(|first| first.get("message"))
        .and_then(|msg| msg.get("content"))
        .map(extract_text)
        .unwrap_or_default();

    let inferred_model = body
        .get("model")
        .and_then(Value::as_str)
        .unwrap_or(model)
        .to_string();

    if text.trim().is_empty() {
        return failure_result(
            &inferred_model,
            "openrouter_empty_response".to_string(),
            OpenRouterCallDiagnostics {
                error_kind: Some("openrouter_empty_response".to_string()),
                http_status: Some(status_code.as_u16()),
                request_id,
                body_preview: preview,
            },
            usage,
        );
    }

    LlmCallResult {
        status: "ok".to_string(),
        text: text.trim().to_string(),
        model: inferred_model,
        usage,
        error: None,
        diagnostics: Some(OpenRouterCallDiagnostics {
            error_kind: None,
            http_status: Some(status_code.as_u16()),
            request_id,
            body_preview: None,
        }),
    }
}

pub async fn chat_completion(model: &str, system_prompt: &str, user_prompt: &str) -> LlmCallResult {
    chat_completion_with_options(
        model,
        system_prompt,
        user_prompt,
        &ChatCompletionOptions::default(),
    )
    .await
}

pub async fn chat_completion_with_options(
    model: &str,
    system_prompt: &str,
    user_prompt: &str,
    options: &ChatCompletionOptions,
) -> LlmCallResult {
    let key = api_key();
    if key.is_empty() {
        return failure_result(
            model,
            "openrouter_api_key_missing".to_string(),
            OpenRouterCallDiagnostics {
                error_kind: Some("openrouter_api_key_missing".to_string()),
                ..OpenRouterCallDiagnostics::default()
            },
            json!({}),
        );
    }

    let mut payload = json!({
        "model": model,
        "stream": false,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
    });

    if let Some(max_tokens) = options.max_tokens {
        payload["max_tokens"] = Value::from(max_tokens);
    }
    if let Some(temperature) = options.temperature {
        payload["temperature"] = Value::from(temperature);
    }

    let endpoint = format!("{}/chat/completions", base_url());
    let client = match Client::builder().timeout(Duration::from_secs(45)).build() {
        Ok(client) => client,
        Err(error) => {
            return failure_result(
                model,
                format!("openrouter_client_build_failed: {error}"),
                OpenRouterCallDiagnostics {
                    error_kind: Some("openrouter_client_build_failed".to_string()),
                    ..OpenRouterCallDiagnostics::default()
                },
                json!({}),
            );
        }
    };

    let response = match client
        .post(endpoint)
        .bearer_auth(key)
        .header("content-type", "application/json")
        .header("accept", "application/json")
        .json(&payload)
        .send()
        .await
    {
        Ok(response) => response,
        Err(error) => {
            let error_kind = if error.is_timeout() {
                "openrouter_timeout"
            } else {
                "openrouter_unreachable"
            };
            return failure_result(
                model,
                format!("{error_kind}: {error}"),
                OpenRouterCallDiagnostics {
                    error_kind: Some(error_kind.to_string()),
                    ..OpenRouterCallDiagnostics::default()
                },
                json!({}),
            );
        }
    };

    parse_response_body(model, response).await
}

pub async fn transcribe_audio(
    model: &str,
    audio_base64: &str,
    audio_format: &str,
) -> LlmCallResult {
    let key = api_key();
    if key.is_empty() {
        return failure_result(
            model,
            "openrouter_api_key_missing".to_string(),
            OpenRouterCallDiagnostics {
                error_kind: Some("openrouter_api_key_missing".to_string()),
                ..OpenRouterCallDiagnostics::default()
            },
            json!({}),
        );
    }

    let payload = json!({
        "model": model,
        "stream": false,
        "temperature": 0.0,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Transcribe this audio exactly. Return plain text only."},
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_base64,
                            "format": audio_format,
                        }
                    }
                ]
            }
        ],
    });

    let endpoint = format!("{}/chat/completions", base_url());
    let client = match Client::builder().timeout(Duration::from_secs(60)).build() {
        Ok(client) => client,
        Err(error) => {
            return failure_result(
                model,
                format!("openrouter_client_build_failed: {error}"),
                OpenRouterCallDiagnostics {
                    error_kind: Some("openrouter_client_build_failed".to_string()),
                    ..OpenRouterCallDiagnostics::default()
                },
                json!({}),
            );
        }
    };

    let response = match client
        .post(endpoint)
        .bearer_auth(key)
        .header("content-type", "application/json")
        .header("accept", "application/json")
        .json(&payload)
        .send()
        .await
    {
        Ok(response) => response,
        Err(error) => {
            let error_kind = if error.is_timeout() {
                "openrouter_timeout"
            } else {
                "openrouter_unreachable"
            };
            return failure_result(
                model,
                format!("{error_kind}: {error}"),
                OpenRouterCallDiagnostics {
                    error_kind: Some(error_kind.to_string()),
                    ..OpenRouterCallDiagnostics::default()
                },
                json!({}),
            );
        }
    };

    parse_response_body(model, response).await
}

#[cfg(test)]
mod tests {
    use super::{classify_json_error, sanitize_body_preview};
    use serde_json::Value;

    #[test]
    fn classifies_empty_body() {
        let error = serde_json::from_str::<Value>("").expect_err("expected parse error");
        assert_eq!(
            classify_json_error(Some("application/json"), "", &error),
            "openrouter_empty_body"
        );
    }

    #[test]
    fn classifies_html_error_body() {
        let body = "<html><body>Bad gateway</body></html>";
        let error = serde_json::from_str::<Value>(body).expect_err("expected parse error");
        assert_eq!(
            classify_json_error(Some("text/html"), body, &error),
            "openrouter_html_error"
        );
    }

    #[test]
    fn classifies_truncated_json_body() {
        let body = "{\"choices\":[{\"message\":{\"content\":\"hello\"}}";
        let error = serde_json::from_str::<Value>(body).expect_err("expected parse error");
        assert_eq!(
            classify_json_error(Some("application/json"), body, &error),
            "openrouter_truncated_body"
        );
    }

    #[test]
    fn classifies_invalid_json_body() {
        let body = "{\"choices\": nope}";
        let error = serde_json::from_str::<Value>(body).expect_err("expected parse error");
        assert_eq!(
            classify_json_error(Some("application/json"), body, &error),
            "openrouter_invalid_json"
        );
    }

    #[test]
    fn sanitizes_body_preview() {
        let preview =
            sanitize_body_preview("  <html>\nboom\tboom  ").expect("preview should exist");
        assert_eq!(preview, "<html> boom boom");
    }
}
