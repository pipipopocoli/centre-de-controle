from __future__ import annotations

from typing import Any


DEFAULT_WEIGHTS = {
    "skill_match": 0.45,
    "availability": 0.20,
    "cost": 0.15,
    "history": 0.20,
}

# Deterministic ranking contract for equal scores.
RANK_TIE_BREAK_CONTRACT = ("score_desc", "agent_id_asc", "request_id_asc")

PROVIDER_COST_SCORE = {
    "openrouter": 0.80,
}

WAITING_STATUSES = {"queued", "dispatched", "reminded", "pinged", "waiting_reconfirm"}
ACTION_STATUSES = {"planning", "executing", "verifying", "in_progress"}
BLOCKED_STATUSES = {"blocked", "error", "failed", "timeout"}


def _clamp01(value: Any, default: float = 0.0) -> float:
    try:
        raw = float(value)
    except (TypeError, ValueError):
        raw = float(default)
    if raw < 0.0:
        return 0.0
    if raw > 1.0:
        return 1.0
    return raw


def _normalized_weights(raw: dict[str, Any] | None) -> dict[str, float]:
    base = dict(DEFAULT_WEIGHTS)
    if isinstance(raw, dict):
        for key in list(base.keys()):
            if key in raw:
                try:
                    base[key] = float(raw[key])
                except (TypeError, ValueError):
                    pass
    total = sum(max(value, 0.0) for value in base.values())
    if total <= 0.0:
        return dict(DEFAULT_WEIGHTS)
    return {key: max(value, 0.0) / total for key, value in base.items()}


def _extract_request_text(payload: dict[str, Any]) -> str:
    msg = payload.get("message") if isinstance(payload.get("message"), dict) else {}
    parts = [
        str(payload.get("request_id") or ""),
        str(payload.get("source") or ""),
        str(msg.get("text") or ""),
        " ".join(str(item) for item in (msg.get("tags") or []) if str(item).strip()),
    ]
    return " ".join(part for part in parts if part).strip().lower()


def _skill_match(agent_meta: dict[str, Any], request_payload: dict[str, Any]) -> float:
    request_text = _extract_request_text(request_payload)
    if not request_text:
        return 0.5

    skills = [str(item).strip().lower() for item in (agent_meta.get("skills") or []) if str(item).strip()]
    role = str(agent_meta.get("role") or "").strip().lower()
    if role:
        skills.append(role)

    if not skills:
        return 0.5

    hits = 0
    for skill in skills:
        if skill and skill in request_text:
            hits += 1
    return _clamp01(hits / max(len(skills), 1), default=0.0)


def _availability(agent_meta: dict[str, Any]) -> float:
    status = str(agent_meta.get("status") or "idle").strip().lower()
    if status in BLOCKED_STATUSES:
        return 0.1
    if status in WAITING_STATUSES:
        return 0.4
    if status in ACTION_STATUSES:
        return 0.65
    return 0.95


def _cost_score(agent_meta: dict[str, Any], cost: dict[str, Any] | None) -> float:
    provider = str(agent_meta.get("platform") or "openrouter").strip().lower()
    if isinstance(cost, dict):
        provider_map = cost.get("provider_score")
        if isinstance(provider_map, dict) and provider in provider_map:
            return _clamp01(provider_map.get(provider), default=PROVIDER_COST_SCORE.get(provider, 0.5))
    return _clamp01(PROVIDER_COST_SCORE.get(provider, 0.5), default=0.5)


def _history_score(history: dict[str, Any] | None) -> float:
    if not isinstance(history, dict):
        return 0.5
    success_rate = history.get("success_rate")
    return _clamp01(success_rate, default=0.5)


def score_task(
    agent_meta: dict[str, Any],
    request_payload: dict[str, Any],
    history: dict[str, Any] | None = None,
    cost: dict[str, Any] | None = None,
    weights: dict[str, Any] | None = None,
) -> float:
    w = _normalized_weights(weights)
    skill = _skill_match(agent_meta, request_payload)
    availability = _availability(agent_meta)
    cost_score = _cost_score(agent_meta, cost)
    history_score = _history_score(history)

    total = (
        w["skill_match"] * skill
        + w["availability"] * availability
        + w["cost"] * cost_score
        + w["history"] * history_score
    )
    return round(total, 6)


def rank_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def _score_for(candidate: dict[str, Any]) -> float:
        if "score" in candidate:
            return float(candidate.get("score") or 0.0)
        return float(
            score_task(
                candidate.get("agent_meta") if isinstance(candidate.get("agent_meta"), dict) else {},
                candidate.get("request_payload") if isinstance(candidate.get("request_payload"), dict) else {},
                history=candidate.get("history") if isinstance(candidate.get("history"), dict) else None,
                cost=candidate.get("cost") if isinstance(candidate.get("cost"), dict) else None,
                weights=candidate.get("weights") if isinstance(candidate.get("weights"), dict) else None,
            )
        )

    ranked = []
    for candidate in candidates:
        row = dict(candidate)
        row["score"] = _score_for(row)
        ranked.append(row)

    # Deterministic tie-break contract: score desc, then agent_id, then request_id.
    ranked.sort(
        key=lambda item: (
            -float(item.get("score") or 0.0),
            str(item.get("agent_id") or ""),
            str(item.get("request_id") or ""),
        )
    )
    return ranked
