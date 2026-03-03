from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from server.llm.agentic_orchestrator import run_agentic_turn  # noqa: E402
from server.llm.openrouter_client import OpenRouterChatResult, OpenRouterUsage  # noqa: E402


class _FakeClient:
    def chat(self, *, model, messages, stream=False, temperature=0.2):  # noqa: ANN001
        return OpenRouterChatResult(
            status="ok",
            model=model,
            text="Scene strategy: découper backend/API/UI en lots parallèles avec checkpoints quotidiens.",
            usage=OpenRouterUsage(input_tokens=20, output_tokens=18, reasoning_tokens=4, raw={}),
            raw={},
            error=None,
        )


def main() -> int:
    result = run_agentic_turn(
        _FakeClient(),  # type: ignore[arg-type]
        mode="scene",
        user_text="Prépare une scène multi-agent pour un gros launch",
        l1_model="liquid/lfm-2.5-1.2b-thinking:free",
        l2_scene_model="arcee-ai/trinity-large-preview:free",
        lfm_spawn_max=3,
        stream_enabled=False,
    )
    assert result.mode == "scene"
    assert result.spawned_agents_count <= 3
    authors = [str(item.get("author")) for item in result.messages]
    assert "scene" in authors
    assert "clems" in authors
    assert any(author.startswith("lfm-agent-") for author in authors), authors
    print("OK: agentic orchestrator scene mode verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

