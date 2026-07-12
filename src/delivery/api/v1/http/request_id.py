from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response

REQUEST_ID_HEADER = "X-Request-ID"


def _is_valid_request_id(*, value: str) -> bool:
    return bool(value) and len(value) <= 128 and all(
        character.isalnum() or character in "-_." for character in value
    )


def install_request_id_middleware(*, app: FastAPI) -> None:
    @app.middleware("http")
    async def attach_request_id(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER, "")
        if not _is_valid_request_id(value=request_id):
            request_id = uuid4().hex

        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id

        return response
