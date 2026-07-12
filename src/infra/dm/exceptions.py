from abc import ABC
from dataclasses import dataclass

from infra.common.exceptions import InfraError


@dataclass(kw_only=True, slots=True)
class DmError(InfraError, ABC):
    """Base error for persistence component failures."""


@dataclass(kw_only=True, slots=True)
class SerializationError(DmError):
    entity: str
    identifier: object
    operation: str

    @property
    def message(self) -> str:
        return (
            f"Could not {self.operation} {self.entity} "
            f"with identifier {self.identifier!r}"
        )
