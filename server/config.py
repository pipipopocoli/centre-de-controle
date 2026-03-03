from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _default_projects_root() -> Path:
    return Path.home() / "Library" / "Application Support" / "Cockpit" / "projects"


@dataclass(frozen=True)
class APISettings:
    projects_root: Path
    secret_key: str
    issuer: str
    access_ttl_seconds: int
    refresh_ttl_seconds: int
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    model_voice_stt: str = "google/gemini-2.5-flash"
    model_l1: str = "liquid/lfm-2.5-1.2b-thinking:free"
    model_l2: str = "arcee-ai/trinity-large-preview:free"
    model_lfm_spawn_max: int = 10
    model_stream_enabled: bool = True

    @classmethod
    def from_env(cls) -> "APISettings":
        projects_root_raw = os.environ.get("COCKPIT_API_PROJECTS_ROOT") or str(_default_projects_root())
        secret_key = os.environ.get("COCKPIT_API_SECRET") or "cockpit-dev-secret-change-me"
        issuer = os.environ.get("COCKPIT_API_ISSUER") or "cockpit-api"
        access_ttl = int(os.environ.get("COCKPIT_API_ACCESS_TTL_SECONDS") or "3600")
        refresh_ttl = int(os.environ.get("COCKPIT_API_REFRESH_TTL_SECONDS") or str(60 * 60 * 24 * 7))
        openrouter_api_key = str(os.environ.get("COCKPIT_OPENROUTER_API_KEY") or "").strip()
        openrouter_base_url = str(os.environ.get("COCKPIT_OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1").strip()
        model_voice_stt = str(os.environ.get("COCKPIT_MODEL_VOICE_STT") or "google/gemini-2.5-flash").strip()
        model_l1 = str(os.environ.get("COCKPIT_MODEL_L1") or "liquid/lfm-2.5-1.2b-thinking:free").strip()
        model_l2 = str(os.environ.get("COCKPIT_MODEL_L2") or "arcee-ai/trinity-large-preview:free").strip()
        raw_spawn = os.environ.get("COCKPIT_MODEL_LFM_SPAWN_MAX") or "10"
        raw_stream = str(os.environ.get("COCKPIT_MODEL_STREAM_ENABLED") or "1").strip().lower()
        try:
            model_lfm_spawn_max = int(raw_spawn)
        except (TypeError, ValueError):
            model_lfm_spawn_max = 10
        model_stream_enabled = raw_stream in {"1", "true", "yes", "on"}
        return cls(
            projects_root=Path(projects_root_raw).expanduser(),
            secret_key=secret_key,
            issuer=issuer,
            access_ttl_seconds=max(access_ttl, 60),
            refresh_ttl_seconds=max(refresh_ttl, 300),
            openrouter_api_key=openrouter_api_key,
            openrouter_base_url=openrouter_base_url or "https://openrouter.ai/api/v1",
            model_voice_stt=model_voice_stt or "google/gemini-2.5-flash",
            model_l1=model_l1 or "liquid/lfm-2.5-1.2b-thinking:free",
            model_l2=model_l2 or "arcee-ai/trinity-large-preview:free",
            model_lfm_spawn_max=max(1, min(model_lfm_spawn_max, 10)),
            model_stream_enabled=model_stream_enabled,
        )
