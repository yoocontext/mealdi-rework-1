from dataclasses import dataclass

from application.common.exceptions import UserNotFoundError
from application.common.use_case import BaseUseCase
from application.dto.messages import Message
from application.interfaces.dm.messages import IMessageDm
from application.interfaces.dm.users import IUserDm


@dataclass(kw_only=True, frozen=True, slots=True)
class ListMessagesCm:
    current_user_id: int
    peer_id: int
    limit: int = 100
    before_id: int | None = None


@dataclass(kw_only=True, frozen=True, slots=True)
class ListMessagesRs:
    messages: tuple[Message, ...]


@dataclass(kw_only=True, slots=True)
class ListMessagesUc(BaseUseCase[ListMessagesCm, ListMessagesRs]):
    """Load a bounded private conversation with an existing peer."""

    _messages: IMessageDm
    _users: IUserDm

    async def act(self, *, command: ListMessagesCm) -> ListMessagesRs:
        # A conversation can only be addressed to an existing peer.
        if await self._users.get_by_id(user_id=command.peer_id) is None:
            raise UserNotFoundError()

        # Load only the authenticated user's bounded chronological window.
        messages = await self._messages.list_conversation(
            first_user_id=command.current_user_id,
            second_user_id=command.peer_id,
            limit=command.limit,
            before_id=command.before_id,
        )

        return ListMessagesRs(messages=messages)
