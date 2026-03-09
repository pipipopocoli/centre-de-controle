use std::collections::BTreeSet;

use serde_json::Value;

use crate::models::ChatMode;

const L1_DEFAULTS: &[&str] = &["victor", "leo", "nova", "vulgarisation"];
const DIRECTABLE: &[&str] = &["clems", "victor", "leo", "nova", "vulgarisation"];

pub fn extract_mentions(text: &str) -> Vec<String> {
    text.split_whitespace()
        .filter_map(|token| token.strip_prefix('@'))
        .map(|raw| {
            raw.chars()
                .take_while(|c| c.is_ascii_alphanumeric() || *c == '-' || *c == '_')
                .collect::<String>()
                .to_lowercase()
        })
        .filter(|v| !v.is_empty())
        .collect()
}

pub fn is_directable_agent(agent_id: &str) -> bool {
    DIRECTABLE.contains(&agent_id) || agent_id.starts_with("agent-")
}

pub fn resolve_direct_target(target_agent_id: Option<&str>, mentions: &[String]) -> String {
    if let Some(target) = target_agent_id {
        if is_directable_agent(target) {
            return target.to_string();
        }
    }

    for mention in mentions {
        if is_directable_agent(mention) {
            return mention.clone();
        }
    }
    "clems".to_string()
}

pub fn conceal_targets(mentions: &[String]) -> Vec<String> {
    let explicit: BTreeSet<String> = mentions
        .iter()
        .filter(|mention| mention.as_str() != "clems")
        .filter(|mention| is_directable_agent(mention))
        .cloned()
        .collect();

    if !mentions.is_empty() && explicit.is_empty() {
        return Vec::new();
    }

    if !explicit.is_empty() {
        return explicit.into_iter().collect();
    }

    let mut out = BTreeSet::new();
    for &agent in L1_DEFAULTS {
        out.insert(agent.to_string());
    }
    for mention in mentions {
        if mention == "clems" {
            continue;
        }
        if is_directable_agent(mention) {
            out.insert(mention.clone());
        }
    }
    out.into_iter().collect()
}

pub fn conceal_targets_from_context(
    context_ref: Option<&Value>,
    mentions: &[String],
) -> Vec<String> {
    if let Some(context_ref) = context_ref {
        if let Some(room_participants) = context_ref
            .get("room_participants")
            .and_then(Value::as_array)
        {
            let explicit: BTreeSet<String> = room_participants
                .iter()
                .filter_map(Value::as_str)
                .map(str::trim)
                .filter(|value| !value.is_empty() && *value != "clems")
                .filter(|value| is_directable_agent(value))
                .map(ToString::to_string)
                .collect();
            if !explicit.is_empty() {
                return explicit.into_iter().collect();
            }
        }
    }

    conceal_targets(mentions)
}

pub fn generate_agent_reply(agent_id: &str, text: &str, mode: ChatMode) -> String {
    match mode {
        ChatMode::Direct => {
            format!(
                "{agent_id}: recu en direct. Action immediate sur: \"{}\".",
                text.trim()
            )
        }
        ChatMode::ConcealRoom => {
            format!(
                "{agent_id}: input capture en conceal room. Je publie mon output live sur cette tache.",
            )
        }
    }
}

pub fn clems_summary(text: &str, context_snippets: &[String]) -> String {
    let clean_text = text.trim();
    if let Some(first_snippet) = context_snippets.first() {
        let normalized = first_snippet.replace('\n', " ");
        let compact = if normalized.chars().count() > 140 {
            let clipped: String = normalized.chars().take(137).collect();
            format!("{clipped}...")
        } else {
            normalized
        };

        return format!(
            "@clems summary: {compact}. Prochaine action: coordonner la suite sur \"{clean_text}\"."
        );
    }

    format!(
        "@clems summary: pas encore de retour exploitable des participants. Prochaine action: relancer la room sur \"{clean_text}\" ou continuer avec moi directement."
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn direct_defaults_to_clems() {
        let mentions = vec!["nobody".to_string()];
        assert_eq!(resolve_direct_target(None, &mentions), "clems");
    }

    #[test]
    fn direct_respects_explicit_mention() {
        let mentions = vec!["leo".to_string(), "clems".to_string()];
        assert_eq!(resolve_direct_target(None, &mentions), "leo");
    }

    #[test]
    fn direct_prefers_explicit_target_agent() {
        let mentions = vec!["leo".to_string()];
        assert_eq!(resolve_direct_target(Some("agent-9"), &mentions), "agent-9");
    }

    #[test]
    fn direct_ignores_invalid_target_agent() {
        let mentions = vec!["leo".to_string()];
        assert_eq!(resolve_direct_target(Some("antigravity"), &mentions), "leo");
    }

    #[test]
    fn conceal_defaults_to_l1_when_no_mentions() {
        let targets = conceal_targets(&[]);
        assert!(targets.contains(&"victor".to_string()));
        assert!(targets.contains(&"leo".to_string()));
        assert!(targets.contains(&"nova".to_string()));
        assert!(targets.contains(&"vulgarisation".to_string()));
    }

    #[test]
    fn conceal_respects_explicit_mentions_only() {
        let mentions = vec!["agent-9".to_string(), "clems".to_string()];
        let targets = conceal_targets(&mentions);
        assert!(targets.contains(&"agent-9".to_string()));
        assert_eq!(targets.len(), 1);
    }

    #[test]
    fn conceal_with_clems_only_keeps_summary_only() {
        let mentions = vec!["clems".to_string()];
        let targets = conceal_targets(&mentions);
        assert!(targets.is_empty());
    }

    #[test]
    fn conceal_context_participants_override_mentions() {
        let context = serde_json::json!({
            "room_participants": ["clems", "leo", "victor"],
        });
        let mentions = vec!["clems".to_string()];
        let targets = conceal_targets_from_context(Some(&context), &mentions);
        assert_eq!(targets, vec!["leo".to_string(), "victor".to_string()]);
    }

    #[test]
    fn mention_parser_handles_symbols() {
        let m = extract_mentions("allo @clems ping @agent-3, merci @victor!");
        assert_eq!(m, vec!["clems", "agent-3", "victor"]);
    }

    #[test]
    fn clems_summary_without_context_is_honest() {
        let summary = clems_summary("relance la room", &[]);
        assert!(summary.contains("pas encore de retour exploitable"));
        assert!(!summary.contains("contribution(s) en attente"));
    }

    #[test]
    fn clems_summary_with_context_uses_real_snippet() {
        let summary = clems_summary("corrige le bug", &[String::from("@leo patch en cours")]);
        assert!(summary.contains("@leo patch en cours"));
        assert!(!summary.contains("contribution(s) en attente"));
    }
}
