from dataclasses import dataclass

from application.common.exceptions import UserNotFoundError
from application.common.use_case import BaseUseCase
from application.dto.users import User
from application.interfaces.dm.users import IUserDm


@dataclass(kw_only=True, frozen=True, slots=True)
class GetUserCm:
    user_id: int


@dataclass(kw_only=True, frozen=True, slots=True)
class GetUserRs:
    user: User


@dataclass(kw_only=True, slots=True)
class GetUserUc(BaseUseCase[GetUserCm, GetUserRs]):
    """Load a public profile or report a missing user."""

    _users: IUserDm

    async def act(self, *, command: GetUserCm) -> GetUserRs:
        # Resolve the requested public profile explicitly.
        user = await self._users.get_by_id(user_id=command.user_id)
        if user is None:
            raise UserNotFoundError()

        return GetUserRs(user=user)
