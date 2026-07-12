from dataclasses import dataclass
from datetime import datetime


@dataclass(kw_only=True, frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime


@dataclass(kw_only=True, frozen=True, slots=True)
class RefreshSession:
    id: int
    user_id: int
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime
