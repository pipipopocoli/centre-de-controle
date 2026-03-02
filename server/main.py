from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.services.wizard_live import (
    load_wizard_live_session,
    run_wizard_live_turn,
    start_wizard_live_session,
    stop_wizard_live_session,
)
from server.config import APISettings
from server.contracts import (
    AgentStatePatch,
    BmadDocUpdate,
    ChatMessageIn,
    DecisionADR,
    DeviceRegisterRequest,
    LoginRequest,
    ProjectCreateRequest,
    ProjectStateSections,
    RefreshRequest,
    RoadmapSections,
    WizardLiveCommandRequest,
)
from server.events import EventBus
from server.rbac import has_permission, permissions_for_role, policy_for_role
from server.repository import DeviceRepository, ProjectRepository, UserRepository
from server.security import TokenError, create_token, decode_token, verify_password


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json(data: Any, status_code: int = 200) -> JSONResponse:
    return JSONResponse(data, status_code=status_code)


def _http_error(status_code: int, detail: str) -> None:
    raise HTTPException(status_code=status_code, detail=detail)


async def _parse_model(request: Request, model_cls: type[BaseModel]) -> BaseModel:
    try:
        payload = await request.json()
    except Exception:
        _http_error(400, "invalid_json_body")
    try:
        return model_cls.model_validate(payload)
    except ValidationError as exc:
        _http_error(422, exc.errors()[0]["msg"] if exc.errors() else "validation_error")


def _bearer_token(request: Request) -> str:
    auth = str(request.headers.get("authorization") or "")
    if not auth.lower().startswith("bearer "):
        _http_error(401, "missing_bearer_token")
    return auth.split(" ", 1)[1].strip()


def _claims_from_token(token: str, *, settings: APISettings, expected_type: str = "access") -> dict[str, Any]:
    try:
        claims = decode_token(
            token,
            secret_key=settings.secret_key,
            issuer=settings.issuer,
            expected_type=expected_type,
        )
    except TokenError as exc:
        _http_error(401, f"invalid_token:{exc}")
    return claims


def _authorize(request: Request, *, permission: str) -> dict[str, Any]:
    settings: APISettings = request.app.state.settings
    token = _bearer_token(request)
    claims = _claims_from_token(token, settings=settings, expected_type="access")
    role = str(claims.get("role") or "viewer")
    if not has_permission(role, permission):
        _http_error(403, f"forbidden:{permission}")
    return claims


async def _publish(request: Request, *, project_id: str, event_type: str, actor: str, payload: dict[str, Any]) -> None:
    bus: EventBus = request.app.state.event_bus
    await bus.publish(
        project_id=project_id,
        event_type=event_type,
        actor=actor,
        payload=payload,
    )


def _result_payload(result: Any) -> dict[str, Any]:
    data = asdict(result)
    runner = data.get("runner")
    if runner is not None:
        data["runner"] = asdict(runner)
    return data


async def healthz(_: Request) -> JSONResponse:
    return _json({"status": "ok"})


async def login(request: Request) -> JSONResponse:
    body = await _parse_model(request, LoginRequest)
    users: UserRepository = request.app.state.users
    settings: APISettings = request.app.state.settings

    user = users.get_by_username(body.username)
    if not user:
        _http_error(401, "invalid_credentials")
    if not verify_password(body.password, str(user.get("password_hash") or "")):
        _http_error(401, "invalid_credentials")

    role = str(user.get("role") or "viewer")
    permissions = permissions_for_role(role)
    user_id = str(user.get("user_id") or body.username)
    access_token = create_token(
        subject=user_id,
        role=role,
        permissions=permissions,
        secret_key=settings.secret_key,
        issuer=settings.issuer,
        token_type="access",
        expires_seconds=settings.access_ttl_seconds,
    )
    refresh_token = create_token(
        subject=user_id,
        role=role,
        permissions=permissions,
        secret_key=settings.secret_key,
        issuer=settings.issuer,
        token_type="refresh",
        expires_seconds=settings.refresh_ttl_seconds,
    )
    return _json(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_ttl_seconds,
            "user_id": user_id,
            "rbac_policy": policy_for_role(role),
        }
    )


