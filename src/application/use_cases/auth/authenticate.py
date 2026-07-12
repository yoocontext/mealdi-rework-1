from dataclasses import dataclass

from application.common.exceptions import InvalidAccessTokenError
from application.common.use_case import BaseUseCase
from application.dto.users import User
from application.interfaces.dm.users import IUserDm
from application.interfaces.security import ITokenService


@dataclass(kw_only=True, frozen=True, slots=True)
class AuthenticateCm:
    access_token: str


@dataclass(kw_only=True, frozen=True, slots=True)
class AuthenticateRs:
    user: User


@dataclass(kw_only=True, slots=True)
class AuthenticateUc(BaseUseCase[AuthenticateCm, AuthenticateRs]):
    """Resolve a valid access token to an existing user.

    Pipeline:
    1. Verify and decode the signed access token.
    2. Load its user and return the application DTO.

    Edge cases:
    - Invalid tokens and deleted users are authentication failures.
    """

    _users: IUserDm
    _tokens: ITokenService

    async def act(self, *, command: AuthenticateCm) -> AuthenticateRs:
        user_id = self._tokens.read_access_subject(token=command.access_token)

        user = await self._users.get_by_id(user_id=user_id)
        if user is None:
            raise InvalidAccessTokenError()

        return AuthenticateRs(user=user)
