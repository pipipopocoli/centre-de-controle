from __future__ import annotations


ROLE_OWNER = "owner"
ROLE_LEAD = "lead"
ROLE_VIEWER = "viewer"

ALL_ROLES = {ROLE_OWNER, ROLE_LEAD, ROLE_VIEWER}

READ_PERMISSIONS = {
    "projects:read",
    "state:read",
    "roadmap:read",
    "decisions:read",
    "agents:read",
    "chat:read",
    "runs:read",
    "bmad:read",
}

LEAD_WRITE_PERMISSIONS = {
    "state:write",
    "roadmap:write",
    "decisions:write",
    "agents:write",
    "chat:write",
    "wizard:run",
    "bmad:write",
    "devices:write",
}

OWNER_EXTRA_PERMISSIONS = {
    "projects:create",
    "projects:write",
    "auth:manage",
}

ROLE_PERMISSIONS = {
    ROLE_OWNER: READ_PERMISSIONS | LEAD_WRITE_PERMISSIONS | OWNER_EXTRA_PERMISSIONS,
    ROLE_LEAD: READ_PERMISSIONS | LEAD_WRITE_PERMISSIONS,
    ROLE_VIEWER: READ_PERMISSIONS,
}


def normalize_role(role: str) -> str:
    token = str(role or "").strip().lower()
    if token in ALL_ROLES:
        return token
    return ROLE_VIEWER


def permissions_for_role(role: str) -> list[str]:
    normalized = normalize_role(role)
    return sorted(ROLE_PERMISSIONS.get(normalized, set()))


def has_permission(role: str, permission: str) -> bool:
    normalized = normalize_role(role)
    if normalized == ROLE_OWNER:
        return True
    return str(permission) in ROLE_PERMISSIONS.get(normalized, set())


def policy_for_role(role: str) -> dict[str, object]:
    normalized = normalize_role(role)
    return {
        "role": normalized,
        "permissions": permissions_for_role(normalized),
    }
