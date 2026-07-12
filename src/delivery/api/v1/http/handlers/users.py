from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, status

from application.use_cases.users import GetUserCm, GetUserUc, ListUsersCm, ListUsersUc
from delivery.api.v1.http.dependencies import CurrentUser
from delivery.api.v1.http.mappers.users import (
    map_user_to_current_rp,
    map_user_to_public_rp,
)
from delivery.api.v1.http.schemas.errors import ErrorResponse
from delivery.api.v1.http.schemas.users import CurrentUserRp, PublicUserRp

router = APIRouter(prefix="/api/v1/http/users", tags=["users"])


@router.get(
    "/me",
    response_model=CurrentUserRp,
    description="Return the authenticated user's profile.",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Access token is missing or invalid.",
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
async def get_me(*, current_user: CurrentUser) -> CurrentUserRp:
    return map_user_to_current_rp(user=current_user)


@router.get(
    "",
    response_model=list[PublicUserRp],
    description="List users available for a conversation.",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Access token is missing or invalid.",
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
async def list_users(
    *,
    current_user: CurrentUser,
    use_case: FromDishka[ListUsersUc],
) -> list[PublicUserRp]:
    result = await use_case.act(
        command=ListUsersCm(current_user_id=current_user.id),
    )

    return [map_user_to_public_rp(user=user) for user in result.users]


@router.get(
    "/{user_id}",
    response_model=PublicUserRp,
    description="Return a user's public profile.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "User was not found.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "Path parameter is invalid.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error.",
        },
    },
)
@inject
async def get_user(
    *,
    user_id: int,
    use_case: FromDishka[GetUserUc],
) -> PublicUserRp:
    result = await use_case.act(command=GetUserCm(user_id=user_id))

    return map_user_to_public_rp(user=result.user)
