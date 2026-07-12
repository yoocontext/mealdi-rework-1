from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, TypeVar

from sqlalchemy import Executable
from sqlalchemy.engine import Result, ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from application.interfaces.transaction import ITransactionManager

OrmT = TypeVar("OrmT")


@dataclass(kw_only=True, slots=True)
class TransactionManager(ITransactionManager):
    """Own the SQLAlchemy session and expose persistence operations to infra."""

    _session: AsyncSession

    def add(self, *, instance: object) -> None:
        self._session.add(instance)

    def add_all(self, *, instances: Iterable[object]) -> None:
        self._session.add_all(list(instances))

    async def delete(self, *, instance: object) -> None:
        await self._session.delete(instance)

    async def flush(self, *, instances: Iterable[object] | None = None) -> None:
        objects = None if instances is None else list(instances)
        await self._session.flush(objects=objects)

    async def refresh(self, *, instance: object) -> None:
        await self._session.refresh(instance)

    async def get(
        self,
        *,
        entity: type[OrmT],
        identifier: object,
    ) -> OrmT | None:
        return await self._session.get(entity, identifier)

    async def execute(self, *, statement: Executable) -> Result[Any]:
        return await self._session.execute(statement)

    async def scalars(self, *, statement: Executable) -> ScalarResult[Any]:
        return await self._session.scalars(statement)

    async def scalar(self, *, statement: Executable) -> Any:
        return await self._session.scalar(statement)

    async def commit(self) -> None:
        await self._session.commit()