async def refresh(request: Request) -> JSONResponse:
    body = await _parse_model(request, RefreshRequest)
    settings: APISettings = request.app.state.settings
    claims = _claims_from_token(body.refresh_token, settings=settings, expected_type="refresh")
    role = str(claims.get("role") or "viewer")
    permissions = permissions_for_role(role)
    user_id = str(claims.get("sub") or "")
    access_token = create_token(
        subject=user_id,
        role=role,
        permissions=permissions,
        secret_key=settings.secret_key,
        issuer=settings.issuer,
        token_type="access",
        expires_seconds=settings.access_ttl_seconds,
    )
    refresh_token = create_token(
        subject=user_id,
        role=role,
        permissions=permissions,
        secret_key=settings.secret_key,
        issuer=settings.issuer,
        token_type="refresh",
        expires_seconds=settings.refresh_ttl_seconds,
    )
    return _json(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_ttl_seconds,
            "user_id": user_id,
            "rbac_policy": policy_for_role(role),
        }
    )


async def logout(request: Request) -> JSONResponse:
    _authorize(request, permission="projects:read")
    return _json({"status": "ok"})


async def list_projects(request: Request) -> JSONResponse:
    _authorize(request, permission="projects:read")
    repo: ProjectRepository = request.app.state.projects
    payload = [item.model_dump() for item in repo.list_projects()]
    return _json(payload)


async def create_project(request: Request) -> JSONResponse:
    claims = _authorize(request, permission="projects:create")
    body = await _parse_model(request, ProjectCreateRequest)
    repo: ProjectRepository = request.app.state.projects
    created = repo.create_project(
        project_id=body.project_id,
        name=body.name,
        linked_repo_path=body.linked_repo_path,
    )
    await _publish(
        request,
        project_id=created.project_id,
        event_type="project.created",
        actor=str(claims.get("sub") or "owner"),
        payload=created.model_dump(),
    )
    return _json(created.model_dump(), status_code=201)


async def get_project(request: Request) -> JSONResponse:
    _authorize(request, permission="projects:read")
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    try:
        payload = repo.get_project(project_id).model_dump()
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    return _json(payload)


async def get_state(request: Request) -> JSONResponse:
    _authorize(request, permission="state:read")
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    try:
        sections = repo.read_state_sections(project_id)
        raw_md = repo.read_state_raw(project_id)
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    return _json({"project_id": project_id, "sections": sections.model_dump(), "raw_md": raw_md})


async def put_state(request: Request) -> JSONResponse:
    claims = _authorize(request, permission="state:write")
    body = await _parse_model(request, ProjectStateSections)
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    try:
        repo.write_state_sections(project_id, body)
        sections = repo.read_state_sections(project_id)
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    await _publish(
        request,
        project_id=project_id,
        event_type="state.updated",
        actor=str(claims.get("sub") or ""),
        payload={"sections": sections.model_dump()},
    )
    return _json({"project_id": project_id, "sections": sections.model_dump()})


async def get_roadmap(request: Request) -> JSONResponse:
    _authorize(request, permission="roadmap:read")
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    try:
        sections = repo.read_roadmap_sections(project_id)
        raw_md = repo.read_roadmap_raw(project_id)
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    return _json({"project_id": project_id, "sections": sections.model_dump(), "raw_md": raw_md})


async def put_roadmap(request: Request) -> JSONResponse:
    claims = _authorize(request, permission="roadmap:write")
    body = await _parse_model(request, RoadmapSections)
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    try:
        repo.write_roadmap_sections(project_id, body)
        sections = repo.read_roadmap_sections(project_id)
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    await _publish(
        request,
        project_id=project_id,
        event_type="roadmap.updated",
        actor=str(claims.get("sub") or ""),
        payload={"sections": sections.model_dump()},
    )
    return _json({"project_id": project_id, "sections": sections.model_dump()})


async def get_decisions(request: Request) -> JSONResponse:
    _authorize(request, permission="decisions:read")
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    try:
        payload = [item.model_dump() for item in repo.read_decisions(project_id)]
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    return _json(payload)


