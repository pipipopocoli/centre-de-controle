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
            text="Prioriser API puis UI, finir tests et livrer.",
            usage=OpenRouterUsage(input_tokens=10, output_tokens=12, reasoning_tokens=2, raw={}),
            raw={},
            error=None,
        )


def main() -> int:
    result = run_agentic_turn(
        _FakeClient(),  # type: ignore[arg-type]
        mode="chat",
        user_text="On lance wave21",
        l1_model="liquid/lfm-2.5-1.2b-thinking:free",
        l2_scene_model="arcee-ai/trinity-large-preview:free",
        lfm_spawn_max=10,
        stream_enabled=True,
    )
    assert result.status == "ok"
    assert result.mode == "chat"
    authors = [str(item.get("author")) for item in result.messages]
    for expected in ["victor", "leo", "nova", "vulgarisation", "clems"]:
        assert expected in authors, authors
    assert result.spawned_agents_count == 0
    print("OK: agentic orchestrator chat mode verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

