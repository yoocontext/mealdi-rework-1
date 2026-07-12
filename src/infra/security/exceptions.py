from abc import ABC
from dataclasses import dataclass

from infra.common.exceptions import InfraError


@dataclass(kw_only=True, slots=True)
class SecurityError(InfraError, ABC):
    """Base error for cryptography and token component failures."""


@dataclass(kw_only=True, slots=True)
class InvalidTokenError(SecurityError):
    @property
    def code(self) -> str:
        return "invalid_token"

    @property
    def message(self) -> str:
        return "Token verification failed"
