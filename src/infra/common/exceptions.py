from abc import ABC
from dataclasses import dataclass

from application.common.exceptions import AppError


@dataclass(kw_only=True, slots=True)
class InfraError(AppError, ABC):
    """Base error for infrastructure failures understood by the project."""
