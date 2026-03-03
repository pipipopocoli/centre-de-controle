from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from server.llm.openrouter_client import OpenRouterChatResult, OpenRouterClient


L1_AGENT_IDS = ["victor", "leo", "nova", "vulgarisation"]


@dataclass(frozen=True)
class AgenticTurnResult:
    status: str
    mode: str
    messages: list[dict[str, Any]]
    clems_summary: str
    spawned_agents_count: int
    model_usage: dict[str, Any]
    error: str | None = None


def _trim_text(value: str, limit: int = 1200) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(limit - 3, 0)] + "..."


def _usage_row(result: OpenRouterChatResult) -> dict[str, Any]:
    return {
        "model": result.model,
        "status": result.status,
        "input_tokens": result.usage.input_tokens,
        "output_tokens": result.usage.output_tokens,
        "reasoning_tokens": result.usage.reasoning_tokens,
        "error": result.error,
    }


def _fallback_l1_text(user_text: str) -> str:
    text = _trim_text(user_text, limit=320)
    return (
        "Plan rapide: clarifier scope, verrouiller critères de succès, puis exécuter lot backend/API/UI. "
        f"Contexte utilisateur: {text}"
    )


def _build_l1_messages(base_text: str) -> list[dict[str, Any]]:
    cleaned = _trim_text(base_text, 1100)
    return [
        {"author": "victor", "text": f"Backend focus: {cleaned}"},
        {"author": "leo", "text": f"UI focus: {cleaned}"},
        {
            "author": "nova",
            "text": (
                f"Research focus: {cleaned} | owner=nova | next_action=validate_assumptions "
                "evidence_path=runs/ latest | decision_tag=adopt"
            ),
        },
        {"author": "vulgarisation", "text": f"Version simple: {cleaned}"},
    ]


def _build_scene_spawn_messages(scene_text: str, spawn_count: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    excerpt = _trim_text(scene_text, 260)
    for index in range(spawn_count):
        out.append(
            {
                "author": f"lfm-agent-{index + 1}",
                "text": f"Subtask {index + 1}/{spawn_count}: execute scene plan chunk from '{excerpt}'.",
            }
        )
    return out


def _parse_json_text(text: str) -> dict[str, Any] | None:
    raw = str(text or "").strip()
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def run_agentic_turn(
    client: OpenRouterClient,
    *,
    mode: str,
    user_text: str,
    l1_model: str,
    l2_scene_model: str,
    lfm_spawn_max: int,
    stream_enabled: bool,
) -> AgenticTurnResult:
    normalized_mode = str(mode or "chat").strip().lower()
    if normalized_mode not in {"chat", "scene"}:
        normalized_mode = "chat"

    usage_rows: list[dict[str, Any]] = []
    safe_user_text = _trim_text(user_text, 4000)

    if normalized_mode == "chat":
        system_prompt = (
            "You are Cockpit L1 orchestration engine. Reply with short actionable text in French. "
            "If possible return compact JSON: {\"core\":\"...\"}."
        )
        primary = client.chat(
            model=l1_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": safe_user_text},
            ],
            stream=bool(stream_enabled),
        )
        usage_rows.append(_usage_row(primary))
        parsed = _parse_json_text(primary.text)
        if parsed and isinstance(parsed.get("core"), str):
            base_text = str(parsed.get("core"))
        elif primary.status == "ok" and primary.text:
            base_text = primary.text
        else:
            base_text = _fallback_l1_text(safe_user_text)

        l1_messages = _build_l1_messages(base_text)
        clems_summary = f"Synthese: {_trim_text(base_text, 380)}"
        if primary.status != "ok":
            return AgenticTurnResult(
                status="degraded",
                mode=normalized_mode,
                messages=l1_messages + [{"author": "clems", "text": clems_summary}],
                clems_summary=clems_summary,
                spawned_agents_count=0,
                model_usage={"calls": usage_rows},
                error=primary.error or "openrouter_chat_failed",
            )
        return AgenticTurnResult(
            status="ok",
            mode=normalized_mode,
            messages=l1_messages + [{"author": "clems", "text": clems_summary}],
            clems_summary=clems_summary,
            spawned_agents_count=0,
            model_usage={"calls": usage_rows},
            error=None,
        )

    scene_prompt = (
        "You are Cockpit scene planner. Return practical scene strategy and decomposition for a software project."
    )
    scene = client.chat(
        model=l2_scene_model,
        messages=[
            {"role": "system", "content": scene_prompt},
            {"role": "user", "content": safe_user_text},
        ],
        stream=bool(stream_enabled),
    )
    usage_rows.append(_usage_row(scene))
    if scene.status == "ok" and scene.text:
        scene_text = scene.text
    else:
        scene_text = f"Scene fallback: {_fallback_l1_text(safe_user_text)}"

    max_spawn = max(1, min(int(lfm_spawn_max), 10))
    estimated_spawn = max(1, min(max_spawn, len(safe_user_text.split()) // 35 + 1))
    spawned = _build_scene_spawn_messages(scene_text, estimated_spawn)
    l1_messages = _build_l1_messages(scene_text)
    summary = f"Scene plan ready. Spawned {estimated_spawn} LFM helper agents."
    all_messages = [{"author": "scene", "text": _trim_text(scene_text, 1800)}] + spawned + l1_messages
    all_messages.append({"author": "clems", "text": summary})

    status = "ok" if scene.status == "ok" else "degraded"
    return AgenticTurnResult(
        status=status,
        mode=normalized_mode,
        messages=all_messages,
        clems_summary=summary,
        spawned_agents_count=estimated_spawn,
        model_usage={"calls": usage_rows},
        error=None if scene.status == "ok" else (scene.error or "openrouter_scene_failed"),
    )

