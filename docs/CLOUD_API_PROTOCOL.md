# Cockpit Cloud API Protocol (Desktop + Android)

Date: 2026-03-03  
Scope: API centrale cloud-first, sans Telegram/WhatsApp.

## Objective

Unifier Desktop et Android sur une source de vérité unique via API/WS.

## Base URL

- Local dev: `http://localhost:8100`
- Healthcheck: `GET /healthz`

## Auth

- `POST /v1/auth/login`
- `POST /v1/auth/refresh`
- `POST /v1/auth/logout`
- Bearer token requis pour toutes les routes métier.
- RBAC roles: `owner`, `lead`, `viewer`.

## Core Contracts

- `ProjectStateSections`
- `RoadmapSections`
- `DecisionADR`
- `WizardLiveOutput`
- `EventEnvelope {event_id, project_id, type, ts, actor, payload, version}`
- `RbacPolicy {role, permissions[]}`

## API Surface (V1)

- `GET /v1/projects`, `POST /v1/projects`, `GET /v1/projects/{id}`
- `GET/PUT /v1/projects/{id}/state`
- `GET/PUT /v1/projects/{id}/roadmap`
- `GET/POST /v1/projects/{id}/decisions`
- `GET /v1/projects/{id}/agents`
- `PATCH /v1/projects/{id}/agents/{agent_id}/state`
- `GET /v1/projects/{id}/chat`
- `POST /v1/projects/{id}/chat/messages`
- `POST /v1/projects/{id}/wizard-live/start|run|stop`
- `GET /v1/projects/{id}/runs`, `GET /v1/projects/{id}/runs/{run_id}`
- `GET/PUT /v1/projects/{id}/bmad/{doc_type}`
- `POST /v1/devices/register`, `DELETE /v1/devices/{id}`
- `WS /v1/projects/{id}/events?token=<access_token>`

## Runtime Notes

- Le backend écrit/relit les artefacts projet (`STATE.md`, `ROADMAP.md`, `DECISIONS.md`, `BMAD/*`, `runs/*`) depuis `COCKPIT_API_PROJECTS_ROOT`.
- Par défaut, la racine est `~/Library/Application Support/Cockpit/projects`.
- Les clients Desktop/Android sont consommateurs API/WS; l’orchestration reste côté backend.

## Run Server

```bash
./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/run_cockpit_api.py --port 8100
```

Override root:

```bash
COCKPIT_API_PROJECTS_ROOT="/path/to/projects" ./.venv/bin/python /Users/oliviercloutier/Desktop/Cockpit/scripts/run_cockpit_api.py
```
