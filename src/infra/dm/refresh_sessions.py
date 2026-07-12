from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select

from application.dto.auth import RefreshSession
from application.interfaces.dm.refresh_sessions import IRefreshSessionDm
from infra.common.transaction import TransactionManager
from infra.dm.exceptions import SerializationError
from infra.dm.mappers.refresh_sessions import map_refresh_session
from infra.orm.refresh_sessions import RefreshSessionOrm


@dataclass(kw_only=True, slots=True)
class RefreshSessionDm(IRefreshSessionDm):
    _tm: TransactionManager

    async def get_by_hash(
        self,
        *,
        token_hash: str,
        for_update: bool = False,
    ) -> RefreshSession | None:
        query = select(RefreshSessionOrm).where(
            RefreshSessionOrm.token_hash == token_hash,
        )
        if for_update:
            query = query.with_for_update()

        result = await self._tm.execute(statement=query)
        orm = result.scalar_one_or_none()

        return None if orm is None else map_refresh_session(orm=orm)

    async def create(
        self,
        *,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshSession:
        orm = RefreshSessionOrm(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self._tm.add(instance=orm)
        await self._tm.flush(instances=[orm])
        await self._tm.refresh(instance=orm)

        return map_refresh_session(orm=orm)

    async def save(self, *, session: RefreshSession) -> RefreshSession:
        orm = await self._tm.get(
            entity=RefreshSessionOrm,
            identifier=session.id,
        )
        if orm is None:
            raise SerializationError(
                entity="refresh session",
                identifier=session.id,
                operation="save",
            )

        orm.revoked_at = session.revoked_at
        await self._tm.flush(instances=[orm])

        return map_refresh_session(orm=orm)
