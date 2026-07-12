from dataclasses import dataclass
from datetime import datetime


@dataclass(kw_only=True, frozen=True, slots=True)
class Message:
    id: int
    sender_id: int
    recipient_id: int
    content: str
    created_at: datetime
