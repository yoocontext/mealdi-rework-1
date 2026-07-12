from collections.abc import AsyncIterator
from datetime import timedelta

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from application.interfaces.clock import IClock
from application.interfaces.dm.likes import ILikeDm
from application.interfaces.dm.messages import IMessageDm
from application.interfaces.dm.posts import IPostDm
from application.interfaces.dm.refresh_sessions import IRefreshSessionDm
from application.interfaces.dm.users import IUserDm
from application.interfaces.security import IPasswordHasher, ITokenService
from application.interfaces.transaction import ITransactionManager
from bootstrap.settings import Settings
from infra.common.clock import SystemClock
from infra.common.transaction import TransactionManager
from infra.dm.likes import LikeDm
from infra.dm.messages import MessageDm
from infra.dm.posts import PostDm
from infra.dm.refresh_sessions import RefreshSessionDm
from infra.dm.users import UserDm
from infra.security.passwords import Argon2PasswordHasher
from infra.security.tokens import JwtTokenService


class InfraProvider(Provider):
    @provide(scope=Scope.APP)
    async def engine(self, *, settings: Settings) -> AsyncIterator[AsyncEngine]:
        engine = create_async_engine(
            settings.database_url,
            echo=settings.sql_echo,
            pool_pre_ping=True,
        )
        try:
            yield engine
        finally:
            await engine.dispose()

    @provide(scope=Scope.APP)
    def session_factory(
        self,
        *,
        engine: AsyncEngine,
    ) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, autoflush=False, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def session(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    @provide(scope=Scope.APP)
    def clock(self) -> IClock:
        return SystemClock()

    @provide(scope=Scope.APP)
    def password_hasher(self) -> IPasswordHasher:
        return Argon2PasswordHasher()

    @provide(scope=Scope.APP)
    def token_service(
        self,
        *,
        settings: Settings,
        clock: IClock,
    ) -> ITokenService:
        return JwtTokenService(
            secret=settings.jwt_secret,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            access_ttl=timedelta(minutes=settings.access_token_ttl_minutes),
            clock=clock,
        )

    @provide(scope=Scope.REQUEST)
    def transaction(self, *, session: AsyncSession) -> TransactionManager:
        return TransactionManager(_session=session)

    @provide(scope=Scope.REQUEST)
    def application_transaction(
        self,
        *,
        transaction: TransactionManager,
    ) -> ITransactionManager:
        return transaction

    @provide(scope=Scope.REQUEST)
    def users(self, *, transaction: TransactionManager) -> IUserDm:
        return UserDm(_tm=transaction)

    @provide(scope=Scope.REQUEST)
    def posts(self, *, transaction: TransactionManager) -> IPostDm:
        return PostDm(_tm=transaction)

    @provide(scope=Scope.REQUEST)
    def likes(self, *, transaction: TransactionManager) -> ILikeDm:
        return LikeDm(_tm=transaction)

    @provide(scope=Scope.REQUEST)
    def messages(self, *, transaction: TransactionManager) -> IMessageDm:
        return MessageDm(_tm=transaction)

    @provide(scope=Scope.REQUEST)
    def refresh_sessions(
        self,
        *,
        transaction: TransactionManager,
    ) -> IRefreshSessionDm:
        return RefreshSessionDm(_tm=transaction)