async def post_decision(request: Request) -> JSONResponse:
    claims = _authorize(request, permission="decisions:write")
    body = await _parse_model(request, DecisionADR)
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    try:
        repo.append_decision(project_id, body)
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    payload = body.model_dump()
    await _publish(
        request,
        project_id=project_id,
        event_type="decisions.appended",
        actor=str(claims.get("sub") or ""),
        payload=payload,
    )
    return _json(payload, status_code=201)


async def get_agents(request: Request) -> JSONResponse:
    _authorize(request, permission="agents:read")
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    try:
        payload = repo.list_agents(project_id)
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    return _json(payload)


async def patch_agent_state(request: Request) -> JSONResponse:
    claims = _authorize(request, permission="agents:write")
    body = await _parse_model(request, AgentStatePatch)
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    agent_id = request.path_params["agent_id"]
    try:
        payload = repo.patch_agent_state(project_id, agent_id, body.model_dump())
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    await _publish(
        request,
        project_id=project_id,
        event_type="agent.state.updated",
        actor=str(claims.get("sub") or ""),
        payload={"agent_id": agent_id, "state": payload},
    )
    return _json(payload)


async def get_chat(request: Request) -> JSONResponse:
    _authorize(request, permission="chat:read")
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    limit_raw = request.query_params.get("limit") or "200"
    try:
        limit = max(int(limit_raw), 1)
    except ValueError:
        limit = 200
    try:
        payload = repo.load_chat(project_id, limit=limit)
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    return _json(payload)


async def post_chat(request: Request) -> JSONResponse:
    claims = _authorize(request, permission="chat:write")
    body = await _parse_model(request, ChatMessageIn)
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    try:
        payload = repo.append_chat(
            project_id,
            {
                "author": str(claims.get("sub") or "operator"),
                "text": body.text,
                "thread_id": body.thread_id,
                "tags": body.tags,
                "mentions": body.mentions,
                "context_ref": body.context_ref,
            },
        )
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    await _publish(
        request,
        project_id=project_id,
        event_type="chat.message.created",
        actor=str(claims.get("sub") or ""),
        payload=payload,
    )
    return _json(payload, status_code=201)


def _resolve_repo_path(repo: ProjectRepository, project_id: str, override: str | None) -> Path:
    if override and str(override).strip():
        return Path(str(override).strip()).expanduser()
    linked = repo.linked_repo_path(project_id)
    if linked:
        return Path(linked).expanduser()
    _http_error(400, "missing_repo_path")


async def wizard_start(request: Request) -> JSONResponse:
    claims = _authorize(request, permission="wizard:run")
    body = await _parse_model(request, WizardLiveCommandRequest)
    repo: ProjectRepository = request.app.state.projects
    settings: APISettings = request.app.state.settings
    project_id = request.path_params["project_id"]
    repo_path = _resolve_repo_path(repo, project_id, body.repo_path)
    result = start_wizard_live_session(
        projects_root=settings.projects_root,
        project_id=project_id,
        repo_path=repo_path,
        trigger=body.trigger or "api_start",
        operator_message=body.operator_message,
        include_full_intake=bool(body.include_full_intake),
        timeout_s=max(int(body.timeout_s), 30),
    )
    payload = _result_payload(result)
    await _publish(
        request,
        project_id=project_id,
        event_type="wizard.live.started",
        actor=str(claims.get("sub") or ""),
        payload={"run_id": payload.get("run_id"), "status": payload.get("status")},
    )
    return _json(payload)


async def wizard_run(request: Request) -> JSONResponse:
    claims = _authorize(request, permission="wizard:run")
    body = await _parse_model(request, WizardLiveCommandRequest)
    repo: ProjectRepository = request.app.state.projects
    settings: APISettings = request.app.state.settings
    project_id = request.path_params["project_id"]
    repo_path = _resolve_repo_path(repo, project_id, body.repo_path)
    session_payload = load_wizard_live_session(settings.projects_root, project_id)
    session_active = bool(session_payload.get("active"))
    result = run_wizard_live_turn(
        projects_root=settings.projects_root,
        project_id=project_id,
        repo_path=repo_path,
        trigger=body.trigger or "api_run",
        operator_message=body.operator_message,
        include_full_intake=bool(body.include_full_intake),
        timeout_s=max(int(body.timeout_s), 30),
        session_active=session_active,
    )
    payload = _result_payload(result)
    await _publish(
        request,
        project_id=project_id,
        event_type="wizard.live.run",
        actor=str(claims.get("sub") or ""),
        payload={"run_id": payload.get("run_id"), "status": payload.get("status")},
    )
    return _json(payload)


