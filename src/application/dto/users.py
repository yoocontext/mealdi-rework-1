from dataclasses import dataclass
from datetime import datetime


@dataclass(kw_only=True, frozen=True, slots=True)
class User:
    id: int
    email: str
    name: str
    password_hash: str
    created_at: datetime
