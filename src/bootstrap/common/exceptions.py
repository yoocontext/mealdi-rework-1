from abc import ABC
from dataclasses import dataclass

from application.common.exceptions import AppError


@dataclass(kw_only=True, slots=True)
class BootstrapError(AppError, ABC):
    """Base error for application assembly and process startup failures."""