async def wizard_stop(request: Request) -> JSONResponse:
    claims = _authorize(request, permission="wizard:run")
    body = await _parse_model(request, WizardLiveCommandRequest)
    repo: ProjectRepository = request.app.state.projects
    settings: APISettings = request.app.state.settings
    project_id = request.path_params["project_id"]
    repo_path = _resolve_repo_path(repo, project_id, body.repo_path)
    result = stop_wizard_live_session(
        projects_root=settings.projects_root,
        project_id=project_id,
        repo_path=repo_path,
        trigger=body.trigger or "api_stop",
    )
    payload = _result_payload(result)
    await _publish(
        request,
        project_id=project_id,
        event_type="wizard.live.stopped",
        actor=str(claims.get("sub") or ""),
        payload={"run_id": payload.get("run_id"), "status": payload.get("status")},
    )
    return _json(payload)


async def get_runs(request: Request) -> JSONResponse:
    _authorize(request, permission="runs:read")
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    try:
        payload = repo.list_runs(project_id)
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    return _json(payload)


async def get_run(request: Request) -> JSONResponse:
    _authorize(request, permission="runs:read")
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    run_id = request.path_params["run_id"]
    try:
        payload = repo.get_run(project_id, run_id)
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    return _json(payload)


async def get_bmad(request: Request) -> JSONResponse:
    _authorize(request, permission="bmad:read")
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    doc_type = request.path_params["doc_type"]
    try:
        payload = repo.get_bmad(project_id, doc_type)
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    except ValueError as exc:
        _http_error(400, str(exc))
    return _json(payload)


async def put_bmad(request: Request) -> JSONResponse:
    claims = _authorize(request, permission="bmad:write")
    body = await _parse_model(request, BmadDocUpdate)
    repo: ProjectRepository = request.app.state.projects
    project_id = request.path_params["project_id"]
    doc_type = request.path_params["doc_type"]
    try:
        payload = repo.put_bmad(project_id, doc_type, body.content)
    except FileNotFoundError as exc:
        _http_error(404, str(exc))
    except ValueError as exc:
        _http_error(400, str(exc))
    await _publish(
        request,
        project_id=project_id,
        event_type="bmad.updated",
        actor=str(claims.get("sub") or ""),
        payload={"doc_type": doc_type},
    )
    return _json(payload)


async def register_device(request: Request) -> JSONResponse:
    claims = _authorize(request, permission="devices:write")
    body = await _parse_model(request, DeviceRegisterRequest)
    devices: DeviceRepository = request.app.state.devices
    saved = devices.upsert(
        user_id=str(claims.get("sub") or "unknown"),
        device_id=body.device_id,
        platform=body.platform,
        fcm_token=body.fcm_token,
        project_ids=body.project_ids,
    )
    return _json(
        {
            "device_id": saved["device_id"],
            "platform": saved["platform"],
            "status": "registered",
            "updated_at": saved["updated_at"],
        },
        status_code=201,
    )


async def delete_device(request: Request) -> JSONResponse:
    _authorize(request, permission="devices:write")
    device_id = request.path_params["device_id"]
    devices: DeviceRepository = request.app.state.devices
    deleted = devices.delete(device_id)
    if not deleted:
        _http_error(404, f"device not found: {device_id}")
    return _json({"device_id": device_id, "status": "deleted"})


