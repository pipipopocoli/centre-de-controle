# OpenRouter Setup (Wave21)

## Required env

```bash
export COCKPIT_OPENROUTER_API_KEY="..."
```

## Optional env

```bash
export COCKPIT_OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
export COCKPIT_MODEL_VOICE_STT="google/gemini-2.5-flash"
export COCKPIT_MODEL_L1="liquid/lfm-2.5-1.2b-thinking:free"
export COCKPIT_MODEL_L2="arcee-ai/trinity-large-preview:free"
export COCKPIT_MODEL_LFM_SPAWN_MAX="10"
export COCKPIT_API_USERNAME="owner"
export COCKPIT_API_PASSWORD="<GENERATE_STRONG_PASSWORD>"
export COCKPIT_API_BOOTSTRAP_OWNER_PASSWORD="<GENERATE_STRONG_PASSWORD>"
```

## Start API

```bash
./.venv/bin/python scripts/run_cockpit_api.py --port 8100
```

## Verify routes

1. Login: `POST /v1/auth/login`
2. Get model routing: `GET /v1/projects/{id}/llm-profile`
3. Chat turn: `POST /v1/projects/{id}/chat/agentic-turn`
4. Voice STT: `POST /v1/projects/{id}/voice/transcribe`

## Security notes

- Do not store API keys in project files.
- Do not commit `.zshrc`, `.zprofile`, or shell secrets.
- API rejects startup when `COCKPIT_OPENROUTER_API_KEY` is missing.
