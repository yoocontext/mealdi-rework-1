from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from application.common.exceptions import (
    AppError,
    ApplicationError,
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)


def _status_code(*, error: AppError) -> int:
    if isinstance(error, AuthenticationError):
        return status.HTTP_401_UNAUTHORIZED
    if isinstance(error, ForbiddenError):
        return status.HTTP_403_FORBIDDEN
    if isinstance(error, NotFoundError):
        return status.HTTP_404_NOT_FOUND
    if isinstance(error, ConflictError):
        return status.HTTP_409_CONFLICT
    if isinstance(error, ApplicationError):
        return status.HTTP_400_BAD_REQUEST

    return status.HTTP_500_INTERNAL_SERVER_ERROR


def _public_message(*, error: AppError) -> str:
    if not isinstance(error, ApplicationError):
        return "Internal application error"

    return error.message


def install_application_error_handlers(*, app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_application_error(
        _request: Request,
        exc: AppError,
    ) -> JSONResponse:
        status_code = _status_code(error=exc)

        headers = {"WWW-Authenticate": "Bearer"} if status_code == 401 else None

        return JSONResponse(
            status_code=status_code,
            content={"detail": _public_message(error=exc)},
            headers=headers,
        )
