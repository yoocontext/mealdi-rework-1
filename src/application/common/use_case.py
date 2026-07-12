from abc import ABC, abstractmethod


class BaseUseCase[CommandT, ResultT](ABC):
    @abstractmethod
    async def act(self, *, command: CommandT) -> ResultT:
        raise NotImplementedError
