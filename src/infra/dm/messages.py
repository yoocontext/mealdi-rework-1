from dataclasses import dataclass

from sqlalchemy import and_, or_, select

from application.dto.messages import Message
from application.interfaces.dm.messages import IMessageDm
from infra.common.transaction import TransactionManager
from infra.dm.mappers.messages import map_message
from infra.orm.messages import MessageOrm


@dataclass(kw_only=True, slots=True)
class MessageDm(IMessageDm):
    _tm: TransactionManager

    async def list_conversation(
        self,
        *,
        first_user_id: int,
        second_user_id: int,
        limit: int = 100,
        before_id: int | None = None,
    ) -> tuple[Message, ...]:
        query = select(MessageOrm).where(
            or_(
                and_(
                    MessageOrm.sender_id == first_user_id,
                    MessageOrm.recipient_id == second_user_id,
                ),
                and_(
                    MessageOrm.sender_id == second_user_id,
                    MessageOrm.recipient_id == first_user_id,
                ),
            ),
        )
        if before_id is not None:
            query = query.where(MessageOrm.id < before_id)

        newest_first = (
            await self._tm.scalars(
                statement=query.order_by(MessageOrm.id.desc()).limit(limit),
            )
        ).all()
        return tuple(map_message(orm=orm) for orm in reversed(newest_first))

    async def create(
        self,
        *,
        sender_id: int,
        recipient_id: int,
        content: str,
    ) -> Message:
        orm = MessageOrm(
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=content,
        )

        self._tm.add(instance=orm)
        await self._tm.flush(instances=[orm])
        await self._tm.refresh(instance=orm)

        return map_message(orm=orm)
