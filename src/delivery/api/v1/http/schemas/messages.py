from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SendMessageRq(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    recipient_id: int = Field(gt=0)
    content: str = Field(min_length=1, max_length=4000)


class MessageRp(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    content: str
    created_at: datetime


class MessageListRp(BaseModel):
    items: list[MessageRp]
