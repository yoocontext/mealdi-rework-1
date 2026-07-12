from typing import Protocol


class ITransactionManager(Protocol):
    async def commit(self) -> None: ...
