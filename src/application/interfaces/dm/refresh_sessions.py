from datetime import datetime
from typing import Protocol

from application.dto.auth import RefreshSession


class IRefreshSessionDm(Protocol):
    async def get_by_hash(
        self,
        *,
        token_hash: str,
        for_update: bool = False,
    ) -> RefreshSession | None: ...

    async def create(
        self,
        *,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshSession: ...

    async def save(self, *, session: RefreshSession) -> RefreshSession: ...
