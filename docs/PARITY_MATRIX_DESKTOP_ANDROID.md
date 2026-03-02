# Desktop vs Android Parity Matrix (V1)

Date: 2026-03-03  
Policy: full UI parity target.

| Capability | Desktop (PySide) | Android (Kotlin/Compose) | API/WS contract |
|---|---|---|---|
| Login / refresh | Required | Required | `/v1/auth/login`, `/v1/auth/refresh` |
| Project switcher | Required | Required | `GET /v1/projects`, `GET /v1/projects/{id}` |
| Chat global/thread | Required | Required | `GET /v1/projects/{id}/chat`, `POST /chat/messages`, `WS /events` |
| Agent grid state | Required | Required | `GET /v1/projects/{id}/agents`, `PATCH /agents/{agent_id}/state` |
| State editor | Required | Required | `GET/PUT /state` |
| Roadmap editor | Required | Required | `GET/PUT /roadmap` |
| Decisions ledger | Required | Required | `GET/POST /decisions` |
| Wizard live start/run/stop | Required | Required | `POST /wizard-live/start|run|stop` |
| Runs browser | Required | Required | `GET /runs`, `GET /runs/{run_id}` |
| BMAD docs | Required | Required | `GET/PUT /bmad/{doc_type}` |
| Live updates | Required | Required | `WS /v1/projects/{id}/events` |
| Device push register | Optional | Required | `POST /v1/devices/register` |

## Out of Scope V1

- Telegram bot
- WhatsApp Cloud API
- Repo write from wizard/orchestrator during planning lanes
