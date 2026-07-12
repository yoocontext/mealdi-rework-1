from application.dto.users import User
from application.use_cases.auth import RegisterUserCm
from delivery.api.v1.http.schemas.users import (
    CurrentUserRp,
    PublicUserRp,
    RegisterUserRq,
)


def map_register_rq_to_cm(*, request: RegisterUserRq) -> RegisterUserCm:
    return RegisterUserCm(
        email=str(request.email),
        name=request.name,
        password=request.password,
    )


def map_user_to_public_rp(*, user: User) -> PublicUserRp:
    return PublicUserRp(
        id=user.id,
        name=user.name,
        created_at=user.created_at,
    )


def map_user_to_current_rp(*, user: User) -> CurrentUserRp:
    return CurrentUserRp(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
    )
