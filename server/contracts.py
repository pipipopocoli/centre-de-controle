from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class RbacPolicy(BaseModel):
    role: Literal["owner", "lead", "viewer"]
    permissions: list[str] = Field(default_factory=list)


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user_id: str
    rbac_policy: RbacPolicy


class ProjectCreateRequest(BaseModel):
    project_id: str
    name: str
    linked_repo_path: str | None = None


class ProjectSummary(BaseModel):
    project_id: str
    name: str
    linked_repo_path: str | None = None
    path: str
    updated_at: str | None = None


class ProjectStateSections(BaseModel):
    phase: str = "Plan"
    objective: str = "TBD"
    now: list[str] = Field(default_factory=list)
    next: list[str] = Field(default_factory=list)
    in_progress: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)


class RoadmapSections(BaseModel):
    now: list[str] = Field(default_factory=list)
    next: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class DecisionADR(BaseModel):
    title: str
    status: str = "Proposed"
    context: str | None = None
    decision: str | None = None
    rationale: str | None = None
    consequences: list[str] = Field(default_factory=list)
    owners: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class AgentStateOut(BaseModel):
    agent_id: str
    name: str | None = None
    phase: str | None = None
    status: str | None = None
    current_task: str | None = None
    blockers: list[str] = Field(default_factory=list)
    heartbeat: str | None = None
    updated_at: str | None = None
    level: int | None = None
    role: str | None = None
    engine: str | None = None
    platform: str | None = None


class AgentStatePatch(BaseModel):
    phase: str | None = None
    status: str | None = None
    current_task: str | None = None
    blockers: list[str] | None = None
    percent: int | None = None
    eta_minutes: int | None = None


class ChatMessageIn(BaseModel):
    text: str
    thread_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    context_ref: dict[str, Any] | None = None


class ChatMessageOut(BaseModel):
    message_id: str | None = None
    timestamp: str
    author: str
    text: str
    tags: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    event: str | None = None
    thread_id: str | None = None


class WizardLiveCommandRequest(BaseModel):
    repo_path: str | None = None
    trigger: str = "api"
    operator_message: str = ""
    include_full_intake: bool = False
    timeout_s: int = 240


class WizardLiveResultOut(BaseModel):
    status: str
    project_id: str
    repo_path: str
    projects_root: str
    run_id: str
    trigger: str
    session_active: bool
    output_json_path: str
    output_md_path: str
    prompt_path: str | None = None
    context_path: str | None = None
    bmad_dir: str
    error: str | None = None


class RunSummary(BaseModel):
    run_id: str
    json_path: str | None = None
    md_path: str | None = None
    generated_at: str | None = None


class RunDetail(BaseModel):
    run_id: str
    json_path: str | None = None
    md_path: str | None = None
    json_payload: dict[str, Any] | None = None
    md_text: str | None = None


class BmadDocResponse(BaseModel):
    project_id: str
    doc_type: Literal["brainstorm", "product_brief", "prd", "architecture", "stories"]
    content: str
    updated_at: str | None = None


class BmadDocUpdate(BaseModel):
    content: str


class DeviceRegisterRequest(BaseModel):
    device_id: str
    platform: Literal["android"] = "android"
    fcm_token: str
    project_ids: list[str] = Field(default_factory=list)


class DeviceRegisterResponse(BaseModel):
    device_id: str
    platform: str
    status: Literal["registered"] = "registered"
    updated_at: str


class DeviceDeleteResponse(BaseModel):
    device_id: str
    status: Literal["deleted"] = "deleted"


class EventEnvelope(BaseModel):
    event_id: str
    project_id: str
    type: str
    ts: datetime
    actor: str
    payload: dict[str, Any]
    version: Literal["v1"] = "v1"


class WizardLiveOutput(BaseModel):
    wizard_version: str
    generated_at_utc: str
    project_id: str
    repo_path: str
    trigger: str
    agent_messages: list[dict[str, Any]]
    clems_summary: dict[str, Any]
    bmad: dict[str, str]
    state_sections: ProjectStateSections
    roadmap_sections: RoadmapSections
    decisions_adrs: list[DecisionADR] = Field(default_factory=list)
