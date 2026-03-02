from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = {}
        self._lock = asyncio.Lock()

    async def publish(self, *, project_id: str, event_type: str, actor: str, payload: dict[str, Any]) -> dict[str, Any]:
        envelope = {
            "event_id": f"evt_{uuid.uuid4().hex}",
            "project_id": project_id,
            "type": event_type,
            "ts": _utc_now().isoformat(),
            "actor": actor,
            "payload": payload,
            "version": "v1",
        }
        async with self._lock:
            targets = list(self._subscribers.get(project_id, set()))
        for queue in targets:
            try:
                queue.put_nowait(envelope)
            except asyncio.QueueFull:
                continue
        return envelope

    async def subscribe(self, project_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=500)
        async with self._lock:
            self._subscribers.setdefault(project_id, set()).add(queue)
        return queue

    async def unsubscribe(self, project_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            values = self._subscribers.get(project_id)
            if not values:
                return
            values.discard(queue)
            if not values:
                self._subscribers.pop(project_id, None)
