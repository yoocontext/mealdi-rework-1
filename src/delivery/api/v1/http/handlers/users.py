from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter

from application.use_cases.users import GetUserCm, GetUserUc, ListUsersCm, ListUsersUc
from delivery.api.v1.http.dependencies import CurrentUser
from delivery.api.v1.http.mappers.users import (
    map_user_to_current_rp,
    map_user_to_public_rp,
)
from delivery.api.v1.http.schemas.users import CurrentUserRp, PublicUserRp

router = APIRouter(prefix="/api/v1/http/users", tags=["users"])


@router.get("/me", response_model=CurrentUserRp)
async def get_me(*, current_user: CurrentUser) -> CurrentUserRp:
    return map_user_to_current_rp(user=current_user)


@router.get("", response_model=list[PublicUserRp])
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


@router.get("/{user_id}", response_model=PublicUserRp)
@inject
async def get_user(
    *,
    user_id: int,
    use_case: FromDishka[GetUserUc],
) -> PublicUserRp:
    result = await use_case.act(command=GetUserCm(user_id=user_id))

    return map_user_to_public_rp(user=result.user)
