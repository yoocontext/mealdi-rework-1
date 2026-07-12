from application.dto.messages import Message
from infra.common.datetime import as_utc
from infra.orm.messages import MessageOrm


def map_message(*, orm: MessageOrm) -> Message:
    return Message(
        id=orm.id,
        sender_id=orm.sender_id,
        recipient_id=orm.recipient_id,
        content=orm.content,
        created_at=as_utc(value=orm.created_at),
    )
