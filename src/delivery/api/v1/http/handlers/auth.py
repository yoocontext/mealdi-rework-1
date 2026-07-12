from datetime import datetime
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from application.interfaces.clock import IClock
from application.use_cases.auth import (
    LoginCm,
    LoginUc,
    LogoutCm,
    LogoutUc,
    RefreshTokensCm,
    RefreshTokensUc,
    RegisterUserUc,
)
from delivery.api.v1.http.mappers.auth import map_login_to_rp, map_token_pair_to_rp
from delivery.api.v1.http.mappers.users import (
    map_register_rq_to_cm,
    map_user_to_current_rp,
)
from delivery.api.v1.http.schemas.auth import (
    LoginRp,
    LogoutRp,
    RefreshTokenRq,
    TokenPairRp,
)
from delivery.api.v1.http.schemas.errors import ErrorResponse
from delivery.api.v1.http.schemas.users import CurrentUserRp, RegisterUserRq
from delivery.common.settings import CookieSettings

router = APIRouter(prefix="/api/v1/http/auth", tags=["auth"])


def _set_access_cookie(
    *,
    response: Response,
    access_token: str,
    expires_at: datetime,
    clock: IClock,
    settings: CookieSettings,
) -> None:
    max_age = max(0, int((expires_at - clock.now()).total_seconds()))
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=max_age,
        httponly=True,
        secure=settings.secure,
        samesite="lax",
        domain=settings.domain,
    )


@router.post(
    "/register",
    response_model=CurrentUserRp,
    status_code=status.HTTP_201_CREATED,
    description="Create a new user account.",
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "A user with this email already exists.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "Request validation failed.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error.",
        },
    },
)
@inject
async def register(
    *,
    request: RegisterUserRq,
    use_case: FromDishka[RegisterUserUc],
) -> CurrentUserRp:
    result = await use_case.act(
        command=map_register_rq_to_cm(request=request),
    )

    return map_user_to_current_rp(user=result.user)


@router.post(
    "/login",
    response_model=LoginRp,
    description="Authenticate a user and issue an access and refresh token.",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Email or password is invalid.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "Request validation failed.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error.",
        },
    },
)
@inject
async def login(
    *,
    response: Response,
    use_case: FromDishka[LoginUc],
    clock: FromDishka[IClock],
    cookie_settings: FromDishka[CookieSettings],
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> LoginRp:
    result = await use_case.act(
        command=LoginCm(email=form.username, password=form.password),
    )
    _set_access_cookie(
        response=response,
        access_token=result.tokens.access_token,
        expires_at=result.tokens.access_expires_at,
        clock=clock,
        settings=cookie_settings,
    )

    return map_login_to_rp(user=result.user, tokens=result.tokens)


@router.post(
    "/refresh",
    response_model=TokenPairRp,
    description="Rotate a refresh token and issue a new token pair.",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Refresh token is invalid or expired.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "Request validation failed.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error.",
        },
    },
)
@inject
async def refresh_tokens(
    *,
    request: RefreshTokenRq,
    response: Response,
    use_case: FromDishka[RefreshTokensUc],
    clock: FromDishka[IClock],
    cookie_settings: FromDishka[CookieSettings],
) -> TokenPairRp:
    result = await use_case.act(
        command=RefreshTokensCm(refresh_token=request.refresh_token),
    )
    _set_access_cookie(
        response=response,
        access_token=result.tokens.access_token,
        expires_at=result.tokens.access_expires_at,
        clock=clock,
        settings=cookie_settings,
    )

    return map_token_pair_to_rp(tokens=result.tokens)


@router.post(
    "/logout",
    response_model=LogoutRp,
    description="Revoke a refresh token when it is active.",
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "Request validation failed.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error.",
        },
    },
)
@inject
async def logout(
    *,
    request: RefreshTokenRq,
    response: Response,
    use_case: FromDishka[LogoutUc],
    cookie_settings: FromDishka[CookieSettings],
) -> LogoutRp:
    await use_case.act(
        command=LogoutCm(refresh_token=request.refresh_token),
    )
    response.delete_cookie(
        key="access_token",
        domain=cookie_settings.domain,
        httponly=True,
        secure=cookie_settings.secure,
        samesite="lax",
    )

    return LogoutRp()
