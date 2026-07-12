from dataclasses import dataclass

from application.common.use_case import BaseUseCase
from application.dto.users import User
from application.interfaces.dm.users import IUserDm


@dataclass(kw_only=True, frozen=True, slots=True)
class ListUsersCm:
    current_user_id: int


@dataclass(kw_only=True, frozen=True, slots=True)
class ListUsersRs:
    users: tuple[User, ...]


@dataclass(kw_only=True, slots=True)
class ListUsersUc(BaseUseCase[ListUsersCm, ListUsersRs]):
    """List chat candidates other than the current user, ordered by name."""

    _users: IUserDm

    async def act(self, *, command: ListUsersCm) -> ListUsersRs:
        # Return only valid conversation candidates for the current user.
        users = await self._users.list_except(user_id=command.current_user_id)
        return ListUsersRs(users=users)
