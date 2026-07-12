from dishka import AsyncContainer
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from application.common.exceptions import AuthenticationError
from application.dto.users import User
from application.use_cases.auth import AuthenticateCm, AuthenticateUc
from delivery.common.connections import MessageConnections
from delivery.common.settings import WebSocketSettings

router = APIRouter(prefix="/api/v1/http/ws", tags=["messages"])


@router.websocket("/messages")
@inject
async def message_events(
    *,
    websocket: WebSocket,
    connections: FromDishka[MessageConnections],
    settings: FromDishka[WebSocketSettings],
) -> None:
    if not settings.allows(origin=websocket.headers.get("origin")):
        await _reject(websocket=websocket)
        return

    user = await _authenticate(websocket=websocket)
    if user is None:
        await _reject(websocket=websocket)
        return

    async with connections.connected(user_id=user.id, websocket=websocket):
        await _wait_for_disconnect(websocket=websocket)


async def _authenticate(*, websocket: WebSocket) -> User | None:
    token = _read_access_token(websocket=websocket)

    try:
        async with websocket.state.dishka_container() as container:
            return await _resolve_user(container=container, token=token)
    except AuthenticationError:
        return None


def _read_access_token(*, websocket: WebSocket) -> str:
    query_token = websocket.query_params.get("access_token")
    if query_token is not None:
        return query_token

    return websocket.cookies.get("access_token", "")


async def _resolve_user(*, container: AsyncContainer, token: str) -> User:
    authenticate = await container.get(AuthenticateUc)
    result = await authenticate.act(
        command=AuthenticateCm(access_token=token),
    )

    return result.user


async def _reject(*, websocket: WebSocket) -> None:
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)


async def _wait_for_disconnect(*, websocket: WebSocket) -> None:
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
