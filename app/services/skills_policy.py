"""Skills Policy Engine — curated-only allowlist with fail-open behavior.

ISSUE-CP-0002: Enforce curated-only policy for skill installation.
- Non-curated skills are blocked in normal mode.
- When the catalog source is unavailable and fail_open=True, the engine
  allows everything and emits a structured warning event.
- Every decision is deterministic (pure function of the allowlist).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class PolicyUnavailableError(Exception):
    """Raised when catalog is unavailable and fail_open is False."""


@dataclass(frozen=True)
class PolicyDecision:
    """Result of evaluating a single skill against the policy."""
    skill_id: str
    allowed: bool
    reason: str
    mode: str  # "normal" | "fail_open"


@dataclass(frozen=True)
class PolicyEvent:
    """Structured warning / info event emitted by the policy engine."""
    timestamp: str
    event_type: str
    skill_id: str | None
    detail: str


class SkillsPolicy:
    """Curated-only policy engine with optional fail-open mode.

    Usage::

        # Normal mode — from a catalog payload
        policy = SkillsPolicy.from_catalog(catalog_list)
        decision = policy.evaluate("openai-docs")

        # Fail-open mode — catalog unavailable
        policy = SkillsPolicy.from_catalog(None, fail_open=True)
        # -> allows everything, logs a warning event
    """

    def __init__(
        self,
        allowlist: set[str],
        *,
        fail_open_active: bool = False,
    ) -> None:
        self._allowlist: set[str] = set(allowlist)
        self._fail_open_active: bool = fail_open_active
        self._events: list[PolicyEvent] = []

    # -- Factory ----------------------------------------------------------

    @classmethod
    def from_catalog(
        cls,
        catalog: list[dict[str, Any]] | None,
        *,
        fail_open: bool = True,
    ) -> "SkillsPolicy":
        """Build a policy from a catalog payload.

        Args:
            catalog: List of skill dicts (must have an ``"id"`` key each),
                     or ``None`` if the catalog source is unavailable.
            fail_open: If True and catalog is None, return a permissive
                       policy with a warning event.  If False, raise
                       :class:`PolicyUnavailableError`.
        """
        if catalog is None:
            if not fail_open:
                raise PolicyUnavailableError(
                    "Catalog source unavailable and fail_open is disabled."
                )
            policy = cls(set(), fail_open_active=True)
            policy._emit(
                "fail_open_no_catalog",
                skill_id=None,
                detail="Catalog source unavailable — fail-open mode active, all skills allowed.",
            )
            return policy

        allowlist: set[str] = set()
        for entry in catalog:
            sid = entry.get("id")
            if isinstance(sid, str) and sid:
                allowlist.add(sid)
        return cls(allowlist, fail_open_active=False)

    # -- Evaluation -------------------------------------------------------

    def evaluate(self, skill_id: str) -> PolicyDecision:
        """Evaluate a single skill against the curated allowlist."""
        if self._fail_open_active:
            self._emit(
                "fail_open_allow",
                skill_id=skill_id,
                detail=f"Allowed (fail-open active): {skill_id}",
            )
            return PolicyDecision(
                skill_id=skill_id,
                allowed=True,
                reason="fail_open",
                mode="fail_open",
            )

        if skill_id in self._allowlist:
            return PolicyDecision(
                skill_id=skill_id,
                allowed=True,
                reason="curated",
                mode="normal",
            )

        self._emit(
            "rejected",
            skill_id=skill_id,
            detail=f"Rejected (not in curated allowlist): {skill_id}",
        )
        return PolicyDecision(
            skill_id=skill_id,
            allowed=False,
            reason="not_in_curated_allowlist",
            mode="normal",
        )

    def evaluate_batch(self, skill_ids: list[str]) -> list[PolicyDecision]:
        """Evaluate multiple skills. Order is preserved."""
        return [self.evaluate(sid) for sid in skill_ids]

    # -- Events -----------------------------------------------------------

    @property
    def events(self) -> list[PolicyEvent]:
        """Accumulated structured events (read-only copy)."""
        return list(self._events)

    # -- Internals --------------------------------------------------------

    def _emit(self, event_type: str, *, skill_id: str | None, detail: str) -> None:
        self._events.append(
            PolicyEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type=event_type,
                skill_id=skill_id,
                detail=detail,
            )
        )