async def websocket_events(websocket: WebSocket) -> None:
    settings: APISettings = websocket.app.state.settings
    bus: EventBus = websocket.app.state.event_bus
    project_id = websocket.path_params["project_id"]
    token = str(websocket.query_params.get("token") or "").strip()
    if not token:
        await websocket.close(code=4401)
        return
    try:
        claims = decode_token(
            token,
            secret_key=settings.secret_key,
            issuer=settings.issuer,
            expected_type="access",
        )
    except TokenError:
        await websocket.close(code=4401)
        return
    role = str(claims.get("role") or "viewer")
    if not has_permission(role, "projects:read"):
        await websocket.close(code=4403)
        return
    await websocket.accept()
    queue = await bus.subscribe(project_id)
    try:
        await websocket.send_json(
            {
                "event_id": "evt_connected",
                "project_id": project_id,
                "type": "connection.ready",
                "ts": _utc_now_iso(),
                "actor": "system",
                "payload": {"user_id": str(claims.get("sub") or "")},
                "version": "v1",
            }
        )
        while True:
            try:
                envelope = await asyncio.wait_for(queue.get(), timeout=25.0)
                await websocket.send_json(envelope)
            except asyncio.TimeoutError:
                await websocket.send_json(
                    {
                        "event_id": "evt_ping",
                        "project_id": project_id,
                        "type": "connection.ping",
                        "ts": _utc_now_iso(),
                        "actor": "system",
                        "payload": {},
                        "version": "v1",
                    }
                )
    except WebSocketDisconnect:
        pass
    finally:
        await bus.unsubscribe(project_id, queue)


def create_app(settings: APISettings | None = None) -> Starlette:
    runtime_settings = settings or APISettings.from_env()
    runtime_settings.projects_root.mkdir(parents=True, exist_ok=True)

    app = Starlette(
        debug=False,
        routes=[
            Route("/healthz", healthz, methods=["GET"]),
            Route("/v1/auth/login", login, methods=["POST"]),
            Route("/v1/auth/refresh", refresh, methods=["POST"]),
            Route("/v1/auth/logout", logout, methods=["POST"]),
            Route("/v1/projects", list_projects, methods=["GET"]),
            Route("/v1/projects", create_project, methods=["POST"]),
            Route("/v1/projects/{project_id:str}", get_project, methods=["GET"]),
            Route("/v1/projects/{project_id:str}/state", get_state, methods=["GET"]),
            Route("/v1/projects/{project_id:str}/state", put_state, methods=["PUT"]),
            Route("/v1/projects/{project_id:str}/roadmap", get_roadmap, methods=["GET"]),
            Route("/v1/projects/{project_id:str}/roadmap", put_roadmap, methods=["PUT"]),
            Route("/v1/projects/{project_id:str}/decisions", get_decisions, methods=["GET"]),
            Route("/v1/projects/{project_id:str}/decisions", post_decision, methods=["POST"]),
            Route("/v1/projects/{project_id:str}/agents", get_agents, methods=["GET"]),
            Route("/v1/projects/{project_id:str}/agents/{agent_id:str}/state", patch_agent_state, methods=["PATCH"]),
            Route("/v1/projects/{project_id:str}/chat", get_chat, methods=["GET"]),
            Route("/v1/projects/{project_id:str}/chat/messages", post_chat, methods=["POST"]),
            Route("/v1/projects/{project_id:str}/wizard-live/start", wizard_start, methods=["POST"]),
            Route("/v1/projects/{project_id:str}/wizard-live/run", wizard_run, methods=["POST"]),
            Route("/v1/projects/{project_id:str}/wizard-live/stop", wizard_stop, methods=["POST"]),
            Route("/v1/projects/{project_id:str}/runs", get_runs, methods=["GET"]),
            Route("/v1/projects/{project_id:str}/runs/{run_id:str}", get_run, methods=["GET"]),
            Route("/v1/projects/{project_id:str}/bmad/{doc_type:str}", get_bmad, methods=["GET"]),
            Route("/v1/projects/{project_id:str}/bmad/{doc_type:str}", put_bmad, methods=["PUT"]),
            Route("/v1/devices/register", register_device, methods=["POST"]),
            Route("/v1/devices/{device_id:str}", delete_device, methods=["DELETE"]),
            WebSocketRoute("/v1/projects/{project_id:str}/events", websocket_events),
        ],
    )
    app.state.settings = runtime_settings
    app.state.projects = ProjectRepository(runtime_settings.projects_root)
    app.state.users = UserRepository(runtime_settings.projects_root)
    app.state.devices = DeviceRepository(runtime_settings.projects_root)
    app.state.event_bus = EventBus()
    return app


app = create_app()
