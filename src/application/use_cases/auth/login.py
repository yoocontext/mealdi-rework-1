from dataclasses import dataclass
from datetime import timedelta

from application.common.exceptions import InvalidCredentialsError
from application.common.use_case import BaseUseCase
from application.dto.auth import TokenPair
from application.dto.users import User
from application.interfaces.clock import IClock
from application.interfaces.dm.refresh_sessions import IRefreshSessionDm
from application.interfaces.dm.users import IUserDm
from application.interfaces.security import IPasswordHasher, ITokenService
from application.interfaces.transaction import ITransactionManager


@dataclass(kw_only=True, frozen=True, slots=True)
class LoginCm:
    email: str
    password: str


@dataclass(kw_only=True, frozen=True, slots=True)
class LoginRs:
    user: User
    tokens: TokenPair


@dataclass(kw_only=True, slots=True)
class LoginUc(BaseUseCase[LoginCm, LoginRs]):
    """Authenticate a user and create a refresh session.

    Pipeline:
    1. Load the normalized email and verify its password.
    2. Issue an access token and opaque refresh token.
    3. Persist only the refresh-token digest, commit, and return both tokens.

    Edge cases:
    - Unknown email and bad password have the same public error.
    """

    _users: IUserDm
    _sessions: IRefreshSessionDm
    _passwords: IPasswordHasher
    _tokens: ITokenService
    _clock: IClock
    _transaction: ITransactionManager
    _refresh_ttl: timedelta

    async def act(self, *, command: LoginCm) -> LoginRs:
        user = await self._authenticate(
            email=command.email,
            password=command.password,
        )
        tokens = await self._open_session(user_id=user.id)

        await self._transaction.commit()

        return LoginRs(user=user, tokens=tokens)

    async def _authenticate(self, *, email: str, password: str) -> User:
        user = await self._users.get_by_email(email=email.strip().casefold())
        if user is None:
            self._passwords.verify_dummy(password=password)
            raise InvalidCredentialsError()

        if not self._passwords.verify(
            password=password,
            password_hash=user.password_hash,
        ):
            raise InvalidCredentialsError()

        return user

    async def _open_session(self, *, user_id: int) -> TokenPair:
        access = self._tokens.issue_access(user_id=user_id)
        refresh_token = self._tokens.create_refresh()
        refresh_expires_at = self._clock.now() + self._refresh_ttl

        await self._sessions.create(
            user_id=user_id,
            token_hash=self._tokens.hash_refresh(token=refresh_token),
            expires_at=refresh_expires_at,
        )

        return TokenPair(
            access_token=access.value,
            refresh_token=refresh_token,
            access_expires_at=access.expires_at,
            refresh_expires_at=refresh_expires_at,
        )
