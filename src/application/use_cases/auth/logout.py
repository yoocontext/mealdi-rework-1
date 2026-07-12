from dataclasses import dataclass, replace

from application.common.use_case import BaseUseCase
from application.interfaces.clock import IClock
from application.interfaces.dm.refresh_sessions import IRefreshSessionDm
from application.interfaces.security import ITokenService
from application.interfaces.transaction import ITransactionManager


@dataclass(kw_only=True, frozen=True, slots=True)
class LogoutCm:
    refresh_token: str


@dataclass(kw_only=True, frozen=True, slots=True)
class LogoutRs:
    revoked: bool


@dataclass(kw_only=True, slots=True)
class LogoutUc(BaseUseCase[LogoutCm, LogoutRs]):
    """Revoke a refresh session without exposing whether a token existed.

    Pipeline:
    1. Resolve the refresh-token digest.
    2. Revoke an active session and commit.
    3. Return whether persisted state changed.

    Edge cases:
    - Unknown or already revoked tokens are idempotent no-ops.
    """

    _sessions: IRefreshSessionDm
    _tokens: ITokenService
    _clock: IClock
    _transaction: ITransactionManager

    async def act(self, *, command: LogoutCm) -> LogoutRs:
        # Lock the presented session so revocation stays idempotent under races.
        token_hash = self._tokens.hash_refresh(token=command.refresh_token)
        session = await self._sessions.get_by_hash(
            token_hash=token_hash,
            for_update=True,
        )
        if session is None or session.revoked_at is not None:
            return LogoutRs(revoked=False)

        # Persist revocation as the only state change of logout.
        await self._sessions.save(
            session=replace(session, revoked_at=self._clock.now()),
        )
        await self._transaction.commit()

        return LogoutRs(revoked=True)
