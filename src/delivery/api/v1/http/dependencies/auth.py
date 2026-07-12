from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Cookie, Depends
from fastapi.security import OAuth2PasswordBearer

from application.dto.users import User
from application.use_cases.auth import AuthenticateCm, AuthenticateUc

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/http/auth/login",
    auto_error=False,
)


@inject
async def get_current_user(
    *,
    authenticate: FromDishka[AuthenticateUc],
    bearer_token: Annotated[str | None, Depends(oauth2_scheme)] = None,
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    result = await authenticate.act(
        command=AuthenticateCm(
            access_token=bearer_token or access_token or "",
        ),
    )

    return result.user


CurrentUser = Annotated[User, Depends(get_current_user)]
