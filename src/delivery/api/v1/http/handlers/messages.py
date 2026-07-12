from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Query, status

from application.use_cases.messages import (
    ListMessagesCm,
    ListMessagesUc,
    SendMessageCm,
    SendMessageUc,
)
from delivery.api.v1.http.dependencies import CurrentUser
from delivery.api.v1.http.mappers.messages import (
    map_message_to_rp,
    map_messages_to_rp,
)
from delivery.api.v1.http.schemas.errors import ErrorResponse
from delivery.api.v1.http.schemas.messages import (
    MessageListRp,
    MessageRp,
    SendMessageRq,
)
from delivery.common.connections import MessageConnections

router = APIRouter(prefix="/api/v1/http/messages", tags=["messages"])


@router.get(
    "/{peer_id}",
    response_model=MessageListRp,
    description="List the authenticated user's conversation with another user.",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Access token is missing or invalid.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Conversation peer was not found.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "Path or query parameters are invalid.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error.",
        },
    },
)
@inject
async def list_messages(
    *,
    peer_id: int,
    current_user: CurrentUser,
    use_case: FromDishka[ListMessagesUc],
    limit: int = Query(default=100, ge=1, le=100),
    before_id: int | None = Query(default=None, gt=0),
) -> MessageListRp:
    result = await use_case.act(
        command=ListMessagesCm(
            current_user_id=current_user.id,
            peer_id=peer_id,
            limit=limit,
            before_id=before_id,
        ),
    )

    return map_messages_to_rp(messages=result.messages)


@router.post(
    "",
    response_model=MessageRp,
    status_code=status.HTTP_201_CREATED,
    description="Send a direct message to another user.",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Access token is missing or invalid.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "A user cannot send a message to themselves.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Message recipient was not found.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "Request validation failed.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error.",
        },
    },
)
@inject
async def send_message(
    *,
    request: SendMessageRq,
    current_user: CurrentUser,
    use_case: FromDishka[SendMessageUc],
    connections: FromDishka[MessageConnections],
) -> MessageRp:
    result = await use_case.act(
        command=SendMessageCm(
            sender_id=current_user.id,
            recipient_id=request.recipient_id,
            content=request.content,
        ),
    )
    response = map_message_to_rp(message=result.message)
    await connections.publish(
        user_ids={result.message.sender_id, result.message.recipient_id},
        payload={
            "type": "message.created",
            "data": response.model_dump(mode="json"),
        },
    )

    return response
