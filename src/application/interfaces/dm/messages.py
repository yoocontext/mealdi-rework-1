from typing import Protocol

from application.dto.messages import Message


class IMessageDm(Protocol):
    async def list_conversation(
        self,
        *,
        first_user_id: int,
        second_user_id: int,
        limit: int = 100,
        before_id: int | None = None,
    ) -> tuple[Message, ...]: ...

    async def create(
        self,
        *,
        sender_id: int,
        recipient_id: int,
        content: str,
    ) -> Message: ...
