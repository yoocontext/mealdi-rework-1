from application.dto.messages import Message
from delivery.api.v1.http.schemas.messages import MessageListRp, MessageRp


def map_message_to_rp(*, message: Message) -> MessageRp:
    return MessageRp(
        id=message.id,
        sender_id=message.sender_id,
        recipient_id=message.recipient_id,
        content=message.content,
        created_at=message.created_at,
    )


def map_messages_to_rp(*, messages: tuple[Message, ...]) -> MessageListRp:
    return MessageListRp(
        items=[map_message_to_rp(message=message) for message in messages],
    )
