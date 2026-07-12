from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from application.common.exceptions import InvalidRefreshTokenError
from application.common.use_case import BaseUseCase
from application.dto.auth import RefreshSession, TokenPair
from application.interfaces.clock import IClock
from application.interfaces.dm.refresh_sessions import IRefreshSessionDm
from application.interfaces.dm.users import IUserDm
from application.interfaces.security import ITokenService
from application.interfaces.transaction import ITransactionManager


@dataclass(kw_only=True, frozen=True, slots=True)
class RefreshTokensCm:
    refresh_token: str


@dataclass(kw_only=True, frozen=True, slots=True)
class RefreshTokensRs:
    tokens: TokenPair


@dataclass(kw_only=True, slots=True)
class RefreshTokensUc(BaseUseCase[RefreshTokensCm, RefreshTokensRs]):
    """Rotate a valid refresh session and issue a new token pair.

    Pipeline:
    1. Resolve the opaque token by its digest.
    2. Validate session status, expiry, and owning user.
    3. Revoke the old session, create its replacement, and commit atomically.
    4. Return a fresh access/refresh pair.

    Edge cases:
    - Missing, revoked, expired, and orphaned sessions are rejected.
    """

    _sessions: IRefreshSessionDm
    _users: IUserDm
    _tokens: ITokenService
    _clock: IClock
    _transaction: ITransactionManager
    _refresh_ttl: timedelta

    async def act(self, *, command: RefreshTokensCm) -> RefreshTokensRs:
        now = self._clock.now()
        session = await self._consume_session(
            refresh_token=command.refresh_token,
            now=now,
        )
        tokens = await self._create_replacement(
            user_id=session.user_id,
            now=now,
        )

        await self._transaction.commit()

        return RefreshTokensRs(tokens=tokens)

    async def _consume_session(
        self,
        *,
        refresh_token: str,
        now: datetime,
    ) -> RefreshSession:
        token_hash = self._tokens.hash_refresh(token=refresh_token)
        found_session = await self._sessions.get_by_hash(
            token_hash=token_hash,
            for_update=True,
        )
        session = self._require_active(session=found_session, now=now)

        if await self._users.get_by_id(user_id=session.user_id) is None:
            raise InvalidRefreshTokenError()

        await self._sessions.save(session=replace(session, revoked_at=now))

        return session

    def _require_active(
        self,
        *,
        session: RefreshSession | None,
        now: datetime,
    ) -> RefreshSession:
        if session is None:
            raise InvalidRefreshTokenError()
        if session.revoked_at is not None:
            raise InvalidRefreshTokenError()
        if session.expires_at <= now:
            raise InvalidRefreshTokenError()

        return session

    async def _create_replacement(self, *, user_id: int, now: datetime) -> TokenPair:
        refresh_token = self._tokens.create_refresh()
        refresh_expires_at = now + self._refresh_ttl

        await self._sessions.create(
            user_id=user_id,
            token_hash=self._tokens.hash_refresh(token=refresh_token),
            expires_at=refresh_expires_at,
        )

        access = self._tokens.issue_access(user_id=user_id)

        return TokenPair(
            access_token=access.value,
            refresh_token=refresh_token,
            access_expires_at=access.expires_at,
            refresh_expires_at=refresh_expires_at,
        )
