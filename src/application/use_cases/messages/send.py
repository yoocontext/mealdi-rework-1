from dataclasses import dataclass

from application.common.exceptions import SelfMessagingError, UserNotFoundError
from application.common.use_case import BaseUseCase
from application.dto.messages import Message
from application.interfaces.dm.messages import IMessageDm
from application.interfaces.dm.users import IUserDm
from application.interfaces.transaction import ITransactionManager


@dataclass(kw_only=True, frozen=True, slots=True)
class SendMessageCm:
    sender_id: int
    recipient_id: int
    content: str


@dataclass(kw_only=True, frozen=True, slots=True)
class SendMessageRs:
    message: Message


@dataclass(kw_only=True, slots=True)
class SendMessageUc(BaseUseCase[SendMessageCm, SendMessageRs]):
    """Persist a direct message from the authenticated sender.

    Pipeline:
    1. Reject self-messaging and require an existing recipient.
    2. Persist content with the authenticated sender id.
    3. Commit and return the saved message for delivery notification.
    """

    _messages: IMessageDm
    _users: IUserDm
    _transaction: ITransactionManager

    async def act(self, *, command: SendMessageCm) -> SendMessageRs:
        await self._require_recipient(
            sender_id=command.sender_id,
            recipient_id=command.recipient_id,
        )

        message = await self._messages.create(
            sender_id=command.sender_id,
            recipient_id=command.recipient_id,
            content=command.content.strip(),
        )
        await self._transaction.commit()

        return SendMessageRs(message=message)

    async def _require_recipient(self, *, sender_id: int, recipient_id: int) -> None:
        if sender_id == recipient_id:
            raise SelfMessagingError()

        if await self._users.get_by_id(user_id=recipient_id) is None:
            raise UserNotFoundError(role="Recipient")
