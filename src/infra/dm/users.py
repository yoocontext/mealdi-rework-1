from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from application.common.exceptions import EmailAlreadyExistsError
from application.dto.users import User
from application.interfaces.dm.users import IUserDm
from infra.common.transaction import TransactionManager
from infra.dm.mappers.users import map_user
from infra.orm.users import UserOrm


@dataclass(kw_only=True, slots=True)
class UserDm(IUserDm):
    _tm: TransactionManager

    async def get_by_id(self, *, user_id: int) -> User | None:
        orm = await self._tm.get(entity=UserOrm, identifier=user_id)

        return None if orm is None else map_user(orm=orm)

    async def get_by_email(self, *, email: str) -> User | None:
        query = select(UserOrm).where(UserOrm.email == email)
        result = await self._tm.execute(
            statement=query,
        )
        orm = result.scalar_one_or_none()

        return None if orm is None else map_user(orm=orm)

    async def list_except(self, *, user_id: int) -> tuple[User, ...]:
        query = (
            select(UserOrm)
            .where(UserOrm.id != user_id)
            .order_by(UserOrm.name, UserOrm.id)
        )

        result = await self._tm.scalars(statement=query)

        return tuple(map_user(orm=orm) for orm in result)

    async def create(
        self,
        *,
        email: str,
        name: str,
        password_hash: str,
    ) -> User:
        orm = UserOrm(email=email, name=name, password_hash=password_hash)

        self._tm.add(instance=orm)
        try:
            await self._tm.flush(instances=[orm])
        except IntegrityError as exc:
            raise EmailAlreadyExistsError() from exc

        await self._tm.refresh(instance=orm)

        return map_user(orm=orm)
