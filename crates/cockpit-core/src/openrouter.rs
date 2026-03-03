use std::{env, time::Duration};

use reqwest::Client;
use serde_json::{Value, json};

#[derive(Debug, Clone)]
pub struct LlmCallResult {
    pub status: String,
    pub text: String,
    pub model: String,
    pub usage: Value,
    pub error: Option<String>,
}

fn api_key() -> String {
    env::var("COCKPIT_OPENROUTER_API_KEY")
        .unwrap_or_default()
        .trim()
        .to_string()
}

fn base_url() -> String {
    env::var("COCKPIT_OPENROUTER_BASE_URL")
        .unwrap_or_else(|_| "https://openrouter.ai/api/v1".to_string())
        .trim_end_matches('/')
        .to_string()
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

pub async fn chat_completion(
    model: &str,
    system_prompt: &str,
    user_prompt: &str,
) -> LlmCallResult {
    let key = api_key();
    if key.is_empty() {
        return LlmCallResult {
            status: "failed".to_string(),
            text: String::new(),
            model: model.to_string(),
            usage: json!({}),
            error: Some("openrouter_api_key_missing".to_string()),
        };
    }

    let payload = json!({
        "model": model,
        "stream": false,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
    });

    let endpoint = format!("{}/chat/completions", base_url());
    let client = match Client::builder().timeout(Duration::from_secs(45)).build() {
        Ok(client) => client,
        Err(error) => {
            return LlmCallResult {
                status: "failed".to_string(),
                text: String::new(),
                model: model.to_string(),
                usage: json!({}),
                error: Some(format!("openrouter_client_build_failed: {error}")),
            };
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
            return LlmCallResult {
                status: "failed".to_string(),
                text: String::new(),
                model: model.to_string(),
                usage: json!({}),
                error: Some(format!("openrouter_unreachable: {error}")),
            };
        }
    };

    let status_code = response.status();
    let body = match response.json::<Value>().await {
        Ok(body) => body,
        Err(error) => {
            return LlmCallResult {
                status: "failed".to_string(),
                text: String::new(),
                model: model.to_string(),
                usage: json!({}),
                error: Some(format!("openrouter_invalid_json: {error}")),
            };
        }
    };

    if !status_code.is_success() {
        let detail = body
            .get("error")
            .and_then(|v| v.get("message").or(Some(v)))
            .and_then(Value::as_str)
            .unwrap_or("openrouter_http_error");
        return LlmCallResult {
            status: "failed".to_string(),
            text: String::new(),
            model: model.to_string(),
            usage: body.get("usage").cloned().unwrap_or_else(|| json!({})),
            error: Some(format!("openrouter_http_{}: {}", status_code.as_u16(), detail)),
        };
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

    if text.is_empty() {
        return LlmCallResult {
            status: "failed".to_string(),
            text,
            model: inferred_model,
            usage: body.get("usage").cloned().unwrap_or_else(|| json!({})),
            error: Some("openrouter_empty_response".to_string()),
        };
    }

    LlmCallResult {
        status: "ok".to_string(),
        text,
        model: inferred_model,
        usage: body.get("usage").cloned().unwrap_or_else(|| json!({})),
        error: None,
    }
}
