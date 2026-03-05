use std::collections::BTreeSet;

use crate::models::ChatMode;

const L1_DEFAULTS: &[&str] = &["victor", "leo", "nova", "vulgarisation"];
const DIRECTABLE: &[&str] = &[
    "clems",
    "victor",
    "leo",
    "nova",
    "vulgarisation",
    "antigravity",
];

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

pub fn resolve_direct_target(mentions: &[String]) -> String {
    for mention in mentions {
        if DIRECTABLE.contains(&mention.as_str()) || mention.starts_with("agent-") {
            return mention.clone();
        }
    }
    "clems".to_string()
}

pub fn conceal_targets(mentions: &[String]) -> Vec<String> {
    let mut out = BTreeSet::new();
    for &agent in L1_DEFAULTS {
        out.insert(agent.to_string());
    }
    for mention in mentions {
        if mention == "clems" {
            continue;
        }
        if DIRECTABLE.contains(&mention.as_str()) || mention.starts_with("agent-") {
            out.insert(mention.clone());
        }
    }
    out.into_iter().collect()
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

pub fn clems_summary(text: &str, contributor_count: usize) -> String {
    format!(
        "@clems summary: {} contribution(s) recues. Prochaine action: executer \"{}\" puis confirmer Now/Next/Blockers.",
        contributor_count,
        text.trim()
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn direct_defaults_to_clems() {
        let mentions = vec!["nobody".to_string()];
        assert_eq!(resolve_direct_target(&mentions), "clems");
    }

    #[test]
    fn direct_respects_explicit_mention() {
        let mentions = vec!["leo".to_string(), "clems".to_string()];
        assert_eq!(resolve_direct_target(&mentions), "leo");
    }

    #[test]
    fn conceal_includes_l1_plus_mentions() {
        let mentions = vec!["agent-9".to_string(), "clems".to_string()];
        let targets = conceal_targets(&mentions);
        assert!(targets.contains(&"victor".to_string()));
        assert!(targets.contains(&"leo".to_string()));
        assert!(targets.contains(&"nova".to_string()));
        assert!(targets.contains(&"vulgarisation".to_string()));
        assert!(targets.contains(&"agent-9".to_string()));
        assert!(!targets.contains(&"clems".to_string()));
    }

    #[test]
    fn mention_parser_handles_symbols() {
        let m = extract_mentions("allo @clems ping @agent-3, merci @victor!");
        assert_eq!(m, vec!["clems", "agent-3", "victor"]);
    }
}
