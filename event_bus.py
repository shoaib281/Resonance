"""SSE event bus for streaming simulation events to the frontend."""

from __future__ import annotations
import asyncio
import json
from typing import Any


class EventBus:
    def __init__(self):
        self.subscribers: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self.subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self.subscribers:
            self.subscribers.remove(q)

    async def emit(self, event_type: str, payload: Any = None):
        data = json.dumps({"type": event_type, "payload": payload or {}})
        for q in self.subscribers:
            await q.put(data)
