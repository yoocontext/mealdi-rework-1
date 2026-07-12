import logging
from collections.abc import Mapping

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from application.common.exceptions import (
    AppError,
    ApplicationError,
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from delivery.api.v1.http.request_id import REQUEST_ID_HEADER
from delivery.api.v1.http.schemas.errors import (
    ErrorBody,
    ErrorResponse,
    ValidationFieldError,
)

logger = logging.getLogger(__name__)

_INTERNAL_ERROR_CODE = "internal_error"
_INTERNAL_ERROR_MESSAGE = "Internal server error"


def _request_id(*, request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    fields: list[ValidationFieldError] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    response_headers = dict(headers or {})
    response_headers[REQUEST_ID_HEADER] = _request_id(request=request)

    body = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            request_id=_request_id(request=request),
            fields=fields,
        ),
    )

    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(exclude_none=True),
        headers=response_headers,
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


def _auth_headers(*, status_code: int) -> dict[str, str]:
    if status_code != status.HTTP_401_UNAUTHORIZED:
        return {}

    return {"WWW-Authenticate": "Bearer"}


def _log_unexpected_error(*, request: Request, error: BaseException) -> None:
    logger.error(
        "Unhandled HTTP error",
        extra={
            "request_id": _request_id(request=request),
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=(type(error), error, error.__traceback__),
    )


def _validation_fields(
    *,
    error: RequestValidationError,
) -> list[ValidationFieldError]:
    return [
        ValidationFieldError(
            path=[
                str(part) if not isinstance(part, int) else part
                for part in item["loc"]
            ],
            message=item["msg"],
        )
        for item in error.errors()
    ]


def _http_error_message(*, error: HTTPException) -> str:
    if isinstance(error.detail, str):
        return error.detail

    return "HTTP request failed"


def install_application_error_handlers(*, app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_application_error(
        request: Request,
        exc: AppError,
    ) -> JSONResponse:
        status_code = _status_code(error=exc)
        if status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            _log_unexpected_error(request=request, error=exc)

        return _response(
            request=request,
            status_code=status_code,
            code=(
                exc.code
                if isinstance(exc, ApplicationError)
                else _INTERNAL_ERROR_CODE
            ),
            message=(
                exc.message
                if isinstance(exc, ApplicationError)
                else _INTERNAL_ERROR_MESSAGE
            ),
            headers=_auth_headers(status_code=status_code),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return _response(
            request=request,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="validation_error",
            message="Request validation failed",
            fields=_validation_fields(error=exc),
        )

    @app.exception_handler(HTTPException)
    async def handle_http_error(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            _log_unexpected_error(request=request, error=exc)

        return _response(
            request=request,
            status_code=exc.status_code,
            code=(
                _INTERNAL_ERROR_CODE
                if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR
                else "http_error"
            ),
            message=(
                _INTERNAL_ERROR_MESSAGE
                if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR
                else _http_error_message(error=exc)
            ),
            headers={
                **(exc.headers or {}),
                **_auth_headers(status_code=exc.status_code),
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        _log_unexpected_error(request=request, error=exc)

        return _response(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=_INTERNAL_ERROR_CODE,
            message=_INTERNAL_ERROR_MESSAGE,
        )
