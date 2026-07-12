import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from fastapi import WebSocket


@dataclass(kw_only=True, slots=True)
class MessageConnections:
    _connections: dict[int, set[WebSocket]] = field(
        default_factory=lambda: defaultdict(set),
    )
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def connect(self, *, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[user_id].add(websocket)

    async def disconnect(self, *, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            connections = self._connections.get(user_id)
            if connections is None:
                return
            connections.discard(websocket)
            if not connections:
                self._connections.pop(user_id, None)

    @asynccontextmanager
    async def connected(
        self,
        *,
        user_id: int,
        websocket: WebSocket,
    ) -> AsyncIterator[None]:
        await self.connect(user_id=user_id, websocket=websocket)

        try:
            yield
        finally:
            await self.disconnect(user_id=user_id, websocket=websocket)

    async def publish(
        self,
        *,
        user_ids: set[int],
        payload: dict[str, object],
    ) -> None:
        async with self._lock:
            targets = [
                (user_id, websocket)
                for user_id in user_ids
                for websocket in self._connections.get(user_id, ())
            ]

        stale: list[tuple[int, WebSocket]] = []
        for user_id, websocket in targets:
            if not await self._send(websocket=websocket, payload=payload):
                stale.append((user_id, websocket))

        for user_id, websocket in stale:
            await self.disconnect(user_id=user_id, websocket=websocket)

    async def _send(
        self,
        *,
        websocket: WebSocket,
        payload: dict[str, object],
    ) -> bool:
        try:
            await websocket.send_json(payload)
        except RuntimeError:
            return False

        return True
